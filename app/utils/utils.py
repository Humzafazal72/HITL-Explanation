import json
from pydantic import BaseModel
from typing import Any

def sse_response(event: str, data: dict, concept_id: str):
    return (
        f"event: {event}\n"
        f"data: {json.dumps({'concept_id': concept_id, **data})}\n\n"
    )


def to_json_safe(obj: Any):
    if isinstance(obj, BaseModel):
        return obj.model_dump()

    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    
    elif isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    
    return obj