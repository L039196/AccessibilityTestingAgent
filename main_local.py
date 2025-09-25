import argparse
from playwright.sync_api import sync_playwright
from agent.local_analyzer import LocalAnalyzer
from agent.reporter import ReportGenerator
from agent.crawler import Crawler
import os

def main(url: str, max_pages: int):
    """
    Main function to run the local accessibility test agent across an entire website.
    """
    print("Starting Website Accessibility Crawler...")

    # 1. Initialize components
    analyzer = LocalAnalyzer()
    reporter = ReportGenerator(report_format="md")
    crawler = Crawler(base_url=url, max_pages=max_pages)
    
    full_report = f"# Accessibility Report for {url}\n\n"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 2. Crawl the website to get all URLs
            urls_to_test = crawler.crawl(page)
            print(f"\nFound {len(urls_to_test)} pages to test.")
            
            # 3. Analyze each URL
            for i, test_url in enumerate(urls_to_test, 1):
                print(f"\n--- Testing page {i}/{len(urls_to_test)}: {test_url} ---")
                try:
                    page.goto(test_url, wait_until="domcontentloaded")
                    violations = analyzer.find_issues(page)
                    page_report = analyzer.format_report(violations, test_url)
                    full_report += page_report
                except Exception as e:
                    print(f"Could not test {test_url}: {e}")
            
            # 4. Save the consolidated report
            report_filename = "accessibility_full_website_report.md"
            reporter.save_report(full_report, report_filename)
            print(f"\nFull website report saved to {os.path.abspath(report_filename)}")

        finally:
            # 5. Clean up
            browser.close()
            print("Agent finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Local Automated Accessibility Testing Agent across a website.")
    parser.add_argument("url", type=str, help="The base URL of the website to test.")
    parser.add_argument("--max-pages", type=int, default=10, help="The maximum number of pages to crawl and test.")
    
    args = parser.parse_args()
    main(args.url, args.max_pages)
