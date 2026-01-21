from core.langgraph_.schema import AgentState
from core.langgraph_.utils import code_generator
from llm.prompts import ASYNC_CODER_SYSTEM_PROMPT


async def async_coder(state: AgentState):
    """
    Generates codes and executes the code to produce figures
    
    :param state: Current state of the Agent
    :type state: AgentState
    """
    contextual_prompts = state["contextual_prompts"]
    config = {"system_instruction": ASYNC_CODER_SYSTEM_PROMPT}

    results = await code_generator(contextual_prompts, config=config)
    return {"async_coder_output": results}
