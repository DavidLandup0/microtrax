from fastapi import FastAPI
from microtrax.backend.routers import experiments, plots, images
from microtrax.backend.services.frontend_service import FrontendService


def create_app(logdir: str) -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(title="microtrax Dashboard", version="0.1.0")

    # Setup frontend serving (production vs development mode)
    FrontendService(app)

    # Store logdir in app state for routers to access
    app.state.logdir = logdir

    # Include routers with dependency injection for logdir
    app.include_router(experiments.router, prefix="/api")
    app.include_router(plots.router, prefix="/api")
    app.include_router(images.router, prefix="/api")

    return app
