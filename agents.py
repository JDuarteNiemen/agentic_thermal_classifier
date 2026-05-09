# imports


from langchain_core.exceptions import OutputParserException
from tools import *
import time
from papers import *
from prompts import *
from helpers import  _build_llm, OLLAMA_MODEL, _max_paper_chars
from states import *


# ---------------------------------------------------------------------------
# GRAPH NODES
# ---------------------------------------------------------------------------

def ClassifyThermalMetadata(state: AgentState) -> dict:
    """Use the LLM to classify the thermal range from metadata."""
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
    """Create library fro  literature associated with the ncbi accession"""
    node='CreateAccessionLibrary'
    nodes = (state.get("nodes") or []) + [node]

    start = time.time() # set start
    CreateLibrary(state['accession'], state['metadata']) # create library for accession

    paper_dir_size=len(os.listdir(state['paper_dir']))
    end = time.time() # set end

    # Updating durations
    duration = round((end-start),2)
    updated_duration=state['duration'] + duration
    timings = state.get("timings", {}).copy()
    timings[node] = duration


    return {'decision': 'ClassifyThermalLiterature',
            'duration': updated_duration,
            'nodes': nodes,
            'timings': timings,
            'paper_dir_size': paper_dir_size,}


def ClassifyThermalLiterature(state: AgentState) -> dict:
    """Use the LLM to classify thermal range of the phage from paper text."""
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

    prompt = CLASSIFYHOSTMETADATAPROMPT(state['metadata'])

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
    #create librbar
    HostLibrary(accession, host)

    #get number of papers
    papers=os.listdir(state['host_paper_dir'])
    host_paper_dir_size=len(papers)

    end = time.time()
    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration
    timings = state.get("timings", {}).copy()


    return {'decision': 'ClassifyThermalRangeHostLiterature',
            'duration': updated_duration,
            'nodes': nodes,
            'timings': timings,
            'host_paper_dir': f'data/accessions/{accession}/library/host_lit',
            'host_paper_dir_size': host_paper_dir_size}




def ClassifyThermalRangeHostLiterature(state: AgentState) -> dict:
    """Use the LLM to Classify thermal range from host literature"""
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
# ================ #
# Democratic Nodes #
# ================ #

def ClassifyThermalMetadataVote(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    llm=llm.with_structured_output(ThermalOutput)

    with open(state['thermal_reasoning_file'], 'w') as f:
        f.write(f'=============Reasoning for {state["accession"]} from metadata=============\n')

    #Defining node and adding it to the list
    node = "ClassifyThermalMetadataVote"
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


    # Update dictionary
    print(f'Classification{repr(out.thermal_range)}')
    thermal = out.thermal_range.strip().lower()
    votes = state.get("thermal_votes", {}).copy()
    try:
        votes[thermal] += 1
    except KeyError:
        return {
            "thermal_votes": votes,
            "decision": 'ClassifyThermalLiteratureVotes',
            "duration": updated_duration,
            "timings": timings,
            "nodes": nodes,
                }

    # Save reasoning
    with open(state['thermal_reasoning_file'], 'a') as f:
        f.write(f'Classification: {out.thermal_range}\n')
        f.write(f'Confidence: {out.thermal_confidence}\n')
        f.write(f'Inference Type: {out.inference_type}\n')
        f.write(f'Reasoning: {out.thermal_reasoning}\n\n\n')


    return {
    "thermal_votes": votes,
    "decision": 'ClassifyThermalLiteratureVotes',
    "duration": updated_duration,
    "timings": timings,
    "nodes": nodes,
}



def ClassifyThermalLiteratureVotes(state: AgentState) -> dict:
    """Use the LLM to vote on the thermal range of each paper."""
    with open(f'{state["thermal_reasoning_file"]}', 'a') as f:
        f.write(f'=============Reasoning for {state["accession"]} from accession literature=============\n')


    node = 'ClassifyThermalLiteratureVotes'
    nodes = (state.get("nodes") or []) + [node]

    votes = state.get("thermal_votes", {}).copy()

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

    # Rank papers and remove any with 0 hits
    ranked_papers = RankPapers(state['paper_dir'], patterns)
    ranked_papers_list = [
        key for key, value in ranked_papers.items()
        if value != 0
    ]


    for paper in ranked_papers_list:
        with open(f"{state['paper_dir']}/{paper}", 'r') as f:
            paper_text = f.read()

        prompt = CLASSIFYTHERMALLITERATUREPROMPT(state['phage'], paper_text, max_chars)

        out = llm.invoke(prompt)
        print(f'{node}: {out}\n\n')

        try:
            if not out.thermal_found:
                continue
        except OutputParserException:
            continue



        #Update dictionary
        thermal = out.thermal_range.strip().lower()
        try:
            votes[thermal] += 1
        except KeyError:
            continue

        # Save reasoning
        with open(state['thermal_reasoning_file'], 'a') as f:
            f.write(f'Paper: {paper}\n')
            f.write(f'Classification: {out.thermal_range}\n')
            f.write(f'Confidence: {out.thermal_confidence}\n')
            f.write(f'Inference Type: {out.inference_type}\n')
            f.write(f'Reasoning: {out.thermal_reasoning}\n\n\n')



    end=time.time()
    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration

    timings = state.get("timings", {}).copy()
    timings[node] = duration

    return {'duration': updated_duration,
            'timings': timings,
            'thermal_votes': votes,
            'nodes': nodes,
            'decision': 'ClassifyThermalRangeHostLiteratureVotes'
            }




def ClassifyThermalRangeHostLiteratureVotes(state: AgentState) -> dict:
    """Use the LLM to extract host species from paper text."""
    node = 'ClassifyThermalRangeHostLiterature'
    nodes = (state.get("nodes") or []) + [node]

    votes = state.get("thermal_votes", {}).copy()

    with open(f"{state['thermal_reasoning_file']}", 'a') as f:
        f.write(f'=============Reasoning for {state["accession"]} from host literature=============\n')

    start = time.time()
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    llm = llm.with_structured_output(ThermalOutput)
    max_chars = _max_paper_chars(model)

    votes = state.get("thermal_votes", {}).copy()

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

    # Ranking papers and skipping any with 0 hits for regex
    ranked_papers = RankPapers(state['host_paper_dir'], patterns)
    ranked_papers_list = [
        key for key, value in ranked_papers.items()
        if value != 0
    ]


    for paper in ranked_papers_list:
        with open(f"{state['host_paper_dir']}/{paper}", 'r') as f:
            paper_text = f.read()

        prompt = CLASSIFYTHERMALLITERATUREPROMPT(phage=state['phage'], paper_text=paper_text, max_chars=max_chars)

        out = llm.invoke(prompt)
        print(f'{node}: {out}\n\n')

        try:
            if not out.thermal_found:
                continue
        except OutputParserException:
            continue

        # Update dictionary
        thermal = out.thermal_range.strip().lower()
        try:
            votes[thermal] += 1
        except KeyError:
            continue

        # Save reasoning
        with open(state['thermal_reasoning_file'], 'a') as f:
            f.write(f'Paper: {paper}\n')
            f.write(f'Classification: {out.thermal_range}\n')
            f.write(f'Confidence: {out.thermal_confidence}\n')
            f.write(f'Inference Type: {out.inference_type}\n')
            f.write(f'Reasoning: {out.thermal_reasoning}\n\n\n')

    end = time.time()
    duration = round((end - start), 2)
    updated_duration = state['duration'] + duration

    timings = state.get("timings", {}).copy()
    timings[node] = duration

    return {'duration': updated_duration,
            'timings': timings,
            'thermal_votes': votes,
            'nodes': nodes,
            'decision': 'ClassifyThermalForcedVote'
            }

def ClassifyThermalForcedVote(state: AgentState) -> dict:
    """Use the LLM to extract host species from metadata."""
    model = state.get("model") or OLLAMA_MODEL
    llm = _build_llm(model)
    llm=llm.with_structured_output(ThermalOutput)

    with open(state['thermal_reasoning_file'], 'a') as f:
        f.write(f'=============Reasoning for {state["accession"]} from metadata (Forced)=============\n')

    #Defining node and adding it to the list
    node = "ClassifyThermalForcedVote"
    nodes = (state.get("nodes") or []) + [node]

    prompt=CLASSIFYTHERMALFORCEDPROMPT(phage=state['phage'], metadata=state['metadata'])

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


    # Update dictionary
    votes = state.get("thermal_votes", {}).copy()
    thermal = out.thermal_range.strip().lower()

    try:
        votes[thermal] += 1
    except KeyError:
        return {
            "thermal_votes": votes,
            "decision": 'end',
            "duration": updated_duration,
            "timings": timings,
            "nodes": nodes,
                }

    # Save reasoning
    with open(state['thermal_reasoning_file'], 'a') as f:
        f.write(f'Classification: {out.thermal_range}\n')
        f.write(f'Confidence: {out.thermal_confidence}\n')
        f.write(f'Inference Type: {out.inference_type}\n')
        f.write(f'Reasoning: {out.thermal_reasoning}\n\n\n')


    return {
    "thermal_votes": votes,
    "decision": 'end',
    "duration": updated_duration,
    "timings": timings,
    "nodes": nodes,
}

