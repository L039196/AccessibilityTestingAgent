import asyncio
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser
from tqdm import tqdm

from .local_analyzer import LocalAnalyzer
from .reporter import ReportGenerator
from .crawler import Crawler

@dataclass
class Config:
    """Configuration for the accessibility agent."""
    base_url: str
    max_pages: int = 10
    browser_types: List[str] = field(default_factory=lambda: ['chromium', 'webkit'])
    device_types: List[str] = field(default_factory=lambda: ['desktop'])
    report_filename: str = "accessibility_report.md"
    report_format: str = "md"
    results_folder: str = "results"
    axe_rules: Optional[Dict[str, Any]] = None
    device_profiles: Optional[Dict[str, Any]] = None

class Agent:
    """
    The core accessibility testing agent.
    It crawls a website, analyzes pages for accessibility issues, and generates a report.
    """
    def __init__(self, config: Config, crawler: "Crawler", analyzer: "LocalAnalyzer", reporter: "ReportGenerator", urls_to_test: Optional[List[str]] = None):
        self.config = config
        self.crawler = crawler
        self.analyzer = analyzer
        self.reporter = reporter
        self.results: Dict[str, List[Dict[str, Any]]] = {}  # Device type -> results
        self.pre_defined_urls = urls_to_test
        
        # Initialize results for each device type
        for device_type in self.config.device_types:
            self.results[device_type] = []

    async def run(self):
        """
        Runs the accessibility test suite across different device types.
        """
        print("Starting Automated Accessibility Test Agent...")
        
        async with async_playwright() as p:
            urls_to_test = self.pre_defined_urls
            if not urls_to_test:
                # 1. Crawl the website to get all URLs if not provided
                print("No URLs provided, starting crawler...")
                urls_to_test = await self._crawl(p)
            else:
                print(f"Using {len(urls_to_test)} URLs provided via CSV.")

            if not urls_to_test:
                print("No pages found to test. Exiting.")
                return

            # Run tests for each device type
            for device_type in self.config.device_types:
                print(f"\n=== Testing on {device_type.upper()} devices ===")
                
                # Add progress bar
                with tqdm(total=len(urls_to_test), desc=f"Analyzing Pages ({device_type})") as pbar:
                    # 2. Set up and run tests in parallel for this device type
                    await self._run_tests_for_device_type(p, urls_to_test, device_type, pbar)

            # 3. Consolidate and save the reports
            self._save_reports()
            
            print("Agent finished.")

    async def _crawl(self, playwright_instance) -> List[str]:
        """Crawl the website to find all pages to test."""
        print("Launching crawler browser...")
        crawler_browser = await playwright_instance.chromium.launch(headless=True)
        page = await crawler_browser.new_page()
        try:
            urls = await self.crawler.crawl(page)
            print(f"\nFound {len(urls)} pages to test.")
            return urls
        finally:
            await page.close()
            await crawler_browser.close()
            print("Crawler browser closed.")

    async def _run_tests_for_device_type(self, playwright_instance, urls: List[str], device_type: str, pbar: "tqdm"):
        """Launch browsers and run tests in parallel for a specific device type."""
        url_queue = asyncio.Queue()
        for url in urls:
            await url_queue.put(url)

        print(f"Launching browsers for {device_type} testing...")
        browsers = await self._launch_browsers_for_device(playwright_instance, device_type)
        if not browsers:
            print(f"No browsers were launched successfully for {device_type}. Skipping.")
            return

        tasks = []
        for i, (browser, device_config) in enumerate(browsers):
            # Since we're using the same browser type (chromium), create descriptive worker names
            browser_name = 'chromium'  # We're now using only chromium for consistency
            
            # Parse device type to find device name
            if device_type.startswith('mobile-'):
                form_factor = 'mobile'
                platform = device_type.replace('mobile-', '')
            elif device_type.startswith('tablet-'):
                form_factor = 'tablet'
                platform = device_type.replace('tablet-', '')
            else:
                form_factor = device_type
                platform = None
            
            # Get device profiles
            if platform:
                device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
            else:
                device_profiles = self.config.device_profiles.get(form_factor, {})
                
            device_name = next(name for name, config in device_profiles.items() if config == device_config)
            worker_name = f"worker-{i+1}-{browser_name}-{device_name.replace(' ', '_')}"
            task = asyncio.create_task(self._worker_for_device(worker_name, browser, device_config, device_type, url_queue, pbar))
            tasks.append(task)

        await url_queue.join()

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        print("Closing browsers...")
        await asyncio.gather(*[b[0].close() for b in browsers])

    async def _launch_browsers_for_device(self, playwright_instance, device_type: str) -> List[tuple]:
        """Launches browsers with device emulation for the specified device type."""
        browsers = []
        
        # Parse device type to determine form factor and platform
        if device_type.startswith('mobile-'):
            form_factor = 'mobile'
            platform = device_type.replace('mobile-', '')
        elif device_type.startswith('tablet-'):
            form_factor = 'tablet'
            platform = device_type.replace('tablet-', '')
        else:
            # Desktop case
            form_factor = device_type
            platform = None
        
        # Get device profiles
        if platform:
            device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
        else:
            device_profiles = self.config.device_profiles.get(form_factor, {})
        
        if not device_profiles:
            print(f"No device profiles found for {device_type}")
            return browsers

        # Use only one browser type (chromium) but launch multiple instances for parallel processing
        # This is more efficient and consistent than mixing different browser engines
        preferred_browser = 'chromium'  # Most reliable and widely supported
        
        # Launch multiple browser instances for parallel processing
        # Create one browser instance per device for better parallelization
        for device_name, device_config in device_profiles.items():
            try:
                print(f"Launching {preferred_browser} instance for {device_name} emulation...")
                # Launch browser with device context
                browser = await getattr(playwright_instance, preferred_browser).launch(headless=True)
                browsers.append((browser, device_config))
            except Exception as e:
                print(f"!!! Could not launch {preferred_browser} with {device_name}: {e}")
                
        # If we want even more parallelization, we can launch additional workers
        # This creates multiple worker instances for the same devices to process URLs faster
        additional_workers = min(2, len(device_profiles))  # Max 2 additional workers per device
        for i in range(additional_workers):
            for device_name, device_config in list(device_profiles.items())[:2]:  # Limit to 2 most important devices
                try:
                    print(f"Launching additional {preferred_browser} worker #{i+1} for {device_name}...")
                    browser = await getattr(playwright_instance, preferred_browser).launch(headless=True)
                    browsers.append((browser, device_config))
                except Exception as e:
                    print(f"!!! Could not launch additional {preferred_browser} worker: {e}")
                    
        return browsers

    async def _worker_for_device(self, name: str, browser: Browser, device_config: Dict[str, Any], device_type: str, queue: asyncio.Queue, pbar: "tqdm"):
        """A worker that processes URLs from a queue with device emulation."""
        print(f"[{name}] starting...")
        while not queue.empty():
            try:
                url = await queue.get()
                report = await self._analyze_page_with_device(browser, url, device_config, device_type)
                self.results[device_type].append(report)
                pbar.update(1)
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{name}] encountered an error: {e}")
                queue.task_done()
        print(f"[{name}] finished.")

    async def _analyze_page_with_device(self, browser: Browser, url: str, device_config: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """Analyzes a single page with device emulation and returns a report."""
        # Create a new context with device emulation
        context = await browser.new_context(
            viewport=device_config['viewport'],
            user_agent=device_config['userAgent'],
            device_scale_factor=device_config.get('deviceScaleFactor', 1),
            is_mobile=device_config.get('isMobile', False),
            has_touch=device_config.get('hasTouch', False)
        )
        
        page = await context.new_page()
        try:
            # Parse device type to find device name
            if device_type.startswith('mobile-'):
                form_factor = 'mobile'
                platform = device_type.replace('mobile-', '')
            elif device_type.startswith('tablet-'):
                form_factor = 'tablet'
                platform = device_type.replace('tablet-', '')
            else:
                form_factor = device_type
                platform = None
            
            # Find device name
            if platform:
                device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
            else:
                device_profiles = self.config.device_profiles.get(form_factor, {})
                
            device_name = next(name for name, config in device_profiles.items() if config == device_config)
            print(f"Testing page: {url} on {browser.browser_type.name} ({device_name})")
            
            await page.goto(url, wait_until="domcontentloaded")
            violations = await self.analyzer.find_issues(page, device_type, device_name)
            report = self.analyzer.format_report(violations, url)
            report['device_type'] = device_type
            report['device_name'] = device_name
            report['browser'] = browser.browser_type.name
            return report
        except Exception as e:
            # Find device name for error report
            if platform:
                device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
            else:
                device_profiles = self.config.device_profiles.get(form_factor, {})
                
            device_name = next((name for name, config in device_profiles.items() if config == device_config), "Unknown")
            
            error_report = {
                "url": url,
                "device_type": device_type,
                "device_name": device_name,
                "browser": browser.browser_type.name,
                "error": f"Could not test {url} on {browser.browser_type.name}. Error: {e}"
            }
            print(error_report["error"])
            return error_report
        finally:
            await page.close()
            await context.close()

    async def _run_tests_in_parallel(self, playwright_instance, urls: List[str], pbar: "tqdm"):
        """Launch browsers and run tests in parallel."""
        url_queue = asyncio.Queue()
        for url in urls:
            await url_queue.put(url)

        print("\nLaunching browsers for parallel testing...")
        browsers = await self._launch_browsers(playwright_instance)
        if not browsers:
            print("No browsers were launched successfully. Exiting.")
            return

        tasks = []
        for i, browser in enumerate(browsers):
            worker_name = f"worker-{self.config.browser_types[i]}"
            task = asyncio.create_task(self._worker(worker_name, browser, url_queue, pbar))
            tasks.append(task)

        await url_queue.join()

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        print("Closing browsers...")
        await asyncio.gather(*[b.close() for b in browsers])

    async def _launch_browsers(self, playwright_instance) -> List[Browser]:
        """Launches the browsers specified in the config."""
        browsers = []
        for browser_type in self.config.browser_types:
            try:
                print(f"Launching {browser_type}...")
                browser = await getattr(playwright_instance, browser_type).launch(headless=True)
                browsers.append(browser)
            except Exception as e:
                print(f"!!! Could not launch {browser_type}: {e}")
        return browsers

    async def _worker(self, name: str, browser: Browser, queue: asyncio.Queue, pbar: "tqdm"):
        """A worker that processes URLs from a queue."""
        print(f"[{name}] starting...")
        while not queue.empty():
            try:
                url = await queue.get()
                report = await self._analyze_page(browser, url)
                self.results.append(report)
                pbar.update(1)
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{name}] encountered an error: {e}")
                queue.task_done()
        print(f"[{name}] finished.")

    async def _analyze_page(self, browser: Browser, url: str) -> Dict[str, Any]:
        """Analyzes a single page and returns a report string."""
        page = await browser.new_page()
        try:
            print(f"Testing page: {url} on {browser.browser_type.name}")
            await page.goto(url, wait_until="domcontentloaded")
            violations = await self.analyzer.find_issues(page)
            return self.analyzer.format_report(violations, url)
        except Exception as e:
            error_report = {
                "url": url,
                "error": f"Could not test {url} on {browser.browser_type.name}. Error: {e}"
            }
            print(error_report["error"])
            return error_report
        finally:
            await page.close()

    def _save_reports(self):
        """Saves the consolidated reports for each device type."""
        # Create results folder structure
        os.makedirs(self.config.results_folder, exist_ok=True)
        
        for device_type, device_results in self.results.items():
            if not device_results:
                print(f"No results found for {device_type}, skipping report generation.")
                continue
            
            # Parse device type to determine folder structure
            if device_type.startswith('mobile-'):
                form_factor = 'mobile'
                platform = device_type.replace('mobile-', '')
                device_folder = os.path.join(self.config.results_folder, form_factor, platform)
                report_name = f"accessibility_report_{form_factor}_{platform}"
            elif device_type.startswith('tablet-'):
                form_factor = 'tablet'
                platform = device_type.replace('tablet-', '')
                device_folder = os.path.join(self.config.results_folder, form_factor, platform)
                report_name = f"accessibility_report_{form_factor}_{platform}"
            else:
                # Desktop case
                device_folder = os.path.join(self.config.results_folder, device_type)
                report_name = f"accessibility_report_{device_type}"
            
            # Create device-specific folder
            os.makedirs(device_folder, exist_ok=True)
            
            # Create device-specific screenshots folder
            screenshots_folder = os.path.join(device_folder, "screenshots")
            os.makedirs(screenshots_folder, exist_ok=True)
            
            # Filter out any results that are just error strings
            valid_results = [r for r in device_results if "error" not in r]
            
            if not valid_results:
                print(f"No valid results for {device_type}, skipping report generation.")
                continue
            
            report_content = self.reporter.generate_report(
                results=valid_results,
                base_url=self.config.base_url,
                report_format=self.config.report_format,
                device_type=device_type
            )
            
            # Generate device-specific filename
            extension = self.config.report_format
            filename = f"{report_name}.{extension}"
            filepath = os.path.join(device_folder, filename)
            
            self.reporter.save_report(report_content, filepath)
            print(f"\n{device_type.capitalize()} report saved to {os.path.abspath(filepath)}")
