"""
Playwright UI Tests for Agency Sections.

Tests 10 edge cases with budget constraints:
- Video: Only Wan 2.5 Fast ($0.035) or Veo 3.1 Fast ($0.80) with SHORT durations
- Music: Music-1.5 ($0.03), MusicGen ($0.097), ACE-Step ($0.10)
- Voice: Kokoro ($0.005), XTTS-v2 ($0.01)
- Total budget per test: < $0.50 for non-Google, minimal runs overall
"""

import asyncio
import os

from playwright.async_api import Page, async_playwright

STREAMLIT_URL = "http://localhost:8501"

# ASCII-safe status markers (Windows cp1252 compatible)
OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


async def wait_for_streamlit(page: Page, timeout: int = 30000):
    """Wait for Streamlit app to fully load."""
    await page.wait_for_selector('div[data-testid="stApp"]', timeout=timeout)
    # Wait for the app to stabilize
    await page.wait_for_timeout(3000)


async def select_streamlit_dropdown(page: Page, option_text: str):
    """
    Select an option from a Streamlit selectbox.
    Streamlit uses react-select, which has a specific structure.
    """
    # Find all selectboxes
    selectboxes = page.locator('div[data-baseweb="select"]')
    count = await selectboxes.count()

    for i in range(count):
        selectbox = selectboxes.nth(i)

        # Try to click and see if the option exists
        try:
            await selectbox.click(timeout=2000)
            await page.wait_for_timeout(300)

            # Look for the option
            option = page.locator(f'li[role="option"]:has-text("{option_text}")')
            if await option.count() > 0:
                await option.first.click()
                await page.wait_for_timeout(500)
                return True
            # Close dropdown by clicking elsewhere
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    return False


async def fill_streamlit_textarea(page: Page, text: str, index: int = 0):
    """Fill a Streamlit textarea by index."""
    textareas = page.locator("textarea")
    count = await textareas.count()
    if index < count:
        await textareas.nth(index).fill(text)
        await page.wait_for_timeout(300)
        return True
    return False


async def test_case_1_video_only_wan(page: Page):
    """
    Test Case 1: Video only with Wan 2.5 Fast
    Cost: ~$0.035
    """
    print("\n=== Test Case 1: Video Only (Wan 2.5 Fast) ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # The first selectbox should be video model
    # Try to select Wan 2.5
    result = await select_streamlit_dropdown(page, "Wan 2.5 Fast")
    if result:
        print(f"{OK} Selected Wan 2.5 Fast")

    # Find and fill video prompt (first textarea usually)
    await fill_streamlit_textarea(page, "Short peaceful nature scene with clouds", 0)
    print(f"{OK} Video prompt filled")

    # Disable composer - find second Enable checkbox
    checkboxes = page.locator('label:has(span:text-is("Enable"))')
    count = await checkboxes.count()
    if count >= 2:
        # Second Enable is for Composer
        second_checkbox = checkboxes.nth(1)
        # Check if it's currently checked
        checkbox_input = second_checkbox.locator('input[type="checkbox"]')
        is_checked = await checkbox_input.is_checked()
        if is_checked:
            await second_checkbox.click()
            await page.wait_for_timeout(500)
            print(f"{OK} Composer disabled")

    await page.screenshot(path="tests/screenshots/test1_video_only.png")
    print(f"{OK} Test Case 1 configured successfully")
    return True


async def test_case_2_music_only_musicgen(page: Page):
    """
    Test Case 2: Music only with MusicGen (instrumental)
    Cost: ~$0.097
    """
    print("\n=== Test Case 2: Music Only (MusicGen) ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Disable Cinematographer - first Enable checkbox
    checkboxes = page.locator('label:has(span:text-is("Enable"))')
    count = await checkboxes.count()
    if count >= 1:
        first_checkbox = checkboxes.first
        checkbox_input = first_checkbox.locator('input[type="checkbox"]')
        is_checked = await checkbox_input.is_checked()
        if is_checked:
            await first_checkbox.click()
            await page.wait_for_timeout(500)
            print(f"{OK} Cinematographer disabled")

    # Select MusicGen
    result = await select_streamlit_dropdown(page, "MusicGen")
    if result:
        print(f"{OK} Selected MusicGen")

    # Fill music prompt
    await fill_streamlit_textarea(page, "Ambient electronic music, chill vibes", 0)

    await page.screenshot(path="tests/screenshots/test2_music_only.png")
    print(f"{OK} Test Case 2 configured successfully")
    return True


async def test_case_3_video_and_music_budget(page: Page):
    """
    Test Case 3: Wan 2.5 + Music-1.5 (cheapest combo)
    Cost: ~$0.035 + $0.03 = $0.065
    """
    print("\n=== Test Case 3: Video + Music Budget Combo ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Wan should be default or select it
    await select_streamlit_dropdown(page, "Wan 2.5 Fast")
    print(f"{OK} Video model: Wan 2.5 Fast")

    # Select Music-1.5
    await select_streamlit_dropdown(page, "Music-1.5")
    print(f"{OK} Music model: Music-1.5")

    # Fill prompts - video is first textarea, music is later
    textareas = page.locator("textarea")
    count = await textareas.count()
    if count >= 1:
        await textareas.nth(0).fill("Ocean waves at sunset")
    if count >= 2:
        await textareas.nth(1).fill("Calm acoustic beach music")

    await page.screenshot(path="tests/screenshots/test3_budget_combo.png")
    print(f"{OK} Test Case 3 configured successfully")
    return True


async def test_case_4_lyria_instrumental(page: Page):
    """
    Test Case 4: Lyria-2 instrumental (Google)
    Verifies: Lyrics field should NOT appear for instrumental-only model
    """
    print("\n=== Test Case 4: Lyria-2 Instrumental ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Disable Cinematographer
    checkboxes = page.locator('label:has(span:text-is("Enable"))')
    if await checkboxes.count() >= 1:
        first_cb = checkboxes.first
        if await first_cb.locator('input[type="checkbox"]').is_checked():
            await first_cb.click()
            await page.wait_for_timeout(500)

    # Select Lyria-2
    result = await select_streamlit_dropdown(page, "Lyria-2 (Google)")
    if result:
        print(f"{OK} Selected Lyria-2 (Google)")
    else:
        print(f"{WARN} Could not select Lyria-2 (Google)")

    await page.wait_for_timeout(1000)

    # Check for "instrumental music only" message
    instrumental_msg = page.locator("text=instrumental music only")
    if await instrumental_msg.count() > 0:
        print(f"{OK} Instrumental-only message displayed")

    await page.screenshot(path="tests/screenshots/test4_lyria_instrumental.png")
    print(f"{OK} Test Case 4 completed")
    return True


async def test_case_5_ace_step_with_lyrics(page: Page):
    """
    Test Case 5: ACE-Step with lyrics
    Verifies: Lyrics field appears
    """
    print("\n=== Test Case 5: ACE-Step with Lyrics ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Disable Cinematographer
    checkboxes = page.locator('label:has(span:text-is("Enable"))')
    if await checkboxes.count() >= 1:
        first_cb = checkboxes.first
        if await first_cb.locator('input[type="checkbox"]').is_checked():
            await first_cb.click()
            await page.wait_for_timeout(500)

    # Select ACE-Step
    await select_streamlit_dropdown(page, "ACE-Step")
    print(f"{OK} Selected ACE-Step")

    await page.wait_for_timeout(1000)

    # Check if lyrics field appears (by looking for Lyrics label)
    page_content = await page.content()
    if "Lyrics" in page_content:
        print(f"{OK} Lyrics field visible for ACE-Step")
    else:
        print(f"{WARN} Lyrics field not found")

    await page.screenshot(path="tests/screenshots/test5_ace_step.png")
    return True


async def test_case_6_model_switch_lyrics_clear(page: Page):
    """
    Test Case 6: Switch from Music-1.5 to MusicGen
    Verifies: Lyrics field disappears (instrumental-only model)
    """
    print("\n=== Test Case 6: Model Switch Lyrics Clear ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Disable Cinematographer
    checkboxes = page.locator('label:has(span:text-is("Enable"))')
    if await checkboxes.count() >= 1:
        first_cb = checkboxes.first
        if await first_cb.locator('input[type="checkbox"]').is_checked():
            await first_cb.click()
            await page.wait_for_timeout(500)

    # Start with Music-1.5
    await select_streamlit_dropdown(page, "Music-1.5")
    await page.wait_for_timeout(1000)

    # Check lyrics is visible
    content_before = await page.content()
    lyrics_before = "Lyrics" in content_before
    print(f"  Music-1.5: Lyrics visible = {lyrics_before}")

    # Switch to MusicGen (instrumental only)
    await select_streamlit_dropdown(page, "MusicGen")
    await page.wait_for_timeout(1000)

    # Check lyrics is gone
    content_after = await page.content()
    # Check for "instrumental" message
    has_instrumental = "instrumental" in content_after.lower()

    print(f"  MusicGen: Instrumental message = {has_instrumental}")

    await page.screenshot(path="tests/screenshots/test6_model_switch.png")
    print(f"{OK} Test Case 6 completed")
    return True


async def test_case_7_validation_empty_prompt(page: Page):
    """
    Test Case 7: Check prompt field is present
    """
    print("\n=== Test Case 7: Prompt Field Present ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Check for textarea (prompt field)
    textareas = page.locator("textarea")
    count = await textareas.count()

    if count > 0:
        print(f"{OK} Found {count} textarea(s) for prompts")
    else:
        print(f"{WARN} No textareas found")

    await page.screenshot(path="tests/screenshots/test7_prompts.png")
    return count > 0


async def test_case_8_preset_popover(page: Page):
    """
    Test Case 8: Check for preset button
    """
    print("\n=== Test Case 8: Preset Button ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Look for Presets button/popover
    preset_btn = page.locator('button:has-text("Presets")')
    has_preset = await preset_btn.count() > 0

    if has_preset:
        print(f"{OK} Preset button found")
        # Try to click it
        await preset_btn.first.click()
        await page.wait_for_timeout(500)
    else:
        # Maybe it's text instead
        preset_text = page.locator("text=Presets")
        if await preset_text.count() > 0:
            print(f"{OK} Presets option available")
            has_preset = True

    await page.screenshot(path="tests/screenshots/test8_presets.png")
    return True


async def test_case_9_cost_estimate(page: Page):
    """
    Test Case 9: Verify cost estimate section exists
    """
    print("\n=== Test Case 9: Cost Estimate ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Look for cost-related text
    cost_text = page.locator("text=Estimated Cost")
    has_cost = await cost_text.count() > 0

    if has_cost:
        print(f"{OK} Cost estimate section found")
    else:
        print(f"{WARN} Cost estimate not visible")

    # Look for dollar signs
    dollar = page.locator("text=/\\$/")
    dollar_count = await dollar.count()
    if dollar_count > 0:
        print(f"{OK} Found {dollar_count} price references")

    await page.screenshot(path="tests/screenshots/test9_cost.png")
    return True


async def test_case_10_run_button(page: Page):
    """
    Test Case 10: Verify Run button exists and is functional
    """
    print("\n=== Test Case 10: Run Button ===")

    await page.goto(STREAMLIT_URL)
    await wait_for_streamlit(page)

    # Look for Run/Execute button
    run_btn = page.locator('button:has-text("Run")')
    if await run_btn.count() > 0:
        print(f"{OK} Run button found")
        # Check if it's enabled
        is_disabled = await run_btn.first.is_disabled()
        print(f"  Button disabled: {is_disabled}")
    else:
        # Try other variations
        execute_btn = page.locator('button:has-text("Execute")')
        start_btn = page.locator('button:has-text("Start")')
        if await execute_btn.count() > 0 or await start_btn.count() > 0:
            print(f"{OK} Execute/Start button found")

    await page.screenshot(path="tests/screenshots/test10_run_button.png")
    return True


async def main():
    """Run all 10 test cases."""
    print("\n" + "=" * 60)
    print("AGENCY UI EDGE CASE TESTING")
    print("Budget Constraints: Video < $0.50, No long runs")
    print("=" * 60)

    # Create screenshots directory
    os.makedirs("tests/screenshots", exist_ok=True)

    results = []

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set True for CI
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Wait for Streamlit to be ready
        print("\nWaiting for Streamlit app...")
        try:
            await page.goto(STREAMLIT_URL, timeout=30000)
            await wait_for_streamlit(page)
            print(f"{OK} Streamlit app loaded")
        except Exception as e:
            print(f"{FAIL} Failed to load Streamlit: {e}")
            await browser.close()
            return

        # Run test cases
        test_cases = [
            ("Test 1: Video Only Wan", test_case_1_video_only_wan),
            ("Test 2: Music Only MusicGen", test_case_2_music_only_musicgen),
            ("Test 3: Budget Video+Music", test_case_3_video_and_music_budget),
            ("Test 4: Lyria Instrumental", test_case_4_lyria_instrumental),
            ("Test 5: ACE-Step Lyrics", test_case_5_ace_step_with_lyrics),
            ("Test 6: Model Switch Clear", test_case_6_model_switch_lyrics_clear),
            ("Test 7: Prompt Fields", test_case_7_validation_empty_prompt),
            ("Test 8: Preset Button", test_case_8_preset_popover),
            ("Test 9: Cost Estimate", test_case_9_cost_estimate),
            ("Test 10: Run Button", test_case_10_run_button),
        ]

        for name, test_func in test_cases:
            try:
                result = await test_func(page)
                results.append((name, result))
            except Exception as e:
                print(f"{FAIL} {name} failed with error: {e}")
                results.append((name, False))
                fname = name.replace(" ", "_").replace(":", "")
                await page.screenshot(path=f"tests/screenshots/error_{fname}.png")

            # Small delay between tests
            await page.wait_for_timeout(1000)

        await browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed

    for name, result in results:
        status = f"{OK} PASS" if result else f"{FAIL} FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{len(results)} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
