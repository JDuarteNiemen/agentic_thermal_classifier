# Documentation of process


# Library Curation
To generate of library of literature for each ncbi accession I start off by pulling all the PubMed Ids (pmids) 
associated with the accession. I then attempt to convert these to PubMed Central ids (pmcids) as these give me access to
the full paper, as opposed to pmids in which only the abstract is avaliable. If there is no pmcid avaliable the abstract 
of the paper is stored.
If there are no PubMed papers avaliable from the intial search, a query search is used in place of accessions to get 
published papers. Again these are converted to pmcids to save the full paper, and the abstract is stored if pmcid is not 
avaliable.


# Host classification
To find the host of the phage I ran each accession through the library generation process and then each paper was passed
through an LLM. The LLM viewed one paper at a time and was tasked with extracting the host species of the given phage.
It was also supplied with the metadata avaliable from ncbi for each accession, in hopes that it would not confuse the
phage in question. 
The output was the name of the host species identified, its reasoning with quotes of the paper and its confidence
[low, medium, high].
If no host was found the LLM would move onto the next paper, with no prior information extracted from previous papers
being passed on. 



# Thermal classification
To thermally classify the accessions, I used the library created by the initial accession pull.(Focused on the phage
protein). The same papers were then put through an LLM. The LLM viewed one paper at a time, its output was the thermal
range, temperature identified, its reasoning and confidence. If it could not be found it was left unknown and the LLM
would move onto the next paper with no prior information extracted from previous papers being passed on.



# Results
To evaluate performance I created an example dataset of 15 protein accession, with 5 from each thermal range. [Mesophile,
thermophile, Psychrophile]. I ran these accessions through my pipeline to find out whether the results it returned were
the same as the ground truths established. 


+-------------+----------------------------------+------------------------------------+------------+-------------------------------------------------------------+
|C1           |C2                                |C3                                  |C4          |C5                                                           |
+-------------+----------------------------------+------------------------------------+------------+-------------------------------------------------------------+
|Thermal Range|Species                           |Host                                |Accession   |Protein                                                      |
|Mesophile    |Tequatrovirus T4                  |Acinetobacter baumannii             |ADI87650    |major head protein, partial [Tequatrovirus T4]               |
|Mesophile    |Teseptimavirus T7                 |Escherichia coli B                  |WXH46553    |terminase large subunit [Teseptimavirus T7]                  |
|Mesophile    |Escherichia phage Lambda          |Escherichia coli                    |WRQ14408    |endolysin [Escherichia phage Lambda]                         |
|Mesophile    |Escherichia phage T2              |Escherichia coli                    |XYW65533    |DNA helicase [Escherichia phage T2]                          |
|Mesophile    |Emesvirus zinderi                 |Escherichia coli                    |SNQ28030    |RNA replicase, beta subunit [Emesvirus zinderi]              |
|Thermophile  |Thermus phage P23-45              |Thermus thermophilus                |A7XXB7      |DNA-packaging protein                                        |
|Thermophile  |Thermus phage TSP4                |Thermus sp. TC4                     |QAY18187    |metal-dependent hydrolase [Thermus phage TSP4]               |
|Thermophile  |Geobacillus virus E2              |Geobacillus                         |YP_001285867|ATPase [Geobacillus virus E2]                                |
|Thermophile  |Rhodothermus phage RM378          |Rhodothermus marinus                |NP_835731   |RNA polymerase sigma factor [Rhodothermus phage RM378]       |
|Thermophile  |Thermus virus YS40                |Thermus thermophilus                |YP_874174   |Fe-S oxidoreductase [Thermus phage phiYS40]                  |
|Psychrophile |Pseudoalteromonas phage vB_Psp_PY6|Pseudoalteromonas sp. YM19          |XJP07760    |terminase large subunit [Pseudoalteromonas phage vB_Psp_PY6] |
|Psychrophile |Pseudoalteromonas phage proACA1-A |Acinetobacter baumannii             |WMT83805    |integrase [Pseudoalteromonas phage proACA1-A]                |
|Psychrophile |Shewanella phage SppYZU05         |Unknown                             |YP_009790355|tail fiber protein [Shewanella phage SppYZU05]               |
|Psychrophile |Colwellia phage 9A                |Colwellia psychrerythraea strain 34H|YP_006489335|hypothetical protein COPG_00149, partial [Colwellia phage 9A]|
|Psychrophile |Polaribacter phage P12002L        |Polaribacter sp. IMCC12002          |YP_009209738|hypothetical protein AVT43_gp78 [Polaribacter phage P12002L] |
+-------------+----------------------------------+------------------------------------+------------+-------------------------------------------------------------+

## Host classification results
These were entered into the example csv, identified 14/15.


## Thermal classification results

This intial iteration has a very simple evaluation output, i will condense the results here
+-------------+------------+------------------+---------------------+-------------------+
|Thermal Range|Accession   | Number of Papers | Number of LLM calls | Total time (mins) |
+-------------+------------+------------------+---------------------+-------------------+
|Unknown      |ADI87650    | 19               | 11                  | 56                |
|Mesophile    |WXH46553    | 20               | 2                   | 7                 | 
|Unknown      |WRQ14408    | 20               | 8                   | 17                |
|Mesophile    |XYW65533    | 20               | 2                   | 6                 |
|Unknown      |SNQ28030    | 21               | 10                  | 513               |
|Thermophile  |A7XXB7      | 11               | 1                   | 3                 |
|Unknown      |QAY18187    | 6                | 1                   | 18                |
|Unknown      |YP_001285867| 3                | 1                   | 4                 | 
|Unknown      |NP_835731   | 3                | 1                   | 7                 |
|Unknown      |YP_874174   | 5                | 2                   | 15                | 
|Unknown      |XJP07760    | 1                | 0                   | 3                 |
|Unknown      |WMT83805    | 20               | 9                   | 552               |  
|Unknown      |YP_009790355| 2                | 1                   | 4                 |
|Unknown      |YP_006489335| 3                | 1                   | 10                |
|Unknown      |YP_009209738| 2                | 1                   | 5                 |
+-------------+------------+------------------+---------------------+--------------------
Accuracy = 3/15
Precision = Mesophile: 1.0, thermophile: 1.0, Psychrophile: NA
Recall = Mesophile: 0.4, thermophile: 0.2, Psychrophile: 0.0
f1 = Mesophile: 0.57, thermophile: 0.33, Psychrophile: 0.0



# Discussion

## Host classification
Worked well identifying hosts, however there were cases were i had to make a decision as the LLM would classify 2 hosts
and i would select the one that best matched. 

## Thermal Classification
Performed poorly, not identifying a single Psychrophile. There were 0 misclassifications which is positive however the
overall performance was poor. There is an issue with many LLM calls returning as none.
In the current state no prior information from past papers can help classify. Each paper is treated independently either
being used to make a classification or being ignored.
There is no chaining of models currently one LLM call being ran. 


## Computational time
These results are slightly biased by hardware issues (my cat unplugged my mac multiple times). There is also little to
no optimisation to speed up results.



## prompts

### Host identification
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

### Thermal classification
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



