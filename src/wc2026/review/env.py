"""Load API keys from a gitignored ``.env`` so runs don't depend on shell exports.

A session ``export`` is lost on a crash, new shell, or reboot; a local ``.env`` file is
permanent and is never committed (see .gitignore). Real environment variables always win
over the file, so CI / one-off overrides still work. Dependency-free (no python-dotenv).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def load_dotenv(path: Path | None = None, *, override: bool = False) -> list[str]:
    """Parse ``.env`` (KEY=VALUE per line) into os.environ. Returns the keys loaded.

    - Lines may use ``export KEY=VALUE``; surrounding quotes are stripped.
    - Blank lines and ``#`` comments are ignored.
    - Existing env vars are preserved unless ``override=True``.
    """
    path = path or (REPO / ".env")
    if not path.exists():
        return []
    loaded = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = val
            loaded.append(key)
    return loaded
