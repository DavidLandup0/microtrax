from pathlib import Path
from typing import Optional

import logging

import subprocess
import signal
import sys

from microtrax.constants import MTX_GLOBALDIR

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_dashboard(logdir: Optional[str] = None, backend_port: int = 8080, host: str = "localhost"):
    """
    Runs the microtrax dashboard.
    FastAPI backend + React frontend.
    """
    if logdir is None:
        logdir = MTX_GLOBALDIR

    logdir = str(Path(logdir).absolute())
    frontend_dir = Path(__file__).parent / 'frontend'

    logging.info("🚀 Starting microtrax dashboard...")
    logging.info(f"📁 Loading experiments from: {logdir}")
    logging.info(f"🎯 Backend API: http://{host}:{backend_port}")
    logging.info(f"🎨 Frontend UI: http://{host}:{backend_port}")
    logging.info(f"📊 API docs: http://{host}:{backend_port}/docs")

    # Start backend in a separate process
    backend_process = None

    def cleanup(signum=None, frame=None):
        """Cleanup processes on exit"""
        logging.info("\n🛑 Shutting down microtrax dashboard...")
        if backend_process:
            backend_process.terminate()
        sys.exit(0)

    # Register cleanup handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:

        backend_process = start_backend(logdir, host, backend_port)

        logging.info("✅ microtrax dashboard is running!")
        logging.info(f"   Backend:  http://localhost:{backend_port}")
        logging.info(f"   Frontend: http://localhost:{backend_port} (bundled)")
        logging.info("   Press Ctrl+C to stop")

        # Wait for processes
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            cleanup()

    except Exception as e:
        logging.info(f"❌ Failed to start dashboard: {e}")
        cleanup()


def start_backend(logdir, host, port):
     # Start FastAPI backend
    logging.info("🔄 Starting FastAPI backend...")
    backend_process = subprocess.Popen([
        sys.executable, '-c',
        f'''import uvicorn; from microtrax.backend.app import create_app; app = create_app("{logdir}"); uvicorn.run(app, host="{host}", port={port}, log_level="warning")'''
    ])

    return backend_process


