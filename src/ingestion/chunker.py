def chunk_text(text: str, max_tokens: int = 300, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i: i + max_tokens]
        chunks.append(" ".join(chunk_words))
        i += max_tokens - overlap
        if i >= len(words):
            break
    return [c for c in chunks if c.strip()]