# Model Benchmarking

Comparing the outputs from various different models


## Overview
Will add a new strategy. V6 is a fast, first to evidence classification

Democratic uses each paper associated with the accession as host as a vote towards the classification. aswell as a 
forced and normal classification from metadata contributing a vote each respectively.


## Model
Will use gemma4 moving forward due to its performance on example data in terms of speed and accuracy
### gemma4:e4b 
Gemma 4 models are designed to deliver frontier-level performance at each size. 
They are well-suited for reasoning, agentic workflows, coding, and multimodal understanding

#### Details
  Model
    architecture        gemma4    
    parameters          8.0B      
    context length      131072    
    embedding length    2560      
    quantization        Q4_K_M    
    requires            0.20.0    

  Capabilities
    completion    
    vision        
    audio         
    tools         
    thinking      

  Parameters
    temperature    1       
    top_k          64      
    top_p          0.95    

  License
    Apache License               
    Version 2.0, January 2004 



# Democratic classifiction

## Pipeline Steps

- Builds a structured library of all accession records for downstream processing.

- LLM call to assess whether the paper is about the phage and whether it may have any clues about the thermal range.

#### IF paper is relevant:
- summarise the paper and write summary to a file

#### IF paper is NOT relevant
- remove it from the library

#### IF no relevant papers
- classify host from metadata or literature

- assess host literature for relevance

- if relevant summarise it and write summary to a file

IF relevant papers:
extract host
get host literature
write them to a file

run the summary through an LLM call. prompting it as to whether the full summary would be talking about a mesophile, thermophile or psychrophile.

summary will be annonymized, the prompt will be to summarise only the target species, but in place of writing the species name
instead it will be a place holder ('the organism' or 'target species' etc..) So thay summary of the accession literature and host can all be in one file.

![Democratic agentic workflow](images/DemocraticGraph.png)



