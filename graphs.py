from states import *
from agents import *

from langgraph.graph import StateGraph, START, END

def route(state: AgentState):
    return state["decision"]

def VisualiseGraph(graph_function):
    graph = graph_function()

    png = graph.get_graph().draw_mermaid_png()

    filename = graph_function.__name__

    with open(f"images/{filename}.png", "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# FAST Graph
# ---------------------------------------------------------------------------


def BuildGraph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Define nodes
    graph.add_node('ClassifyThermalMetadata', ClassifyThermalMetadata)
    graph.add_node('CreateAccessionLibrary', CreateAccessionLibrary)
    graph.add_node('ClassifyThermalLiterature', ClassifyThermalLiterature)
    graph.add_node('ClassifyHostMetadata', ClassifyHostMetadata)
    graph.add_node('ClassifyHostLiterature', ClassifyHostLiterature)
    graph.add_node('CreateHostLibrary', CreateHostLibrary)
    graph.add_node('ClassifyThermalRangeHostLiterature', ClassifyThermalRangeHostLiterature)
    graph.add_node('ClassifyThermalForced', ClassifyThermalForced)

    # Define paths
    # Can thermal range be confidently inferred from metadata
    graph.add_edge(START, 'ClassifyThermalMetadata')

    graph.add_conditional_edges('ClassifyThermalMetadata', route,
                                {'end': END,
                                 'CreateAccessionLibrary': 'CreateAccessionLibrary'})

    graph.add_edge('CreateAccessionLibrary', 'ClassifyThermalLiterature')

    graph.add_conditional_edges('ClassifyThermalLiterature', route,
                               {'end': END,
                                'ClassifyHostMetadata': 'ClassifyHostMetadata'})

    graph.add_conditional_edges('ClassifyHostMetadata', route,
                               {'ClassifyHostLiterature': 'ClassifyHostLiterature',
                                'CreateHostLibrary': 'CreateHostLibrary'})

    graph.add_conditional_edges('ClassifyHostLiterature', route,
                               {'ClassifyThermalForced': 'ClassifyThermalForced',
                                'CreateHostLibrary': 'CreateHostLibrary'})

    graph.add_edge('CreateHostLibrary', 'ClassifyThermalRangeHostLiterature')

    graph.add_conditional_edges('ClassifyThermalRangeHostLiterature', route,
                               {'end': END,
                                'ClassifyThermalForced': 'ClassifyThermalForced'})

    graph.add_edge('ClassifyThermalForced', END)

    return graph.compile()





# ---------------------------------------------------------------------------
# DEMOCRATIC Graph
# ---------------------------------------------------------------------------
def DemocraticGraph():
    graph = StateGraph(AgentState)

    #Define nodes
    graph.add_node('CreateAccessionLibrary', CreateAccessionLibrary)
    graph.add_node('ClassifyHostMetadata', ClassifyHostMetadata)
    graph.add_node('ClassifyHostLiterature', ClassifyHostLiterature)
    graph.add_node('CreateHostLibrary', CreateHostLibrary)
    graph.add_node('ClassifyThermalMetadataVote', ClassifyThermalMetadataVote)
    graph.add_node('ClassifyThermalLiteratureVotes', ClassifyThermalLiteratureVotes)
    graph.add_node('ClassifyThermalRangeHostLiteratureVotes', ClassifyThermalRangeHostLiteratureVotes)
    graph.add_node('ClassifyThermalForcedVote', ClassifyThermalForcedVote)


    #Define paths
    graph.add_edge(START, 'CreateAccessionLibrary')
    graph.add_edge('CreateAccessionLibrary', 'ClassifyHostMetadata')
    graph.add_conditional_edges('ClassifyHostMetadata', route,
                                {'CreateHostLibrary': 'CreateHostLibrary',
                                 'ClassifyHostLiterature': 'ClassifyHostLiterature'})
    graph.add_edge('ClassifyHostLiterature', 'CreateHostLibrary')
    graph.add_edge('CreateHostLibrary', 'ClassifyThermalMetadataVote')
    graph.add_edge('ClassifyThermalMetadataVote', 'ClassifyThermalLiteratureVotes')
    graph.add_edge('ClassifyThermalLiteratureVotes', 'ClassifyThermalRangeHostLiteratureVotes')
    graph.add_edge('ClassifyThermalRangeHostLiteratureVotes', 'ClassifyThermalForcedVote')
    graph.add_edge('ClassifyThermalForcedVote', END)

    return graph.compile()

