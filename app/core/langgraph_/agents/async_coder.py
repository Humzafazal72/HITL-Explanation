from core.langgraph_.schema import AgentState
from core.langgraph_.utils import code_generator
from llm.prompts import PromptManager


async def async_coder(state: AgentState):
    """
    Generates codes and executes the code to produce figures

    :param state: Current state of the Agent
    :type state: AgentState
    """
    pm = PromptManager(type_="async_coder")
    system_prompt = pm.get_system_prompt(version="1.0")

    contextual_prompts = state["contextual_prompts"]
    config = {"system_instruction": system_prompt}

    results = await code_generator(contextual_prompts, config=config)
    return {"async_coder_output": results}
