"""
Client wrapper for connecting to the local LM Studio server.
No API keys or cloud costs required. Uses the OpenAI python client format.
"""
import os
import json
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Defaults to the reachable LM Studio IP/port provided by the user
raw_url = os.getenv("LM_STUDIO_URL", "http://172.19.121.89:1234")
if not raw_url.endswith("/v1"):
    raw_url = raw_url.rstrip("/") + "/v1"
LM_STUDIO_URL = raw_url

try:
    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client for LM Studio: {e}")
    client = None

def call_local_llm(prompt: str, error_msg: Optional[str] = None) -> str:
    """
    Sends a prompt to the local model hosted in LM Studio.
    If 'error_msg' is provided, it means this is a retry attempt after a parsing failure.
    """
    if not client:
        raise RuntimeError("LLM client not initialized. Is the openai package installed?")
        
    messages = [
        {"role": "system", "content": "You are a precise JSON-only data extraction assistant. Output ONLY raw JSON, with no markdown blocks or surrounding text."}
    ]
    
    if error_msg:
        # If this is a retry, append the previous error
        prompt = f"{prompt}\n\nWARNING - Previous attempt failed with: {error_msg}. Please fix the JSON output."
        
    messages.append({"role": "user", "content": prompt})
    
    try:
        # We don't hardcode a model name so LM Studio uses whatever is loaded (e.g. SmolLM-3B)
        response = client.chat.completions.create(
            model="local-model",
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            # If the model/server supports response_format, uncomment the line below:
            # response_format={ "type": "json_object" } 
        )
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown formatting if the model ignored the system prompt
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()
        
    except Exception as e:
        logger.error(f"LM Studio connection failed: {e}")
        raise
