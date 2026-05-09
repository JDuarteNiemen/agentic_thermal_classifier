from typing import TypedDict, Optional
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Fast State
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
    thermal_votes: Optional[dict] = None
    thermal_reasoning_file: str


    # paper info
    paper_dir: str
    paper_dir_size: int
    host_paper_dir: str
    host_paper_dir_size: int
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
# Democratic State
# ---------------------------------------------------------------------------
class DemocraticState(TypedDict):
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
    paper_dir_size: int
    host_paper_dir: str
    host_paper_dir_size: int
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
