import os
from pathlib import Path
from typing import Optional
import webbrowser

import logging

import subprocess
import signal
import sys

from microtrax.constants import MTX_GLOBALDIR

def run_dashboard(logdir: Optional[str] = None, backend_port: int = 8080, frontend_port=3000, host: str = "localhost"):
    """
    Runs the microtrax dashboard.
    FastAPI backend + React frontend.
    """
    if logdir is None:
        logdir = MTX_GLOBALDIR

    logdir = str(Path(logdir).absolute())
    frontend_dir = Path(__file__).parent / 'frontend'
    node_modules = frontend_dir / 'node_modules'

    logging.info("🚀 Starting microtrax dashboard...")
    logging.info(f"📁 Loading experiments from: {logdir}")
    logging.info(f"🎯 Backend API: http://{host}:{backend_port}")
    logging.info(f"🎨 Frontend UI: http://localhost:{frontend_port}")
    logging.info(f"📊 API docs: http://{host}:{backend_port}/docs")

    # Check if npm is available
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.info("❌ npm not found. Please install Node.js and npm to use the React frontend.")

    if not node_modules.exists():
        logging.info("📦 Installing frontend dependencies...")
        subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)

    # Start backend in a separate process
    backend_process = None
    frontend_process = None

    def cleanup(signum=None, frame=None):
        """Cleanup processes on exit"""
        logging.info("\n🛑 Shutting down microtrax dashboard...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(0)

    # Register cleanup handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:

        backend_process = start_backend(logdir, host, backend_port)
        frontend_process = start_frontend(frontend_dir, frontend_port)

        logging.info("✅ microtrax dashboard is running!")
        logging.info(f"   Backend:  http://localhost:{backend_port}")
        logging.info(f"   Frontend: http://localhost:{frontend_port}")
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


def start_frontend(frontend_dir, port=3000):
    # Start React frontend
    logging.info("🔄 Starting React frontend...")
    frontend_process = subprocess.Popen([
        'npm', 'start', # Add port here
    ], cwd=frontend_dir, env={**os.environ, 'BROWSER': 'none'})

    # TODO: This is a stand-in for detecting when the app is actually up.
    # For now, just give it a couple of seconds to boot up before the browser is opened.
    import time
    time.sleep(3)
    webbrowser.open(f'http://localhost:{port}')

    return frontend_process
