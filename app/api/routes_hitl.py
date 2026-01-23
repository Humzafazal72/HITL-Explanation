import os
import random
from langgraph.types import Command
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from schema import ResumePayload
from utils import sse_response, to_json_safe, get_graph

router = APIRouter()


@router.get("/api/start_agent_hitl")
async def start_agent_hitl(concept: str = Query(...)):
    graph_app, cm = await get_graph()
    concept_id = random.randint(0, 100000) + random.randint(0, 90000)

    config = {"configurable": {"thread_id": concept_id}}
    # state = {
    #     "concept": concept,
    #     "explainer_output": {
    #         "context": "Have you ever needed to find the shortest distance between two points — like walking diagonally across a rectangular park instead of along its sides? Pythagoras’ Theorem helps us calculate that diagonal distance without measuring it directly. It’s one of the simplest and most powerful connections between shapes and numbers in geometry.",
    #         "steps": [
    #             "1. Picture a right-angled triangle — the kind of triangle where one corner is exactly 90°. Label the shorter sides that meet at the right angle ‘a’ and ‘b’, and the longest side (the slanted one) as ‘c’.",
    #             "2. Imagine drawing a square on each of the three sides of the triangle. Each square’s area matches the square of that side’s length — so you get areas a², b², and c².",
    #             "3. The beautiful relationship Pythagoras discovered is that the two smaller squares together perfectly fill the largest one. In algebra, that’s written as a² + b² = c².",
    #             "4. This formula works for every right-angled triangle and allows you to find any missing side if you know the other two — no measuring tape needed!",
    #         ],
    #         "conclusion": "Pythagoras’ Theorem reveals a deep link between geometry and algebra: in any right-angled triangle, the square on the hypotenuse equals the sum of the squares on the other two sides.",
    #     },
    # }

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


@router.post("/api/resume_agent_hitl")
async def resume_agent_hitl(data: ResumePayload):
    graph_app, cm = await get_graph()
    config = {"configurable": {"thread_id": data.concept_id}}

    to_delete = []

    # if the interrupt happened after figure generation.
    if data.type == "figure":
        # get the figures that need to be delete
        if data.decision.change:
            for fig, description in data.decision.change_descriptions.items():
                if description == "delete":
                    to_delete.append(fig)

        print("To Delete: ",to_delete)
        # remove the figures from the change descriptions that are to be deleted
        for fig in to_delete:
            del data.decision.change_descriptions[fig]
        
        # delete the figure to be deleted from the storage
        for fig in to_delete:
            os.remove(f"Storage/{str(data.concept_id)}/{fig}.png")

        # after deletion if no changes left set change to False
        if not data.decision.change_descriptions:
            data.decision.change = False
        
        print("DATA: ",data)

    async def event_generator():
        try:
            async for event in graph_app.astream(
                Command(resume=data.decision), config=config
            ):
                for node_name, node_output in event.items():
                    last_node_executed = node_name
                    yield sse_response(
                        event=node_name,
                        data={
                            "payload": (
                                (to_json_safe(node_output))
                                if node_name != "__interrupt__"
                                else node_output[0].value
                            )
                        },
                        concept_id=data.concept_id,
                    )

            # Check if the graph execution has ended.
            if last_node_executed!="__interrupt__":
                yield sse_response(
                    event="__END__",
                    data={"":""},
                    concept_id=data.concept_id
                )

        finally:
            await cm.__aexit__(None, None, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
