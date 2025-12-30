from llm.clients import openai_client
from llm.prompts import EXPLAINER_SYSTEM_PROMPT
from core.langgraph_.schema import AgentState, ExplainerOutput

def explainer(state: AgentState):
    """Generates intuitive explanations for the concept."""
    
    if hasattr(state,"explainer_decision"):
        content = f"Concept: {state['concept']}\n<Explanation Generated>\n{str(state['explainer_output'])}\n<Suggested Changes>\n{state['explainer_decision'].comment}"
        print(content)
    else:
        content = state["concept"]

    response = openai_client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {"role": "system", "content": EXPLAINER_SYSTEM_PROMPT},
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