#!/usr/bin/env bash
# Bootstrap + run the planet simulator. Nothing installed system-wide:
# uv lives in ~/.local/bin (or wherever its installer puts it) and the
# Python deps live in a project-local .venv managed by uv.

set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    # Also pick up uv if it was installed in this shell session but PATH
    # hasn't been re-exported yet.
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found — installing to ~/.local/bin (no sudo, no system Python touched)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Creates .venv if missing, installs/updates deps from pyproject.toml/uv.lock.
uv sync --quiet

exec uv run python main.py "$@"
