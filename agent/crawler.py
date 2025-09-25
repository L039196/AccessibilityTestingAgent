from playwright.async_api import Page
from urllib.parse import urljoin, urlparse

class Crawler:
    """
    A simple web crawler to find all unique, same-domain links on a website.
    """
    def __init__(self, base_url: str, max_pages: int = 10):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.urls_to_visit = [base_url]
        self.visited_urls = set()

    async def crawl(self, page: Page) -> list[str]:
        """
        Crawls the website starting from the base URL to find links.

        Args:
            page: The initial Playwright Page object to start crawling from.

        Returns:
            A list of unique URLs found on the website, up to max_pages.
        """
        while self.urls_to_visit and len(self.visited_urls) < self.max_pages:
            url = self.urls_to_visit.pop(0)
            if url in self.visited_urls:
                continue

            try:
                print(f"Crawling: {url}")
                await page.goto(url, wait_until="domcontentloaded")
                self.visited_urls.add(url)

                links = await page.eval_on_selector_all("a[href]", "elements => elements.map(el => el.href)")
                
                for link in links:
                    absolute_link = urljoin(url, link)
                    parsed_link = urlparse(absolute_link)
                    
                    # Ensure the link is on the same domain and is a new, valid URL
                    if (parsed_link.netloc == self.domain and 
                        parsed_link.scheme in ["http", "https"] and
                        absolute_link not in self.visited_urls and
                        absolute_link not in self.urls_to_visit):
                        self.urls_to_visit.append(absolute_link)

            except Exception as e:
                print(f"Could not crawl {url}: {e}")

        return list(self.visited_urls)
