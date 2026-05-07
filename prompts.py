# PROMPTS BEING USED IN THE WORKFLOW
from helpers import _truncate

def CLASSIFYTHERMALMETADATAPROMPT(metadata):
    return f"""
ROLE:
You are a microbiology information extraction system.

TASK:
Determine the thermal range of the bacteriophage or its host using ONLY metadata.

DATA SOURCE:
Metadata only.

STRICT RULES:
- Use ONLY the provided metadata.
- Do NOT use external knowledge.
- Do NOT infer from organism names, taxonomy, or prior knowledge.
- If no relevant information is present, return None.

DEFINITIONS:
- psychrophile: cold environments (e.g. Arctic, ice, deep sea)
- mesophile: moderate environments (e.g. soil, freshwater, host-associated)
- thermophile: hot environments (e.g. hot springs, hydrothermal vents)

INFERENCE RULES:
- explicit: temperature or growth conditions directly stated
- inferred: environment strongly implies thermal range
- none: no relevant information present

CONFIDENCE GUIDELINES:
- high: explicitly stated
- medium: strongly implied from environment
- low: weak or uncertain evidence

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "thermal_range": "psychrophile | mesophile | thermophile | None",
    "temperature": "exact value or None",
    "inference_type": "explicit | inferred | none",
    "thermal_reasoning": "step-by-step explanation based only on metadata",
    "thermal_confidence": "low | medium | high",
    "thermal_found": true/false
}}

METADATA:
{metadata}
"""


def CLASSIFYTHERMALLITERATUREPROMPT(phage, paper_text, max_chars):
    return  f"""
ROLE:
You are an expert microbiology information extraction system.

TASK:
Determine the thermal characteristics of the bacteriophage from the paper.

TARGET:
Phage: {phage}

DATA SOURCE:
Scientific paper text.

STRICT RULES:
- Use ONLY the provided paper text.
- Do NOT use external knowledge.
- Do NOT infer from organism names, taxonomy, or prior knowledge.
- You MAY infer thermal range from the host ONLY if the paper explicitly links host and phage biology.
- If no relevant information is present, return None.

DEFINITIONS:
- psychrophile: optimal growth < 15°C
- mesophile: 15–45°C
- thermophile: > 45°C

INFERENCE RULES:
- explicit: temperature or growth conditions directly stated
- inferred: strongly implied from described environment or host (if explicitly linked)
- none: no relevant information present

CONFIDENCE GUIDELINES:
- high: explicitly stated
- medium: strongly implied
- low: weak or uncertain evidence

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "thermal_range": "psychrophile | mesophile | thermophile | None",
    "temperature": "exact value or None",
    "inference_type": "explicit | inferred | none",
    "thermal_reasoning": "step-by-step explanation including quotes from the paper",
    "thermal_confidence": "low | medium | high",
    "thermal_found": true/false
}}

PAPER TEXT:
{_truncate(paper_text, max_chars)}
"""

def CLASSIFYHOSTMETADATAPROMPT(metadata):
    return f"""
ROLE:
You are a microbiology information extraction system.

TASK:
Extract the bacteriophage host organism ONLY if explicitly stated in the metadata.

DATA SOURCE:
Metadata only.

STRICT RULES:
- Use ONLY the provided metadata.
- Do NOT use external knowledge.
- Do NOT infer or guess.
- Copy values EXACTLY as written.
- If no host is explicitly present, return None.

TAXONOMIC LEVEL DEFINITIONS:
- family: e.g. Enterobacteriaceae
- genus: e.g. Escherichia
- species: e.g. Escherichia coli
- strain: e.g. E. coli K12, strain MG1655

INFERENCE RULES:
- explicit: host directly stated
- inferred: NOT ALLOWED
- none: no host present

CONFIDENCE GUIDELINES:
- high: explicitly stated
- medium: minor ambiguity in formatting
- low: unclear or partial mention

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "host_species": "<exact value OR None>",
    "taxonomic_level": "family | genus | species | strain | None",
    "host_reasoning": "step-by-step explanation based only on metadata OR 'not present in metadata'",
    "host_confidence": "low | medium | high",
    "host_found": true/false
}}

METADATA:
{metadata}
"""


def CLASSIFYHOSTLITERATUREPROMPT(phage, paper_text, max_chars):
    return f"""
ROLE:
You are an expert microbiology information extraction system.

TASK:
Identify the host species of the bacteriophage.

TARGET:
Phage: {phage}

DATA SOURCE:
Scientific paper text.

STRICT RULES:
- Use ONLY the provided paper text.
- Do NOT use external knowledge.
- Do NOT guess or infer beyond explicitly stated relationships.
- Ensure the host corresponds to the target phage.
- If no host is explicitly stated, return None.

TAXONOMIC LEVEL DEFINITIONS:
- family, genus, species, strain (same rules as metadata)

INFERENCE RULES:
- explicit: host directly stated
- inferred: only if the paper clearly links host to the phage
- none: no host present

CONFIDENCE GUIDELINES:
- high: explicitly stated
- medium: strongly implied
- low: weak or uncertain evidence

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "host_species": "<value OR None>",
    "taxonomic_level": "family | genus | species | strain | None",
    "host_reasoning": "step-by-step explanation including quotes from the paper",
    "host_confidence": "low | medium | high",
    "host_found": true/false
}}

PAPER TEXT:
{_truncate(paper_text, max_chars)}
"""


def CLASSIFYTHERMALRANGEHOSTLITERATUREPROMPT(host, paper_text, max_chars):
    return f"""
ROLE:
You are an expert microbiology information extraction system.

TASK:
Determine the thermal characteristics of the host organism from the paper.

TARGET:
Host: {host}

DATA SOURCE:
Scientific paper text.

STRICT RULES:
- Use ONLY the provided paper text.
- Do NOT use external knowledge.
- Do NOT infer from organism names or taxonomy.
- If no relevant information is present, return None.

DEFINITIONS:
- psychrophile: < 15°C
- mesophile: 15–45°C
- thermophile: > 45°C

INFERENCE RULES:
- explicit: temperature or growth conditions directly stated
- inferred: strongly implied from described environment
- none: no relevant information present

CONFIDENCE GUIDELINES:
- high: explicitly stated
- medium: strongly implied
- low: weak or uncertain evidence

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "thermal_range": "psychrophile | mesophile | thermophile | None",
    "temperature": "exact value or None",
    "inference_type": "explicit | inferred | none",
    "thermal_reasoning": "step-by-step explanation including quotes from the paper",
    "thermal_confidence": "low | medium | high",
    "thermal_found": true/false
}}

PAPER TEXT:
{_truncate(paper_text, max_chars)}
"""

def CLASSIFYTHERMALFORCEDPROMPT(phage, metadata):
    return f"""
ROLE:
You are an expert microbiology information extraction system.

TASK:
Assign a thermal range classification to the target bacteriophage using metadata.

TARGET:
Phage: {phage}

DATA SOURCE:
Metadata only.

MANDATORY CLASSIFICATION RULE:
You MUST return exactly ONE thermal classification:
- psychrophile
- mesophile
- thermophile

You are NEVER allowed to return:
- None
- unknown
- uncertain
- ambiguous
- multiple classifications

DECISION RULES:
1. Use explicit metadata evidence if present.
2. If no explicit evidence exists, infer from environmental context.
3. If environmental context is weak or absent, assign the MOST PROBABLE classification based on available metadata.
4. If no useful metadata exists, default to "mesophile" as the fallback class.

THERMAL DEFINITIONS:
- psychrophile: cold-associated environments (<15°C)
- mesophile: moderate environments (15–45°C)
- thermophile: high-temperature environments (>45°C)

INFERENCE TYPES:
- explicit: directly stated
- inferred: strongly implied by metadata
- forced: selected due to insufficient evidence using fallback rules

CONFIDENCE GUIDELINES:
- high: directly supported
- medium: strongly inferred
- low: weak evidence / fallback classification

OUTPUT FORMAT (STRICT JSON ONLY):
{{
    "thermal_range": "psychrophile | mesophile | thermophile",
    "thermal_reasoning": "step-by-step explanation of decision process",
    "inference_type": "explicit | inferred | forced",
    "thermal_confidence": "high | medium | low",
    "thermal_found": true
}}

IMPORTANT:
You MUST return valid JSON.
You MUST assign exactly one thermal range.

METADATA:
{metadata}
"""