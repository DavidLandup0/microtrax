"""Frontend serving service - handles both development and production modes"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


class FrontendService:
    """
    Service to handle frontend serving logic.
    I.e. whether microtrax was built from `pip`'s installer
    or source.
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self._setup_frontend()

    def _setup_frontend(self):
        current_dir = Path(__file__).parent.parent.parent  # microtrax/
        frontend_build_dir = current_dir / "frontend" / "build"
        self._serve_frontend(frontend_build_dir)

    def _serve_frontend(self, frontend_build_dir: Path):
        """Setup production mode with bundled static files"""
        print("📦 Using bundled frontend")

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(frontend_build_dir / "static")), name="static")

        @self.app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            return FileResponse(str(frontend_build_dir / "index.html"))

        # Override root to serve React app
        @self.app.get("/")
        async def root():
            return FileResponse(str(frontend_build_dir / "index.html"))
