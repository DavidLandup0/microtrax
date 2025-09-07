from fastapi import APIRouter, HTTPException, Request

from microtrax.backend.services.experiment_service import load_experiments, get_experiment_images
from microtrax.backend.domain.schemas import ImagesRequest

router = APIRouter(prefix="/api", tags=["images"])

@router.post("/images")
async def get_images(request: Request, images_request: ImagesRequest):
    """Get images from an experiment"""
    logdir = request.app.state.logdir

    try:
        experiments = load_experiments(logdir)
        images = get_experiment_images(experiments, images_request.experiment)
        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
