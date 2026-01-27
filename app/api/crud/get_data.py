from pathlib import Path
from fastapi import APIRouter, Query, HTTPException

from utils import get_graph, encode_image

router = APIRouter()


@router.get("/crud/get_data/")
async def get_data(concept_id: int = Query(), diagrams: bool = Query(default=True)):
    try:
        graph_app, cm = await get_graph()
        config = {"configurable": {"thread_id": concept_id}}
        graph_state = await graph_app.aget_state(config=config)
        graph_state = graph_state.values

        explanation = graph_state["explainer_output"]

        explanation_steps_w_fig = []
        if diagrams:
            for i, explanation_text in enumerate(explanation["steps"]):
                fig_name = f"fig_{i}.png"
                fig_path = Path(f"Storage/{str(concept_id)}/{fig_name}")  # Fixed: was using fig_name variable in path
                
                step_data = {
                    "text": explanation_text,
                    "figure": encode_image(fig_path) if fig_path.exists() else None
                }
                explanation_steps_w_fig.append(step_data)
        else:
            # If diagrams not requested, just return text
            explanation_steps_w_fig = [{"text": step, "figure": None} for step in explanation["steps"]]

        return {
            "concept_id": concept_id,
            "context": explanation["context"],
            "steps": explanation_steps_w_fig,
            "conclusion": explanation["conclusion"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")
    
    finally:
        await cm.__aexit__(None, None, None)