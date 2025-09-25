import asyncio
from playwright.async_api import async_playwright
import argparse

async def main(url: str):
    """
    Launches a browser for manual login and saves the authentication state.
    """
    print("--- Automated Accessibility Test Agent: Authentication Setup ---")
    print("\nA browser window will now open.")
    print(f"1. Please navigate to the login page if not already there ({url}).")
    print("2. Log in with a valid user account.")
    print("3. Once you are successfully logged in and on the main dashboard/landing page, close the browser window.")
    print("\nThe authentication state will be saved automatically.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)

        # Wait for the user to close the browser.
        # This is a simple way to detect when they are done with the login process.
        page.on('close', lambda: print("\nBrowser closed. Saving authentication state..."))
        await page.wait_for_event('close')

        # Save authentication state to a file
        await context.storage_state(path="auth.json")
        await browser.close()
        
        print("\n✅ Authentication state saved successfully to 'auth.json'.")
        print("You can now run the main agent, and it will use this login session.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the authentication setup for the Accessibility Agent.")
    parser.add_argument("url", type=str, help="The starting URL for the website, preferably the login page.")
    args = parser.parse_args()
    
    asyncio.run(main(args.url))
