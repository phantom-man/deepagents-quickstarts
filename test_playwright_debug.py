"""Playwright debug script for dashboard testing."""
import asyncio
from playwright.async_api import async_playwright


async def test_dashboard():
    """Test the dashboard and report what's working."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture API calls
        api_calls = []
        
        async def log_request(request):
            if '/api/' in request.url:
                api_calls.append(request.url)
        
        page.on('request', log_request)
        
        print('Loading dashboard...')
        await page.goto(
            'https://env-monitor-dashboard-758343025648.us-central1.run.app',
            timeout=60000
        )
        await page.wait_for_timeout(5000)
        
        print('\n=== API Calls Made ===')
        for url in api_calls:
            print(f'  {url}')
        if not api_calls:
            print('  (none)')
        
        # Get page text
        text = await page.inner_text('body')
        print('\n=== Page Content (first 2500 chars) ===')
        print(text[:2500])
        
        # Screenshot
        await page.screenshot(path='dashboard_debug.png', full_page=True)
        print('\nScreenshot saved to dashboard_debug.png')
        
        await browser.close()


if __name__ == '__main__':
    asyncio.run(test_dashboard())
