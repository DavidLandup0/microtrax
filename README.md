<div align="center"><h1>microtrax</h1></div>
<div align="center"><h6>Yet Another Experiment Tracking Library</h6></div>

<div align="center"><h3>Local, minimalist, micro experiment tracking for Machine Learning/Deep Learning workflows.</h1></div>

<hr>

<div align="center">
Free. Fully local. Lightweight.
</div>
<hr>

No accounts, no setups. 3 lines to track.

`microtrax` attempts to be a modern, minimalist library for experiment tracking. Inspired by TensorBoard.

<div align="center"><h2>Quickstart</h1></div>

```bash
$ pip install microtrax
```

```python
import microtrax as mtx

epochs = 10
mtx.init('./logbook_dir') #, optionally also track_resources=True)

for i in range(epochs):
    mtx.log({
        "step": i,
        "loss": epochs-i
    })

mtx.finish()
```

Then serve the dashboard:

```
$ mtx serve -f ./logbook_dir
```

This automatically starts both the FastAPI backend and React frontend!


It's called a quickstart as if there's anything else you can do with it. Actually, that's pretty much it.

<div align="center"><h2>Design Philosophy</h2></div>

- Free forever.
- Simplicity > feature-richness.
- Research-experience first.
- Framework agnostic - no specialized adapters for different libraries nor ecosystem favoritism. Log whatever.
- Lightweight footprint. No hogging the CPU or memory.
- Easily extendable (standard stack + simple to add new components/routes)
- No setups, no accounts, no enterprise versions.

<div align="center"><h2>Learning microtrax in 10 seconds</h2></div>

- **Experiment:** whatever happens between `mtx.init()` and `mtx.finish()`, housing a series of `mtx.log()`s.
- **Logbook:** Collection of experiments in a log directory.
- **Dashboard:** Where your visualizations go. You can select which experiments to visualize and overlay from the logbook.

No need to learn anything else to use `microtrax`.

<div align="center"><h2>CLI Usage</h2></div>

After installation, you can use the `mtx` command:

```bash
# Start the dashboard 
mtx serve -f ./logbook_dir -p 8080

# Start with Docker Compose
mtx serve -f ./logbook_dir --docker

# List all experiments in a directory
mtx list -f ./logbook_dir

# Serve with custom host/port
mtx serve -f ./logbook_dir --host 0.0.0.0 -p 3000
```

**Commands:**
- `mtx serve` - Start the interactive dashboard web server
- `mtx list` - List all experiments in the specified directory

**Options:**
- `-f, --logdir` - Directory containing experiments (default: ~/.microtrax)
- `-p, --port` - Port to run dashboard on (default: 8080, frontend runs on 3000)  
- `--host` - Host to bind to (default: localhost)
- `--docker` - Run using Docker Compose instead of local servers

**Note**: In pip install mode, the dashboard serves on the backend port. In development mode (git clone), frontend runs separately on port 3000.

<br>

# microtrax - Bird's Eye View

From a bird's eye view, `microtrax` has four main components:

- **Core:** Core operations like `mtx.init()`, `mtx.log()` and `mtx.finish()`, as well as handling of I/O
- **CLI:** Runner for the CLI commands like `mtx list` and `mtx serve`
- **Backend:** FastAPI server + routers for exposing a logdir's logs
- **Frontend:** React frontend for visualizing data provided by the server via Plotly

### Why React + FastAPI and not something "simpler"? 

Because this is a hackable, extendable, simple format. We want to make it as easy as possible to extend and tweak the library.
Proprietary formats, uncommon libs or "simplifying" by obscurity go against the core principles of the library.

- Need a new widget -> Add a single React component in `/frontend/src/components`
- Need a new server endpoint -> Add a single endpoint in FastAPI's routers in `/backend/routers`

A highly standard stack ensures that the widest number of users can easily and comfortably understand and extend the library as needed.


```

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                               microtrax                                     │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐      ┌───────────────────┐    ┌─────────────────────────────┐
  │   User Code     │      │   File System     │    │        Dashboard            │
  │                 │      │                   │    │                             │
  │  mtx.init()     │─────▶│  ~/.microtrax/    │◀───│ ┌─────────────────────────┐ │
  │  mtx.log({...}) │      │    experiments/   │    │ │    React Frontend       │ │
  │  mtx.finish()   │      │    resources/     │    │ │    (Port 3000)          │ │
  │                 │      │                   │    │ │  - Plot visualizations  │ │
  └─────────────────┘      │  exp_id.jsonl     │    │ │  - Experiment browser   │ │
                           │  (w/ base64 imgs) │    │ │  - Settings panel       │ │
  ┌───────────────────┐    │  resources.jsonl  │    │ └─────────────────────────┘ │
  │   Core Module     │    │                   │    │             │               │
  │                   │───▶│                   │    │           HTTP              │
  │ • Experiment      │    └───────────────────┘    │             │               │
  │ • ResourceTracker │                             │ ┌─────────────────────────┐ │
  │ • I/O Utils       │   ┌──────────────────┐      │ │   FastAPI Backend       │ │
  │ • Image Processing│   │       CLI        │──────│ │   (Port 8080)           │ │
  └───────────────────┘   │                  │      │ │                         │ │
                          │  mtx serve       │      │ │  /api/experiments       │ │
                          │  mtx list        │      │ │  /api/plots             │ │
                          └──────────────────┘      │ │  /api/images            │ │
                                                    │ │  /api/plot-options      │ │
                                                    │ └─────────────────────────┘ │
                                                    └─────────────────────────────┘

  Data Flow:
  User Code ─> JSONL -> File System -> Backend -> JSON -> Frontend -> User
```

# git clone vs pip install

When you run `git clone`, you 'll get both the source code for the frontend, backend and core libraries. This makes it possible to run `npm start` for the frontend:

```
$ git clone https://github.com/DavidLandup0/microtrax.git
$ cd microtrax
$ pip install -e .
```

When installing with `pip`, we can only ship Python + static files. The `pip` installable version of `microtrax` ships the frontend as a pre-built bundle of static files. 

This means the frontend is served as static files rather than through `npm start`:

```
$ pip install microtrax
```

# Docker Compose

You can also run the `microtrax` dashboard through Docker Compose for containerized deployment.

## Setup

1. Configure your experiment log directory in `.env`:
```bash
# Directory where experiment logs are stored
MICROTRAX_LOGDIR=./my_experiments
```

2. Run the stack:
```bash
docker-compose up
```

This will start:
- **Backend API** on port 8080
- **Frontend dashboard** on port 3000

The frontend automatically proxies API requests to the backend container via `nginx`.

## Configuration

The `MICROTRAX_LOGDIR` environment variable specifies where your experiment logs are stored on the host machine. This directory is mounted into the backend container at `/data`.

Default: `~/.microtrax` if not specified

## Access

- Dashboard: http://localhost:3000
- Backend API: http://localhost:8080

The frontend handles routing and proxies `/api/*` requests to the backend automatically.

# Contributing

We welcome contributions to `microtrax`! 
It's community-first, so any and every issue and idea will be considered.
This guide will help you get started if you'd like to propose a change.

## Getting Started

1. **Fork and clone the repository**
    
```bash
$ git clone https://github.com/yourusername/microtrax.git
$ cd microtrax
```

2. Set up development environment

```bash
# Install Python dependencies
$ pip install microtrax
$ pip install pytest ruff

# Install frontend dependencies  
$ cd microtrax/frontend
$ npm install
```

3. Run tests

```bash
# Python tests
pytest
# Format code
make format
```

## Development Workflow

### Backend Changes

- Location: `/microtrax/backend/`
- For routers: `/backend/routers/`
- For endpoints: `/backend/routers/router_name.py`
- For business logic: `/backend/services/`
- For data models: `/backend/domain/schemas.py`

### Frontend Changes

- Location: `/microtrax/frontend/src/`
- For new components: `/frontend/src/components/`

### Core Changes

- Location: `/microtrax/core.py`, `/microtrax/io_utils.py`
- Experiment tracking logic
- File I/O operations
- Image processing

### Code Standards
- Python: Follow PEP 8, use type hints, run ruff for linting


### Submitting Changes

1. Create a feature branch
```
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Test
4. Submit a pull request

### Questions?

- Check existing issues on GitHub
- Start a discussion for feature ideas

# Citation

If you happen to use `microtrax` for your research, and publish your results - we'd appreciate a citation~

```
@misc{landup2025microtrax,
  title={microtrax},
  author={David Landup},
  year={2025},
  howpublished={\url{https://github.com/DavidLandup0/microtrax/}},
}
```