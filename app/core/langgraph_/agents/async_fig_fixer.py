from core.langgraph_.schema import AgentState
from core.langgraph_.utils import code_generator, get_contextual_prompt
from llm.prompts import FIXER_SYSTEM_PROMPT


async def async_fig_fixer(state: AgentState):
    """
    fix the figures as suggested by the user

    :param state: Current state of the agent
    :type state: AgentState
    """
    generated_codes = state["async_coder_output"].copy()
    contextual_prompts = state["contextual_prompts"].copy()
    change_descriptions = state["fig_decision"].change_descriptions
    concept = state["concept"]

    prompts = []

    # create prompts for figures that need to be fixed.
    for fig_name, change_desc in change_descriptions.items():
        prompts.append(
            {
                "figure_id": fig_name,
                "prompt": f"""
                <Concept Name>\n{concept}\n
                <Input Prompt>\n{get_contextual_prompt(contextual_prompts,fig_name)}\n
                <Generated Code>\n{generated_codes[fig_name]}\n
                <Changes to be made>\n{change_desc}
                """,
            }
        )

    config = {"system_instruction": FIXER_SYSTEM_PROMPT}

    results = await code_generator(prompts=prompts, config=config)
    return {"async_fig_fixer_output": results}
