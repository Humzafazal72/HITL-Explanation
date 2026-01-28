from langgraph.graph import StateGraph, START, END
from core.langgraph_.schema import AgentState
from core.langgraph_.agents import (
    explainer,
    fig_reviewer,
    async_fig_fixer,
    async_explanation_processor,
    async_coder,
    explaination_decision_controller,
    explanation_reviewer,
    contextual_prompt_generator,
    fig_decision_controller,
)


def dummy(state: AgentState):
    """Simple passthrough to establish context"""
    return state


workflow_hitl = StateGraph(AgentState)

# create nodes
workflow_hitl.add_node("explainer", explainer)
# workflow_hitl.add_node("explainer", dummy)
workflow_hitl.add_node("explanation_reviewer", explanation_reviewer)
workflow_hitl.add_node(
    "explaination_decision_controller", explaination_decision_controller
)
# workflow_hitl.add_node("async_explanation_processor", dummy)
workflow_hitl.add_node("async_explanation_processor", async_explanation_processor)
workflow_hitl.add_node("contextual_prompt_generator", contextual_prompt_generator)
workflow_hitl.add_node("async_coder_hitl", async_coder)
workflow_hitl.add_node("fig_reviewer", fig_reviewer)
workflow_hitl.add_node("async_fig_fixer", async_fig_fixer)

# create edges
workflow_hitl.add_edge(START, "explainer")
workflow_hitl.add_edge("explainer", "explanation_reviewer")
workflow_hitl.add_conditional_edges(
    "explanation_reviewer",
    explaination_decision_controller,
    {"fix": "explainer", "continue": "async_explanation_processor"},
)
workflow_hitl.add_edge("async_explanation_processor", "contextual_prompt_generator")
workflow_hitl.add_edge("contextual_prompt_generator", "async_coder_hitl")
workflow_hitl.add_edge("async_coder_hitl", "fig_reviewer")
workflow_hitl.add_conditional_edges(
    "fig_reviewer", 
    fig_decision_controller, 
    {"fix": "async_fig_fixer", "continue": END}
)
workflow_hitl.add_edge("async_fig_fixer", "fig_reviewer")
