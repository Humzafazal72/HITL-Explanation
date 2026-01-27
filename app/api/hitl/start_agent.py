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

    # dummy data
    state = {
        "concept": concept,
        "concept_id": str(concept_id),
        "explainer_output": {
            "context": "Have you ever needed to find the shortest distance between two points — like walking diagonally across a rectangular park instead of along its sides? Pythagoras’ Theorem helps us calculate that diagonal distance without measuring it directly. It’s one of the simplest and most powerful connections between shapes and numbers in geometry.",
            "steps": [
                "1. Picture a right-angled triangle — the kind of triangle where one corner is exactly 90°. Label the shorter sides that meet at the right angle ‘a’ and ‘b’, and the longest side (the slanted one) as ‘c’.",
                "2. Imagine drawing a square on each of the three sides of the triangle. Each square’s area matches the square of that side’s length — so you get areas a², b², and c².",
                "3. The beautiful relationship Pythagoras discovered is that the two smaller squares together perfectly fill the largest one. In algebra, that’s written as a² + b² = c².",
                "4. This formula works for every right-angled triangle and allows you to find any missing side if you know the other two — no measuring tape needed!",
            ],
            "conclusion": "Pythagoras’ Theorem reveals a deep link between geometry and algebra: in any right-angled triangle, the square on the hypotenuse equals the sum of the squares on the other two sides.",
        },
    }

    # state = {"concept": concept, "concept_id": str(concept_id)}

    async def event_generator():
        try:
            async for event in graph_app.astream(input=state, config=config):
                for node_name, node_output in event.items():
                    print("node name: ",node_name)
                    print("node output: ",node_output)
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
