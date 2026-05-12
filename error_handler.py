# error_handler.py — Challenge 3 error handling

import os
import logging

logger = logging.getLogger(__name__)


def validate_api_key() -> bool:
    """Check API key exists before starting server.
    Call this at startup — fail fast rather than on first request."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment.")
        print("Check your .env file exists and contains the key.")
        return False
    if not key.startswith("sk-ant-"):
        print("ERROR: API key format looks wrong — should start with sk-ant-")
        return False
    logger.info("API key validated successfully")
    return True


def format_error_response(error: Exception, context: str) -> dict:
    """Build a consistent error response structure."""
    error_str = str(error).lower()
    if "authentication" in error_str:
        message = "API key invalid — check your .env file"
    elif "rate" in error_str:
        message = "Rate limit hit — wait 60 seconds and retry"
    elif "timeout" in error_str:
        message = "Request timed out — Claude did not respond"
    else:
        message = f"Error in {context}: {str(error)}"
    logger.error(f"{context}: {str(error)}")
    return {"status": "error", "message": message}
