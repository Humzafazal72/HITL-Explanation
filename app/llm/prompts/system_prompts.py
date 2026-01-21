with open("llm/prompts/explainer.txt", "r", encoding="utf-8") as file:
    EXPLAINER_SYSTEM_PROMPT = file.read()

with open("llm/prompts/prompter.txt", "r", encoding="utf-8") as file:
    PROMPTER_SYSTEM_PROMPT = file.read()

with open("llm/prompts/async_coder.txt", "r", encoding="utf-8") as file:
    ASYNC_CODER_SYSTEM_PROMPT = file.read()

with open("llm/prompts/code_fixer.txt", "r", encoding="utf-8") as file:
    FIXER_SYSTEM_PROMPT = file.read()

with open("llm/prompts/tts_preprocessor.txt", "r", encoding="utf-8") as file:
    TTS_PREPROCESSOR_SYSTEM_PROMPT = file.read()

with open("llm/prompts/snippet_generator.txt", "r", encoding="utf-8") as file:
    SNIPPET_GENERATOR_SYSTEM_PROMPT = file.read()
