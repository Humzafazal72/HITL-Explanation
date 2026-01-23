import yaml
from typing import Literal


def load_yaml(path: str) -> dict:
    """
    loads a yaml file into a dict
    
    :param path: path of the yaml file
    :type path: str
    """
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)
    

class PromptManager:
    def __init__(
        self,
        type_: Literal[
            "async_coder",
            "code_fixer",
            "explainer",
            "prompter",
            "snippet_generator",
            "tts_preprocessor",
        ],
    ):
        self.data = load_yaml(f"llm/prompts/{type_}.yaml")["version"]
    
    def get_system_prompt(self, version: str = None) -> str:
        if not version:
            max_version = max(self.data.keys())
            return self.data.get(max_version,None)
            
        else:
            return self.data.get(version,None)
