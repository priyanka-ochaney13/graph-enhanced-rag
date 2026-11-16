from src.config import settings

try:
    from langfuse.decorators import observe, langfuse_context

    _LANGFUSE_OK = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
except Exception:
    _LANGFUSE_OK = False

    def observe(*args, **kwargs):
        def _decorator(fn):
            return fn
        return _decorator


def traced(name: str):
    if _LANGFUSE_OK:
        return observe(name=name)
    return lambda fn: fn