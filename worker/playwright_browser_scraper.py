import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright

# Initialize module-level logging configuration
logger = logging.getLogger("playwright_browser_scraper")

async def _scrape_with_browser(url: str) -> str | None:
    """
    Spins up Playwright, navigates to the URL, and returns the verified page title.
    """
    async with async_playwright() as p:
        logger.info(f"Launching headless browser engine for: {url}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            logger.info(f"Navigating to browser context target: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Fetch the page title to prove it worked
            page_title = await page.title()
            logger.info(f'Successfully verified page title: "{page_title}"')
            return page_title
            
        except Exception as e:
            logger.error(f"Failed to extract page context from {url}: {e}", exc_info=True)
            return None
            
        finally:
            # Clean up browser processes
            logger.debug("Terminating browser instance processes and context loops.")
            await browser.close()

def scrape_with_browser(url: str) -> str | None:
    """
    Synchronous wrapper that bridges external synchronous code 
    to the internal async Playwright logic.
    """
    logger.info(f"Initializing standard scraping execution sequence for: {url}")
    return asyncio.run(_scrape_with_browser(url))