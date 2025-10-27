from playwright.async_api import Page, Playwright
from axe_core_python.async_playwright import Axe
import json
import uuid
import os
import re

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
                    # Generate screenshot filename
                    clean_device_type = device_type.replace('-', '_')
                    screenshot_filename = f"screenshot_{clean_device_type}_{device_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    
                    # Try enhanced screenshot capture with multiple strategies
                    captured_path = await self._take_element_screenshot_robust(page, node, screenshot_path)
                    node['screenshot'] = captured_path
                    
                except Exception as e:
                    print(f"Could not take screenshot for node {node.get('target')}: {e}")
                    node['screenshot'] = None
        
        return violations

    async def _take_element_screenshot_robust(self, page: Page, node: dict, screenshot_path: str) -> str:
        """
        Enhanced screenshot capture with multiple fallback strategies.
        
        Args:
            page: The Playwright Page object
            node: The violation node containing target selectors
            screenshot_path: Path where screenshot should be saved
            
        Returns:
            Screenshot path if successful, None if all strategies fail
        """
        if not node.get('target'):
            return None
            
        target_selector = node['target'][0]
        
        # Strategy 1: Direct element screenshot with visibility check
        try:
            element = await page.query_selector(target_selector)
            if element:
                # Check if element is visible and has dimensions
                is_visible = await element.is_visible()
                bounding_box = await element.bounding_box()
                
                if is_visible and bounding_box and bounding_box['width'] > 0 and bounding_box['height'] > 0:
                    await element.screenshot(path=screenshot_path, timeout=10000)
                    print(f"✓ Direct screenshot successful for: {target_selector[:50]}...")
                    return screenshot_path
        except Exception as e:
            print(f"Strategy 1 failed for {target_selector[:50]}...: {e}")

        # Strategy 2: Simplified selector
        try:
            simplified_selector = self._simplify_selector(target_selector)
            if simplified_selector != target_selector:
                element = await page.query_selector(simplified_selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.screenshot(path=screenshot_path, timeout=10000)
                        print(f"✓ Simplified selector screenshot successful: {simplified_selector[:50]}...")
                        return screenshot_path
        except Exception as e:
            print(f"Strategy 2 failed for simplified selector: {e}")

        # Strategy 3: ID-based fallback
        try:
            id_selector = self._extract_id_selector(target_selector)
            if id_selector:
                element = await page.query_selector(id_selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.screenshot(path=screenshot_path, timeout=10000)
                        print(f"✓ ID-based screenshot successful: {id_selector}")
                        return screenshot_path
        except Exception as e:
            print(f"Strategy 3 failed for ID selector: {e}")

        # Strategy 4: Page screenshot with element highlighting
        try:
            await self._highlight_element_area(page, target_selector)
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"✓ Page screenshot with highlighting successful")
            return screenshot_path
        except Exception as e:
            print(f"Strategy 4 failed for page screenshot: {e}")

        print(f"✗ All screenshot strategies failed for: {target_selector[:50]}...")
        return None

    def _simplify_selector(self, selector: str) -> str:
        """
        Simplify complex CSS selectors by removing problematic parts.
        
        Args:
            selector: Original CSS selector
            
        Returns:
            Simplified selector string
        """
        # Remove nth-child selectors
        simplified = re.sub(r':nth-child\([^)]+\)', '', selector)
        
        # Remove escaped characters common in Tailwind CSS
        simplified = re.sub(r'\\[0-9a-fA-F]+', '', simplified)
        simplified = re.sub(r'\\\.', '.', simplified)
        simplified = re.sub(r'\\\[', '[', simplified)
        simplified = re.sub(r'\\\]', ']', simplified)
        
        # Remove complex pseudo-selectors
        simplified = re.sub(r':not\([^)]+\)', '', simplified)
        simplified = re.sub(r':has\([^)]+\)', '', simplified)
        
        # Clean up multiple spaces and leading/trailing spaces
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        
        # If selector becomes empty or too simple, return first part
        if not simplified or simplified in [' ', '.', '#']:
            parts = selector.split(' ')
            for part in parts:
                if part and (part.startswith('#') or part.startswith('.')):
                    return part
        
        return simplified if simplified else selector

    def _extract_id_selector(self, selector: str) -> str:
        """
        Extract ID-based selector from complex selector.
        
        Args:
            selector: Original CSS selector
            
        Returns:
            ID selector if found, None otherwise
        """
        # Look for ID in the selector
        id_match = re.search(r'#([a-zA-Z0-9_-]+)', selector)
        if id_match:
            return f"#{id_match.group(1)}"
        
        # Look for data-id or similar attributes
        data_id_match = re.search(r'\[data-id="([^"]+)"\]', selector)
        if data_id_match:
            return f'[data-id="{data_id_match.group(1)}"]'
            
        return None

    async def _highlight_element_area(self, page: Page, selector: str) -> None:
        """
        Highlight the area where the element should be for page screenshots.
        
        Args:
            page: The Playwright Page object
            selector: CSS selector of the element to highlight
        """
        try:
            # Inject highlighting script
            highlight_script = f"""
            (function() {{
                const elements = document.querySelectorAll('{selector}');
                elements.forEach(el => {{
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        const highlight = document.createElement('div');
                        highlight.style.position = 'fixed';
                        highlight.style.left = rect.left + 'px';
                        highlight.style.top = rect.top + 'px';
                        highlight.style.width = Math.max(rect.width, 10) + 'px';
                        highlight.style.height = Math.max(rect.height, 10) + 'px';
                        highlight.style.border = '3px solid red';
                        highlight.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                        highlight.style.zIndex = '10000';
                        highlight.style.pointerEvents = 'none';
                        highlight.className = 'accessibility-highlight';
                        document.body.appendChild(highlight);
                    }}
                }});
            }})();
            """
            await page.evaluate(highlight_script)
            
            # Wait a bit for highlight to render
            await page.wait_for_timeout(500)
        except Exception as e:
            print(f"Could not highlight element: {e}")

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
