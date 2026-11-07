from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from mcp.server.sse import SseServerTransport
from mcp.server.mcpserver import MCPServer
from mcp.types import Tool, TextContent
from pydantic import BaseModel
from google import genai
import mcp.types as types
import os
import uuid
import anyio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

sse_transport = SseServerTransport("/messages/")
mcp_server = MCPServer("antigravity-bridge")

client = genai.Client(http_options={'api_version': 'v1beta'})
interaction = None
interactions = {}

class ChatRequest(BaseModel):
    message: str
    interaction_id: str | None = None

@mcp_server.tool()
async def send_message(message: str) -> list[TextContent]:
    """Send a message to the Google Interactions API via antigravity agent"""
    global interaction
    try:
        if interaction is None:
             global client
             interaction = client.interactions.create(
                 agent='antigravity-preview-latest',
                 environment={'type': 'remote'}
             )

        if hasattr(interaction, "send_message"):
             resp = interaction.send_message(message)
             reply_text = resp.text if hasattr(resp, "text") else str(resp)
        elif hasattr(interaction, "send"):
             resp = interaction.send(message)
             reply_text = ""
             if hasattr(resp, "text"):
                 reply_text = resp.text
             else:
                 for event in resp:
                     if hasattr(event, "text"):
                          reply_text += event.text
                     elif hasattr(event, "content") and hasattr(event.content, "parts"):
                          for part in event.content.parts:
                              if hasattr(part, "text") and part.text:
                                  reply_text += part.text
        else:
             reply_text = "Unsupported interaction method"
        return [TextContent(type="text", text=reply_text)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

@app.post("/chat")
async def chat(request: ChatRequest):
    interaction_id = request.interaction_id

    if not interaction_id or interaction_id not in interactions:
        interaction_id = str(uuid.uuid4())
        interactions[interaction_id] = client.interactions.create(
            agent='antigravity-preview-latest',
            environment={'type': 'remote'}
        )

    curr_interaction = interactions[interaction_id]

    try:
        if hasattr(curr_interaction, "send_message"):
            resp = curr_interaction.send_message(request.message)
            reply_text = resp.text if hasattr(resp, "text") else str(resp)
        elif hasattr(curr_interaction, "send"):
            resp = curr_interaction.send(request.message)
            reply_text = ""
            if hasattr(resp, "text"):
                 reply_text = resp.text
            else:
                 for event in resp:
                     if hasattr(event, "text"):
                          reply_text += event.text
                     elif hasattr(event, "content") and hasattr(event.content, "parts"):
                          for part in event.content.parts:
                              if hasattr(part, "text") and part.text:
                                  reply_text += part.text
        else:
             reply_text = "Unsupported interaction method"
    except Exception as e:
        reply_text = f"Error during interaction: {e}"

    return {"interaction_id": interaction_id, "reply": reply_text}

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )
    return Response()

app.mount("/messages/", app=sse_transport.handle_post_message)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r") as f:
        return f.read()
