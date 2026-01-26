import random
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from utils import sse_response, to_json_safe, get_graph

router = APIRouter()


@router.get("/hitl/start_agent_hitl")
async def start_agent_hitl(concept: str = Query(...)):
    graph_app, cm = await get_graph()
    concept_id = random.randint(0, 100000) + random.randint(0, 90000)

    config = {"configurable": {"thread_id": concept_id}}

    state = {"concept": concept, "concept_id": str(concept_id)}

    async def event_generator():
        try:
            async for event in graph_app.astream(input=state, config=config):
                for node_name, node_output in event.items():
                    yield sse_response(
                        event=node_name,
                        data={
                            "payload": (
                                to_json_safe(node_output)
                                if node_name != "__interrupt__"
                                else node_output[0].value
                            )
                        },
                        concept_id=concept_id,
                    )
        finally:
            await cm.__aexit__(None, None, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
