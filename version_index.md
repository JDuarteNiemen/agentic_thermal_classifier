# Index file for different versions

## V3
Model = qwen3.5
STEPS:
- Creates library for accession

- Scan to check if host is present in metadata

- LLM call to identify host using only metadata

- LLM call to indentify thermal range using only metadata

- LLM call to identify host if wasnt extracted from metadata. Papers are ranked based on regex scan of keywords.

Improved results output
Reasoning is set to false, this causes massive decrease in time taken for each LLM call

Uses same agents as v3 for now.
Implementing a graph for agents. Fleshing out the proper state
