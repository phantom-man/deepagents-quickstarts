import time
from playwright.sync_api import sync_playwright

def run_streamlit_test():
    with sync_playwright() as p:
        # Launch browser (headless=True for automation)
        print("🎬 Launching Browser (Headless Mode)...")
        browser = p.chromium.launch(headless=True, slow_mo=50) 
        # Set viewport to ensure visibility
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        
        print("🌍 Opening localhost:8501...")
        try:
            page.goto("http://localhost:8501", timeout=30000)
        except Exception as e:
            print(f"❌ Failed to reach localhost:8501. Is app running? {e}")
            return

        # Wait for Streamlit to load
        print("⏳ Waiting for app interaction...")
        time.sleep(5) 
        
        print("✍️ locating Chat Input...")
        
        # Dump content for debugging if we fail
        try:
            # Wait for root element to be ATTACHED (ignoring visibility)
            page.wait_for_selector("#root", state="attached", timeout=10000)
            print("✅ Root element attached.")

            # Try to locate the text area with specific aria-label found in debug.html
            selector = 'textarea[aria-label="Enter Commercial Concept / Directive"]'
            print(f"Waiting for {selector}...")
            # Wait for attached, not visible
            page.wait_for_selector(selector, state="attached", timeout=20000)
            
            prompt = 'Create a music video called "Hello World", the song for the video should have two lyrics "Hello World", this should be a 30 second video.'
            
            print(f"⌨️ Typing prompt: {prompt[:50]}...")
            # FORCE fill
            page.fill(selector, prompt, force=True)
            time.sleep(1) # Visual pause
            
            print("👆 clicking ACTION! button...")
            try:
                # Find button by text
                # Force click even if it thinks it's not visible
                page.click('button:has-text("ACTION!")', timeout=5000, force=True)
                print("✅ ACTION button clicked!")
                
                # Wait for some result or thinking indicator
                print("⏳ Waiting for agents to start (45s)...")
                time.sleep(45) # Give it time to process
                
                # Take a screenshot to prove it worked
                page.screenshot(path="agent_running.png")
                print("📸 Screenshot saved to agent_running.png")
                
            except Exception as e:
                    print(f"❌ Could not click ACTION button: {e}")
        
        except Exception as e:
            print(f"❌ Interaction Failed: {e}")
            print("📝 Dumping page content to debug_page.html...")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
        
        browser.close()

if __name__ == "__main__":
    run_streamlit_test()
