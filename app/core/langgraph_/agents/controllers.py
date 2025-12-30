from core.langgraph_.schema import AgentState

def explaination_decision_controller(state: AgentState):
    if state["explainer_decision"].change:
        return "fix"
    else:
        return "continue"
    
def fig_decision_controller(state: AgentState):
    if state["fig_decision"].change:
        return "fix"
    else:
        return "continue"