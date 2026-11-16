import json
import re
from src.llm import chat_reasoning


ENTITY_PROMPT = """Extract entities and relationships from the text.
Return ONLY valid JSON with this schema:
{{"entities": [{{"name": "...", "type": "PERSON|ORG|PRODUCT|PLACE|OTHER"}}],
 "relationships": [{{"source": "...", "target": "...", "type": "..."}}]}}
Text:
{text}"""

def extract_graph(text: str) -> dict:
    raw = chat_reasoning([
        {"role": "system", "content": "You are a precise information extraction engine. Output only JSON."},
        {"role": "user", "content": ENTITY_PROMPT.format(text=text[:4000])},
    ])
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(match.group(0)) if match else {"entities": [], "relationships": []}
    except Exception:
        return {"entities": [], "relationships": []}