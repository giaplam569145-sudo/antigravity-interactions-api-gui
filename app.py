import json
import uuid
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Google Interactions API to OpenAI Middleware")

# A simple session store to keep track of interactions
SESSIONS: Dict[str, str] = {} # Map from our generated session_id to Google Interaction name

google_client = genai.Client(http_options={'api_version': 'v1beta'})

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible /v1/chat/completions endpoint.
    Maps OpenAI format to Google's Interactions API.
    """
    try:
        body_bytes = await request.body()
        if not body_bytes:
            raise HTTPException(status_code=400, detail="Empty request body")
        req_data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    messages = req_data.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="Messages array is required")

    model = req_data.get("model", "antigravity-preview-latest")

    session_id = request.headers.get("X-Session-Id")
    interaction_id = None

    if session_id and session_id in SESSIONS:
        interaction_id = SESSIONS[session_id]
        logger.info(f"Resuming session {session_id}, interaction_name {interaction_id}")
    else:
        if not session_id:
            session_id = str(uuid.uuid4())
        logger.info(f"Creating new session {session_id}")

    user_message = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    prompt = user_message.get("content", "")

    try:
        kwargs = {
            "agent": "antigravity-preview-latest",
            "environment": {"type": "remote"},
            "contents": [prompt]
        }
        if interaction_id:
            kwargs["name"] = interaction_id

        response = google_client.interactions.create(**kwargs)

        # Save interaction ID for future turns if it's new
        if hasattr(response, 'name') and response.name:
            interaction_id = response.name
            SESSIONS[session_id] = interaction_id

        reply_text = ""
        if hasattr(response, 'text'):
            reply_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                reply_text = response.candidates[0].content.parts[0].text
        else:
            reply_text = str(response)

        resp_data = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_text,
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "session_id": session_id,
            "interaction_id": interaction_id
        }

        headers = {"X-Session-Id": session_id}
        return JSONResponse(content=resp_data, headers=headers)

    except Exception as e:
        logger.error(f"Error calling Interactions API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
