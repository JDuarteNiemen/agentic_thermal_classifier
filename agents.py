# imports
from platform import node

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
import requests
from typing import TypedDict
import json
from tools import *
import time
from papers import *

# Set model to be used
OLLAMA_MODEL = "qwen3.5"
OLLAMA_BASE_URL = "http://localhost:11434"


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    #model
    model: str

    # Phage Specific metric
    accession: str
    phage: str #species name
    metadata: str

    #  host classification
    host: str
    taxonomic_level: str
    host_reasoning: str
    host_confidence: str
    host_source: str
    host_found: bool

    # thermal classification
    thermal_range: str
    temperature: str
    thermal_reasoning: str
    thermal_confidence: str
    thermal_source: str
    thermal_found: bool
    inference_type:str

    # paper info
    paper_dir: str
    host_paper_dir: str
    host_paper: str
    thermal_paper: str
    #may need to add extra paper things e.g. number of papers and current paper/ seperate accession and host papers

    #meta information
    duration: float
    decision: str
    nodes: list
    timings: dict
    JSONDecodeError: bool

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



# ---------------------------------------------------------------------------
# GRAPH NODES
# ---------------------------------------------------------------------------

def ClassifyThermalMetadata(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)

    node = "ClassifyThermalMetadata"
    nodes = (state.get("nodes") or []) + [node]

    prompt = f"""
    You are a microbiology information extraction system.

    TASK:
    Determine the thermal range of the bacteriophage or its host using ONLY metadata.

    PRIMARY OBJECTIVE:
    First, identify any metadata describing:
    - isolation source (e.g. soil, seawater, human gut, hot spring, Arctic ice)
    - environmental origin
    - sampling location context
    - host organism environment
    - temperature-related descriptors

    CRITICAL RULES:
    - ONLY use information explicitly present in the metadata.
    - Do NOT use external biological knowledge.
    - Do NOT assume thermal range from organism name, host name or taxonomy.
    - If no relevant metadata exists, return None.
    - You MAY infer thermal range ONLY if environmental context strongly implies it.

    METADATA:
    {state['metadata']}

    OUTPUT FORMAT (STRICT JSON ONLY):
    {{
        "thermal_range": "psychrophile | mesophile | thermophile | None",
        "inference_type": "explicit | inferred | none",
        "thermal_reasoning": "step-by-step explanation of how metadata led to decision",
        "thermal_found": Boolean True or False depending on whether a thermal range can be found in the metadata
    }}

    THERMAL MAPPING RULES:
    - psychrophile → Arctic, deep sea, polar, ice, permafrost environments
    - mesophile → soil, host-associated, freshwater, general environments
    - thermophile → hot springs, geothermal, hydrothermal vents, compost heaps

    INFERENCE RULES:
    - explicit: metadata directly states temperature or growth condition
    - inferred: environment strongly implies thermal range
    - none: no environmental information available

    DECISION RULES:
    - PRIORITISE isolation source and environment fields over all other metadata.
    - Use ONLY metadata evidence — never external biology assumptions.
    """
    start=time.time()
    out = llm.invoke(prompt)
    end = time.time()
    duration = round((end-start),2)

    #update duration
    updated_duration=state['duration'] + duration

    #update timings
    timings = state.get("timings", {}).copy()
    timings[node] = duration

    try:
        data = json.loads(out.content)
    except json.JSONDecodeError:
        return {
            'decision': 'CreateAccessionLibrary',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'JSONDecodeError': True
        }


    if data.get('thermal_found'):
        return {
        "thermal_range": data.get("thermal_range", None),
        "inference_type": data.get("inference_type", None),
        "thermal_reasoning": data.get("thermal_reasoning", None),
        "thermal_source": 'metadata',
        "thermal_found": True,
        "decision": 'end',
        "duration": updated_duration,
        "timings": timings,
        "nodes": nodes,

    }
    else:
        return {'decision': 'CreateAccessionLibrary',
                'duration': updated_duration,
                'nodes':nodes,
                'timings': timings}


def CreateAccessionLibrary(state: AgentState) -> dict:
    node='CreateAccessionLibrary'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time() # set start
    CreateLibrary(state['accession'], state['metadata']) # create library for accession
    end = time.time() # set end

    # Updating durations
    duration = round((end-start),2)
    updated_duration=state['duration'] + duration
    timings = state.get("timings", {}).copy()
    timings[node] = duration


    return {'decision': 'ClassifyThermalLiterature',
            'duration': updated_duration,
            'nodes': nodes,
            'timings': timings}


def ClassifyThermalLiterature(state: AgentState) -> dict:
    """Use the LLM to extract host species from paper text."""
    node='ClassifyThermalLiterature'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time()
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    max_chars = _max_paper_chars(model)


    patterns = {
    # organisms
    "mesophile": r"\bmesophil(?:e|ic|es|icity)?\b",
    "psychrophile": r"\bpsychrophil(?:e|ic|es|icity)?\b",
    "thermophile": r"\bthermophil(?:e|ic|es|icity)?\b",
    # temperature concepts
    "temperature": r"\btemperatur(e|es)?\b",
    "optimal_growth": r"\boptimal(?:ly)?\s+(growth|temperature|growing)\b",
    # units
    "celsius": r"\b\d+(?:\.\d+)?\s?°?\s?[Cc]\b|\bCelsius\b",
    "kelvin": r"\b\d+(?:\.\d+)?\s?[Kk]\b|\bKelvin\b"
}

    ranked_papers=RankPapers(state['paper_dir'], patterns)
    ranked_papers_list=list(ranked_papers.keys())
    found_thermal=False

    for paper in ranked_papers_list:
        with open(f"{state['paper_dir']}/{paper}", 'r') as f:
            paper_text=f.read()




        prompt = f"""You are an expert microbiology information extraction system.
    
        Your task is to determine the thermal characteristics of the organism needed from information described in the paper.
    
        The organism in question: {state['phage']}
    
        STRICT RULES:
        - Only use information explicitly stated in the paper.
        - Do NOT infer thermal range from species name, host name or prior knowledge.
        - If no temperature or thermal information is stated, return None.
        - You can infer the thermal range based on hosts thermal range if the paper supports a link between phage and host bacteria.
    
        THERMAL CLASS DEFINITIONS:
        - psychrophile: optimal growth < 15°C
        - mesophile: 15–45°C
        - thermophile: > 45°C
        Return ONLY valid JSON with:
        - "thermal_range": one of ["psychrophile", "mesophile", "thermophile", None]
        - "temperature": exact temperature or range quoted from the paper, or None
        - "thermal_reasoning":  Step by step explanation of what led to your answer, including quotes from the paper
        - "inference_type": "explicit | inferred | none",
        - "thermal_confidence": one of ["low", "medium", "high"]
        - "thermal_found": Boolean True or False depending on whether a thermal range can be found in the paper.
    
        INFERENCE RULES:
        - explicit: literature directly states temperature or growth condition
        - inferred: environment strongly implies thermal range. The environmental conditions of the host are explicitly stated in the paper.
        - none: no environmental information available
        
        CONFIDENCE GUIDELINES:
        - high: explicitly stated in paper 
        - medium: strongly implied in paper
        - low: weak or uncertain evidence
    
        Paper text:
        {_truncate(paper_text, max_chars)}
        """

        out = llm.invoke(prompt)

        try:
            data = json.loads(out.content)
        except json.JSONDecodeError:
            continue



        if data.get('thermal_found'): # if a result is found
            found_thermal=True
            end = time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration

            return {
                "thermal_range": data.get("thermal_range", None),
                "temperature": data.get("temperature", None),
                "inference_type": data.get("inference_type", None),
                "thermal_reasoning": data.get("thermal_reasoning", None),
                "thermal_confidence": data.get("thermal_confidence", None),
                "thermal_source": 'literature',
                "thermal_found": True,
                "decision": "end",
                "duration": updated_duration,
                "timings": timings,
                "nodes": nodes,
                'thermal_paper': paper
            }

    if not found_thermal:
        end = time.time()
        duration = round((end - start), 2)
        updated_duration = state['duration'] + duration
        timings = state.get("timings", {}).copy()
        timings[node] = duration

        return {
            "decision": 'ClassifyHostMetadata',
            'duration': updated_duration,
            'timings': timings,
            'nodes': nodes,

        }

def ClassifyHostMetadata(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    node='ClassifyHostMetadata'
    nodes = (state.get("nodes") or []) + [node]

    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)




    prompt = f"""
    You are a microbiology information extraction system.
    TASK:
    Extract the bacteriophage host organism ONLY if it is explicitly stated in the METADATA.
    CRITICAL RULES:
    - ONLY use information explicitly written in the metadata.
    - Do NOT infer, guess, or use biological prior knowledge.
    - If not explicitly present, return None.
    - Copy values EXACTLY as written (no paraphrasing or normalization).
    METADATA:
    {state['metadata']}
    OUTPUT FORMAT (STRICT JSON ONLY, NOTHING ELSE):
    {{
        "host_species": "<exact value OR None>",
        "taxonomic_level": family | genus | species | strain | None,
        "host_reasoning": "step-by-step explanation of how metadata led to decision" OR 'not present in metadata',
        "host_found": True/False
    }}
    TAXONOMIC_LEVEL RULES:
    - family: host is only given at family level (e.g. "Enterobacteriaceae")
    - genus: only genus is given (e.g. "Escherichia")
    - species: full binomial name is given (e.g. "Escherichia coli")
    - strain: isolate/strain designation is given (e.g. "E. coli K12", "strain MG1655")
    - None: no explicit host information is present
    DECISION RULES:
    - If multiple host candidates exist, choose the MOST SPECIFIC one.
    - Do NOT upgrade genus → species unless species is explicitly written.
    """

    start = time.time()
    out = llm.invoke(prompt)
    end = time.time()

    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration
    timings = state.get("timings", {}).copy()
    timings[node] = duration

    try:
        data = json.loads(out.content)
    except json.JSONDecodeError:
        return {
            'decision': 'ClassifyHostLiterature',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'JSONDecodeError': True
        }

    if data.get('host_found'):

        return {
            "host_species": data.get("host_species", None),
            "host_found": data.get("host_found", None),
            "taxonomic_level": data.get("taxonomic_level", None),
            "host_reasoning": data.get("host_reasoning", None),
            'host_source': 'metadata',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'decision': 'CreateHostLibrary',
        }
    else:
        return {
            'decision': 'ClassifyHostLiterature',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
        }

def ClassifyHostLiterature(state: AgentState) -> dict:
    node='ClassifyHostLiterature'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time()

    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    max_chars = _max_paper_chars(model)



    patterns={
    "infection_terms": r"\b(infects?|infecting|infected)\b",
    "isolation_terms": r"\b(isolated from|recovered from|obtained from|detected in)\b",
    "host_terms": r"\b(host bacterium|host bacteria|bacterial host)\b",
    "phage_of": r"\bphage (?:of|infecting)\b",
}
    ranked_papers=RankPapers(state['paper_dir'], patterns)
    ranked_papers_list=list(ranked_papers.keys())

    host_found=False

    for paper in ranked_papers_list:
        with open(f"{state['paper_dir']}/{paper}", 'r') as f:
            paper_text=f.read()

        prompt = f"""You are an expert microbiology information extraction system.
            Your task is to identify the host species of a bacteriophage.
            DATA SOURCES:
            1. Paper text (primary source of truth)
            2. Target species
    
    
            RULES:
            - ALWAYS prioritise information explicitly stated in the paper text.
            - If the host species is clearly stated in the paper, use that.
            - Ensure the host is for the target species
            - Do NOT guess or infer based on species names, environment, or prior knowledge.
    
    
            Return ONLY valid JSON with:
            - "host_species": the host organism or None
            - "taxonomic_level": family | genus | species | strain | None, 
            - "host_reasoning": Step by step explanation of what led to your answer, including quotes from the paper
            - "host_confidence": one of ["low", "medium", "high"]
            - "host_found": True/False
            
            TAXONOMIC_LEVEL RULES:
            - family: host is only given at family level (e.g. "Enterobacteriaceae")
            - genus: only genus is given (e.g. "Escherichia")
            - species: full binomial name is given (e.g. "Escherichia coli")
            - strain: isolate/strain designation is given (e.g. "E. coli K12", "strain MG1655")
            - None: no explicit host information is present
    
            CONFIDENCE GUIDELINES:
            - high: explicitly stated in paper 
            - medium: strongly implied in paper
            - low: weak or uncertain evidence
    
            Target species:
            {state['phage']}
    
            Paper text:
            {_truncate(paper_text, max_chars)}
            """

        out = llm.invoke(prompt)

        try:
            data = json.loads(out.content)
        except json.JSONDecodeError:
            return {}

        if data.get("host_found"):
            host_found=True
            end=time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration
            return {
                "host": data.get("host_species", None),
                "taxonomic_level": data.get("taxonomic_level", None),
                "host_reasoning": data.get("host_reasoning", None),
                "host_confidence": data.get("host_confidence", None),
                "host_found": True,
                "host_source": 'literature',
                'host_paper': paper,
                'duration': updated_duration,
                'timings': timings,
                'nodes': nodes,
                'decision': 'CreateHostLibrary',
            }
    if not host_found:
        end = time.time()
        duration = round((end - start), 2)
        updated_duration = state['duration'] + duration
        timings = state.get("timings", {}).copy()
        timings[node] = duration

        return {
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'decision': 'ClassifyThermalForced'
            }


def CreateHostLibrary(state: AgentState) -> dict:
    node='CreateHostLibrary'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time()
    host=state.get('host_species')
    accession=state.get('accession')

    HostLibrary(accession, host)
    end = time.time()
    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration
    timings = state.get("timings", {}).copy()


    return {'decision': 'ClassifyThermalRangeHostLiterature',
            'duration': updated_duration,
            'nodes': nodes,
            'timings': timings,
            'host_paper_dir': f'data/accessions/{accession}/library/host_lit'}




def ClassifyThermalRangeHostLiterature(state: AgentState) -> dict:
    """Use the LLM to extract host species from paper text."""
    node = 'ClassifyThermalRangeHostLiterature'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time()
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    max_chars = _max_paper_chars(model)


    patterns = {
        # organisms
        "mesophile": r"\bmesophil(?:e|ic|es|icity)?\b",
        "psychrophile": r"\bpsychrophil(?:e|ic|es|icity)?\b",
        "thermophile": r"\bthermophil(?:e|ic|es|icity)?\b",
        # temperature concepts
        "temperature": r"\btemperatur(e|es)?\b",
        "optimal_growth": r"\boptimal(?:ly)?\s+(growth|temperature|growing)\b",
        # units
        "celsius": r"\b\d+(?:\.\d+)?\s?°?\s?[Cc]\b|\bCelsius\b",
        "kelvin": r"\b\d+(?:\.\d+)?\s?[Kk]\b|\bKelvin\b"
    }

    ranked_papers = RankPapers(state['host_paper_dir'], patterns)
    ranked_papers_list=list(ranked_papers.keys())
    found_thermal = False

    for paper in ranked_papers_list:
        with open(f"{state['host_paper_dir']}/{paper}", 'r') as f:
            paper_text = f.read()

        prompt = f"""You are an expert microbiology information extraction system.

            Your task is to determine the thermal characteristics of the organism needed from information described in the paper.

            The organism in question: {state['phage']}

            STRICT RULES:
            - Only use information explicitly stated in the paper.
            - Do NOT infer thermal range from species name or prior knowledge.
            - If no temperature or thermal information is stated, return None.

            THERMAL CLASS DEFINITIONS:
            - psychrophile: optimal growth < 15°C
            - mesophile: 15–45°C
            - thermophile: > 45°C
            Return ONLY valid JSON with:
            - "thermal_range": one of ["psychrophile", "mesophile", "thermophile", None]
            - "temperature": exact temperature or range quoted from the paper, or None
            - "thermal_reasoning":  Step by step explanation of what led to your answer, including quotes from the paper
            - "inference_type": "explicit | inferred | none",
            - "thermal_confidence": one of ["low", "medium", "high"]
            - "thermal_found": Boolean True or False depending on whether a thermal range can be found in the paper.

            INFERENCE RULES:
            - explicit: metadata directly states temperature or growth condition
            - inferred: environment strongly implies thermal range
            - none: no environmental information available

            CONFIDENCE GUIDELINES:
            - high: explicitly stated in paper 
            - medium: strongly implied in paper
            - low: weak or uncertain evidence

            Paper text:
            {_truncate(paper_text, max_chars)}
            """

        out = llm.invoke(prompt)

        try:
            data = json.loads(out.content)
        except json.JSONDecodeError:
            continue

        if data.get('thermal_found'):  # if a result is found
            found_thermal = True
            end = time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration

            return {
                "thermal_range": data.get("thermal_range", None),
                "temperature": data.get("temperature", None),
                "inference_type": data.get("inference_type", None),
                "thermal_reasoning": data.get("thermal_reasoning", None),
                "thermal_confidence": data.get("thermal_confidence", None),
                "thermal_source": 'host_literature',
                "thermal_found": True,
                "decision": "end",
                "duration": updated_duration,
                "timings": timings,
                "nodes": nodes,
                'thermal_paper': paper
            }

    if not found_thermal:
        end = time.time()
        duration = round((end - start), 2)
        updated_duration = state['duration'] + duration
        timings = state.get("timings", {}).copy()
        timings[node] = duration

        return {
            "decision": 'ClassifyThermalForced',
            'duration': updated_duration,
            'timings': state['timings'],
            'nodes': nodes,

        }


def ClassifyThermalForced(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)

    node='ClassifyThermalForced'
    nodes = (state.get("nodes") or []) + [node]

    prompt = f"""You are an expert microbiology information extraction system.
        Your task is to identify the thermal range of a bacteriophage.
        DATA SOURCES:
        1. Metadata

        RULES:
        - Ensure the thermal range is for the target species
        - You must return an answer. USe any information possible but you must return an answer for the thermal range.


        Return ONLY valid JSON with:
        - "thermal_range": the thermal range of the bacteriophage. One of ['mesophile', 'thermophile', 'psychrophile']
        - "thermal_reasoning":  Step by step explanation of what led to your answer, including quotes from the paper
        - "inference_type": "explicit | inferred | none",
        


        Target species:
        {state["phage"]}

        Metadata:
        {state["metadata"]}
        """
    start=time.time()
    out = llm.invoke(prompt)
    end = time.time()
    duration = round((end-start),2)

    #update duration
    updated_duration=state['duration'] + duration

    #update timings
    timings = state.get("timings", {}).copy()
    timings[node] = duration

    try:
        data = json.loads(out.content)
    except json.JSONDecodeError:
        return {
            'decision': 'end',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'JSONDecodeError': True
        }


    return {
        "thermal_range": data.get("thermal_range"),
        "inference_type": 'forced',
        "thermal_reasoning": 'forced',
        "thermal_source": 'metadata',
        "thermal_found": True,
        "decision": 'end',
        "duration": updated_duration,
        "timings": timings,
        "nodes": nodes,

    }



# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
def route(state: AgentState):
    return state["decision"]


def BuildGraph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Define nodes
    graph.add_node('ClassifyThermalMetadata', ClassifyThermalMetadata)
    graph.add_node('CreateAccessionLibrary', CreateAccessionLibrary)
    graph.add_node('ClassifyThermalLiterature', ClassifyThermalLiterature)
    graph.add_node('ClassifyHostMetadata', ClassifyHostMetadata)
    graph.add_node('ClassifyHostLiterature', ClassifyHostLiterature)
    graph.add_node('CreateHostLibrary', CreateHostLibrary)
    graph.add_node('ClassifyThermalRangeHostLiterature', ClassifyThermalRangeHostLiterature)
    graph.add_node('ClassifyThermalForced', ClassifyThermalForced)

    # Define paths
    # Can thermal range be confidently inferred from metadata
    graph.add_edge(START, 'ClassifyThermalMetadata')

    graph.add_conditional_edges('ClassifyThermalMetadata', route,
                                {'end': END,
                                 'CreateAccessionLibrary': 'CreateAccessionLibrary'})

    graph.add_edge('CreateAccessionLibrary', 'ClassifyThermalLiterature')

    graph.add_conditional_edges('ClassifyThermalLiterature', route,
                               {'end': END,
                                'ClassifyHostMetadata': 'ClassifyHostMetadata'})

    graph.add_conditional_edges('ClassifyHostMetadata', route,
                               {'ClassifyHostLiterature': 'ClassifyHostLiterature',
                                'CreateHostLibrary': 'CreateHostLibrary'})

    graph.add_conditional_edges('ClassifyHostLiterature', route,
                               {'ClassifyThermalForced': 'ClassifyThermalForced',
                                'CreateHostLibrary': 'CreateHostLibrary'})

    graph.add_edge('CreateHostLibrary', 'ClassifyThermalRangeHostLiterature')

    graph.add_conditional_edges('ClassifyThermalRangeHostLiterature', route,
                               {'end': END,
                                'ClassifyThermalForced': 'ClassifyThermalForced'})

    graph.add_edge('ClassifyThermalForced', END)

    return graph.compile()

def VisualiseGraph():
    graph = BuildGraph()

    png = graph.get_graph().draw_mermaid_png()
    with open("images/graph.png", "wb") as f:
        f.write(png)


def MESOTHERMOPSYCHRO(accession: str, model: str) -> AgentState:

    metadata=FetchNcbiMetadata(accession)
    phage=metadata.get('organism', 'unknown')

    graph = BuildGraph()

    result=graph.invoke({
    #model
    'model': model or OLLAMA_MODEL,
    # Phage Specific metric
    'accession': accession,
    'phage': phage, #species name
    'metadata': metadata,

    #  host classification
    'host': None,
    'taxonomic_level': None,
    'host_reasoning': None,
    'host_confidence': None,
    'host_source': None,
    'host_found': False,

    # thermal classification
    'thermal_range': None,
    'temperature': None,
    'thermal_reasoning': None,
    'thermal_confidence': None,
    'thermal_source': None,
    'thermal_found': False,
    'inference_type': None,

    # paper info
    'paper_dir': f'data/accessions/{accession}/library/accession_lit',
    'host_paper_dir': None,
    'host_paper': None,
    'thermal_paper': None,
    #may need to add extra paper things e.g. number of papers and current paper/ seperate accession and host papers

    #meta information
    'duration': 0.0,
    'decision': '',
    'nodes': [],
    'timings': {},
    'JSONDecodeError': False
    })

    return result