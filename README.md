# AI Webhook Processor

## What this does
A FastAPI Python server that receives data from n8n workflows via HTTP,
processes it with Claude AI, and returns structured JSON responses.
Bridges no-code n8n automation with custom Python AI logic.

## The problem it solves
n8n workflows cannot run custom Python logic natively. This server
exposes any Python function as an HTTP endpoint — making it callable
from n8n, Make.com, or any other automation tool via HTTP Request node.

## Measurable result
- Response time: under 3 seconds per request (including Claude API call)
- Endpoints available: 2 (/analyse and /classify)
- Successfully called from n8n Cloud during testing: yes
- Tasks supported: summarise, extract_actions, sentiment, classify

## Tech stack — 2026 versions
- Python 3.12.0
- FastAPI 0.115
- Uvicorn (ASGI server)
- Anthropic SDK 0.40.0
- Claude claude-sonnet-4-5

## How it works
1. Python starts a FastAPI server on port 8000
2. ngrok creates a public tunnel so n8n Cloud can reach it
3. n8n HTTP Request node sends POST request with JSON body
4. FastAPI validates the request using Pydantic BaseModel
5. Python calls Claude with a task-specific prompt
6. Claude returns structured JSON analysis
7. FastAPI returns the result to n8n as a JSON response
8. n8n uses the result in subsequent workflow nodes

## API endpoints

### GET /
Health check — confirms server is running

### POST /analyse
Analyse text with task types: summarise, extract_actions, sentiment
Request: {"text": "...", "task": "summarise", "client_name": "..."}
Response: {"status": "success", "task": "...", "result": {...}}

### POST /classify
Classify text into custom categories
Request: {"text": "...", "categories": ["urgent", "standard", "low"]}
Response: {"status": "success", "classification": {...}}

## How to run
python processor.py
# Server starts at http://localhost:8000
# Interactive docs at http://localhost:8000/docs

## Error handling
- API key validated at startup — server refuses to start without it
- Invalid task types return 400 with list of valid options
- Claude API failures return 500 with descriptive error message
- All requests and errors logged to terminal with timestamps


## Screenshots
[https://imgur.com/xihRBGo]
[https://imgur.com/17PrcZM]
[https://imgur.com/2nkBRGH]
