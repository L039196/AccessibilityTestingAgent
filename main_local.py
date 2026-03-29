import argparse
import asyncio
from playwright.async_api import async_playwright
from agent.local_analyzer import LocalAnalyzer
from agent.reporter import ReportGenerator
from agent.crawler import Crawler
import os

async def main(url: str, max_pages: int):
    """
    Main function to run the local accessibility test agent across an entire website.
    """
    print("Starting Website Accessibility Crawler...")

    # 1. Initialize components
    analyzer = LocalAnalyzer()
    reporter = ReportGenerator()
    crawler = Crawler(base_url=url, max_pages=max_pages)
    
    # Clean old screenshots ONCE before all tests
    screenshots_dir = os.path.join("results", "desktop", "screenshots")
    analyzer._clean_old_screenshots(screenshots_dir)
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Collect results from all pages
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 2. Crawl the website to get all URLs
            urls_to_test = await crawler.crawl(page)
            print(f"\nFound {len(urls_to_test)} pages to test.")
            
            # 3. Analyze each URL
            for i, test_url in enumerate(urls_to_test, 1):
                print(f"\n--- Testing page {i}/{len(urls_to_test)}: {test_url} ---")
                try:
                    await page.goto(test_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Add timeout to prevent hanging on complex pages
                    violations = await asyncio.wait_for(
                        analyzer.find_issues(page),
                        timeout=90.0  # 90 second max per page
                    )
                    
                    page_result = analyzer.format_report(violations, test_url)
                    all_results.append(page_result)
                    
                except asyncio.TimeoutError:
                    print(f"⚠️  Timeout: Analysis took longer than 90 seconds for {test_url}")
                    all_results.append({
                        'url': test_url,
                        'violations': [],
                        'error': 'Timeout after 90 seconds'
                    })
                except Exception as e:
                    print(f"Could not test {test_url}: {e}")
                    # Add error result
                    all_results.append({
                        'url': test_url,
                        'violations': [],
                        'error': str(e)
                    })
            
            # 4. Generate reports in multiple formats
            print("\n" + "="*70)
            print("📊 Generating reports...")
            print("="*70)
            
            # Generate Markdown report
            md_report = reporter.generate_report(all_results, url, "md", "desktop")
            print(f"✅ Markdown report saved to: results/desktop/accessibility_report.md")
            
            # Generate HTML report
            html_report = reporter.generate_report(all_results, url, "html", "desktop")
            print(f"✅ HTML report saved to: results/desktop/accessibility_report.html")
            
            # Generate JSON report
            json_report = reporter.generate_report(all_results, url, "json", "desktop")
            print(f"✅ JSON report saved to: results/desktop/accessibility_report.json")

        finally:
            # 5. Clean up
            await browser.close()
            print("Agent finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Local Automated Accessibility Testing Agent across a website.")
    parser.add_argument("url", type=str, help="The base URL of the website to test.")
    parser.add_argument("--max-pages", type=int, default=10, help="The maximum number of pages to crawl and test.")
    
    args = parser.parse_args()
    asyncio.run(main(args.url, args.max_pages))
