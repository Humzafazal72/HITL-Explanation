from fastapi import APIRouter, Query, HTTPException

from utils import remove_figures
router = APIRouter()

@router.delete("/crud/delete_figures")
async def delete_figures(concept_id = Query(...)):
    try:
        remove_figures(concept_id=str(concept_id))
    except Exception as e:
        return HTTPException(status_code=500, detail=f"{e}")
