from playwright.async_api import Page, Playwright
from axe_core_python.async_playwright import Axe
import json
import uuid
import os
import re
import asyncio

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

        # Limit screenshots to prevent infinite loops and resource exhaustion
        max_screenshots_per_page = 10
        screenshot_count = 0

        for violation in violations:
            if screenshot_count >= max_screenshots_per_page:
                print(f"⚠️ Screenshot limit reached ({max_screenshots_per_page}), skipping remaining violations")
                break
                
            # Limit screenshots per violation to prevent too many
            max_screenshots_per_violation = 3
            violation_screenshot_count = 0
            
            for node in violation['nodes']:
                if screenshot_count >= max_screenshots_per_page or violation_screenshot_count >= max_screenshots_per_violation:
                    break
                    
                try:
                    # Generate screenshot filename
                    clean_device_type = device_type.replace('-', '_')
                    screenshot_filename = f"screenshot_{clean_device_type}_{device_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    
                    # Try enhanced screenshot capture with timeout to prevent hanging
                    captured_path = await asyncio.wait_for(
                        self._take_element_screenshot_robust(page, node, screenshot_path),
                        timeout=10.0  # 10 second timeout per screenshot
                    )
                    
                    # Validate screenshot
                    if captured_path and await self._validate_screenshot(captured_path):
                        node['screenshot'] = captured_path
                        screenshot_count += 1
                        violation_screenshot_count += 1
                        print(f"✓ Screenshot captured for violation element ({screenshot_count}/{max_screenshots_per_page})")
                    else:
                        node['screenshot'] = None
                    
                except asyncio.TimeoutError:
                    print(f"⚠️ Screenshot timeout for node {node.get('target', 'unknown')}")
                    node['screenshot'] = None
                except Exception as e:
                    print(f"⚠️ Screenshot failed for node {node.get('target', 'unknown')}: {e}")
                    node['screenshot'] = None
        
        print(f"✅ Analysis complete: {len(violations)} violations found, {screenshot_count} screenshots taken")
        return violations

    async def analyze_page(self, page: Page, url: str, device_type: str = "desktop", device_name: str = "Desktop") -> list:
        """
        Analyze a page for accessibility issues (method expected by Agent class).
        This is a wrapper around find_issues for compatibility.
        
        Args:
            page: The Playwright Page object to analyze.
            url: The URL being analyzed.
            device_type: The type of device (desktop, mobile, tablet).
            device_name: The specific device name.
            
        Returns:
            A list of violation dictionaries with enhanced metadata.
        """
        try:
            violations = await self.find_issues(page, device_type, device_name)
            
            # Add metadata to each violation
            for violation in violations:
                violation['url'] = url
                violation['device_type'] = device_type
                violation['device_name'] = device_name
                violation['timestamp'] = violation.get('timestamp', '')
                
            return violations
            
        except Exception as e:
            print(f"❌ Error analyzing page {url}: {e}")
            return [{
                'url': url,
                'device_type': device_type,
                'device_name': device_name,
                'error': str(e),
                'description': f"Analysis failed for {url}",
                'violations': []
            }]

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
                    # Check if element is too small for meaningful screenshot
                    min_width, min_height = 50, 20
                    if bounding_box['width'] < min_width or bounding_box['height'] < min_height:
                        print(f"Element too small ({bounding_box['width']}x{bounding_box['height']}), using context screenshot")
                        # Take screenshot with padding around the element
                        await self._take_context_screenshot(page, element, screenshot_path)
                    else:
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
            # Try to find element for highlighting
            element = await page.query_selector(target_selector)
            if element:
                await self._highlight_target_element(page, element)
            else:
                # Use the old text-based highlighting as fallback
                await self._highlight_element_area(page, target_selector)
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"✓ Page screenshot with highlighting successful")
            return screenshot_path
        except Exception as e:
            print(f"Strategy 4 failed for page screenshot: {e}")

        print(f"✗ All screenshot strategies failed for: {target_selector[:50]}...")
        return None

    async def _take_context_screenshot(self, page: Page, element, screenshot_path: str) -> None:
        """
        Take a screenshot with context around a small element.
        
        Args:
            page: The Playwright Page object
            element: The element to capture with context
            screenshot_path: Path where screenshot should be saved
        """
        try:
            # Get element bounding box
            bounding_box = await element.bounding_box()
            if not bounding_box:
                # Fallback to full page screenshot
                await page.screenshot(path=screenshot_path, full_page=False)
                return
            
            # Calculate context area with padding
            padding = 100  # pixels
            viewport_size = page.viewport_size
            if callable(viewport_size):
                viewport_size = await viewport_size()
            
            # Ensure we don't go outside viewport bounds
            x = max(0, bounding_box['x'] - padding)
            y = max(0, bounding_box['y'] - padding)
            width = min(viewport_size['width'] - x, bounding_box['width'] + (2 * padding))
            height = min(viewport_size['height'] - y, bounding_box['height'] + (2 * padding))
            
            # Ensure minimum screenshot size
            min_size = 200
            if width < min_size:
                width = min(min_size, viewport_size['width'])
                x = max(0, bounding_box['x'] - (width - bounding_box['width']) // 2)
            if height < min_size:
                height = min(min_size, viewport_size['height'])
                y = max(0, bounding_box['y'] - (height - bounding_box['height']) // 2)
            
            # Highlight the target element before screenshot
            await self._highlight_target_element(page, element)
            
            # Take context screenshot
            await page.screenshot(
                path=screenshot_path,
                clip={'x': x, 'y': y, 'width': width, 'height': height}
            )
            
            print(f"Context screenshot taken: {width}x{height} with element highlighted")
            
        except Exception as e:
            print(f"Context screenshot failed, taking full page: {e}")
            # Fallback to full page screenshot
            await page.screenshot(path=screenshot_path, full_page=False)

    async def _highlight_target_element(self, page: Page, element) -> None:
        """
        Add visual highlighting to the target element for screenshots.
        
        Args:
            page: The Playwright Page object
            element: The element to highlight
        """
        try:
            # Inject highlighting script for the specific element (simplified to prevent loops)
            highlight_script = """
            (element) => {
                if (element) {
                    // Remove any existing highlights (limit to prevent infinite operations)
                    const existingHighlights = document.querySelectorAll('.accessibility-highlight');
                    if (existingHighlights.length < 100) {  // Safety limit
                        existingHighlights.forEach(h => h.remove());
                    }
                    
                    // Create simple highlight overlay
                    const highlight = document.createElement('div');
                    const rect = element.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        highlight.style.position = 'fixed';
                        highlight.style.left = rect.left + 'px';
                        highlight.style.top = rect.top + 'px';
                        highlight.style.width = rect.width + 'px';
                        highlight.style.height = rect.height + 'px';
                        highlight.style.border = '2px solid red';
                        highlight.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                        highlight.style.zIndex = '999999';
                        highlight.style.pointerEvents = 'none';
                        highlight.className = 'accessibility-highlight';
                        document.body.appendChild(highlight);
                    }
                }
            }
            """
            await element.evaluate(highlight_script)
            
            # Shorter wait to prevent hanging
            await page.wait_for_timeout(200)
        except Exception as e:
            # Silently fail highlighting to prevent spam
            pass

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

    async def _validate_screenshot(self, screenshot_path: str) -> bool:
        """
        Validate that a screenshot is not empty or too small.
        
        Args:
            screenshot_path: Path to the screenshot file
            
        Returns:
            True if screenshot is valid, False otherwise
        """
        try:
            import os
            from PIL import Image
            
            # Check file size
            if not os.path.exists(screenshot_path):
                return False
                
            file_size = os.path.getsize(screenshot_path)
            if file_size < 1000:  # Less than 1KB is suspicious
                print(f"Screenshot file too small: {file_size} bytes")
                return False
            
            # Check image dimensions
            with Image.open(screenshot_path) as img:
                width, height = img.size
                if width < 50 or height < 20:
                    print(f"Screenshot dimensions too small: {width}x{height}")
                    return False
                
                # Check if image is mostly empty (same color)
                pixels = list(img.getdata())
                if len(set(pixels)) < 5:  # Less than 5 unique colors
                    print(f"Screenshot appears mostly empty (only {len(set(pixels))} unique colors)")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Error validating screenshot: {e}")
            return False

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
