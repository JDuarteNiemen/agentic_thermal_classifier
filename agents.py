# imports
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END


# Set model to be used
OLLAMA_MODEL = "qwen3.5"
OLLAMA_BASE_URL = "http://localhost:11434"

tools={
    'FetchNcbiMetadata': FetchNcbiMetadata
}


model=ChatOllama(
    model="qwen3.5",
)
