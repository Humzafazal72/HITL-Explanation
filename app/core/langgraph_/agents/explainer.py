from llm.clients import openai_client
from llm.prompts import PromptManager
from core.langgraph_.schema import AgentState, ExplainerOutput


def explainer(state: AgentState):
    """
    Generates intuitive explanations for a mathematical concept.
    
    :param state: The current state of the agent
    :type state: AgentState
    """

    # check if a review has been demanded by the client.
    if hasattr(state, "explainer_decision"):
        if state["explainer_decision"].change:
            content = f"""Concept: {state['concept']}\n
                    <Explanation Generated>\n
                    {str(state['explainer_output'])}\n
                    <Suggested Changes>\n
                    {state['explainer_decision'].comment}"""
    else:
        content = state["concept"]

    pm = PromptManager(type_="explainer")
    explainer_system_prompt = pm.get_system_prompt()
    # Generate and Parse an Explanation
    response = openai_client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {"role": "system", "content": explainer_system_prompt},
            {"role": "user", "content": content},
        ],
        text_format=ExplainerOutput,
    )
    parsed = response.output_parsed

    return {
        "explainer_output": {
            "context": parsed.context,
            "steps": parsed.steps,
            "conclusion": parsed.conclusion,
        }
    }
