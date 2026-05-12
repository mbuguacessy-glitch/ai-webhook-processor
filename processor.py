# processor.py — Webhook Data Processor
# A FastAPI server that receives data from n8n,
# processes it with Claude, and returns structured JSON
# Python 3.12 | FastAPI 0.115 | Anthropic SDK 0.40.0
# Start: python processor.py
# Docs: http://localhost:8000/docs

import os
import json
import logging
import uvicorn
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from error_handler import validate_api_key

# Add right before uvicorn.run() at the bottom
if __name__ == "__main__":
    if not validate_api_key():
        exit(1)  # stop before starting the server
    print("=== Document Processor API Starting ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ── Setup ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

claude = Anthropic()

app = FastAPI(
    title="Document Processor API",
    description="Receives data from n8n, processes with Claude",
    version="1.0.0"
)

# ── Data Models ───────────────────────────────────


class AnalyseRequest(BaseModel):
    """Data n8n sends to the /analyse endpoint."""
    text: str                       # required — the text to analyse
    task: str = "summarise"        # optional — what to do with it
    client_name: str = "Unknown"   # optional — for personalisation


class ClassifyRequest(BaseModel):
    """Data n8n sends to the /classify endpoint."""
    text: str                       # required — text to classify
    categories: list[str] = [       # optional — allowed categories
        "urgent", "standard", "low"
    ]

# ── Helper Functions ──────────────────────────────


def call_claude(prompt: str, max_tokens: int = 500) -> str:
    """Call Claude and return the response text.
    Raises an exception if the API call fails."""
    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def clean_json(text: str) -> str:
    """Remove markdown code blocks if Claude added them."""
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    return text.strip()

# ── Endpoints ─────────────────────────────────────


@app.get("/")
async def health_check():
    """Health check — confirms the server is running.
    n8n can call this to verify the connection."""
    return {
        "status": "running",
        "message": "Document Processor API is ready",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyse")
async def analyse_text(request: AnalyseRequest):
    """Analyse text sent from n8n.
    Accepts task types: summarise, extract_actions, sentiment.
    Returns structured JSON n8n can use in subsequent nodes."""
    logger.info(
        f"Analyse request — task: {request.task} — client: {request.client_name}")

    # Build prompt based on the requested task
    task_prompts = {
        "summarise": f"""Summarise this text in 2 sentences.
Return ONLY JSON: {{"summary": "...", "key_points": ["...", "..."]}}
Text: {request.text}""",

        "extract_actions": f"""Extract all action items from this text.
Return ONLY JSON: {{"action_items": ["...", "..."], "count": 0}}
Text: {request.text}""",

        "sentiment": f"""Analyse the sentiment of this text.
Return ONLY JSON: {{"sentiment": "positive|neutral|negative",
"confidence": "high|medium|low", "reason": "..."}}
Text: {request.text}"""
    }

    if request.task not in task_prompts:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task '{request.task}'. Use: {list(task_prompts.keys())}"
        )

    try:
        raw = call_claude(task_prompts[request.task])
        result = json.loads(clean_json(raw))
        return {
            "status": "success",
            "task": request.task,
            "client_name": request.client_name,
            "result": result,
            "processed_at": datetime.now().isoformat()
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500,
                            detail="Claude returned invalid JSON. Try again.")
    except Exception as e:
        logger.error(f"Analyse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify")
async def classify_text(request: ClassifyRequest):
    """Classify text into one of the provided categories.
    n8n can use this to route emails, documents, or support tickets."""
    logger.info(f"Classify request — categories: {request.categories}")

    prompt = f"""Classify this text into exactly one of these categories:
{', '.join(request.categories)}

Return ONLY JSON: {{"category": "...", "confidence": "high|medium|low",
"reason": "one sentence explaining the classification"}}

Text: {request.text}"""

    try:
        raw = call_claude(prompt, max_tokens=200)
        result = json.loads(clean_json(raw))
        return {
            "status": "success",
            "classification": result,
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Classify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Run the server ─────────────────────────────────
if __name__ == "__main__":
    print("=== Document Processor API Starting ===")
    print("Docs available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
