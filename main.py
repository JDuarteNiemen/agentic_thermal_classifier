from papers import *
from graphs import *
from agents import *


def MESOTHERMOPSYCHRO(accession: str, model: str,) -> AgentState:

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


def DemocraticTMP(accession: str, model: str) -> AgentState:

    metadata=FetchNcbiMetadata(accession)
    phage=metadata.get('organism', 'unknown')

    os.makedirs(f'data/accessions/{accession}/reasoning', exist_ok=True)
    WriteJson(metadata, f'data/accessions/{accession}/{accession}')

    graph = DemocraticGraph()

    result = graph.invoke({
        # model
        'model': model or OLLAMA_MODEL,
        # Phage Specific metric
        'accession': accession,
        'phage': phage,  # species name
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
        'thermal_votes': {'mesophile': 0, 'thermophile': 0, 'psychrophile': 0, 'none': 0},
        'thermal_reasoning_file': f'data/accessions/{accession}/reasoning/reasoning.txt',


        # paper info
        'paper_dir': f'data/accessions/{accession}/library/accession_lit',
        'paper_dir_size': 0,
        'host_paper_dir': f'data/accessions/{accession}/library/host_lit',
        'host_paper_dir_size': 0,
        'host_paper': None,
        'thermal_paper': None,
        # may need to add extra paper things e.g. number of papers and current paper/ seperate accession and host papers

        # meta information
        'duration': 0.0,
        'decision': '',
        'nodes': [],
        'timings': {},
        'JSONDecodeError': False
    })

    return result

def SummaryTMP(accession: str, model: str) -> AgentState:

    metadata=FetchNcbiMetadata(accession)
    phage=metadata.get('organism', 'unknown')

    os.makedirs(f'data/accessions/{accession}', exist_ok=True)

    WriteJson(metadata, f'data/accessions/{accession}/{accession}')

    graph = SummaryGraph()
    result = graph.invoke({
        #model
        'model': model or OLLAMA_MODEL,
        #phage specific metrics
        'accession': accession,
        'phage': phage,
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
        'thermal_found': False,


        #paper info
        'summary_file': f'data/accessions/{accession}/summary/summary.txt',
        'paper_dir': f'data/accessions/{accession}/library/accession_lit',
        'paper_dir_size': 0,
        'relevant_accession_papers': [],
        'relevant_accession_dir_size': 0,
        'host_paper_dir': f'data/accessions/{accession}/library/host_lit',
        'host_paper_dir_size': 0,
        'relevant_host_papers': [],
        'relevant_host_dir_size': 0,

        # meta information
        'duration': 0.0,
        'decision': '',
        'nodes': [],
        'timings': {},
        'JSONDecodeError': False
    })

    return result