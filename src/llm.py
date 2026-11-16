from groq import Groq
from src.config import settings

_client = None

def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client

def chat_fast(messages: list[dict], temperature: float = 0.0) -> str:
    client = get_groq_client()
    resp = client.chat.completions.create(
        model=settings.groq_model_fast,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def chat_reasoning(messages: list[dict], temperature: float = 0.1) -> str:
    client = get_groq_client()
    resp = client.chat.completions.create(
        model=settings.groq_model_reasoning,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""