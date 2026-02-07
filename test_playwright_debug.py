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
        
        # Wait for graphs to potentially load - look for dash-graph elements
        print('Waiting for graphs to load...')
        try:
            await page.wait_for_selector('.dash-graph', timeout=15000)
            print('Found dash-graph elements')
        except Exception:
            print('No dash-graph elements found after 15s')
        
        # Additional wait for API callbacks
        await page.wait_for_timeout(5000)
        
        print('\n=== API Calls Made ===')
        for url in api_calls:
            info = api_responses.get(url, {})
            status = info.get('status', '?')
            keys = info.get('keys', '?')
            print(f'  [{status}] {url}')
            print(f'       Keys: {keys}')
        if not api_calls:
            print('  (none - callbacks may call internal API)')
        
        # Check for specific data elements
        print('\n=== Data Presence Check ===')
        
        # Check AQI gauge
        try:
            aqi_text = await page.inner_text('#aqi-gauge-container')
            print(f'AQI Gauge: {"HAS DATA" if "Air Quality" in aqi_text else "EMPTY"}')
        except Exception:
            print('AQI Gauge: NOT FOUND')
        
        # Check weather summary  
        try:
            weather_text = await page.inner_text('#weather-summary-container')
            has_weather = 'N/A' not in weather_text and 'Unavailable' not in weather_text
            print(f'Weather: {"HAS DATA" if has_weather else "N/A or UNAVAILABLE"}')
        except Exception:
            print('Weather: NOT FOUND')
        
        # Count graphs
        graphs = await page.query_selector_all('.dash-graph')
        print(f'Graph elements found: {len(graphs)}')
        
        # Check category graphs container
        try:
            graphs_container = await page.query_selector('#category-graphs-container')
            if graphs_container:
                graphs_html = await graphs_container.inner_html()
                print(f'Category graphs container HTML length: {len(graphs_html)}')
                if 'No data' in graphs_html:
                    print('  Contains "No data" message')
                if 'Select categories' in graphs_html:
                    print('  Contains "Select categories" message')
        except Exception as e:
            print(f'Category graphs check error: {e}')
        
        # Get full body text to diagnose
        body_text = await page.inner_text('body')
        
        # Check for loaded categories
        if 'Loaded:' in body_text:
            # Find the line with "Loaded:"
            for line in body_text.split('\n'):
                if 'Loaded:' in line:
                    print(f'Categories status: {line.strip()}')
                    break
        
        # Check for errors
        if 'Error' in body_text:
            print('\n=== ERRORS FOUND ===')
            for line in body_text.split('\n'):
                if 'Error' in line or 'error' in line:
                    print(f'  {line[:150]}')
        
        # Take screenshot
        await page.screenshot(path='dashboard_debug.png', full_page=True)
        print('\nScreenshot saved to dashboard_debug.png')
        
        await browser.close()
        print('\n=== Test Complete ===')


if __name__ == '__main__':
    asyncio.run(test_dashboard())
