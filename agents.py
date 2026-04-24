# imports
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
import requests
from typing import TypedDict
import json

# Set model to be used
OLLAMA_MODEL = "qwen3.5"
OLLAMA_BASE_URL = "http://localhost:11434"


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    paper_text: str
    source_path: str | None
    model: str
    metadata: dict[str, str]
    # outputs
    host_species: str
    reasoning: str
    confidence: str
    thermal_range: str
    temperature: str
    thermal_reasoning: str
    thermal_confidence: str


def _build_llm(model: str | None = None) -> ChatOllama:
    return ChatOllama(
        model=model or OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0,
        num_predict=4096,
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


def IdentifyHost(state: AgentState) -> dict:
    """Use the LLM to extract host species from paper text."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    max_chars = _max_paper_chars(model)
    ctx_tokens = _get_model_context_length(model)

    paper_len = len(state["paper_text"])
    chars_used = min(paper_len, max_chars)
    parse_pct = round((chars_used / paper_len) * 100, 1) if paper_len > 0 else 100.0

    prompt = f"""You are an expert microbiology information extraction system.
    Your task is to identify the host species of a bacteriophage.
    DATA SOURCES:
    1. Paper text (primary source of truth)
    2. Metadata (secondary source, may contain host or ecological clues)
    
    RULES:
    - ALWAYS prioritise information explicitly stated in the paper text.
    - If the host species is clearly stated in the paper, use that.
    - If the paper does NOT explicitly state the host species:
        - You MAY use metadata if it directly specifies the host.
        - Otherwise return "Unknown".
        
    - Do NOT guess or infer based on species names, environment, or prior knowledge.
    - Do NOT assume the host from genus/species familiarity.
    
    METADATA:
    {state['metadata']}
    Return ONLY valid JSON with:
    - "host_species": the host organism or "Unknown"
    - "reasoning": MUST explain whether the answer came from paper or metadata, and include a direct quote if from the paper
    - "confidence": one of ["low", "medium", "high"]
    
    CONFIDENCE GUIDELINES:
    - high: explicitly stated in paper or metadata
    - medium: strongly implied in paper or metadata
    - low: weak or uncertain evidence
    
    Paper text:
    {_truncate(state["paper_text"], max_chars)}
    """

    out=_stream_invoke(llm, prompt, label='host')

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {}

    return {
        "host_species": data.get("host_species", "Unknown"),
        "reasoning": data.get("reasoning", ""),
        "confidence": data.get("confidence", "low"),
}



def IdentifyThermalRange(state: AgentState) -> dict:
    """Use the LLM to extract host species from paper text."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    max_chars = _max_paper_chars(model)
    ctx_tokens = _get_model_context_length(model)

    paper_len = len(state["paper_text"])
    chars_used = min(paper_len, max_chars)
    parse_pct = round((chars_used / paper_len) * 100, 1) if paper_len > 0 else 100.0

    prompt = f"""You are an expert microbiology information extraction system.

    Your task is to determine the thermal characteristics of the organism described in the paper.

    STRICT RULES:
    - Only use information explicitly stated in the paper.
    - Do NOT infer thermal range from species name or prior knowledge.
    - Do NOT rely on the provided host_species unless the paper explicitly links it to temperature.
    - If no temperature or thermal information is stated, return "unknown".
    
    THERMAL CLASS DEFINITIONS:
    - psychrophile: optimal growth < 15°C
    - mesophile: 15–45°C
    - thermophile: > 45°C
    Return ONLY valid JSON with:
    - "thermal_range": one of ["psychrophile", "mesophile", "thermophile", "unknown"]
    - "temperature": exact temperature or range quoted from the paper, or "unknown"
    - "thermal_reasoning": MUST include a direct quote from the paper supporting your answer
    - "thermal_confidence": one of ["low", "medium", "high"]

    Paper text:
    {_truncate(state["paper_text"], max_chars)}
    """

    out=_stream_invoke(llm, prompt, label='thermal_range')

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {}

    return {
        "thermal_range": data.get("thermal_range", "Unknown"),
        "temperature": data.get("temperature", "Unknown"),
        "thermal_reasoning": data.get("thermal_reasoning", ""),
        "thermal_confidence": data.get("thermal_confidence", "low"),
}

#
# prompt = f"""You are an academic librarian AI. Analyse the following academic paper text and extract metadata.
#
# Return your answer as a JSON object with exactly these keys:
# - "Phage Species": The phage species this is about, mark Unknown if it cannot be deduced (string)
# - "Host Species": The species of bacteria this phage infects, mark Unknown if it cannot be deduced (string)
# - "Reasoning": Your reasoning for making this decision, quote the paper here. (string)
# - "Confidence": A confidence score low/medium/high (string)
#
# Paper text:{paper_text}
#
# Respond ONLY with the JSON object, no other text. Dont include newline characters."""


