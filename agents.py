# imports
from platform import node

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langchain_core.exceptions import OutputParserException
import requests
from typing import TypedDict, Optional
import json
from tools import *
import time
from papers import *
from pydantic import BaseModel
from prompts import *
from helpers import _truncate, _build_llm, OLLAMA_MODEL, OLLAMA_BASE_URL, _max_paper_chars


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
# Structured Output States
# ---------------------------------------------------------------------------
# Thermal Classification output state
class ThermalOutput(BaseModel):
    thermal_range: str
    temperature: Optional[str] = None
    inference_type: str
    thermal_reasoning: str
    thermal_confidence: Optional[str] = None
    thermal_found: bool

class HostOutput(BaseModel):
    host: str
    taxonomic_level: str
    host_reasoning: str
    host_found: bool



# ---------------------------------------------------------------------------
# GRAPH NODES
# ---------------------------------------------------------------------------

def ClassifyThermalMetadata(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    llm=llm.with_structured_output(ThermalOutput)

    node = "ClassifyThermalMetadata"
    nodes = (state.get("nodes") or []) + [node]

    prompt=CLASSIFYTHERMALMETADATAPROMPT(state['metadata'])

    start=time.time()
    out = llm.invoke(prompt)
    print(f'{node}: {out}\n\n')
    end = time.time()
    duration = round((end-start),2)

    #update duration
    updated_duration=state['duration'] + duration

    #update timings
    timings = state.get("timings", {}).copy()
    timings[node] = duration

    try:
        if not out.thermal_found:
            return {
                'decision': 'CreateAccessionLibrary',
                'nodes': nodes,
                'duration': updated_duration,
                'timings': timings,
            }
    except OutputParserException:
        return {
            'decision': 'CreateAccessionLibrary',
                'nodes': nodes,
                'duration': updated_duration,
                'timings': timings,
                'JSONDecodeError': True
            }



    if out.thermal_found:
        return {
        "thermal_range": out.thermal_range,
        "inference_type": out.inference_type,
        "thermal_reasoning": out.thermal_reasoning,
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
    llm = llm.with_structured_output(ThermalOutput)
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


        prompt = CLASSIFYTHERMALLITERATUREPROMPT(state['phage'], paper_text, max_chars)

        out = llm.invoke(prompt)
        print(f'{node}: {out}\n\n')

        try:
            if not out.thermal_found:
                continue
        except OutputParserException:

            continue




        if out.thermal_found: # if a result is found
            found_thermal=True
            end = time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration

            return {
                "thermal_range": out.thermal_range,
                "temperature": out.temperature,
                "inference_type": out.inference_type,
                "thermal_reasoning": out.thermal_reasoning,
                "thermal_confidence": out.thermal_confidence,
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
    llm = llm.with_structured_output(HostOutput)

    prompt = CLASSIFYTHERMALMETADATAPROMPT(state['metadata'])

    start = time.time()
    out = llm.invoke(prompt)
    print(f'{node}: {out}\n\n')
    end = time.time()

    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration
    timings = state.get("timings", {}).copy()
    timings[node] = duration


    if out.host_found:
        return {
            "host": out.host,
            "host_found": out.host_found,
            "taxonomic_level": out.taxonomic_level,
            "host_reasoning": out.host_reasoning,
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
    llm = llm.with_structured_output(HostOutput)
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

        prompt = CLASSIFYHOSTLITERATUREPROMPT(state['phage'], paper_text, max_chars)

        out = llm.invoke(prompt)
        print(f'{node}: {out}\n\n')


        if not host_found:
            continue

        if out.host_found:
            host_found=True
            end=time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration
            return {
                "host": out.host,
                "taxonomic_level": out.taxonomic_level,
                "host_reasoning": out.host_reasoning,
                "host_confidence": out.host_confidence,
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
    host=state.get('host')
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
    llm = llm.with_structured_output(ThermalOutput)
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

        prompt = CLASSIFYTHERMALRANGEHOSTLITERATUREPROMPT(state['host'], paper_text, max_chars)

        out = llm.invoke(prompt)
        print(f'{node}: {out}\n\n')


        if not out.thermal_found:
            continue

        if out.thermal_found:  # if a result is found
            found_thermal = True
            end = time.time()
            duration = round((end - start), 2)
            updated_duration = state['duration'] + duration
            timings = state.get("timings", {}).copy()
            timings[node] = duration

            return {
                "thermal_range": out.thermal_range,
                "temperature": out.temperature,
                "inference_type": out.inference_type,
                "thermal_reasoning": out.thermal_reasoning,
                "thermal_confidence": out.thermal_confidence,
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
    llm = llm.with_structured_output(ThermalOutput)

    node='ClassifyThermalForced'
    nodes = (state.get("nodes") or []) + [node]

    prompt = CLASSIFYTHERMALFORCEDPROMPT(state['phage'], state['metadata'])
    start=time.time()
    out = llm.invoke(prompt)
    print(f'{node}: {out}\n\n')
    end = time.time()
    duration = round((end-start),2)

    #update duration
    updated_duration=state['duration'] + duration

    #update timings
    timings = state.get("timings", {}).copy()
    timings[node] = duration


    if not out.thermal_found:
        return {
            'decision': 'end',
            'nodes': nodes,
            'duration': updated_duration,
            'timings': timings,
            'JSONDecodeError': True
        }


    return {
        "thermal_range": out.thermal_range,
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

    os.makedirs(f'data/accessions/{accession}', exist_ok=True)
    WriteJson(metadata, f'data/accessions/{accession}/{accession}')

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