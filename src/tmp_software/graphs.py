from .states import *
from .nodes import *


from langgraph.graph import StateGraph, START, END

def route(state):
    return state["decision"]

def VisualiseGraph(graph_function, save_dir):
    graph = graph_function()

    png = graph.get_graph().draw_mermaid_png()

    filename = graph_function.__name__

    with open(f"{save_dir}/{filename}.png", "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# FAST Graph
# ---------------------------------------------------------------------------
def FastGraph() -> StateGraph:
    graph = StateGraph(FastState)

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
    graph = StateGraph(DemocraticState)

    #Define nodes
    graph.add_node('DemocraticCreateAccessionLibrary', DemocraticCreateAccessionLibrary)
    graph.add_node('DemocraticClassifyHostMetadata', DemocraticClassifyHostMetadata)
    graph.add_node('DemocraticClassifyHostLiterature', DemocraticClassifyHostLiterature)
    graph.add_node('DemocraticCreateHostLibrary', DemocraticCreateHostLibrary)
    graph.add_node('DemocraticClassifyThermalMetadata', DemocraticClassifyThermalMetadata)
    graph.add_node('DemocraticClassifyThermalLiterature', DemocraticClassifyThermalLiterature)
    graph.add_node('DemocraticClassifyThermalRangeHostLiterature', DemocraticClassifyThermalRangeHostLiterature)
    graph.add_node('DemocraticClassifyThermalForced', DemocraticClassifyThermalForced)


    #Define paths
    graph.add_edge(START, 'DemocraticCreateAccessionLibrary')
    graph.add_edge('DemocraticCreateAccessionLibrary', 'DemocraticClassifyHostMetadata')
    graph.add_conditional_edges('DemocraticClassifyHostMetadata', route,
                                {'DemocraticCreateHostLibrary': 'DemocraticCreateHostLibrary',
                                 'DemocraticClassifyHostLiterature': 'DemocraticClassifyHostLiterature'})
    graph.add_edge('DemocraticClassifyHostLiterature', 'DemocraticCreateHostLibrary')
    graph.add_edge('DemocraticCreateHostLibrary', 'DemocraticClassifyThermalMetadata')
    graph.add_edge('DemocraticClassifyThermalMetadata', 'DemocraticClassifyThermalLiterature')
    graph.add_edge('DemocraticClassifyThermalLiterature', 'DemocraticClassifyThermalRangeHostLiterature')
    graph.add_edge('DemocraticClassifyThermalRangeHostLiterature', 'DemocraticClassifyThermalForced')
    graph.add_edge('DemocraticClassifyThermalForced', END)

    return graph.compile()

# ---------------------------------------------------------------------------
# SUMMARY Graph
# ---------------------------------------------------------------------------
def SummaryGraph():
    graph = StateGraph(SummaryState)

    # Define nodes
    graph.add_node('SummaryCreateAccessionLibrary', SummaryCreateAccessionLibrary)
    graph.add_node('SummaryClassifyHostMetadata', SummaryClassifyHostMetadata)
    graph.add_node('SummaryClassifyHostLiterature', SummaryClassifyHostLiterature)
    graph.add_node('SummaryCreateHostLibrary', SummaryCreateHostLibrary)
    graph.add_node('FilterRelevantLiterature', FilterRelevantLiterature)
    graph.add_node('FilterRelevantHostLiterature', FilterRelevantHostLiterature)
    graph.add_node('SummariseLiterature', SummariseLiterature)
    graph.add_node('ClassifySummary', ClassifySummary)
    graph.add_node('SummaryClassifyThermalForced', SummaryClassifyThermalForced)

    # Define paths
    graph.add_edge(START, 'SummaryCreateAccessionLibrary')
    graph.add_edge('SummaryCreateAccessionLibrary', 'SummaryClassifyHostMetadata')
    graph.add_conditional_edges('SummaryClassifyHostMetadata', route,
                                {'SummaryCreateHostLibrary': 'SummaryCreateHostLibrary',
                                        'SummaryClassifyHostLiterature': 'SummaryClassifyHostLiterature'})
    graph.add_conditional_edges('SummaryClassifyHostLiterature', route,
                                {'SummaryCreateHostLibrary': 'SummaryCreateHostLibrary',
                                 'SummaryClassifyThermalForced': 'SummaryClassifyThermalForced',})
    graph.add_conditional_edges('SummaryCreateHostLibrary', route,
                                {'SummaryClassifyThermalForced': 'SummaryClassifyThermalForced',
                                 'FilterRelevantLiterature': 'FilterRelevantLiterature',})
    graph.add_edge('SummaryCreateHostLibrary', 'FilterRelevantLiterature')
    graph.add_edge('FilterRelevantLiterature', 'FilterRelevantHostLiterature')
    graph.add_conditional_edges('FilterRelevantHostLiterature', route,
                                {'SummaryClassifyThermalForced': 'SummaryClassifyThermalForced',
                                 'SummariseLiterature': 'SummariseLiterature',})
    graph.add_edge('SummariseLiterature', 'ClassifySummary')
    graph.add_conditional_edges('ClassifySummary', route,
                                {'SummaryClassifyThermalForced': 'SummaryClassifyThermalForced',
                                 'end': END})
    graph.add_edge('SummaryClassifyThermalForced', END)

    return graph.compile()


