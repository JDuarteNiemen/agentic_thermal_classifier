# V8 Implementing the summary workflow


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



# Summary classifiction

## 1. Load Accession
- Load accession metadata.
- Build a local working library for the accession.

---

## 2. Retrieve Associated Literature
- Collect all papers linked to the accession.
- Store papers as text files for processing.

---

## 3. Literature Relevance Screening
For each paper associated with the accession:

- Run an LLM classification step to determine:
  - Whether the paper is about the target phage.
  - Whether it contains information related to thermal range or temperature adaptation.

### If relevant:
- Generate a concise summary of the paper.
- Save the summary to file.
- Keep the paper in the working library.

### If not relevant:
- Remove the paper from the working library.

---

## 4. Check for Relevant Phage Literature

### If relevant phage papers exist:
#### Extract Host Information
- Extract host organism(s) from the relevant literature.
- Retrieve host-associated literature.
- Summarise relevant host literature.
- Save summaries to file.

### If no relevant phage papers exist:
#### Fallback Host-Based Analysis
- Infer or classify the host organism using:
  - accession metadata
  - linked literature

- Retrieve host-associated literature.

- Assess host literature for relevance to thermal adaptation.

### If relevant:
- Generate summaries of the host literature.
- Save summaries to file.

---

## 5. Final Fallback: Forced Metadata Classification

### Trigger condition:
- No relevant phage literature exists.
- No relevant host literature exists.
- No usable literature is available for the accession.

### Steps:
- Perform a forced classification using only available metadata, including:
  - host taxonomy
  - isolation source
  - geographic information
  - environmental descriptors
  - accession annotations

- Infer the most likely thermal category from metadata alone.

---

## 6. Combine and Anonymise Summaries
### Trigger condition:
- Relevant literature summaries exist.

### Steps:
- Combine:
  - phage literature summaries
  - host literature summaries

- Replace species names with placeholders such as:
  - `"the organism"`
  - `"the target species"`

### Purpose:
- Prevent species-name bias during classification.

---

## 7. Thermal Classification
### If literature summaries exist:
- Pass the anonymised summary into a final LLM classification step.

### If no literature summaries exist:
- Use the forced metadata classification result.

### Target classifications:
- Psychrophile
- Mesophile
- Thermophile

---

## 8. Save Outputs
Store:
- accession metadata
- relevance decisions
- extracted hosts
- literature summaries
- anonymised summaries
- metadata-only classification (if used)
- final thermal classification
![Summary agentic workflow](images/SummaryGraph.png)



