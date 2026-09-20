from langgraph.graph import END, START, StateGraph

from agentguard.agent.nodes import explanation_node, gateway_node
from agentguard.agent.state import AgentState


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("gateway", gateway_node)
    builder.add_node("explain", explanation_node)
    builder.add_edge(START, "gateway")
    builder.add_edge("gateway", "explain")
    builder.add_edge("explain", END)
    return builder.compile()


graph = build_graph()
