import json
from typing import Any
from pydantic import BaseModel
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from core.langgraph_.Workflow import workflow_hitl

db_path = "Storage/Database/state.db"

def sse_response(event: str, data: dict, concept_id: str):
    """
    Generate SSE compatible response for the client
    
    :param event: name of event
    :type event: str
    :param data: data to be sent to the client
    :type data: dict
    :param concept_id: concept id.
    :type concept_id: str
    """
    return (
        f"event: {event}\n"
        f"data: {json.dumps({'concept_id': concept_id, **data})}\n\n"
    )


def to_json_safe(obj: Any):
    """
    Convert any obj to json compatible dict.
    
    :param obj: object to be made compatible.
    :type obj: Any
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()

    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [to_json_safe(v) for v in obj]

    return obj

async def get_graph():
    cm = AsyncSqliteSaver.from_conn_string(db_path)
    checkpointer = await cm.__aenter__()
    graph = workflow_hitl.compile(checkpointer=checkpointer)
    return graph, cm


def upload_diagrams(directory_name: str):
    pass


def add_explanation_db(explainer_output: dict, concept_id: int):
    pass