from playwright.async_api import Page, Playwright
from axe_core_python.async_playwright import Axe
import json
import uuid
import os

class LocalAnalyzer:
    """
    Analyzes a web page for accessibility issues using the axe-core engine.
    This analyzer runs locally without needing an API key.
    """
    def __init__(self, axe_rules: dict = None):
        self.axe = Axe()
        self.axe_rules = axe_rules

    async def find_issues(self, page: Page, device_type: str = "desktop", device_name: str = "Desktop") -> list:
        """
        Runs the axe-core accessibility analysis on the given Playwright page.
        For each violation, it takes a screenshot of the failing element.

        Args:
            page: The Playwright Page object to analyze.
            device_type: The type of device (desktop, mobile, tablet).
            device_name: The specific device name for screenshot organization.

        Returns:
            A list of violation dictionaries, with screenshot data added to each node.
        """
        print(f"Running axe-core analysis on {page.url}...")
        results = await self.axe.run(page, context=self.axe_rules)
        
        violations = results['violations']

        # Convert device type to proper hierarchical path
        if device_type.startswith('mobile-'):
            platform = device_type.replace('mobile-', '')
            screenshots_dir = os.path.join("results", "mobile", platform, "screenshots")
        elif device_type.startswith('tablet-'):
            platform = device_type.replace('tablet-', '')
            screenshots_dir = os.path.join("results", "tablet", platform, "screenshots")
        else:
            # Desktop or other devices
            screenshots_dir = os.path.join("results", device_type, "screenshots")
            
        os.makedirs(screenshots_dir, exist_ok=True)

        for violation in violations:
            for node in violation['nodes']:
                try:
                    # Use the first target selector
                    target_selector = node['target'][0]
                    element = await page.query_selector(target_selector)
                    if element:
                        # Generate a cleaner filename for the screenshot
                        # Convert device_type for filename: mobile-ios -> mobile_ios
                        clean_device_type = device_type.replace('-', '_')
                        screenshot_filename = f"screenshot_{clean_device_type}_{device_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
                        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                        
                        # Take screenshot of the element
                        await element.screenshot(path=screenshot_path)
                        
                        # Add screenshot path to the node data
                        node['screenshot'] = screenshot_path
                except Exception as e:
                    print(f"Could not take screenshot for node {node.get('target')}: {e}")
                    node['screenshot'] = None
        
        return violations

    def format_report(self, violations: list, url: str) -> dict:
        """
        Formats the list of violations into a structured dictionary.

        Args:
            violations: A list of violation dictionaries from axe-core.
            url: The URL of the page that was tested.

        Returns:
            A dictionary containing the url and the violations.
        """
        return {
            "url": url,
            "violations": violations
        }
