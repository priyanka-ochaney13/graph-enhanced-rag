import re

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(above|prior|previous)", re.IGNORECASE),
    re.compile(r"<\s*/?\s*(system|assistant|user)\s*>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\]", re.IGNORECASE),
]


def screen_chunk(text: str) -> tuple[bool, str | None]:
    """Return (is_safe, reason)."""
    for pat in _INJECTION_PATTERNS:
        m = pat.search(text)
        if m:
            return False, f"Suspicious pattern: {m.group(0)[:60]}"
    return True, None


def sanitize_output(text: str) -> str:
    text = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"on\w+\s*=\s*['\"].*?['\"]", "", text, flags=re.IGNORECASE)
    return text.strip()