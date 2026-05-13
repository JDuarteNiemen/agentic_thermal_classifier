from typing import TypedDict, Optional, Dict, List
from pydantic import BaseModel



# ---------------------------------------------------------------------------
# Shared Core State
# ---------------------------------------------------------------------------

class BaseState(TypedDict):

    # model
    model: str

    # phage specific metrics
    accession: str
    phage: str
    metadata: str

    # host classification
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
    thermal_found: bool

    # shared paper info
    paper_dir: str
    paper_dir_size: int
    host_paper_dir: str
    host_paper_dir_size: int

    # meta information
    duration: float
    decision: str

    nodes: List[str]
    timings: Dict[str, float]
    JSONDecodeError: bool

# ---------------------------------------------------------------------------
# Shared Inference State
# Used by Fast + Democratic
# ---------------------------------------------------------------------------

class InferenceState(BaseState):
    thermal_source: str
    inference_type: str
    host_paper: str
    thermal_paper: str

# ---------------------------------------------------------------------------
# Fast State
# ---------------------------------------------------------------------------
class FastState(InferenceState):
    pass

# ---------------------------------------------------------------------------
# Democratic State
# ---------------------------------------------------------------------------
class DemocraticState(InferenceState):
    thermal_votes: Optional[dict]
    thermal_reasoning_file: str

# ---------------------------------------------------------------------------
# Summary State
# ---------------------------------------------------------------------------
class SummaryState(BaseState):
    summary_file: str
    relevant_accession_papers: List[str]
    relevant_accession_dir_size: int
    relevant_host_papers: List[str]
    relevant_host_dir_size: int

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

class SummaryOutput(BaseModel):
    summary: str

class RelevantOutput(BaseModel):
    verdict: bool
    reasoning: str
