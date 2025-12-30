from typing import List, TypedDict
from pydantic import BaseModel

class ExplainerOutput(BaseModel):
    context: str
    steps: List[str]
    conclusion: str

class TTSInput(BaseModel):
    output: List[str]

class PrompterOutput(BaseModel):
    prompts: List[str]

class SnippetGeneratorOutput(BaseModel):
    context_snippets: List[str]
    step_snippets: List[List[str]]
    conclusion_snippets: List[str]

class ExplanationDecision(BaseModel):
    change: bool
    comment: str

class FigureDecision(BaseModel):
    change: bool
    change_descriptions: dict[str,str]

class ContextualPrompt(BaseModel):
    figure_id: str
    prompt: str

class AgentState(TypedDict):
    explainer_output: ExplainerOutput
    concept: str
    explainer_decision: ExplanationDecision
    prompter_output: PrompterOutput
    tts_preprocessor_output: TTSInput
    snippet_generator_output: SnippetGeneratorOutput 
    contextual_prompts: List[ContextualPrompt]
    async_coder_output: dict[str,str]
    fig_decision: FigureDecision
    async_fig_fixer_output: dict[str,str]