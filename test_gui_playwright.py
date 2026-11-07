import asyncio
from playwright.async_api import async_playwright
import uvicorn
import multiprocessing
import time
import requests
from app import app
from unittest.mock import patch

def run_server():
    from test_app import MockClient
    import app as backend_app
    backend_app.client = MockClient()
    uvicorn.run(backend_app.app, host="127.0.0.1", port=8000)

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Go to the local app
        await page.goto("http://127.0.0.1:8000")

        # Check title
        title = await page.title()
        assert title == "Google InteractionsAPI to ACP"

        # Type in the message box
        await page.fill("#user-input", "Hello world")

        # Click send
        await page.click("#send-button")

        # Wait for the response to appear (we mocked it so it should be "mocked reply")
        await page.wait_for_selector(".agent-message", timeout=5000)

        agent_messages = await page.query_selector_all(".agent-message")
        text = await agent_messages[0].inner_text()
        assert "mocked reply" in text

        print("GUI Test Passed!")
        await browser.close()

if __name__ == "__main__":
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()

    # wait for server to start
    for _ in range(30):
        try:
            requests.get("http://127.0.0.1:8000")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    try:
        asyncio.run(run_test())
    finally:
        server_process.terminate()
        server_process.join()
