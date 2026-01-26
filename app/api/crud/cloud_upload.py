import shutil
from fastapi import APIRouter, Depends

from utils import get_graph, upload_diagrams, add_to_explanation_db
from database import get_explanation_db


router = APIRouter()


@router.post("/crud/add_to_cloud/")
async def add_to_cloud(concept_id: int, db=Depends(get_explanation_db)):
    try:
        graph_app, cm = await get_graph()
        config = {"configurable": {"thread_id": concept_id}}

        graph_state = await graph_app.aget_state(config=config)
        graph_state = graph_state.values

        concept_name = graph_state["concept"]
        concept_id = graph_state["concept_id"]
        explanation = graph_state["explainer_output"]
        snippets = graph_state["snippet_generator_output"]
        tts = graph_state["tts_preprocessor_output"]["output"]

        upload_diagrams(str(concept_id))

        await add_to_explanation_db(
            explainer_output=explanation,
            concept_id=int(concept_id),
            concept_name=concept_name,
            tts_data=tts,
            snippets_data=snippets,
            db=db,
        )

        shutil.rmtree(f"Storage/{str(concept_id)}")

        return {"status": "200", "data": "Data uploaded to the cloud successfully!"}

    except Exception as e:
        return {"status": 500, "data": "Something went wrong!"}
