# v7
Adding a democratic workflow
## Overview
Will add a new strategy. V6 is a fast, first to evidence classification

Democratic uses each paper associated with the accession as host as a vote towards the classification. aswell as a 
forced and normal classification of metadata contributing a vote each respectively.


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

### 1. Accession Library Creation
- Builds a structured library of all accession records for downstream processing.

---

### 2. Host Identification
- Attempts to identify the host organism directly from accession metadata.

#### IF host is found in metadata:
- Store host assignment

#### IF host is NOT found:
- Retrieve accession-linked literature
- Attempt host identification from literature

#### IF host is still NOT found:
- Continue pipeline without host assignment

---

### 3. Accession-linked Literature Retrieval
- Retrieves all literature associated with the accession record.

---

### 4. Thermal Range Classification from Accession papers
- Performs thermal range classification using:
  - accession metadata
  - accession-linked literature (if literature has at least one hit for the regex)

- Each successful classification contributes a **vote** toward a thermal category.

#### Output:
- Accession-level thermal votes

---

### 5. Host Literature Retrieval
- IF a host organism was identified:
  - Retrieve literature associated with the host organism.

#### IF no host was identified:
- Skip to final vote aggregation

---

### 6. Thermal Range Classification from Host Literature
- Performs thermal range classification using host-associated literature. (if paper has at least one hit on regex scan)

- Each successful classification contributes an additional **vote** toward a thermal category.

#### Output:
- Host-derived thermal votes

---

### 7. Vote Aggregation and Final Thermal Assignment
- Aggregates all thermal classification votes generated from:
  - accession metadata
  - accession-linked literature
  - host-associated literature

- The thermal range with the highest total number of votes is selected as the final classification.

#### Output:
- Final thermal range assignment
- Vote distribution across thermal categories

![Democratic agentic workflow](images/DemocraticGraph.png)



