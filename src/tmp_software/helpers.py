from langchain_ollama import ChatOllama
import requests


# Set model to be used
OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_BASE_URL = "http://localhost:11434"

# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def _build_llm(model: str | None = None) -> ChatOllama:
    return ChatOllama(
        model=model or OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0,
        num_predict=4096,
        reasoning=False,
        cache=False
    )




# Module-level streaming callback (set by analyse_paper, read by nodes)
_stream_callback = None

# Cache for model context sizes so we only query Ollama once per model
_model_ctx_cache: dict[str, int] = {}

# Rough ratio: ~3.5 characters per token for English academic text.
_CHARS_PER_TOKEN = 3.5
# Reserve tokens for the prompt template, instructions, and LLM output.
_RESERVED_TOKENS = 2048
# Absolute fallback if we cannot reach Ollama
_FALLBACK_MAX_CHARS = 12000

def _get_model_context_length(model: str) -> int:
    """Query Ollama for the model's context window size (in tokens)."""
    if model in _model_ctx_cache:
        return _model_ctx_cache[model]
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/show",
            json={"name": model},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        # model_info may contain a key like
        #   "<arch>.context_length" (e.g. "llama.context_length")
        ctx = None
        model_info = data.get("model_info", {})
        for key, value in model_info.items():
            if "context_length" in key:
                ctx = int(value)
                break

        # Some models expose it in the top-level parameters string instead
        if ctx is None:
            params = data.get("parameters", "")
            for line in params.splitlines():
                if "num_ctx" in line:
                    ctx = int(line.split()[-1])
                    break

        ctx = ctx or 4096  # conservative default if nothing found
        _model_ctx_cache[model] = ctx
        return ctx
    except Exception:
        return 4096


def _max_paper_chars(model: str) -> int:
    """Calculate the maximum characters of paper text we can safely include."""
    ctx_tokens = _get_model_context_length(model)
    usable_tokens = ctx_tokens - _RESERVED_TOKENS
    if usable_tokens < 1_024:
        usable_tokens = 1_024  # never go below a reasonable minimum
    return int(usable_tokens * _CHARS_PER_TOKEN)

def _truncate(text: str, max_chars: int = _FALLBACK_MAX_CHARS) -> str:
    """Keep the first portion of the paper to stay within context limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"

def _stream_invoke(llm: ChatOllama, prompt: str, label: str) -> str:
    """Stream an LLM call, sending chunks to _stream_callback, return full text.

    Stops early once a complete top-level JSON object ``{...}`` has been received
    to prevent the model from rambling / repeating itself.
    """
    cb = _stream_callback
    if cb:
        cb(f"\n--- {label} ---\n")
    collected: list[str] = []
    brace_depth = 0
    in_json = False
    json_complete = False
    for chunk in llm.stream(prompt):
        token = chunk.content
        collected.append(token)
        if cb and token:
            cb(token)
        # Track outermost { ... } to detect JSON completion
        for ch in token:
            if ch == "{":
                in_json = True
                brace_depth += 1
            elif ch == "}" and in_json:
                brace_depth -= 1
                if brace_depth == 0:
                    json_complete = True
        if json_complete:
            break
    return "".join(collected)