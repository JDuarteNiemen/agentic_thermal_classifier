from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
import requests
from typing import TypedDict
import json


# Set model to be used
OLLAMA_MODEL = "qwen3.5"
OLLAMA_BASE_URL = "http://localhost:11434"


class AgentState(TypedDict):
    paper_text: str
    source_path: str | None
    model: str
    metadata: dict[str, str]
    phage: str
    # outputs
    host_species: str
    host_reasoning: str
    host_confidence: str
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
        reasoning=False
    )


def IdentifyThermalRangeNoContext(state: AgentState):
    """Use the LLM to extract thermal range from metadata using no literature context."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)

    prompt=f"""You are an expert microbiology information extraction system.
    Your task is to identify the thermal range of a bacteriophage.
    DATA SOURCES:
    1. Metadata

    RULES:
    - Ensure the thermal range is for the target species
    - You must return an answer. USe any infomation possible but you must return an answer for the thermal range.

    
    Return ONLY valid JSON with:
    - "thermal_range": the thermal range of the bacteriophage. One of ['mesophile', 'thermophile', 'psychrophile']

    
    Target species:
    {state["phage"]}
    
    Metadata:
    {state["metadata"]}
    """
    out = llm.invoke(prompt)
    print(f'LLM OUTPUT: {out}')

    try:
        data = json.loads(out.content)
    except json.JSONDecodeError:
        return {}

    return {
        "thermal_range": data.get("thermal_range", "unknown"),
    }


def IdentifyThermalRangeName(state: AgentState):
    """Use the LLM to extract phage thermal range using only the phage name."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)

    prompt = f"""You are an expert microbiology information extraction system.
    Your task is to identify the thermal range of a bacteriophage.
    DATA SOURCES:
    1. Phage Species

    RULES:
    - Ensure the thermal range is for the target species
    - You must return an answer for the thermal range. 


    Return ONLY valid JSON with:
    - "thermal_range": the thermal range of the bacteriophage. One of ['mesophile', 'thermophile', 'psychrophile']


    Target species:
    {state["phage"]}

    """
    out = llm.invoke(prompt)
    print(f'LLM OUTPUT: {out}')

    try:
        data = json.loads(out.content)
    except json.JSONDecodeError:
        return {}

    return {
        "thermal_range": data.get("thermal_range", "unknown"),
    }