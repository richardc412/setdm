# Backend

This service is a lightweight FastAPI application that runs inside the
[`uv`](https://docs.astral.sh/uv/) toolchain.

## Requirements

- Python 3.12 (see `.python-version`)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) ≥ 0.4

`uv sync` takes care of creating and reusing `.venv/`, so you usually do not
need to activate a virtual environment manually.

## Setup

```bash
cd /Users/idkdude/Desktop/setdm/backend
uv sync
```

`uv sync` installs the dependencies pinned in `pyproject.toml` and `uv.lock`.
It downloads the wheels and keeps the local `.venv` aligned with the lockfile.

## Common commands

- Show `uv` version: `uv --version`
- Install or update dependencies: `uv sync`
- Regenerate `uv.lock` after dependency changes: `uv lock`
- Run the FastAPI dev server (reload enabled): `uv run fastapi dev app/main.py --port 8000 --reload`
- Run FastAPI with production defaults: `uv run fastapi run app/main.py --host 0.0.0.0 --port 8000`
- Inspect registered routes: `uv run fastapi routes app.main:app`

FastAPI commands work without the `uv run` prefix if you activate `.venv`
yourself (for example: `source .venv/bin/activate`):

- `fastapi dev app/main.py --port 8000 --reload`
- `fastapi run app/main.py --host 0.0.0.0 --port 8000`
- `fastapi routes app.main:app`

Use `fastapi dev` for hot-reload during development and `fastapi run` for the
production-ready Uvicorn server.
