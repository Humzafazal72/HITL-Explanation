from core.langgraph_.schema import AgentState


def explaination_decision_controller(state: AgentState):
    """
    Checks if the user requires a change in the explanation
    
    :param state: The Current state of the Agent.
    :type state: AgentState
    """
    if state["explainer_decision"].change:
        return "fix"
    else:
        return "continue"


def fig_decision_controller(state: AgentState):
    """
    Checks if the user requires a change in any of the diagrams
    
    :param state: The current state of the agent.
    :type state: AgentState
    """
    if state["fig_decision"].change:
        return "fix"
    else:
        return "continue"
