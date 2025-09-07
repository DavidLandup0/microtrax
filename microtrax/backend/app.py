from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from microtrax.backend.routers import experiments, plots, images


def create_app(logdir: str) -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(title="microtrax Dashboard", version="0.1.0")

    # Enable CORS for React frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store logdir in app state for routers to access
    app.state.logdir = logdir

    @app.get("/")
    async def root():
        return {"message": "microtrax API", "docs": "/docs"}

    # Include routers with dependency injection for logdir
    app.include_router(experiments.router)
    app.include_router(plots.router)
    app.include_router(images.router)

    return app
