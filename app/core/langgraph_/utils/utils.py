import re
import asyncio
from e2b_code_interpreter import Sandbox

from llm.tools import python_tool
from llm.clients import google_client


def parse_code(generated_code: str):
    """
    Parse the LLM generated code for execution

    :param generated_code: LLM generated code.
    :type generated_code: str
    """
    match = re.search(r"```(?:python)?\n(.*?)```", generated_code, re.DOTALL)
    code = match.group(1).strip() if match else generated_code.strip()
    return code


async def call_gemini(prompt: str, google_client, config: dict, model: str):
    """
    create an async thread for a gemini call

    :param prompt: prompt the gemini call
    :type prompt: str
    :param google_client: gemini client
    :param config: system prompt and other congfigurations
    :type config: dict
    :param model: Name of the gemini model to use
    :type model: str
    """
    return await asyncio.to_thread(
        google_client.models.generate_content,
        model=model,
        contents=prompt,
        config=config,
    )


async def code_generator(
    prompts: dict[str, str], config: dict[str, str], concept_id: str
):
    """
    generate and execute code given prompts.

    :param prompts: dict of figure names and their corresponding prompt
    :type prompts: dict[str, str]
    :param config: System prompt and other configs for the llm.
    :type config: dict[str, str]
    """

    # Wrap each task with its figure_id
    async def process_figure(fig_id, prompt, concept_id):
        try:
            response = await call_gemini(
                prompt=prompt,
                google_client=google_client,
                config=config,
                model="gemini-2.5-pro",
            )
            parsed_code = parse_code(response.text)
            parsed_code = 'import matplotlib\nmatplotlib.use("Agg")\n' + parsed_code

            sbx = Sandbox.create(template="diag-gen", allow_internet_access=False)
            execution = sbx.run_code(code=parsed_code, language="python")

            content = sbx.files.read(f"/home/user/{fig_id}.png", format="bytes")

            output_path = f"Storage/{concept_id}/{fig_id}.png"

            # Write bytes to disk
            with open(output_path, "wb") as f:
                f.write(content)
            return fig_id, response.text
        except Exception as e:
            return fig_id, {"error": str(e)}

    # Create all tasks
    tasks = [process_figure(item["figure_id"], item["prompt"], concept_id=concept_id) for item in prompts]

    results = {}
    # Process as they complete
    for coro in asyncio.as_completed(tasks):
        fig_id, result = await coro
        results[fig_id] = result

    return results


def get_contextual_prompt(contextual_prompts: list, fig_name: str):
    """
    retrieve a contexual prompt from a list of contexual prompts

    :param contextual_prompts: list of all contexual prompts
    :type contextual_prompts: list
    :param fig_name: Name of the fig for which the contexual prompt is needed
    :type fig_name: str
    """
    for contextual_prompt in contextual_prompts:
        if contextual_prompt["figure_id"] == fig_name:
            return contextual_prompt["prompt"]

    return "Unable to find the initial prompt."
