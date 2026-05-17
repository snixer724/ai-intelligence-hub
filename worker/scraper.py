import asyncio
from playwright.async_api import async_playwright

async def run_playwright_check(url: str) -> str | None:
    """
    Spins up Playwright, navigates to the URL, and returns the verified page title.
    """
    async with async_playwright() as p:
        # Launch a headless browser instance
        print(f'[PLAYWRIGHT] Launching headless browser for {url}', flush=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f'[PLAYWRIGHT] Launching browser to navigate to {url}', flush=True)
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Fetch the page title to prove it worked
            page_title = await page.title()
            print(f'[PLAYWRIGHT] Successfully verified page title: "{page_title}"', flush=True)
            return page_title
            
        except Exception as e:
            print(f'[PLAYWRIGHT ERROR] Failed to load {url}: {e}', flush=True)
            return None
            
        finally:
            # Clean up browser processes
            await browser.close()

def get_url_title(url: str) -> str | None:
    """
    Synchronous wrapper that bridges external synchronous code 
    to the internal async Playwright logic.
    """
    print(f'[PLAYWRIGHT] Starting Playwright check for {url}', flush=True)
    return asyncio.run(run_playwright_check(url))