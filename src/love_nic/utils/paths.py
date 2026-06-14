"""Utilitarios de caminho para modo desenvolvimento e executavel."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _project_root() -> Path:
    # src/love_nic/utils/paths.py -> raiz do projeto
    return Path(__file__).resolve().parents[3]


def resolve_path(*parts: str) -> str:
    """Resolve caminhos tanto no source quanto no executavel do PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(getattr(sys, "_MEIPASS"))
    else:
        base_path = _project_root()

    return os.fspath(base_path.joinpath(*parts))
