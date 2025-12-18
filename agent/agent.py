import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from tqdm import tqdm

from .local_analyzer import LocalAnalyzer
from .reporter import ReportGenerator
from .crawler import Crawler
from .sso_auth_manager import SSOAuthManager
from .exceptions import (
    NavigationError,
    TransientNavigationError,
    AnalysisError,
    TransientAnalysisError,
    AuthenticationError,
    ConfigurationError,
    BrowserError
)
from .logger import setup_logger, PerformanceLogger, log_test_start, log_test_complete, log_test_error, log_retry_attempt
from .retry_handler import RetryHandler, RetryConfig
from .config_validator import ConfigValidator

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
    max_workers: int = 8  # Number of parallel tabs
    parallel: bool = True
    additional_workers_per_device: int = 2
    max_concurrent_tabs: int = 6
    max_tabs_per_authentication_group: int = 4
    parallel_config: Optional[Dict[str, Any]] = None
    timeout_config: Optional[Dict[str, Any]] = None
    
    # New: Retry configuration
    max_retries: int = 2
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 10.0
    
    # New: Logging configuration
    log_level: str = "INFO"
    enable_json_logs: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        ConfigValidator.validate_and_raise(self)
        ConfigValidator.create_directories(self)

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
        self.sso_authenticator = None
        self.authenticated_context = None
        
        # Initialize logger
        self.logger = setup_logger(
            name="accessibility_agent",
            log_level=config.log_level,
            enable_json=config.enable_json_logs
        )
        
        # Initialize retry handler
        retry_config = RetryConfig(
            max_retries=config.max_retries,
            initial_delay=config.retry_initial_delay,
            max_delay=config.retry_max_delay
        )
        self.retry_handler = RetryHandler(retry_config)
        
        # Initialize SSO if enabled
        if self.config.use_sso:
            self.sso_authenticator = SSOAuthManager()
            self.logger.info(f"SSO authentication enabled with provider: {self.config.sso_provider}")
        
        # Initialize results for each device type
        for device_type in self.config.device_types:
            self.results[device_type] = []
        
        self.logger.info(f"Agent initialized with {len(config.device_types)} device types, max_workers={config.max_workers}")

    def _cleanup_old_results(self, device_type: str = None):
        """
        Clean up old screenshots and HTML reports before starting a new test run.
        This prevents mixing old and new screenshots and ensures fresh results.
        
        Args:
            device_type: If provided, only clean this device type. If None, clean all.
        """
        import shutil
        
        devices_to_clean = [device_type] if device_type else self.config.device_types
        
        for dtype in devices_to_clean:
            # Determine the correct path based on device type
            if dtype.startswith('mobile-'):
                platform = dtype.replace('mobile-', '')
                results_dir = os.path.join("results", "mobile", platform)
            elif dtype.startswith('tablet-'):
                platform = dtype.replace('tablet-', '')
                results_dir = os.path.join("results", "tablet", platform)
            else:
                results_dir = os.path.join("results", dtype)
            
            screenshots_dir = os.path.join(results_dir, "screenshots")
            
            # Clean screenshots directory
            if os.path.exists(screenshots_dir):
                try:
                    shutil.rmtree(screenshots_dir)
                    self.logger.info(f"Cleaned old screenshots from {screenshots_dir}")
                    print(f"🧹 Cleaned old screenshots for {dtype}")
                except Exception as e:
                    self.logger.warning(f"Could not clean screenshots directory {screenshots_dir}: {e}")
            
            # Clean old HTML reports (keep structure, just remove the HTML file)
            html_report = os.path.join(results_dir, "accessibility_report.html")
            if os.path.exists(html_report):
                try:
                    os.remove(html_report)
                    self.logger.info(f"Removed old HTML report from {results_dir}")
                except Exception as e:
                    self.logger.warning(f"Could not remove old HTML report {html_report}: {e}")

    async def run(self):
        """
        Runs the accessibility test suite across different device types.
        Visual Testing Agent Pattern: Group by MFA template, authenticate once, share context
        """
        self.logger.info("="*60)
        self.logger.info("Starting Automated Accessibility Test Agent")
        self.logger.info("="*60)
        print("Starting Automated Accessibility Test Agent...")
        
        # Clean up old screenshots and reports before starting new test
        print("🧹 Cleaning up old results...")
        self._cleanup_old_results()
        
        overall_start_time = time.time()
        
        try:
            async with async_playwright() as p:
                urls_to_test = self.pre_defined_urls
                if not urls_to_test:
                    # 1. Crawl the website to get all URLs if not provided
                    self.logger.info("No URLs provided, starting crawler...")
                    print("No URLs provided, starting crawler...")
                    urls_to_test = await self._crawl(p)
                else:
                    self.logger.info(f"Using {len(urls_to_test)} URLs from input")
                    print(f"Using {len(urls_to_test)} URLs provided via CSV.")

                if not urls_to_test:
                    self.logger.warning("No pages found to test")
                    print("No pages found to test. Exiting.")
                    return

                # Convert URLs/TestConfigs to test configs dict format
                test_configs = self._create_test_configs_from_input(urls_to_test)
                self.logger.info(f"Loaded {len(test_configs)} test configurations")

                # Run tests for each device type
                for device_type in self.config.device_types:
                    self.logger.info(f"Starting tests for device type: {device_type}")
                    print(f"\n=== Testing on {device_type.upper()} devices ===")
                    
                    device_start_time = time.time()
                    
                    # Add progress bar
                    with tqdm(total=len(test_configs), desc=f"Analyzing Pages ({device_type})") as pbar:
                        try:
                            # 2. Visual Testing Agent Pattern: Group by MFA template and run with shared context
                            await self._run_tests_grouped_by_mfa(p, test_configs, device_type, pbar)
                        except Exception as e:
                            self.logger.error(f"Error testing device type {device_type}: {e}", exc_info=True)
                            print(f"❌ Error testing {device_type}: {e}")
                    
                    device_duration = time.time() - device_start_time
                    self.logger.info(f"Completed {device_type} tests in {device_duration:.2f}s")

                # 3. Consolidate and save the reports
                self._save_reports()
                
                overall_duration = time.time() - overall_start_time
                
                # Log summary statistics
                total_tests = sum(len(results) for results in self.results.values())
                total_violations = sum(
                    len(result.get('violations', []))
                    for results in self.results.values()
                    for result in results
                )
                failed_tests = sum(
                    1 for results in self.results.values()
                    for result in results
                    if result.get('error')
                )
                
                self.logger.info("="*60)
                self.logger.info("Test Run Summary")
                self.logger.info(f"  Total Tests: {total_tests}")
                self.logger.info(f"  Failed Tests: {failed_tests}")
                self.logger.info(f"  Total Violations: {total_violations}")
                self.logger.info(f"  Duration: {overall_duration:.2f}s")
                self.logger.info("="*60)
                
                print(f"\n✅ Agent finished in {overall_duration:.2f}s")
                print(f"   Tests: {total_tests} | Failed: {failed_tests} | Violations: {total_violations}")
                
        except Exception as e:
            self.logger.critical(f"Fatal error in test run: {e}", exc_info=True)
            print(f"\n❌ Fatal error: {e}")
            raise

    def _create_test_configs_from_input(self, urls_or_configs: List) -> List[Dict[str, Any]]:
        """
        Convert URLs or TestConfig objects to unified test config dict format.
        Supports both simple URL strings and TestConfig objects from enhanced CSV.
        """
        from .csv_loader import TestConfig
        
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
        
        return test_configs

    async def _detect_auth_requirement(self, browser: Browser, url: str, device_type: str) -> tuple[bool, str]:
        """
        Dynamically detect if a URL requires authentication by attempting to load it.
        Returns: (requires_auth: bool, mfa_template: str)
        """
        context = None
        page = None
        try:
            device_config = self._get_device_config(device_type)
            context_options = {
                'viewport': device_config.get('viewport', {'width': 1920, 'height': 1080}),
                'user_agent': device_config.get('userAgent', ''),
                'device_scale_factor': device_config.get('deviceScaleFactor', 1),
                'is_mobile': device_config.get('isMobile', False),
                'has_touch': device_config.get('hasTouch', False)
            }
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            # Try to navigate to the URL with better wait strategy
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for page to be fully stable
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            await page.wait_for_timeout(1500)
            
            # Get the current URL after any redirects
            current_url = page.url
            
            # Check if we were redirected to a login page
            login_indicators = [
                'login.microsoftonline.com',
                'login.microsoft.com',
                'accounts.google.com',
                'okta.com',
                'auth0.com',
                'sso.',
                'login.',
                '/login',
                '/signin',
                '/auth'
            ]
            
            for indicator in login_indicators:
                if indicator in current_url.lower():
                    print(f"🔒 Auth required for {url} (redirected to {current_url[:100]}...)")
                    
                    # Determine MFA template based on redirect
                    if 'microsoftonline.com' in current_url or 'microsoft.com' in current_url:
                        return (True, 'lilly')
                    elif 'okta.com' in current_url:
                        return (True, 'okta')
                    elif 'auth0.com' in current_url:
                        return (True, 'auth0')
                    else:
                        return (True, 'lilly')  # Default to lilly
            
            # No redirect to login page - URL is public
            print(f"🌐 Public URL: {url}")
            return (False, 'public')
            
        except Exception as e:
            # If there's an error, assume it might need auth
            print(f"⚠️  Error checking {url}: {str(e)[:100]}")
            return (False, 'public')  # Default to public on error
            
        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    async def _run_tests_with_dynamic_auth_detection(self, playwright_instance, test_configs: List[Dict[str, Any]], device_type: str, pbar: "tqdm"):
        """
        Visual Testing Agent Pattern: Dynamically detect auth requirements by trying URLs first.
        This eliminates the need for hardcoded domain patterns.
        """
        # Step 1: Launch ONE browser for detection
        print(f"🔍 Detecting authentication requirements for {len(test_configs)} URLs...")
        browser = await playwright_instance.chromium.launch(headless=self.config.headless)
        
        try:
            # Step 2: Try each URL to detect auth requirements
            for config in test_configs:
                requires_auth, mfa_template = await self._detect_auth_requirement(browser, config['url'], device_type)
                config['requiresAuth'] = requires_auth
                config['mfaTemplate'] = mfa_template
            
        finally:
            await browser.close()
        
        # Step 3: Group tests by MFA template (now that we know which need auth)
        test_groups = self._group_tests_by_mfa(test_configs)
        print(f"\n📋 Grouped into {len(test_groups)} groups: {list(test_groups.keys())}")
        
        # Print summary
        for template, tests in test_groups.items():
            if template == 'public':
                print(f"   🌐 Public URLs: {len(tests)}")
            else:
                print(f"   🔐 {template.upper()} URLs: {len(tests)}")
        
        # Step 4: Process each MFA group
        for mfa_template, tests in test_groups.items():
            print(f"\n{'='*60}")
            if mfa_template == 'public':
                print(f"🌐 Processing PUBLIC URLs ({len(tests)} tests)")
            else:
                print(f"🔐 Processing {mfa_template.upper()} URLs ({len(tests)} tests - will authenticate once)")
            print(f"{'='*60}")
            
            # Step 5: Launch ONE browser per group
            browser = await playwright_instance.chromium.launch(headless=self.config.headless)
            
            try:
                # Step 6: Authenticate if needed (creates shared context)
                shared_context = await self._authenticate_and_create_context(browser, mfa_template, device_type)
                
                # Step 7: Run all tests in this group using parallel tabs
                await self._run_parallel_tests_in_shared_context(browser, shared_context, tests, device_type, pbar)
                
            finally:
                # Clean up browser
                await browser.close()

    async def _run_tests_grouped_by_mfa(self, playwright_instance, test_configs: List[Dict[str, Any]], device_type: str, pbar: "tqdm"):
        """
        Visual Testing Agent Pattern: Group tests by MFA template and run with shared context
        """
        # Step 1: Group tests by MFA template
        test_groups = self._group_tests_by_mfa(test_configs)
        print(f"📋 Grouped into {len(test_groups)} MFA groups: {list(test_groups.keys())}")
        
        # Step 2: Process each MFA group
        for mfa_template, tests in test_groups.items():
            print(f"\n🔐 Processing {mfa_template} group ({len(tests)} tests)")
            
            # Step 3: Launch ONE browser per group
            browser = await playwright_instance.chromium.launch(headless=self.config.headless)
            
            try:
                # Step 4: Authenticate if needed (creates shared context)
                shared_context = await self._authenticate_and_create_context(browser, mfa_template, device_type)
                
                # Step 5: Run all tests in this group using parallel tabs
                await self._run_parallel_tests_in_shared_context(browser, shared_context, tests, device_type, pbar)
                
            finally:
                # Clean up browser
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
        """Authenticate with MFA template and create shared context with error handling."""
        device_config = self._get_device_config(device_type)
        
        context_options = {
            'viewport': device_config.get('viewport', {'width': 1920, 'height': 1080}),
            'user_agent': device_config.get('userAgent', ''),
            'device_scale_factor': device_config.get('deviceScaleFactor', 1),
            'is_mobile': device_config.get('isMobile', False),
            'has_touch': device_config.get('hasTouch', False)
        }
        
        if mfa_template != 'public' and self.config.use_sso and self.sso_authenticator:
            self.logger.info(f"Authenticating with {mfa_template} SSO template")
            print(f"🔐 Authenticating with {mfa_template} SSO...")
            
            try:
                # Initialize the SSO authenticator with the browser
                await self.sso_authenticator.initialize(browser)
                
                # Authenticate using the template with performance tracking and device-specific config
                with PerformanceLogger(self.logger, "SSO Authentication", mfa_template=mfa_template):
                    auth_result = await self.sso_authenticator.authenticate_with_template(
                        mfa_template,
                        context_options=context_options  # Pass device config to SSO!
                    )
                
                if auth_result.success and auth_result.authenticated_context:
                    self.logger.info(f"SSO authentication successful for template: {mfa_template}")
                    print("✅ SSO authentication successful!")
                    # Use the authenticated context directly
                    return auth_result.authenticated_context
                else:
                    error_msg = auth_result.error_message or "Unknown authentication error"
                    self.logger.error(f"SSO authentication failed: {error_msg}", extra={"mfa_template": mfa_template})
                    print(f"❌ SSO authentication failed: {error_msg}")
                    raise AuthenticationError(error_msg, provider=mfa_template)
                    
            except AuthenticationError:
                # Re-raise authentication errors
                raise
            except Exception as e:
                error_msg = f"Unexpected error during SSO authentication: {str(e)}"
                self.logger.error(error_msg, exc_info=True, extra={"mfa_template": mfa_template})
                print(f"❌ {error_msg}")
                raise AuthenticationError(error_msg, provider=mfa_template, details={"error": str(e)})
        
        # Create a regular context (for public URLs)
        self.logger.debug(f"Creating regular context for device type: {device_type}")
        shared_context = await browser.new_context(**context_options)
        return shared_context

    async def _run_parallel_tests_in_shared_context(self, browser: Browser, shared_context, tests: List[Dict[str, Any]], device_type: str, pbar: "tqdm"):
        """
        Visual Testing Agent Pattern: Run tests in parallel using tabs from shared context
        """
        print(f"⚡ Running {len(tests)} tests in parallel with {self.config.max_workers} concurrent tabs")
        
        # Create semaphore to limit concurrent tabs
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def test_single_url_in_tab(test_config: Dict[str, Any], tab_index: int):
            async with semaphore:
                result = await self._test_url_in_shared_tab(shared_context, test_config, device_type, tab_index)
                if result:
                    self.results[device_type].append(result)
                pbar.update(1)
        
        # Run all tests in parallel - Visual Testing Agent pattern!
        tasks = [test_single_url_in_tab(test, i) for i, test in enumerate(tests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Close shared context
        await shared_context.close()

    async def _test_url_in_shared_tab(self, shared_context, test_config: Dict[str, Any], device_type: str, tab_index: int) -> Dict[str, Any]:
        """Test a single URL in its own tab using shared authenticated context with retry logic."""
        url = test_config['url']
        
        # Wrapper function for retry
        async def test_with_retry():
            page = None
            start_time = time.time()
            
            try:
                # Log test start
                log_test_start(self.logger, url, device_type, tab_index)
                
                # Create new tab from shared context
                page = await shared_context.new_page()
                
                auth_status = "🔐" if test_config['requiresAuth'] else ""
                print(f"{auth_status} Tab-{tab_index+1}: Testing {url}")
                
                # Navigate to URL with proper error handling
                timeout = 60000 if test_config['requiresAuth'] else 30000
                try:
                    # Use networkidle for better page load detection
                    await page.goto(url, wait_until="networkidle", timeout=timeout)
                    
                    # For authenticated pages, wait for dynamic content to fully load
                    if test_config['requiresAuth']:
                        # Wait for page to be stable
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        # Additional wait for any client-side rendering
                        await asyncio.sleep(2)
                        
                except TimeoutError as e:
                    self.logger.warning(f"Navigation timeout for {url}, continuing with partial page load")
                    raise TransientNavigationError(f"Timeout loading {url}", url=url)
                    
                except Exception as e:
                    error_msg = str(e)
                    if "net::ERR_" in error_msg or "NS_ERROR_" in error_msg:
                        # Network errors are usually transient
                        raise TransientNavigationError(f"Network error: {error_msg}", url=url)
                    else:
                        raise NavigationError(f"Navigation failed: {error_msg}", url=url)
                
                # Run accessibility analysis
                try:
                    violations = await self.analyzer.find_issues(page, device_type, "default")
                    report = self.analyzer.format_report(violations, url)
                    
                    # Log success
                    duration = time.time() - start_time
                    log_test_complete(self.logger, url, len(report.get('violations', [])), duration, tab_index)
                    
                    return report
                    
                except Exception as e:
                    self.logger.error(f"Accessibility analysis failed for {url}: {e}")
                    raise TransientAnalysisError(f"Analysis failed: {str(e)}", url=url)
                
            except (TransientNavigationError, TransientAnalysisError) as e:
                # These are retryable errors
                raise
                
            except Exception as e:
                # Non-retryable errors
                self.logger.error(f"Test failed for {url}: {type(e).__name__}: {str(e)}", exc_info=True)
                raise
                
            finally:
                # Close only the tab, keep shared context for other tabs
                if page:
                    try:
                        await page.close()
                    except Exception as e:
                        self.logger.warning(f"Error closing page: {e}")
        
        # Execute with retry logic
        try:
            return await self.retry_handler.retry_async(
                test_with_retry,
                retryable_exceptions=(TransientNavigationError, TransientAnalysisError)
            )
        except Exception as e:
            # All retries exhausted or non-retryable error
            log_test_error(self.logger, url, e, self.config.max_retries, tab_index)
            return {
                'url': url,
                'name': test_config.get('name', url),
                'violations': [],
                'error': str(e),
                'error_type': type(e).__name__,
                'retries_exhausted': isinstance(e, (TransientNavigationError, TransientAnalysisError))
            }

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
        """
        Visual Testing Agent Pattern:
        1. Launch ONE browser
        2. Authenticate SSO (if needed) - creates ONE authenticated context
        3. Create multiple pages (tabs) from that context
        4. Run tests in parallel using those tabs
        """
        print(f"🚀 Launching browser for {device_type} testing...")
        
        # Step 1: Launch ONE browser
        browser = await playwright_instance.chromium.launch(headless=self.config.headless)
        
        try:
            # Step 2: Authenticate SSO if needed (creates authenticated context)
            if self.config.use_sso and self.sso_authenticator:
                print(f"🔐 Authenticating with SSO provider: {self.config.sso_provider}...")
                auth_context = await self.sso_authenticator.authenticate(
                    browser,
                    provider=self.config.sso_provider or 'lilly',
                    headless=self.config.headless
                )
                print("✅ SSO authentication successful!")
                self.authenticated_context = auth_context
            else:
                # No SSO - create regular context
                self.authenticated_context = None
            
            # Step 3: Get device configuration
            device_config = self._get_device_config(device_type)
            
            # Step 4: Run tests in parallel with multiple tabs
            await self._run_parallel_tests(browser, urls, device_type, device_config, pbar)
            
        finally:
            # Clean up
            print("🔄 Closing browser...")
            await browser.close()
    
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
        
        # Return the first device config
        return list(device_profiles.values())[0] if device_profiles else {}
    
    async def _run_parallel_tests(self, browser: Browser, urls: List[str], device_type: str, device_config: Dict[str, Any], pbar: "tqdm"):
        """
        Run tests in parallel using multiple tabs (Visual Testing Agent pattern).
        Each URL gets tested in its own tab, but all tabs share the same browser and context.
        """
        # Create a semaphore to limit concurrent tabs
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def test_url_in_tab(url: str, tab_index: int):
            async with semaphore:
                result = await self._test_single_url(browser, url, device_type, device_config, tab_index)
                if result:
                    self.results[device_type].append(result)
                pbar.update(1)
        
        # Run all tests in parallel - this is the key Visual Testing Agent pattern!
        print(f"⚡ Running {len(urls)} tests in parallel with {self.config.max_workers} concurrent tabs")
        tasks = [test_url_in_tab(url, i) for i, url in enumerate(urls)]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _test_single_url(self, browser: Browser, url: str, device_type: str, device_config: Dict[str, Any], tab_index: int) -> Dict[str, Any]:
        """
        Test a single URL in its own tab.
        This is the Visual Testing Agent pattern - each test gets a new page from the shared context.
        """
        context = None
        page = None
        try:
            # Create context options
            context_options = {
                'viewport': device_config.get('viewport', {'width': 1920, 'height': 1080}),
                'user_agent': device_config.get('userAgent', ''),
                'device_scale_factor': device_config.get('deviceScaleFactor', 1),
                'is_mobile': device_config.get('isMobile', False),
                'has_touch': device_config.get('hasTouch', False)
            }
            
            # CRITICAL: If we have an authenticated context, use its storage state
            # This shares the SSO session across all tabs!
            if self.authenticated_context:
                storage_state = await self.authenticated_context.storage_state()
                context_options['storage_state'] = storage_state
            
            # Create a new context for this test (with shared auth)
            context = await browser.new_context(**context_options)
            
            # Create a new page (tab) in this context
            page = await context.new_page()
            
            auth_status = "🔐" if self.authenticated_context else ""
            print(f"{auth_status} Tab-{tab_index+1}: Testing {url}")
            
            # Navigate to the URL
            timeout = 60000 if self.authenticated_context else 30000
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
            except Exception as e:
                print(f"⚠️  Tab-{tab_index+1}: Navigation warning: {str(e)[:100]}")
                # Continue with analysis anyway
            
            # Run accessibility analysis
            violations = await self.analyzer.find_issues(page, device_type, "default")
            report = self.analyzer.format_report(violations, url)
            
            return report
            
        except Exception as e:
            print(f"❌ Tab-{tab_index+1}: Error testing {url}: {str(e)}")
            return {
                'url': url,
                'violations': [],
                'error': str(e)
            }
        finally:
            # Clean up page and context
            if page:
                try:
                    await page.close()
                except:
                    pass
            if context:
                try:
                    await context.close()
                except:
                    pass

    def _save_reports(self):
        """Save all test results to reports with proper error handling."""
        for device_type, results in self.results.items():
            if results:
                self.logger.info(f"Generating {device_type} report with {len(results)} test results")
                print(f"\n=== Generating {device_type} Report ===")
                
                try:
                    output_dir = f"{self.config.results_folder}/{device_type}"
                    self.reporter.generate_report(
                        results, 
                        base_url=self.config.base_url,
                        report_format=self.config.report_format,
                        device_type=device_type
                    )
                    self.logger.info(f"Report saved successfully to: {output_dir}")
                    print(f"✅ Report saved to: {output_dir}")
                except Exception as e:
                    self.logger.error(f"Failed to generate report for {device_type}: {e}", exc_info=True)
                    print(f"❌ Error generating report: {e}")
            else:
                self.logger.warning(f"No results to save for {device_type}")
                print(f"⚠️  No results to save for {device_type}")
