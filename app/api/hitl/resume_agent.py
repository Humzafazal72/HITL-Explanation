import os
from fastapi import APIRouter
from langgraph.types import Command
from fastapi.responses import StreamingResponse

from schema import ResumePayload
from utils import sse_response, to_json_safe, get_graph

router = APIRouter()


@router.post("/hitl/resume_agent_hitl")
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

        # remove the figures from the change descriptions that are to be deleted
        for fig in to_delete:
            del data.decision.change_descriptions[fig]
        
        # delete the figure to be deleted from the storage
        for fig in to_delete:
            os.remove(f"Storage/{str(data.concept_id)}/{fig}.png")

        # after deletion if no changes left set change to False
        if not data.decision.change_descriptions:
            data.decision.change = False
    
    else:
        if data.decision.comment == "":
            data.decision.change = False
        
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
