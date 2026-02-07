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
        api_responses = {}
        
        async def log_request(request):
            if '/api/' in request.url:
                api_calls.append(request.url)
        
        async def log_response(response):
            if '/api/' in response.url:
                try:
                    data = await response.json()
                    api_responses[response.url] = {
                        'status': response.status,
                        'keys': list(data.keys()) if isinstance(data, dict) else 'list'
                    }
                except Exception:
                    api_responses[response.url] = {'status': response.status, 'keys': 'error'}
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        print('Loading dashboard...')
        await page.goto(
            'https://env-monitor-dashboard-758343025648.us-central1.run.app',
            timeout=60000
        )
        await page.wait_for_timeout(8000)  # Wait for callbacks to complete
        
        print('\n=== API Calls Made ===')
        for url in api_calls:
            info = api_responses.get(url, {})
            status = info.get('status', '?')
            keys = info.get('keys', '?')
            print(f'  [{status}] {url}')
            print(f'       Keys: {keys}')
        if not api_calls:
            print('  (none)')
        
        # Check for specific data elements
        print('\n=== Data Presence Check ===')
        
        # Check AQI gauge
        aqi_text = await page.inner_text('#aqi-gauge-container')
        print(f'AQI Gauge: {"HAS DATA" if "Air Quality" in aqi_text else "EMPTY"}')
        
        # Check weather summary  
        weather_text = await page.inner_text('#weather-summary-container')
        has_weather = 'N/A' not in weather_text and 'Unavailable' not in weather_text
        print(f'Weather: {"HAS DATA" if has_weather else "N/A or UNAVAILABLE"}')
        print(f'  Content: {weather_text[:100]}...')
        
        # Check categories loaded indicator
        cat_summary = await page.inner_text('#categories-summary-container')
        print(f'Categories Summary: {cat_summary[:200]}...')
        
        # Check graph container
        graphs_container = await page.query_selector('#category-graphs-container')
        if graphs_container:
            graphs_html = await graphs_container.inner_html()
            graph_count = graphs_html.count('dash-graph')
            print(f'Graphs Rendered: {graph_count}')
            
            if 'No data' in graphs_html:
                print('  WARNING: Some graphs show "No data"')
        
        # Get body text for overall view
        text = await page.inner_text('body')
        
        # Check for errors
        if 'Error' in text:
            print('\n=== ERRORS FOUND ===')
            for line in text.split('\n'):
                if 'Error' in line or 'error' in line:
                    print(f'  {line[:100]}')
        
        # Take screenshot
        await page.screenshot(path='dashboard_debug.png', full_page=True)
        print('\nScreenshot saved to dashboard_debug.png')
        
        await browser.close()
        print('\n=== Test Complete ===')


if __name__ == '__main__':
    asyncio.run(test_dashboard())
