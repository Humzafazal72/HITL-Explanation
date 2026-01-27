from llm.prompts import PromptManager
from core.langgraph_.schema import AgentState
from core.langgraph_.utils import code_generator


async def async_coder(state: AgentState):
    """
    Generates codes and executes the code to produce figures

    :param state: Current state of the Agent
    :type state: AgentState
    """
    pm = PromptManager(type_="async_coder")
    system_prompt = pm.get_system_prompt(version="1.0")

    contextual_prompts = state["contextual_prompts"]
    concept_id = str(state["concept_id"])
    config = {"system_instruction": system_prompt}

    results = await code_generator(
        contextual_prompts, config=config, concept_id=concept_id
    )
    return {"async_coder_output": results}
