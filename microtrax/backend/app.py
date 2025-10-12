from fastapi import FastAPI
from microtrax.backend.routers import experiments, plots, images, text
from microtrax.backend.services.frontend_service import FrontendService


def create_app(logdir: str) -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(title="microtrax Dashboard", version="0.1.0")

    # Store logdir in app state for routers to access
    app.state.logdir = logdir

    app.include_router(experiments.router)
    app.include_router(plots.router)
    app.include_router(images.router)
    app.include_router(text.router)

    FrontendService(app)

    return app
