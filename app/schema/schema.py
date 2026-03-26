from typing import Union, Literal, List
from pydantic import BaseModel, Field
from core.langgraph_.schema import ExplanationDecision, FigureDecision


class ExplanationResume(BaseModel):
    concept_id: str
    type: Literal["explanation"]
    decision: ExplanationDecision


class FigureResume(BaseModel):
    concept_id: str
    type: Literal["figure"]
    decision: FigureDecision


ResumePayload = Union[ExplanationResume, FigureResume]

class ExplanationStart(BaseModel):
    concept: str
    lesson_num: int
    chapter_name: str
    chapter_num: int
    grade: Literal["O-1","O-2","A-1","A-2"]
    sublessons: List[str]
