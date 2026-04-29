# Index file for different versions

## V2
Model = qwen3.5
STEPS:
- Creates library for accession

- Scan to check if host is present in metadata

- LLM call to identify host using only metadata

- LLM call to indentify thermal range using only metadata

- LLM call to identify host if wasnt extracted from metadata. Papers are ranked based on regex scan of keywords.

Improved results output


