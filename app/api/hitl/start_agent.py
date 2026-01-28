import json
import asyncio
import random
from fastapi import APIRouter, Query
from sse_starlette import EventSourceResponse

from utils import get_graph

router = APIRouter()


@router.get("/hitl/start_agent_hitl")
async def start_agent_hitl(concept: str = Query(...)):
    graph_app, cm = await get_graph()
    concept_id = str(random.randint(0, 100000) + random.randint(0, 90000))
    config = {"configurable": {"thread_id": concept_id}}

    # dummy data
    state = {
        "concept": concept,
        "concept_id": concept_id,
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
        "prompter_output": {
            "prompts": [
                "Draw a right-angled triangle. Label the two shorter sides 'a' and 'b'. Label the hypotenuse 'c'. Indicate the 90-degree angle.",
                "Draw the right-angled triangle with sides 'a', 'b', and 'c'. Construct a square outwards on each side, labeling their areas 'a²', 'b²', and 'c²' respectively.",
                "Draw the right-angled triangle with the three squares on its sides. Label the areas of the squares as 'a²', 'b²', and 'c²'. Show a visual indication that the areas of the two smaller squares combine to equal the area of the largest square.",
                "No figure",
            ]
        },
        "tts_preprocessor_output": {
            "output": [
                "First, picture a right-angled triangle – that's the kind where one corner is exactly ninety degrees. We'll label the two shorter sides that meet at that right angle as 'a' and 'b', and the longest side, the slanted one, as 'c'.",
                "Next, imagine drawing a square on each of the triangle's three sides. The area of each square will match the square of its side's length. So, you'd have squares with areas of 'a squared', 'b squared', and 'c squared'.",
                "The beautiful relationship Pythagoras discovered is that those two smaller squares, when put together, perfectly fill the largest one. In algebra, we write that as 'a squared plus b squared equals c squared'.",
                "This amazing formula works for every single right-angled triangle! It lets you find any missing side's length if you already know the other two — and you won't even need a measuring tape!",
            ]
        },
        "snippet_generator_output": {
            "context_snippets": ["Shortest distance (diagonal)", "Geometry ↔ Numbers"],
            "step_snippets": [
                ["Right-angled triangle", "90° angle", "Sides a, b, hypotenuse c"],
                ["Squares on sides", "Areas a², b², c²"],
                ["a² + b² = c²", "Smaller squares = Largest square"],
                ["Works for ALL right triangles", "Find any missing side"],
            ],
            "conclusion_snippets": [
                "Geometry ↔ Algebra link",
                "Right triangle: c² = a² + b²",
            ],
        },
    }

    # state = {"concept": concept, "concept_id": str(concept_id)}

    async def event_generator():
        try:
            async for event in graph_app.astream(input=state, config=config):
                for node_name, node_output in event.items():
                    yield {
                        "event": node_name,
                        "id": concept_id,
                        "data": json.dumps(
                            (
                                {"": ""}
                                if node_name != "__interrupt__"
                                else node_output[0].value
                            )
                        ),
                    }
        finally:
            await cm.__aexit__(None, None, None)

    return EventSourceResponse(event_generator(), media_type="text/event-stream")

# @router.get("/hitl/start_agent_hitl")
# async def start_agent_hitl(concept: str = Query(...)):
#     graph_app, cm = await get_graph()
#     concept_id = str(random.randint(0, 100000) + random.randint(0, 90000))

#     config = {"configurable": {"thread_id": concept_id}}

#     state = state = {
#         "concept": concept,
#         "concept_id": concept_id,
#         "explainer_output": {
#             "context": "Have you ever needed to find the shortest distance between two points — like walking diagonally across a rectangular park instead of along its sides? Pythagoras’ Theorem helps us calculate that diagonal distance without measuring it directly. It’s one of the simplest and most powerful connections between shapes and numbers in geometry.",
#             "steps": [
#                 "1. Picture a right-angled triangle — the kind of triangle where one corner is exactly 90°. Label the shorter sides that meet at the right angle ‘a’ and ‘b’, and the longest side (the slanted one) as ‘c’.",
#                 "2. Imagine drawing a square on each of the three sides of the triangle. Each square’s area matches the square of that side’s length — so you get areas a², b², and c².",
#                 "3. The beautiful relationship Pythagoras discovered is that the two smaller squares together perfectly fill the largest one. In algebra, that’s written as a² + b² = c².",
#                 "4. This formula works for every right-angled triangle and allows you to find any missing side if you know the other two — no measuring tape needed!",
#             ],
#             "conclusion": "Pythagoras’ Theorem reveals a deep link between geometry and algebra: in any right-angled triangle, the square on the hypotenuse equals the sum of the squares on the other two sides.",
#         },
#         "prompter_output": {
#             "prompts": [
#                 "Draw a right-angled triangle. Label the two shorter sides 'a' and 'b'. Label the hypotenuse 'c'. Indicate the 90-degree angle.",
#                 "Draw the right-angled triangle with sides 'a', 'b', and 'c'. Construct a square outwards on each side, labeling their areas 'a²', 'b²', and 'c²' respectively.",
#                 "Draw the right-angled triangle with the three squares on its sides. Label the areas of the squares as 'a²', 'b²', and 'c²'. Show a visual indication that the areas of the two smaller squares combine to equal the area of the largest square.",
#                 "No figure",
#             ]
#         },
#         "tts_preprocessor_output": {
#             "output": [
#                 "First, picture a right-angled triangle – that's the kind where one corner is exactly ninety degrees. We'll label the two shorter sides that meet at that right angle as 'a' and 'b', and the longest side, the slanted one, as 'c'.",
#                 "Next, imagine drawing a square on each of the triangle's three sides. The area of each square will match the square of its side's length. So, you'd have squares with areas of 'a squared', 'b squared', and 'c squared'.",
#                 "The beautiful relationship Pythagoras discovered is that those two smaller squares, when put together, perfectly fill the largest one. In algebra, we write that as 'a squared plus b squared equals c squared'.",
#                 "This amazing formula works for every single right-angled triangle! It lets you find any missing side's length if you already know the other two — and you won't even need a measuring tape!",
#             ]
#         },
#         "snippet_generator_output": {
#             "context_snippets": ["Shortest distance (diagonal)", "Geometry ↔ Numbers"],
#             "step_snippets": [
#                 ["Right-angled triangle", "90° angle", "Sides a, b, hypotenuse c"],
#                 ["Squares on sides", "Areas a², b², c²"],
#                 ["a² + b² = c²", "Smaller squares = Largest square"],
#                 ["Works for ALL right triangles", "Find any missing side"],
#             ],
#             "conclusion_snippets": [
#                 "Geometry ↔ Algebra link",
#                 "Right triangle: c² = a² + b²",
#             ],
#         },
#     }

#     async def event_generator():
#         try:
#             # Convert astream to an async iterator we can timeout
#             stream_iter = graph_app.astream(input=state, config=config).__aiter__()
            
#             while True:
#                 try:
#                     # Try to get next event with 10 second timeout
#                     event = await asyncio.wait_for(stream_iter.__anext__(), timeout=10.0)
                    
#                     for node_name, node_output in event.items():
#                         print("node name: ", node_name)
#                         print("node output: ", node_output)
                        
#                         yield {
#                             "event": node_name,
#                             "id": concept_id,
#                             "data": json.dumps(
#                                 {"": ""} if node_name != "__interrupt__" else node_output[0].value
#                             ),
#                         }
                        
#                 except asyncio.TimeoutError:
#                     # No event in 10 seconds, send heartbeat
#                     print("Sending heartbeat")
#                     yield {
#                         "event": "heartbeat",
#                         "id": concept_id,
#                         "data": json.dumps({"status": "processing"})
#                     }
                    
#                 except StopAsyncIteration:
#                     # Stream ended normally
#                     print("Stream completed")
#                     break
                    
#         finally:
#             await cm.__aexit__(None, None, None)

#     return EventSourceResponse(event_generator(), media_type="text/event-stream")
