"""
Shared utility module imported by all 4 agent Lambda handlers.
Wraps the Groq API (OpenAI-compatible), handles JSON parsing,
and strips markdown fences from LLM responses.
"""

import json
import os
import re
from openai import OpenAI

__all__ = ['call_llm', 'parse_json_response', 'extract_code_block', 'safe_call_llm_json']

def get_client() -> OpenAI:
    """
    Returns an OpenAI client pointed at Groq's base URL.
    Reads GROQ_API_KEY from os.environ.
    """
    return OpenAI(
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

def call_llm(prompt: str, max_tokens: int = 2000) -> str:
    """
    Makes a single chat completion call to Groq.
    Uses model "llama3-70b-8192".
    Raises exception on API error (do not swallow).
    """
    client = get_client()
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def parse_json_response(text: str) -> dict:
    """
    Takes raw LLM output and returns parsed dict.
    """
    # 1. Strip leading/trailing whitespace
    cleaned_text = text.strip()
    
    # 2. Remove opening ```json or ``` with regex
    cleaned_text = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned_text)
    
    # 3. Remove closing ```
    cleaned_text = cleaned_text.replace('```', '')
    
    # 4. Find first { character and slice from there
    start_index = cleaned_text.find('{')
    if start_index == -1:
        raise json.JSONDecodeError("No '{' found in the response.", cleaned_text, 0)
    
    cleaned_text = cleaned_text[start_index:]
    
    # Additionally find last } character to drop trailing explanation text
    end_index = cleaned_text.rfind('}')
    if end_index != -1:
        cleaned_text = cleaned_text[:end_index + 1]
    
    # 5. json.loads() the result
    return json.loads(cleaned_text)

def extract_code_block(text: str) -> str:
    """
    Takes raw LLM output containing a code block, returns clean code string.
    """
    if "```python" in text:
        parts = text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            code_part = parts[1]
            # Strip potential language tag like 'bash\n' or 'json\n'
            code_part = re.sub(r'^[a-z]+\n', '', code_part, flags=re.IGNORECASE)
            return code_part.strip()
            
    return text.strip()

def safe_call_llm_json(prompt: str, max_tokens: int = 2000, retries: int = 2) -> dict:
    """
    Calls call_llm() and parse_json_response() with retry logic.
    """
    last_raw_response = ""
    for attempt in range(retries + 1):
        try:
            current_prompt = prompt
            if attempt > 0:
                current_prompt += (
                    "\n\nCRITICAL INSTRUCTION: Your response must be ONLY a valid JSON object.\n"
                    "      No explanation. No markdown. No ```json fences. Start with { end with }."
                )
            
            last_raw_response = call_llm(current_prompt, max_tokens)
            parsed_json = parse_json_response(last_raw_response)
            return parsed_json
        except Exception:
            if attempt == retries:
                return {
                    "error": f"JSON parse failed after {retries} attempts",
                    "raw": last_raw_response
                }
    
    return {}
