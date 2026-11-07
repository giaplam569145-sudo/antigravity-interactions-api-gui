import json
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    import google.genai as genai
except ImportError:
    genai = None

app = FastAPI(title="Google Antigravity Interactions API GUI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_genai_client(api_key: Optional[str] = None):
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Kein GEMINI_API_KEY gefunden. Bitte in der GUI eingeben oder als Umgebungsvariable setzen.")
    return genai.Client(api_key=key, http_options={"api_version": "v1beta"})


class InteractionRequest(BaseModel):
    agent: str = Field(default="antigravity-preview-latest", description="Der Name des Antigravity-Agenten/Modells")
    input_text: str = Field(..., description="Die Eingabeaufforderung / Nachricht")
    system_instruction: Optional[str] = Field(None, description="Optionale Systemanweisung")
    previous_interaction_id: Optional[str] = Field(None, description="ID der vorherigen Interaktion für Multi-Turn Konversation")
    environment_type: str = Field(default="remote", description="Environment-Typ, Standard 'remote'")
    stream: bool = Field(default=True, description="Ob die Antwort gestreamt werden soll")
    api_key: Optional[str] = Field(None, description="Optionaler Gemini API Key")


class CodeSnippetRequest(BaseModel):
    agent: str = "antigravity-preview-latest"
    input_text: str = "Hallo Welt!"
    system_instruction: Optional[str] = None
    previous_interaction_id: Optional[str] = None
    environment_type: str = "remote"
    stream: bool = True


@app.get("/api/health")
def health_check():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {"status": "ok", "has_api_key_configured": has_key}


@app.get("/api/models")
def list_models():
    """Gibt die Antigravity-Modellvarianten und Standardwerte zurück."""
    return {
        "models": [
            {
                "id": "antigravity-preview-latest",
                "name": "Antigravity Preview (Latest)",
                "description": "Neueste Vorschauversion des Antigravity Agenten mit Denkprozess & autonomer Ausführung.",
                "default": True,
            },
            {
                "id": "antigravity-preview-09-2026",
                "name": "Antigravity Preview (09-2026)",
                "description": "Gepinnte Version September 2026.",
                "default": False,
            },
            {
                "id": "antigravity-preview-05-2026",
                "name": "Antigravity Preview (05-2026)",
                "description": "Frühe Version Mai 2026.",
                "default": False,
            },
        ]
    }


@app.post("/api/code-snippet")
def generate_code_snippets(req: CodeSnippetRequest):
    """Generiert fertigen Python-, cURL- und Node.js-Code für die aktuellen Parameter."""
    py_args = [f"agent={req.agent!r}", f"environment={{'type': {req.environment_type!r}}}", f"input={req.input_text!r}"]
    if req.system_instruction:
        py_args.append(f"system_instruction={req.system_instruction!r}")
    if req.previous_interaction_id:
        py_args.append(f"previous_interaction_id={req.previous_interaction_id!r}")
    if req.stream:
        py_args.append("stream=True")

    python_snippet = f'''import os
from google import genai

# InteractionsAPI erfordert derzeit api_version='v1beta'
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
    http_options={{"api_version": "v1beta"}}
)
'''
    if req.stream:
        python_snippet += f'''
# 1. Interaktion streamen
stream = client.interactions.create(
    {",\n    ".join(py_args)}
)

for event in stream:
    # Event-Typen: InteractionCreatedEvent, StepStart, StepDelta, StepStop, InteractionCompletedEvent
    if hasattr(event, "delta") and event.delta and getattr(event.delta, "text", None):
        print(event.delta.text, end="", flush=True)
    elif hasattr(event, "interaction"):
        print(f"\\n[Status: {{event.interaction.status}}, ID: {{event.interaction.id}}]")
'''
    else:
        python_snippet += f'''
# 1. Interaktion anfordern
interaction = client.interactions.create(
    {",\n    ".join(py_args)}
)

print("ID:", interaction.id)
print("Status:", interaction.status)
print("Antwort:", interaction.output_text)
if interaction.steps:
    for step in interaction.steps:
        if step.type == "thought":
            print("[Thought / Überlegung]:", step.summary)
'''

    # cURL Snippet
    curl_body: Dict[str, Any] = {
        "agent": req.agent,
        "environment": {"type": req.environment_type},
        "input": req.input_text,
    }
    if req.system_instruction:
        curl_body["system_instruction"] = req.system_instruction
    if req.previous_interaction_id:
        curl_body["previous_interaction_id"] = req.previous_interaction_id

    body_json = json.dumps(curl_body, indent=2)
    stream_flag = "?alt=sse" if req.stream else ""
    curl_snippet = f'''curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions{stream_flag}" \\
  -H "Content-Type: application/json" \\
  -H "x-goog-api-key: $GEMINI_API_KEY" \\
  -d '{body_json}'
'''

    # JavaScript/TypeScript Snippet
    node_body = {
        "agent": req.agent,
        "environment": {"type": req.environment_type},
        "input": req.input_text,
    }
    if req.system_instruction:
        node_body["system_instruction"] = req.system_instruction
    if req.previous_interaction_id:
        node_body["previous_interaction_id"] = req.previous_interaction_id

    js_snippet = f'''// Node.js / JavaScript Fetch
const apiKey = process.env.GEMINI_API_KEY;
const response = await fetch("https://generativelanguage.googleapis.com/v1beta/interactions", {{
  method: "POST",
  headers: {{
    "Content-Type": "application/json",
    "x-goog-api-key": apiKey
  }},
  body: JSON.stringify({json.dumps(node_body, indent=4)})
}});

const data = await response.json();
console.log("Interaktions-ID:", data.id);
console.log("Antwort:", data.output_text);
'''

    return {
        "python": python_snippet,
        "curl": curl_snippet,
        "javascript": js_snippet,
    }


@app.post("/api/interact")
async def create_interaction(req: InteractionRequest):
    try:
        client = get_genai_client(req.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    kwargs: Dict[str, Any] = {
        "agent": req.agent,
        "environment": {"type": req.environment_type},
        "input": req.input_text,
    }
    if req.system_instruction:
        kwargs["system_instruction"] = req.system_instruction
    if req.previous_interaction_id:
        kwargs["previous_interaction_id"] = req.previous_interaction_id

    if req.stream:

        def event_generator():
            try:
                stream = client.interactions.create(stream=True, **kwargs)
                for chunk in stream:
                    chunk_type = type(chunk).__name__
                    chunk_data = chunk.model_dump() if hasattr(chunk, "model_dump") else {}
                    event_payload = {
                        "type": chunk_type,
                        "data": chunk_data,
                    }
                    yield f"data: {json.dumps(event_payload)}\n\n"
            except Exception as ex:
                err_payload = {"type": "error", "error": str(ex)}
                yield f"data: {json.dumps(err_payload)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    else:
        try:
            interaction = client.interactions.create(stream=False, **kwargs)
            interaction_data = interaction.model_dump() if hasattr(interaction, "model_dump") else str(interaction)
            return {"interaction": interaction_data}
        except Exception as ex:
            raise HTTPException(status_code=500, detail=str(ex))


@app.get("/api/interactions/{interaction_id}")
def get_interaction(interaction_id: str, api_key: Optional[str] = None):
    try:
        client = get_genai_client(api_key)
        interaction = client.interactions.get(interaction_id)
        return {"interaction": interaction.model_dump() if hasattr(interaction, "model_dump") else str(interaction)}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Antigravity Interactions API GUI is running. static/index.html not created yet."}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
