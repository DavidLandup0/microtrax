"""Frontend serving service - handles both development and production modes"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        """Configure frontend serving based on environment"""
        # Detect if we're running from pip install (static files) or source (dev mode)
        current_dir = Path(__file__).parent.parent.parent  # microtrax/
        frontend_build_dir = current_dir / "frontend" / "build"
        has_built_frontend = frontend_build_dir.exists()

        if has_built_frontend:
            self._setup_production_mode(frontend_build_dir)
        else:
            self._setup_development_mode()

    def _setup_production_mode(self, frontend_build_dir: Path):
        """Setup production mode with bundled static files"""
        print("📦 Using bundled frontend")

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(frontend_build_dir / "static")), name="static")

        # Serve React app for all non-API routes
        @self.app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            # API routes should not be caught by this
            if full_path.startswith("api/") or full_path == "docs" or full_path == "openapi.json":
                return {"error": "Not found"}
            # Serve index.html for all other routes (React Router)
            return FileResponse(str(frontend_build_dir / "index.html"))

        # Override root to serve React app
        @self.app.get("/")
        async def root():
            return FileResponse(str(frontend_build_dir / "index.html"))

    def _setup_development_mode(self):
        """Setup development mode with CORS for separate React dev server"""
        print("🛠️  Using development mode (expecting React dev server on :3000)")

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.get("/")
        async def root():
            return {"message": "microtrax API", "docs": "/docs", "frontend": "http://localhost:3000"}
