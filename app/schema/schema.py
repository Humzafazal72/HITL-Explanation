from typing import Union, Literal
from pydantic import BaseModel, Field
from core.langgraph_.schema import ExplanationDecision, FigureDecision

class ExplanationResume(BaseModel):
    concept_id: int
    type: Literal["explanation"]
    decision: ExplanationDecision

class FigureResume(BaseModel):
    concept_id: int
    type: Literal["figure"]
    decision: FigureDecision

ResumePayload = Union[ExplanationResume, FigureResume]