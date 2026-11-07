import subprocess
import time
import requests
from playwright.sync_api import sync_playwright

def main():
    print("Starting backend test server...")
    proc = subprocess.Popen(["python3", "-m", "uvicorn", "app:app", "--port", "8123"])

    # Wait for server to come up
    for _ in range(20):
        try:
            r = requests.get("http://localhost:8123/api/health")
            if r.status_code == 200:
                print("Server is ready!")
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://localhost:8123/")

            # 1. Verify Page Title and Header
            title = page.title()
            print("Page Title:", title)
            assert "Antigravity" in title

            # 2. Check API Status Badge
            badge_text = page.locator("#api-status-badge").inner_text()
            print("Badge text:", badge_text)
            assert "API Key aktiv" in badge_text

            # 3. Check Live Code Generator updates
            code_display = page.locator("#code-snippet-display").inner_text()
            print("Initial Python snippet length:", len(code_display))
            assert "agent='antigravity-preview-latest'" in code_display

            # 4. Switch to cURL snippet
            page.locator('button.lang-btn[data-lang="curl"]').click()
            curl_code = page.locator("#code-snippet-display").inner_text()
            print("cURL code snippet:", curl_code[:60])
            assert "curl -X POST" in curl_code
            assert "v1beta/interactions" in curl_code

            # 5. Click a preset template chip (e.g. Hello World)
            page.locator('button.chip[data-template="hello"]').click()
            val = page.locator("#prompt-input").input_value()
            print("Template loaded prompt:", val[:30])
            assert "Hallo!" in val

            # 6. Switch tabs: Check Raw JSON and InteractionsAPI Guide
            page.locator('button.tab-btn[data-tab="guide-view"]').click()
            assert page.locator("#guide-view").is_visible()
            guide_h2 = page.locator("#guide-view h2").inner_text()
            print("Guide header:", guide_h2)
            assert "Crashkurs" in guide_h2

            # Switch back to conversation
            page.locator('button.tab-btn[data-tab="conversation-view"]').click()
            assert page.locator("#conversation-view").is_visible()

            # 7. Test Theme Toggle
            page.locator("#theme-toggle").click()
            theme = page.evaluate("() => document.body.getAttribute('data-theme')")
            print("Theme toggled to:", theme)
            assert theme == "light"

            print("All GUI end-to-end assertions PASSED successfully!")
            browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
