import asyncio

from llm.clients import google_client
from core.langgraph_.utils import call_gemini
from core.langgraph_.schema import (
    AgentState,
    PrompterOutput,
    TTSInput,
    SnippetGeneratorOutput,
)
from llm.prompts import (
    PROMPTER_SYSTEM_PROMPT,
    SNIPPET_GENERATOR_SYSTEM_PROMPT,
    TTS_PREPROCESSOR_SYSTEM_PROMPT,
)


async def async_explanation_processor(state: AgentState):
    """
    This function asychronously processes the explanation and creates input for the
    coder node, the tts system and snippets for showing on the board.

    :param state: The current state of the agent
    :type state: AgentState
    """

    # converts each explanation step into a prompt for the coder.
    prompter_prompt = f"Concept: {state['concept']}\nExplanation Steps: {str(state['explainer_output']['steps'])}"
    prompter_config = {
        "system_instruction": PROMPTER_SYSTEM_PROMPT,
        "response_mime_type": "application/json",
        "response_schema": PrompterOutput,
    }

    # converts the explanation into tts friendly content.
    tts_preprocessor_prompt = state["explainer_output"]["steps"]
    tts_preprocessor_config = {
        "system_instruction": TTS_PREPROCESSOR_SYSTEM_PROMPT,
        "response_mime_type": "application/json",
        "response_schema": TTSInput,
    }

    # converts the explanation into board friendly snippets.
    snippet_generator_prompt = (
        f"Concept: {state['concept']}\nExplanation: {str(state['explainer_output'])}"
    )
    snippet_generator_config = {
        "system_instruction": SNIPPET_GENERATOR_SYSTEM_PROMPT,
        "response_mime_type": "application/json",
        "response_schema": SnippetGeneratorOutput,
    }

    model = "gemini-2.5-flash"

    # create asyncio threads(tasks) for each part.
    tasks = [
        call_gemini(
            prompt=prompter_prompt,
            config=prompter_config,
            google_client=google_client,
            model=model,
        ),
        call_gemini(
            prompt=tts_preprocessor_prompt,
            config=tts_preprocessor_config,
            google_client=google_client,
            model=model,
        ),
        call_gemini(
            prompt=snippet_generator_prompt,
            config=snippet_generator_config,
            google_client=google_client,
            model=model,
        ),
    ]
    responses = await asyncio.gather(*tasks)

    # find out which response is from a certain task
    output = {}
    for response in responses:
        parsed_response = response.parsed
        if hasattr(parsed_response, "context_snippets"):  # for snippets
            output["snippet_generator_output"] = {
                "context_snippets": parsed_response.context_snippets,
                "step_snippets": parsed_response.step_snippets,
                "conclusion_snippets": parsed_response.conclusion_snippets,
            }

        elif hasattr(parsed_response, "prompts"):  # for prompts
            output["prompter_output"] = {"prompts": parsed_response.prompts}

        elif hasattr(parsed_response, "output"):  # for tts
            output["tts_preprocessor_output"] = {"output": parsed_response.output}

    return output
