from fastapi import APIRouter, HTTPException, Request

from microtrax.backend.services.text_service import load_text_data
from microtrax.backend.domain.schemas import TextRequest

router = APIRouter(prefix="/api", tags=["text"])

@router.post("/text")
async def get_text(request: Request, text_request: TextRequest):
    """Get text data from an experiment"""
    logdir = request.app.state.logdir

    try:
        text_data = load_text_data(logdir, text_request.experiment)
        return text_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
