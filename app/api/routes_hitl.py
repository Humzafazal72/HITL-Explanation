import random
import json
from langgraph.types import Command
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from core.langgraph_.Workflow import workflow_hitl
from utils import sse_response, to_json_safe
from schema import ResumePayload

router = APIRouter()

graph_app = None
db_path = "Storage/Database/state.db"

# async def compile_graph():
#     global graph_app, db_path
#     if graph_app is None:
#         async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
#             graph_app =  workflow_hitl.compile(checkpointer=checkpointer)
    
#     return graph_app

async def get_graph():
    cm = AsyncSqliteSaver.from_conn_string(db_path)
    checkpointer = await cm.__aenter__()
    graph = workflow_hitl.compile(checkpointer=checkpointer)
    return graph, cm



@router.get("/api/v1/start_agent_hitl")
async def start_agent_hitl(concept: str = Query(...)):
    graph_app, cm = await get_graph()

    concept_id = random.randint(0,1000000)
    config = {"configurable": {"thread_id": concept_id}}
    state = {
                "concept": concept,
                "explainer_output":{
                "context": "Have you ever needed to find the shortest distance between two points — like walking diagonally across a rectangular park instead of along its sides? Pythagoras’ Theorem helps us calculate that diagonal distance without measuring it directly. It’s one of the simplest and most powerful connections between shapes and numbers in geometry.",
                "steps": [
                    "1. Picture a right-angled triangle — the kind of triangle where one corner is exactly 90°. Label the shorter sides that meet at the right angle ‘a’ and ‘b’, and the longest side (the slanted one) as ‘c’.",
                    "2. Imagine drawing a square on each of the three sides of the triangle. Each square’s area matches the square of that side’s length — so you get areas a², b², and c².",
                    "3. The beautiful relationship Pythagoras discovered is that the two smaller squares together perfectly fill the largest one. In algebra, that’s written as a² + b² = c².",
                    "4. This formula works for every right-angled triangle and allows you to find any missing side if you know the other two — no measuring tape needed!"
                ],
                "conclusion": "Pythagoras’ Theorem reveals a deep link between geometry and algebra: in any right-angled triangle, the square on the hypotenuse equals the sum of the squares on the other two sides."
            }
        }
    
    async def event_generator():
        try:
            async for event in graph_app.astream(input=state, config=config):
                for node_name, node_output in event.items():
                    yield sse_response(
                        event=node_name,
                        data={"payload": to_json_safe(node_output) if node_name!="__interrupt__" else node_output[0].value},
                        concept_id=concept_id
                    )
        finally:
            # IMPORTANT: close sqlite connection when stream ends
            await cm.__aexit__(None, None, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/v1/resume_agent_hitl")
async def resume_agent_hitl(
    data: ResumePayload
):
    graph_app, cm = await get_graph()
    config = {"configurable": {"thread_id": data.concept_id}}

    async def event_generator():
        try:
            async for event in graph_app.astream(
                Command(resume=data.decision),
                config=config
            ):
                for node_name, node_output in event.items():
                    
                    yield sse_response(
                        event=node_name,
                        data={"payload": (to_json_safe(node_output)) if node_name!="__interrupt__" else node_output[0].value},
                        concept_id=data.concept_id
                    )
        finally:
            await cm.__aexit__(None, None, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
