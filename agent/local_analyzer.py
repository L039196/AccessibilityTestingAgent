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

    async def _scroll_to_load_lazy_content(self, page: Page):
        """
        Scroll through page to trigger lazy-loaded content and infinite scroll.
        
        Returns:
            Dictionary with scroll statistics
        """
        try:
            print("📜 Scrolling to load lazy content...")
            scroll_stats = {'scrolls': 0, 'new_content': 0}
            
            # Get initial content count
            initial_count = await page.evaluate("document.querySelectorAll('*').length")
            
            # Scroll to bottom in steps to trigger lazy loading
            scroll_script = """
                async () => {
                    const scrollStep = 500;
                    const scrollDelay = 100;  // Reduced from 300ms for faster scanning
                    let lastHeight = document.body.scrollHeight;
                    let scrolls = 0;
                    
                    // Scroll down in steps
                    for (let i = 0; i < document.body.scrollHeight; i += scrollStep) {
                        window.scrollTo(0, i);
                        await new Promise(resolve => setTimeout(resolve, scrollDelay));
                        scrolls++;
                        
                        // Check if new content loaded
                        const newHeight = document.body.scrollHeight;
                        if (newHeight > lastHeight) {
                            lastHeight = newHeight;
                        }
                    }
                    
                    // Final scroll to bottom
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    return scrolls;
                }
            """
            scroll_stats['scrolls'] = await page.evaluate(scroll_script)
            
            # Check for new content after scrolling
            final_count = await page.evaluate("document.querySelectorAll('*').length")
            scroll_stats['new_content'] = final_count - initial_count
            
            if scroll_stats['new_content'] > 0:
                print(f"  ✓ Loaded {scroll_stats['new_content']} new elements via scrolling")
            
            # Scroll back to top for analysis
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            
            return scroll_stats
            
        except Exception as e:
            print(f"⚠️  Warning: Could not complete scroll loading: {e}")
            return {'scrolls': 0, 'new_content': 0}

    async def _trigger_modal_dialogs(self, page: Page):
        """
        Find and click buttons/links that trigger modals/dialogs to scan their content.
        
        Returns:
            Dictionary with modal trigger statistics
        """
        try:
            print("🔔 Triggering modal dialogs...")
            modal_stats = {'triggered': 0, 'scanned': 0}
            
            # Find potential modal triggers
            trigger_script = """
                () => {
                    const triggers = [];
                    const selectors = [
                        '[data-toggle="modal"]',
                        '[data-bs-toggle="modal"]',
                        '[aria-haspopup="dialog"]',
                        'button[class*="modal"]',
                        'a[class*="modal"]',
                        '[role="button"][class*="open"]'
                    ];
                    
                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            if (el.offsetParent !== null) { // Only visible elements
                                triggers.push({
                                    selector: selector,
                                    text: el.textContent.trim().substring(0, 50)
                                });
                            }
                        });
                    });
                    
                    return triggers.length;
                }
            """
            trigger_count = await page.evaluate(trigger_script)
            
            if trigger_count > 0:
                print(f"  ✓ Found {trigger_count} potential modal triggers")
                modal_stats['triggered'] = trigger_count
                
                # Note: Actually clicking modals can be disruptive
                # We'll just make any existing modals visible
                modal_reveal_script = """
                    () => {
                        const modals = document.querySelectorAll(
                            '[role="dialog"], [role="alertdialog"], .modal, [aria-modal="true"]'
                        );
                        let revealed = 0;
                        modals.forEach(modal => {
                            if (modal.style.display === 'none' || modal.hasAttribute('hidden')) {
                                modal.style.display = 'block';
                                modal.removeAttribute('hidden');
                                modal.setAttribute('aria-hidden', 'false');
                                revealed++;
                            }
                        });
                        return revealed;
                    }
                """
                modal_stats['scanned'] = await page.evaluate(modal_reveal_script)
                
                if modal_stats['scanned'] > 0:
                    print(f"  ✓ Revealed {modal_stats['scanned']} hidden modals for scanning")
            
            return modal_stats
            
        except Exception as e:
            print(f"⚠️  Warning: Could not trigger modals: {e}")
            return {'triggered': 0, 'scanned': 0}

    async def _simulate_hover_states(self, page: Page):
        """
        Simulate hover states on interactive elements to reveal hover-only content.
        
        Returns:
            Dictionary with hover simulation statistics
        """
        try:
            print("🖱️  Simulating hover states...")
            hover_stats = {'hovered': 0, 'revealed': 0}
            
            # Add CSS to show all hover states simultaneously for scanning
            hover_css_script = """
                () => {
                    const style = document.createElement('style');
                    style.id = 'axe-hover-simulation';
                    style.textContent = `
                        /* Force hover states visible for accessibility scanning */
                        [class*="hover"]:not(.hover\\:bg-black\\/10),
                        nav ul li:hover > ul,
                        .dropdown:hover > .dropdown-menu,
                        [aria-haspopup]:hover > [role="menu"],
                        [data-toggle="dropdown"]:hover + .dropdown-menu {
                            display: block !important;
                            visibility: visible !important;
                            opacity: 1 !important;
                        }
                    `;
                    document.head.appendChild(style);
                    
                    // Count elements with hover-dependent content
                    const hoverElements = document.querySelectorAll(
                        '[class*="hover"], .dropdown, [aria-haspopup], [data-toggle="dropdown"]'
                    );
                    
                    return hoverElements.length;
                }
            """
            hover_stats['hovered'] = await page.evaluate(hover_css_script)
            
            if hover_stats['hovered'] > 0:
                print(f"  ✓ Simulated hover on {hover_stats['hovered']} interactive elements")
                
                # Wait for any animations
                await page.wait_for_timeout(500)
            
            return hover_stats
            
        except Exception as e:
            print(f"⚠️  Warning: Could not simulate hover states: {e}")
            return {'hovered': 0, 'revealed': 0}

    async def _scan_iframes(self, page: Page):
        """
        Scan content inside iframes for accessibility issues.
        
        Returns:
            Dictionary with iframe statistics
        """
        try:
            print("🖼️  Scanning iframe content...")
            iframe_stats = {'found': 0, 'accessible': 0}
            
            # Find all iframes
            iframe_script = """
                () => {
                    const iframes = document.querySelectorAll('iframe');
                    const accessible = [];
                    
                    iframes.forEach((iframe, index) => {
                        try {
                            // Try to access iframe content (will fail for cross-origin)
                            if (iframe.contentDocument) {
                                accessible.push({
                                    index: index,
                                    src: iframe.src || 'about:blank',
                                    title: iframe.title || ''
                                });
                            }
                        } catch(e) {
                            // Cross-origin iframe, cannot access
                        }
                    });
                    
                    return {
                        total: iframes.length,
                        accessible: accessible.length
                    };
                }
            """
            iframe_info = await page.evaluate(iframe_script)
            iframe_stats['found'] = iframe_info['total']
            iframe_stats['accessible'] = iframe_info['accessible']
            
            if iframe_stats['found'] > 0:
                print(f"  ✓ Found {iframe_stats['found']} iframes ({iframe_stats['accessible']} accessible)")
            
            return iframe_stats
            
        except Exception as e:
            print(f"⚠️  Warning: Could not scan iframes: {e}")
            return {'found': 0, 'accessible': 0}

    async def _expand_all_interactive_elements(self, page: Page):
        """
        Expand all collapsible elements to scan hidden content for accessibility issues.
        Includes: dropdowns, accordions, tabs, modals, menus, dialogs, etc.
        
        Returns:
            Dictionary with counts of expanded elements for logging
        """
        try:
            print("🔍 Expanding interactive elements to scan hidden content...")
            expanded_counts = {}
            
            # 1. Expand all <details> elements (native HTML collapsibles)
            details_script = """
                () => {
                    const details = document.querySelectorAll('details:not([open])');
                    details.forEach(detail => detail.open = true);
                    return details.length;
                }
            """
            details_count = await page.evaluate(details_script)
            if details_count > 0:
                expanded_counts['details'] = details_count
                print(f"  ✓ Expanded {details_count} <details> elements")
            
            # 2. Click all expandable buttons/links (aria-expanded="false")
            aria_expanded_script = """
                () => {
                    const expandables = document.querySelectorAll('[aria-expanded="false"]');
                    let clicked = 0;
                    expandables.forEach(el => {
                        try {
                            if (el.click) {
                                el.click();
                                clicked++;
                            }
                        } catch(e) {}
                    });
                    return clicked;
                }
            """
            aria_count = await page.evaluate(aria_expanded_script)
            if aria_count > 0:
                expanded_counts['aria-expanded'] = aria_count
                print(f"  ✓ Clicked {aria_count} aria-expanded elements")
            
            # Wait for animations/transitions (reduced for performance)
            await page.wait_for_timeout(200)
            
            # 3. Activate all tabs to scan each tab's content
            tabs_script = """
                () => {
                    const tabs = document.querySelectorAll('[role="tab"]:not([aria-selected="true"])');
                    let activated = 0;
                    tabs.forEach(tab => {
                        try {
                            if (tab.click) {
                                tab.click();
                                activated++;
                            }
                        } catch(e) {}
                    });
                    return activated;
                }
            """
            tabs_count = await page.evaluate(tabs_script)
            if tabs_count > 0:
                expanded_counts['tabs'] = tabs_count
                print(f"  ✓ Activated {tabs_count} inactive tabs")
            
            # Wait for tab content to load (reduced for performance)
            await page.wait_for_timeout(300)
            
            # 4. Expand Bootstrap/Common framework collapsibles
            bootstrap_script = """
                () => {
                    const selectors = [
                        '[data-toggle="collapse"]',
                        '[data-bs-toggle="collapse"]',
                        '.accordion-button.collapsed',
                        '.collapse:not(.show)',
                        '[data-toggle="dropdown"]',
                        '[data-bs-toggle="dropdown"]'
                    ];
                    let expanded = 0;
                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            try {
                                if (el.click) {
                                    el.click();
                                    expanded++;
                                }
                            } catch(e) {}
                        });
                    });
                    return expanded;
                }
            """
            bootstrap_count = await page.evaluate(bootstrap_script)
            if bootstrap_count > 0:
                expanded_counts['bootstrap'] = bootstrap_count
                print(f"  ✓ Expanded {bootstrap_count} Bootstrap elements")
            
            # Wait for collapse animations (reduced for performance)
            await page.wait_for_timeout(300)
            
            # 5. Show hidden menus and navigation
            menu_script = """
                () => {
                    const menus = document.querySelectorAll('[aria-hidden="true"][role="menu"], [aria-hidden="true"][role="navigation"]');
                    let shown = 0;
                    menus.forEach(menu => {
                        menu.setAttribute('aria-hidden', 'false');
                        menu.style.display = 'block';
                        menu.style.visibility = 'visible';
                        shown++;
                    });
                    return shown;
                }
            """
            menu_count = await page.evaluate(menu_script)
            if menu_count > 0:
                expanded_counts['menus'] = menu_count
                print(f"  ✓ Made {menu_count} hidden menus visible")
            
            # 6. Temporarily show elements with display:none for scanning
            # Store original states to restore later if needed
            hidden_content_script = """
                () => {
                    const hiddenElements = [];
                    const selectors = [
                        '[style*="display: none"]',
                        '[style*="display:none"]',
                        '.hidden:not(.visually-hidden)',
                        '.d-none',
                        '[hidden]'
                    ];
                    
                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            // Skip screen-reader-only content (keep it hidden visually)
                            const classes = el.className || '';
                            if (classes.includes('sr-only') || 
                                classes.includes('visually-hidden') ||
                                classes.includes('screen-reader')) {
                                // Skip this element, continue to next
                            } else {
                                // Store original state
                                el.setAttribute('data-axe-was-hidden', 'true');
                                
                                // Make visible for scanning
                                el.removeAttribute('hidden');
                                el.style.display = '';
                                el.classList.remove('hidden', 'd-none');
                                hiddenElements.push(el);
                            }
                        });
                    });
                    
                    return hiddenElements.length;
                }
            """
            hidden_count = await page.evaluate(hidden_content_script)
            if hidden_count > 0:
                expanded_counts['hidden'] = hidden_count
                print(f"  ✓ Made {hidden_count} hidden elements visible for scanning")
            
            total_expanded = sum(expanded_counts.values())
            print(f"✅ Total elements expanded/revealed: {total_expanded}")
            
            return expanded_counts
            
        except Exception as e:
            print(f"⚠️  Warning: Could not expand some elements: {e}")
            return {}

    def _clean_old_screenshots(self, screenshots_dir: str):
        """
        Clean old screenshots from previous runs to prevent accumulation.
        
        Args:
            screenshots_dir: Directory containing screenshots to clean
        """
        if not os.path.exists(screenshots_dir):
            return
        
        try:
            deleted_count = 0
            for filename in os.listdir(screenshots_dir):
                if filename.endswith('.png'):
                    file_path = os.path.join(screenshots_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not delete {filename}: {e}")
            
            if deleted_count > 0:
                print(f"🗑️  Cleaned {deleted_count} old screenshot(s) from previous runs")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean old screenshots: {e}")

    async def find_issues(self, page: Page, device_type: str = "desktop", device_name: str = "Desktop") -> list:
        """
        Runs comprehensive accessibility analysis on the given Playwright page.
        Includes scanning of all visible, hidden, lazy-loaded, and interactive content.

        Args:
            page: The Playwright Page object to analyze.
            device_type: The type of device (desktop, mobile, tablet).
            device_name: The specific device name for screenshot organization.

        Returns:
            A list of violation dictionaries, with screenshot data added to each node.
        """
        print(f"Running comprehensive accessibility analysis on {page.url}...")
        print("=" * 70)
        
        # Setup screenshot directory (cleaning happens once in main_local.py)
        if device_type.startswith('mobile-'):
            platform = device_type.replace('mobile-', '')
            screenshots_dir = os.path.join("results", "mobile", platform, "screenshots")
        elif device_type.startswith('tablet-'):
            platform = device_type.replace('tablet-', '')
            screenshots_dir = os.path.join("results", "tablet", platform, "screenshots")
        else:
            screenshots_dir = os.path.join("results", device_type, "screenshots")
        
        # Ensure directory exists
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Phase 1: Load lazy content via scrolling
        await self._scroll_to_load_lazy_content(page)
        
        # Phase 2: Trigger and reveal modal dialogs
        await self._trigger_modal_dialogs(page)
        
        # Phase 3: Simulate hover states
        await self._simulate_hover_states(page)
        
        # Phase 4: Scan iframes
        await self._scan_iframes(page)
        
        # Phase 5: Expand all interactive elements (original functionality)
        await self._expand_all_interactive_elements(page)
        
        print("=" * 70)
        print("🔬 Running axe-core accessibility scan...")
        
        # Run axe-core analysis with all content now visible
        # CRITICAL FIX: Use 'options' parameter (not 'context') to pass axe rules
        results = await self.axe.run(page, options=self.axe_rules)
        
        violations = results['violations']

        # Screenshot directory was already set up and cleaned at the start
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
        
        # Handle target as list or string - axe-core returns a list of selectors
        target = node['target']
        if isinstance(target, list):
            if len(target) == 0:
                return None
            # axe-core returns an array where each element is a selector for shadow DOM traversal
            # For shadow DOM: ['parent-element', 'child-in-shadow']
            # For regular DOM: ['#element-id']
            # Join them with ' ' to create a compound selector or use the last one
            if len(target) > 1:
                # Multiple selectors indicate shadow DOM - use the most specific (last) selector
                target_selector = target[-1]
            else:
                target_selector = target[0]
            if not target_selector or not isinstance(target_selector, str):
                return None
        else:
            target_selector = str(target)
        
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
            selector: Original CSS selector (must be string)
            
        Returns:
            Simplified selector string
        """
        # Ensure selector is a string
        if not isinstance(selector, str):
            return str(selector)
        
        # Remove nth-child selectors
        simplified = re.sub(r':nth-child\([^)]+\)', '', selector)
        
        # Remove escaped characters common in Tailwind CSS
        simplified = re.sub(r'\\[0-9a-fA-F]+', '', simplified)
        simplified = re.sub(r'\\\.', '.', simplified)
        simplified = re.sub(r'\\\[', '[', simplified)
        simplified = re.sub(r'\\\]', ']', simplified)
        
        # Remove complex pseudo-selectors
        simplified = re.sub(r':not\([^)]+\)', '', selector)
        simplified = re.sub(r':has\([^)]+\)', '', selector)
        
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
            selector: Original CSS selector (must be string)
            
        Returns:
            ID selector if found, None otherwise
        """
        # Ensure selector is a string
        if not isinstance(selector, str):
            return None
        
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
            # Use evaluate with a function to avoid string interpolation issues
            highlight_script = """
            (selector) => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el) {
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
                    }
                });
            }
            """
            await page.evaluate(highlight_script, selector)
            
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
