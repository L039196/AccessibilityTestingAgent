import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class BrowserController:
    """Controls the browser and captures page data."""
    def __init__(self):
        self.browser = None
        self.playwright = None

    async def start(self):
        """Starts the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False) # Set headless=True for background execution

    async def stop(self):
        """Stops the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def capture_page_data(self, url: str):
        """Navigates to a URL and captures all relevant data."""
        page = await self.browser.new_page()
        try:
            await page.goto(url)
            
            screenshot = await page.screenshot()
            dom = await page.content()
            accessibility_tree = await page.accessibility.snapshot()
            
            page_data = {
                'url': url,
                'screenshot': screenshot,
                'dom': dom,
                'accessibility_tree': accessibility_tree,
            }
            return page_data
        finally:
            await page.close()

    async def get_interactive_elements(self, dom: str):
        """Extracts all interactive elements from the DOM."""
        soup = BeautifulSoup(dom, 'html.parser')
        selectors = "a, button, input, [role='button'], [role='link']"
        elements = soup.select(selectors)
        return elements

    async def perform_action(self, page, action_index: int, elements):
        """Performs an action on the page, like clicking an element."""
        if action_index < len(elements):
            element_to_click = elements[action_index]
            selector = self._get_unique_selector(element_to_click)
            if selector:
                try:
                    await page.click(selector, timeout=5000)
                except Exception as e:
                    print(f"Could not click element with selector {selector}: {e}")
        else:
            # Handle other actions like scrolling
            await page.evaluate("window.scrollBy(0, 500)")

    def _get_unique_selector(self, element):
        """Generates a unique CSS selector for a BeautifulSoup element."""
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # Fallback to a more complex selector if no ID is present
        path = []
        for parent in element.parents:
            if parent.name == 'body':
                break
            siblings = parent.find_all(element.name, recursive=False)
            if len(siblings) > 1:
                index = siblings.index(element) + 1
                path.insert(0, f"{element.name}:nth-of-type({index})")
            else:
                path.insert(0, element.name)
        
        return " > ".join(path)
