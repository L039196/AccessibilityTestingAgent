import asyncio
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from tqdm import tqdm

from .local_analyzer import LocalAnalyzer
from .reporter import ReportGenerator
from .crawler import Crawler
from .sso_auth_manager import SSOAuthManager
from .csv_loader import TestConfig

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
    use_sso: bool = False
    sso_provider: Optional[str] = None
    headless: bool = True
    parallel: bool = True
    max_workers: int = 8
    additional_workers_per_device: int = 2
    max_concurrent_tabs: int = 6
    max_tabs_per_authentication_group: int = 4
    parallel_config: Optional[Dict[str, Any]] = None
    timeout_config: Optional[Dict[str, Any]] = None

class Agent:
    """
    The core accessibility testing agent following Visual Testing Agent pattern.
    Groups tests by authentication requirement and runs them in parallel with shared SSO sessions.
    """
    def __init__(self, config: Config, crawler: "Crawler", analyzer: "LocalAnalyzer", reporter: "ReportGenerator", urls_to_test: Optional[List] = None):
        self.config = config
        self.crawler = crawler
        self.analyzer = analyzer
        self.reporter = reporter
        self.results: Dict[str, List[Dict[str, Any]]] = {}
        self.pre_defined_urls = urls_to_test or []
        self.sso_authenticator = None
        
        # Initialize SSO if enabled
        if self.config.use_sso:
            self.sso_authenticator = SSOAuthManager()
        
        # Initialize results for each device type
        for device_type in self.config.device_types:
            self.results[device_type] = []

    async def run(self):
        """
        Runs the accessibility test suite across different device types.
        Visual Testing Agent Pattern: Group by MFA template, authenticate once, share context
        """
        print("Starting Automated Accessibility Test Agent...")
        
        async with async_playwright() as p:
            urls_to_test = self.pre_defined_urls
            if not urls_to_test:
                print("No URLs provided, starting crawler...")
                urls_to_test = await self._crawl(p)
            else:
                print(f"Using {len(urls_to_test)} URLs/configs provided.")

            if not urls_to_test:
                print("No pages found to test. Exiting.")
                return

            # Convert URLs/TestConfigs to test configs dict format
            test_configs = self._create_test_configs_from_input(urls_to_test)

            # Run tests for each device type
            for device_type in self.config.device_types:
                print(f"\n=== Testing on {device_type.upper()} devices ===")
                
                with tqdm(total=len(test_configs), desc=f"Analyzing Pages ({device_type})") as pbar:
                    await self._run_tests_grouped_by_mfa(p, test_configs, device_type, pbar)

            self._save_reports()
            print("Agent finished.")

    def _create_test_configs_from_input(self, urls_or_configs: List) -> List[Dict[str, Any]]:
        """
        Convert URLs or TestConfig objects to unified test config dict format.
        Supports both simple URL strings and TestConfig objects from enhanced CSV.
        """
        test_configs = []
        for item in urls_or_configs:
            if isinstance(item, TestConfig):
                # Enhanced CSV format with auth info
                config = {
                    'url': item.url,
                    'name': item.name or item.url.split('/')[-1] or 'home',
                    'requiresAuth': item.requires_auth,
                    'mfaTemplate': item.mfa_template if item.requires_auth else 'public'
                }
            elif isinstance(item, str):
                # Simple URL string - assume public
                config = {
                    'url': item,
                    'name': item.split('/')[-1] or 'home',
                    'requiresAuth': False,
                    'mfaTemplate': 'public'
                }
            else:
                # Already a dict
                config = item
            
            test_configs.append(config)
        
        return test_configs

    async def _run_tests_grouped_by_mfa(self, playwright_instance, test_configs: List[Dict[str, Any]], device_type: str, pbar: "tqdm"):
        """
        Visual Testing Agent Pattern: Group tests by MFA template and run with shared context
        """
        # Step 1: Group tests by MFA template
        test_groups = self._group_tests_by_mfa(test_configs)
        print(f"📋 Grouped into {len(test_groups)} MFA groups: {list(test_groups.keys())}")
        
        # Step 2: Process each MFA group
        for mfa_template, tests in test_groups.items():
            if mfa_template == 'public':
                print(f"\n🌐 Processing PUBLIC group ({len(tests)} tests)")
            else:
                print(f"\n🔐 Processing {mfa_template.upper()} group ({len(tests)} tests)")
            
            # Step 3: Launch ONE browser per group
            browser = await playwright_instance.chromium.launch(headless=self.config.headless)
            
            try:
                # Step 4: Authenticate if needed (creates shared context)
                shared_context = await self._authenticate_and_create_context(browser, mfa_template, device_type)
                
                # Step 5: Run all tests in this group using parallel tabs
                await self._run_parallel_tests_in_shared_context(browser, shared_context, tests, device_type, pbar)
                
            finally:
                await browser.close()

    def _group_tests_by_mfa(self, test_configs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group tests by MFA template to minimize authentication calls."""
        groups = {}
        
        for config in test_configs:
            template = config['mfaTemplate'] if config['requiresAuth'] else 'public'
            
            if template not in groups:
                groups[template] = []
            groups[template].append(config)
        
        return groups

    async def _authenticate_and_create_context(self, browser: Browser, mfa_template: str, device_type: str):
        """Authenticate with MFA template and create shared context."""
        device_config = self._get_device_config(device_type)
        
        context_options = {
            'viewport': device_config.get('viewport', {'width': 1920, 'height': 1080}),
            'user_agent': device_config.get('userAgent', ''),
            'device_scale_factor': device_config.get('deviceScaleFactor', 1),
            'is_mobile': device_config.get('isMobile', False),
            'has_touch': device_config.get('hasTouch', False)
        }
        
        if mfa_template != 'public' and self.config.use_sso and self.sso_authenticator:
            print(f"🔐 Authenticating with {mfa_template} SSO...")
            
            # Initialize the SSO authenticator with the browser
            await self.sso_authenticator.initialize(browser)
            
            # Authenticate using the template
            auth_result = await self.sso_authenticator.authenticate_with_template(mfa_template)
            
            if auth_result.success and auth_result.authenticated_context:
                print("✅ SSO authentication successful!")
                # Use the authenticated context directly
                return auth_result.authenticated_context
            else:
                error_msg = auth_result.error_message or "Unknown error"
                print(f"❌ SSO authentication failed: {error_msg}")
                # Fall back to creating a regular context
        
        shared_context = await browser.new_context(**context_options)
        return shared_context

    async def _run_parallel_tests_in_shared_context(self, browser: Browser, shared_context, tests: List[Dict[str, Any]], device_type: str, pbar: "tqdm"):
        """
        Visual Testing Agent Pattern: Run tests in parallel using tabs from shared context
        """
        print(f"⚡ Running {len(tests)} tests in parallel with {self.config.max_workers} concurrent tabs")
        
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def test_single_url_in_tab(test_config: Dict[str, Any], tab_index: int):
            async with semaphore:
                result = await self._test_url_in_shared_tab(shared_context, test_config, device_type, tab_index)
                if result:
                    self.results[device_type].append(result)
                pbar.update(1)
        
        tasks = [test_single_url_in_tab(test, i) for i, test in enumerate(tests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        await shared_context.close()

    async def _test_url_in_shared_tab(self, shared_context, test_config: Dict[str, Any], device_type: str, tab_index: int) -> Dict[str, Any]:
        """Test a single URL in its own tab using shared authenticated context."""
        page = None
        try:
            page = await shared_context.new_page()
            
            url = test_config['url']
            auth_status = "🔐" if test_config['requiresAuth'] else "🌐"
            print(f"{auth_status} Tab-{tab_index+1}: Testing {url}")
            
            timeout = 60000 if test_config['requiresAuth'] else 30000
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
            except Exception as e:
                print(f"⚠️  Tab-{tab_index+1}: Navigation warning: {str(e)[:100]}")
            
            violations = await self.analyzer.find_issues(page, device_type, "default")
            report = self.analyzer.format_report(violations, url)
            
            return report
            
        except Exception as e:
            print(f"❌ Tab-{tab_index+1}: Error testing {test_config['url']}: {str(e)}")
            return {
                'url': test_config['url'],
                'violations': [],
                'error': str(e)
            }
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

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

    def _get_device_config(self, device_type: str) -> Dict[str, Any]:
        """Get the first device configuration for the given device type."""
        if device_type.startswith('mobile-'):
            form_factor = 'mobile'
            platform = device_type.replace('mobile-', '')
        elif device_type.startswith('tablet-'):
            form_factor = 'tablet'
            platform = device_type.replace('tablet-', '')
        else:
            form_factor = device_type
            platform = None
        
        if platform:
            device_profiles = self.config.device_profiles.get(form_factor, {}).get(platform, {})
        else:
            device_profiles = self.config.device_profiles.get(form_factor, {})
        
        return list(device_profiles.values())[0] if device_profiles else {}

    def _save_reports(self):
        """Save all test results to reports."""
        import os
        for device_type, results in self.results.items():
            if results:
                print(f"\n=== Generating {device_type} Report ===")
                output_dir = f"{self.config.results_folder}/{device_type}"
                
                # Ensure output directory exists
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate report content
                report_content = self.reporter.generate_report(
                    results, 
                    self.config.base_url,
                    self.config.report_format,
                    device_type
                )
                
                # Determine file extension
                ext = "html" if self.config.report_format == "html" else self.config.report_format
                report_file = f"{output_dir}/accessibility_report.{ext}"
                
                # Save report
                self.reporter.save_report(report_content, report_file)
                print(f"✅ Report saved to: {report_file}")
            else:
                print(f"No results to save for {device_type}")
