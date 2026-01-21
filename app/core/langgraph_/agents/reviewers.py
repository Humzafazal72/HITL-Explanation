from core.langgraph_.schema import AgentState
from langgraph.types import interrupt


def explanation_reviewer(state: AgentState):
    """
    Review the explanation by taking input from the user
    
    :param state: The current state of the agent
    :type state: AgentState
    """
    decision = interrupt(
        value={
            "type": "explanation",
            "prompt": "Does the explanation need any modifications? If yes, add comments.",
        }
    )
    return {"explainer_decision": decision}


def fig_reviewer(state: AgentState):
    """
    Review the figures by taking input from the user
    
    :param state: The current state of the agent
    :type state: AgentState
    """
    decision = interrupt(
        value={
            "type": "figure",
            "prompt": "Review the generated figures and suggest changes.",
        },
    )
    return {"fig_decision": decision}
