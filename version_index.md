# Model Benchmarking

Comparing the outputs from various different models


## Overview
Using the method outlined in v4 to test the accuracy of different models.

## Models 
### qwen3.5
Qwen 3.5 is a family of open-source multimodal models that delivers exceptional utility and performance.

#### Details
 Model
    architecture        qwen35    
    parameters          9.7B      
    context length      262144    
    embedding length    4096      
    quantization        Q4_K_M    
    requires            0.17.1    

  Capabilities
    completion    
    vision        
    tools         
    thinking      

  Parameters
    presence_penalty    1.5     
    temperature         1       
    top_k               20      
    top_p               0.95    

  License
    Apache License               
    Version 2.0, January 2004  



### gemma4:e4b 
Gemma 4 models are designed to deliver frontier-level performance at each size. They are well-suited for reasoning, agentic workflows, coding, and multimodal understanding

#### Details


### granite4.1:8b
Granite 4.1 language models are a family of state-of-the-art open foundation models featuring dense decoder-only architectures

#### Details




---


## Pipeline Steps

### 1. Accession Library Creation
- Builds a structured library of all accession records for downstream processing.

---

### 2. Thermal Identification from Metadata
- Scans metadata to determine whether thermal range information is already present.

#### IF thermal range is found:
- Return thermal range

#### IF NOT:
- Proceed to literature retrieval

---

### 3. Accession-linked Literature Analysis
- Retrieves literature associated with the accession for thermal inference.

---

### 4. Thermal Range Identification from Accession Literature
- Classifies thermal range using accession-linked literature.

#### IF thermal range is found:
- Return thermal range

#### IF NOT:
- Proceed to host identification step

---

### 5. Host Identification
- Identifies host organism associated with the accession.

#### IF host is NOT found:
- Perform forced classification using metadata
- Return thermal range

#### IF host IS found:
- Proceed to host literature retrieval

---

### 6. Literature Retrieval for Host (Query Search)
- Retrieves literature associated with the identified host.

---

### 7. Thermal Range Identification from Host Literature
- Classifies thermal range using host-associated literature.

#### IF thermal range is found:
- Return thermal range

#### IF NOT:
- Proceed to final fallback classification

---

### 8. Forced Classification Using Phage Metadata
- Applies final fallback thermal classification using phage-level metadata.

#### Output:
- Return thermal range

---

![Agentic Workflow](images/graph.png)

Total Duration: 38.38 minutes



