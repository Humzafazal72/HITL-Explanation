import re
import asyncio

from llm.tools import python_tool
from llm.prompts import ASYNC_CODER_SYSTEM_PROMPT
from llm.clients import google_client


def parse_code(generated_code: str):
    match = re.search(r"```(?:python)?\n(.*?)```", generated_code, re.DOTALL)
    code = match.group(1).strip() if match else generated_code.strip()
    return code


async def call_gemini(prompt: str, google_client, config: dict, model: str):
    return await asyncio.to_thread(google_client.models.generate_content, 
                                   model = model,
                                   contents=prompt,
                                   config = config)


async def code_generator(prompts: dict[str, str], config: dict[str, str]):
    # Wrap each task with its figure_id
    async def process_figure(fig_id, prompt):
        try:
            response = await call_gemini(prompt=prompt, google_client=google_client, config=config, model='gemini-2.5-pro')
            parsed_code = parse_code(response.text)
            parsed_code = 'import matplotlib\nmatplotlib.use("Agg")\n' + parsed_code
            try:
                python_tool.run(parsed_code)
                exec_status = "ok"
            except Exception as e:
                exec_status = str(e)
                print(exec_status)
            return fig_id, response.text
        except Exception as e:
            return fig_id, {"error": str(e)}
    
    # Create all tasks
    tasks = [
        process_figure(item["figure_id"], item["prompt"])
        for item in prompts
    ]
    
    results = {}
    # Process as they complete
    for coro in asyncio.as_completed(tasks):
        fig_id, result = await coro
        results[fig_id] = result
    
    return results

def get_contextual_prompt(contextual_prompts: list, fig_name):
    for contextual_prompt in contextual_prompts:
        if contextual_prompt["figure_id"] == fig_name:
            return contextual_prompt["prompt"]

    return "Unable to find the initial prompt." 