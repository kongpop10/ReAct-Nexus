"""
LLM client initialization for the ReAct application.
"""
from openai import OpenAI

def get_openai_client(api_key, base_url="https://openrouter.ai/api/v1"):
    """Initialize an OpenAI client with the given API key and base URL.

    The default base URL is for OpenRouter, but any compatible API endpoint can be used.
    """
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=base_url)
