1. Write the FastAPI app setup, static file serving, MCP server, and `google-genai` integration in `app.py`.
2. Implement the `/chat` endpoint logic, `/sse`, `/messages/` endpoints, and `@mcp_server.tool()` in `app.py`.
3. Verify `app.py` syntax using `python3 -m py_compile app.py`.
4. Create `static/index.html` with chat UI structure, and `static/style.css` with styling.
5. Create `static/app.js` with client logic for interacting with `/chat`.
6. Verify file creation with `ls -la static/`.
7. Write unit tests in `test_app.py` to verify the `/chat` endpoint returns an expected response.
8. Write a Playwright script in `test_gui_playwright.py` to test typing and sending a message in the UI.
9. Execute tests using `python3 -m unittest test_app.py` and `python3 test_gui_playwright.py` to ensure correctness.
10. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
