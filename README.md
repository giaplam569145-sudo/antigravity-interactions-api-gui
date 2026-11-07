# Google Antigravity Interactions API GUI & Explorer

Eine interaktive, moderne GUI-Anwendung zum Kennenlernen, Austesten und Verstehen von Googles **Interactions API** für das **Antigravity**-Modell (`antigravity-preview-latest`).

Neben einer Chat- und Test-Oberfläche bietet die Anwendung einen **Echtzeit-Code-Generator**, der für jeden API-Call automatisch die passenden Befehle in **Python** (`google-genai`), **cURL** und **JavaScript / Node.js** anzeigt und per Klick kopierbar macht.

---

## 🌟 Features

1. **Interactions API Playground**:
   - Direkte Interaktion mit dem Antigravity-Agenten (`antigravity-preview-latest`, `antigravity-preview-09-2026`, etc.).
   - Live-Streaming via **Server-Sent Events (SSE)** (`StepDelta`, `StepStart`, `StepStop`, `InteractionCompletedEvent`).
   - Unterstützung für **System Instructions** und **Environment**-Konfiguration (`type: remote`).
   - Visualisierung von **Denkschritten** (`thought`-Steps) separat von der Modellausgabe.
   - Anzeige von **Token-Statistiken** (Input, Thought, Output Tokens).

2. **Stateful Multi-Turn Sessions**:
   - Automatische Übergabe und Verkettung der `previous_interaction_id`.
   - Demonstration, wie Konversationszustände serverseitig fortgeführt werden, ohne den kompletten Verlauf erneut übertragen zu müssen.
   - Button zum Zurücksetzen / Starten einer neuen Konversation.

3. **Lerneffekt & Code-Export**:
   - **Live Code Snippets**: Passen sich in Echtzeit an (inklusive aller Parameter, System-Prompts, IDs).
   - Ein-Klick-Kopieren für **Python (google-genai SDK)**, **cURL** und **JavaScript / Fetch**.
   - **Raw JSON / Steps Explorer**: Zeigt die vollständige Rohantwort der Interactions API.
   - **Interaktives Handbuch / Crashkurs**: Erklärt wichtige Konzepte (warum `agent` statt `model`, `v1beta`, `environment`, etc.).
   - **Vordefinierte Lernszenarien**:
     - *Hello World*
     - *Denkschritte / Math (Schritt-für-Schritt-Logik)*
     - *Multi-Turn State (Gedächtnis-Test)*
     - *Persona / System Prompt (Piratenstil, etc.)*

---

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.10+
- Ein `GEMINI_API_KEY` (kann als Umgebungsvariable gesetzt oder direkt in der GUI eingegeben werden).

### Installation
```bash
pip install -r requirements.txt
```
*(Oder: `pip install google-genai fastapi uvicorn requests playwright`)*

### Starten der GUI
```bash
export GEMINI_API_KEY="dein-api-key"
python3 app.py
```
Öffne anschließend im Browser: **[http://localhost:8000](http://localhost:8000)**

---

## 🧪 Tests ausführen

- **Unit- & API-Tests**:
  ```bash
  python3 -m unittest test_app.py
  ```
- **Playwright End-to-End GUI Test**:
  ```bash
  python3 test_gui_playwright.py
  ```

---

## 📖 Wichtige Erkenntnisse zur Interactions API

1. **Agent vs. Model**:
   `antigravity-preview-latest` ist als autonomer Agent typisiert. Im Python-SDK muss `agent='antigravity-preview-latest'` anstelle von `model=...` verwendet werden.
2. **API Version**:
   Die Interactions API und das Environment-Attribut erfordern derzeit `http_options={'api_version': 'v1beta'}`.
3. **Environment**:
   Muss auf `environment={'type': 'remote'}` gesetzt sein.
4. **State Chaining**:
   Folgefragen übergeben die ID der vorherigen Interaktion als `previous_interaction_id`.
