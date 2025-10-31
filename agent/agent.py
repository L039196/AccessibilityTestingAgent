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
    headless: bool = True
    parallel: bool = True
    max_workers: int = 8
    additional_workers_per_device: int = 2

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
        self._current_browser = None  # Store browser reference for cleanup
        
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

            # Close main browser if it exists
            if self._current_browser:
                print("Closing main browser...")
                await self._current_browser.close()
                
            # 3. Consolidate and save the reports
            self._save_reports()
            
            print("Agent finished.")

    async def _crawl(self, playwright_instance) -> List[str]:
        """Crawl the website to find all pages to test."""
        print("Launching crawler browser...")
        crawler_browser = await playwright_instance.chromium.launch(headless=self.config.headless)
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
        """Launch browsers and run tests for a specific device type (parallel or sequential)."""
        if self.config.parallel:
            await self._run_tests_parallel(playwright_instance, urls, device_type, pbar)
        else:
            await self._run_tests_sequential(playwright_instance, urls, device_type, pbar)

    async def _run_tests_parallel(self, playwright_instance, urls: List[str], device_type: str, pbar: "tqdm"):
        """Launch a single browser and run tests in parallel using multiple tabs in shared context."""
        print(f"Setting up parallel testing for {device_type} with {len(urls)} URLs...")
        
        # Launch single browser instance
        preferred_browser = 'chromium'
        try:
            browser = await getattr(playwright_instance, preferred_browser).launch(
                headless=self.config.headless,
                args=['--disable-features=VizDisplayCompositor'] if not self.config.headless else []
            )
            self._current_browser = browser
            print(f"✅ Browser launched successfully for {device_type}")
        except Exception as e:
            print(f"❌ Failed to launch browser: {e}")
            return

        # Create single shared context for this device type
        try:
            context = await self._create_shared_context_for_device(browser, device_type)
            if not context:
                print(f"❌ Failed to create shared context for {device_type}. Skipping.")
                await browser.close()
                return
            
            print(f"✅ Created shared browser context for {device_type}")
            
            # Calculate number of concurrent tabs based on config (limit to prevent resource issues)
            max_concurrent_tabs = min(len(urls), self.config.max_workers, 3)  # Limit to 3 tabs for stability
            print(f"🔄 Using {max_concurrent_tabs} concurrent tabs for parallel testing")

            # Create URL queue for workers
            url_queue = asyncio.Queue()
            for url in urls:
                await url_queue.put(url)

            # Create worker tasks - each gets a new tab in the shared context
            tasks = []
            for i in range(max_concurrent_tabs):
                worker_name = f"tab-worker-{i+1}-{device_type}"
                task = asyncio.create_task(
                    self._tab_worker_with_shared_context(worker_name, context, device_type, url_queue, pbar)
                )
                tasks.append(task)

            print(f"🚀 Running {len(urls)} tests across {max_concurrent_tabs} tabs...")

            # Wait for all URLs to be processed
            try:
                await asyncio.wait_for(url_queue.join(), timeout=300.0)  # 5 minute timeout
                print(f"✅ All URLs processed for {device_type}")
            except asyncio.TimeoutError:
                print("⚠️ Warning: Queue processing timed out after 5 minutes")

            # Cancel remaining tasks and cleanup
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for task cleanup
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10.0)
            except asyncio.TimeoutError:
                print("⚠️ Warning: Task cleanup timed out")

            # Close the shared context
            try:
                await context.close()
                print(f"✅ Shared context closed for {device_type}")
            except Exception as e:
                print(f"⚠️ Warning: Error closing context: {e}")
        
        except Exception as e:
            print(f"❌ Error creating shared context: {e}")
        finally:
            # Close the browser
            try:
                await browser.close()
                print(f"✅ Browser closed for {device_type}")
            except Exception as e:
                print(f"⚠️ Warning: Error closing browser: {e}")

    async def _create_shared_context_for_device(self, browser, device_type: str):
        """Create a single shared context for the device type (like VisualTestingAgent)."""
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
        if platform and self.config.device_profiles:
            device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
        elif self.config.device_profiles:
            device_profiles = self.config.device_profiles.get(form_factor, {})
        else:
            # Fallback if no device profiles are configured
            device_profiles = {"default": {}}
        
        if not device_profiles:
            print(f"No device profiles found for {device_type}.")
            return None

        # Use the first device profile for the shared context
        first_device_name, first_device_config = next(iter(device_profiles.items()))
        
        try:
            print(f"Creating shared context for {first_device_name}...")
            # Convert device config to Playwright format
            playwright_config = self._convert_device_config(first_device_config)
            context = await browser.new_context(**playwright_config)
            print(f"✅ Shared context created for {first_device_name}")
            return context
        except Exception as e:
            print(f"❌ Could not create shared context for {first_device_name}: {e}")
            return None

    async def _tab_worker_with_shared_context(self, worker_name: str, context, device_type: str, url_queue: asyncio.Queue, pbar: "tqdm"):
        """A worker that processes URLs from a queue using tabs in shared context (like VisualTestingAgent)."""
        print(f"[{worker_name}] 🚀 Starting tab worker...")
        
        page = None  # Initialize page variable
        
        try:
            # Create a new page (tab) in the shared context
            page = await context.new_page()
            print(f"[{worker_name}] 📄 Created new tab in shared context")
        except Exception as e:
            print(f"[{worker_name}] ❌ Failed to create tab: {e}")
            return
        
        try:
            processed_count = 0
            while True:
                try:
                    # Get URL from queue with timeout to avoid infinite loop
                    url = await asyncio.wait_for(url_queue.get(), timeout=3.0)
                    print(f"[{worker_name}] 🔍 Testing ({processed_count + 1}): {url}")
                    
                    # Navigate to the page
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Run accessibility analysis with limited retries
                    try:
                        issues = await self.analyzer.find_issues(page, device_type, f"{worker_name}")
                        
                        # Store result
                        self.results[device_type].append({
                            'url': url,
                            'device': worker_name,
                            'violations': issues,  # ✅ Fixed: Use 'violations' key that reporter expects
                            'issues': issues,      # Keep for backward compatibility
                            'analysis': {'violations': issues}
                        })
                        
                        print(f"[{worker_name}] ✅ Completed ({processed_count + 1}): {url}")
                        processed_count += 1
                        
                    except Exception as analysis_error:
                        print(f"[{worker_name}] ⚠️ Analysis failed for {url}: {analysis_error}")
                        # Still count as processed to avoid infinite loops
                        processed_count += 1
                    
                    pbar.update(1)
                    url_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No more items in queue, worker can exit
                    print(f"[{worker_name}] 🏁 No more work available, processed {processed_count} URLs")
                    break
                except asyncio.CancelledError:
                    print(f"[{worker_name}] 🛑 Worker cancelled after processing {processed_count} URLs")
                    break
                except Exception as e:
                    print(f"[{worker_name}] ❌ Error processing URL: {e}")
                    pbar.update(1)
                    url_queue.task_done()
                    processed_count += 1
                    
                    # Break after too many errors to prevent infinite loops
                    if processed_count > len(self.config.device_types) * 10:  # Safety limit
                        print(f"[{worker_name}] 🚨 Too many errors, stopping worker")
                        break
                        
        except Exception as worker_error:
            print(f"[{worker_name}] 💥 Worker crashed: {worker_error}")
        finally:
            # CRITICAL: Always close the page/tab
            if page:
                try:
                    await page.close()
                    print(f"[{worker_name}] 🗑️ Tab closed successfully")
                except Exception as e:
                    print(f"[{worker_name}] ⚠️ Error closing tab: {e}")
            else:
                print(f"[{worker_name}] ⚠️ No page to close")
            
            print(f"[{worker_name}] 🏁 Worker finished")





    async def _run_tests_sequential(self, playwright_instance, urls: List[str], device_type: str, pbar: "tqdm"):
        """Run tests sequentially for a specific device type (one browser with sequential processing)."""
        print(f"Running sequential tests for {device_type}...")
        
        # Launch single browser instance
        preferred_browser = 'chromium'
        try:
            browser = await getattr(playwright_instance, preferred_browser).launch(headless=self.config.headless)
            print(f"Browser launched for sequential testing on {device_type}")
        except Exception as e:
            print(f"Failed to launch browser: {e}")
            return
        
        # Get device profiles for this device type
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
        if platform and self.config.device_profiles:
            device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
        elif self.config.device_profiles:
            device_profiles = self.config.device_profiles.get(form_factor, {})
        else:
            # Fallback if no device profiles are configured
            device_profiles = {"default": {}}
        
        if not device_profiles:
            print(f"No device profiles found for {device_type}. Skipping.")
            await browser.close()
            return
            
        try:
            # Process each device sequentially
            for device_name, device_config in device_profiles.items():
                print(f"Testing on {device_name}...")
                
                # Create context for this device
                playwright_config = self._convert_device_config(device_config)
                context = await browser.new_context(**playwright_config)
                
                # Test all URLs on this device
                for url in urls:
                    try:
                        await self._test_single_url_with_context(context, device_config, device_type, url, device_name)
                        pbar.update(1)
                    except Exception as e:
                        print(f"Error testing {url} on {device_name}: {e}")
                        pbar.update(1)
                
                # Close context after testing all URLs for this device
                await context.close()
                print(f"Completed testing on {device_name}")
                
        finally:
            await browser.close()
            print(f"Browser closed for {device_type}")

    async def _test_single_url_with_context(self, context, device_config, device_type: str, url: str, device_name: str):
        """Test a single URL using an existing context."""
        print(f"Testing page: {url} on {device_name}")
        
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Run accessibility analysis
            issues = await self.analyzer.find_issues(page, device_type, device_name)
            
            # Store result
            self.results[device_type].append({
                'url': url,
                'device': device_name,
                'violations': issues,  # ✅ Fixed: Use 'violations' key that reporter expects
                'issues': issues,      # Keep for backward compatibility
                'analysis': {'violations': issues}
            })
            
        except Exception as e:
            print(f"Error analyzing {url} on {device_name}: {e}")
        finally:
            await page.close()


    def _convert_device_config(self, device_config: dict) -> dict:
        """Convert device config from JSON format to Playwright format."""
        playwright_config = {}
        
        # Map the config parameters to Playwright format
        if 'viewport' in device_config:
            playwright_config['viewport'] = device_config['viewport']
        if 'userAgent' in device_config:
            playwright_config['user_agent'] = device_config['userAgent']
        if 'deviceScaleFactor' in device_config:
            playwright_config['device_scale_factor'] = device_config['deviceScaleFactor']
        if 'isMobile' in device_config:
            playwright_config['is_mobile'] = device_config['isMobile']
        if 'hasTouch' in device_config:
            playwright_config['has_touch'] = device_config['hasTouch']
        if 'colorScheme' in device_config:
            playwright_config['color_scheme'] = device_config['colorScheme']
        if 'reducedMotion' in device_config:
            playwright_config['reduced_motion'] = device_config['reducedMotion']
        if 'forcedColors' in device_config:
            playwright_config['forced_colors'] = device_config['forcedColors']
            
        return playwright_config

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
