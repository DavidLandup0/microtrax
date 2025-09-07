#!/usr/bin/env python3
"""
microtrax CLI interface
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path

from microtrax.core import serve
from microtrax.backend.services.experiment_service import load_experiments
from microtrax.constants import MTX_GLOBALDIR

def resolve_logdir(args):
    return args.logdir or MTX_GLOBALDIR

def cmd_serve(args):
    if args.docker:
        return cmd_serve_docker(args)

    logdir = resolve_logdir(args)

    if not Path(logdir).exists():
        print(f"❌ Logdir does not exist: {logdir}")
        print("Run some experiments first or specify a different directory with -f")
        return 1

    try:
        print(f"📁 Loading experiments from: {logdir}")
        experiments = load_experiments(logdir)

        if not experiments:
            print(f"⚠️  No experiments found in {logdir}")
            print("Run some experiments first!")
        else:
            print(f"📊 Found {len(experiments)} experiments")

        serve(logdir, args.port, args.host)

        # Keep the main thread alive
        try:
            import threading
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
            return 0

    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return 1

def cmd_serve_docker(args):
    logdir = resolve_logdir(args)

    # Find the project root (where docker-compose.yml is)
    current_path = Path(__file__).parent
    project_root = None

    # Walk up the directory tree looking for docker-compose.yml
    for parent in [current_path] + list(current_path.parents):
        if (parent / "docker-compose.yml").exists():
            project_root = parent
            break

    if not project_root:
        print("❌ docker-compose.yml not found. Make sure you're in the microtrax project directory.")
        return 1

    print(f"📁 Using logdir: {logdir}")
    print(f"🐳 Starting Docker Compose from: {project_root}")

    # Set environment variables for docker-compose
    env = os.environ.copy()
    env["MICROTRAX_LOGDIR"] = str(Path(logdir).resolve())

    try:
        # Run docker-compose up
        cmd = ["docker-compose", "up"]
        process = subprocess.run(
            cmd,
            cwd=project_root,
            env=env,
            check=False  # Don't raise exception on non-zero exit
        )

        return process.returncode

    except FileNotFoundError:
        print("❌ docker-compose command not found. Please install Docker Compose.")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 Docker Compose stopped")
        return 0
    except Exception as e:
        print(f"❌ Failed to start Docker Compose: {e}")
        return 1

def cmd_list(args):
    logdir = resolve_logdir(args)

    try:
        experiments = load_experiments(logdir)

        if not experiments:
            print(f"No experiments found in {logdir}")
            return 0

        print(f"📊 Found {len(experiments)} experiments in {logdir}:\n")

        for exp_id, exp_data in experiments.items():
            metadata = exp_data.get('metadata', {})
            logs_count = len(exp_data.get('logs', []))

            start_time = metadata.get('start_time_iso', 'Unknown')
            status = metadata.get('status', 'unknown')

            print(f"🧪 {exp_id}")
            print(f"   Started: {start_time}")
            print(f"   Status:  {status}")
            print(f"   Steps:   {logs_count}")
            print()

        return 0

    except Exception as e:
        print(f"❌ Failed to list experiments: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        prog="mtx",
        description="microtrax - Local-first experiment tracking"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start the full dashboard (React frontend + FastAPI backend)')
    serve_parser.add_argument('-f', '--logdir', help='Directory containing experiments (default: ~/.microtrax)')
    serve_parser.add_argument('-p', '--port', type=int, default=8080, help='Backend port (default: 8080, frontend runs on 3000)')
    serve_parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    serve_parser.add_argument('--docker', action='store_true', help='Run using Docker Compose instead of local servers')
    serve_parser.set_defaults(func=cmd_serve)

    # List command
    list_parser = subparsers.add_parser('list', help='List experiments')
    list_parser.add_argument('-f', '--logdir', help='Directory containing experiments (default: ~/.microtrax)')
    list_parser.set_defaults(func=cmd_list)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run the command
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
