"""Environment variable helpers.

This module centralizes configuration and `.env` loading.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    hf_token: Optional[str]


def load_env(repo_root: Optional[Path] = None) -> None:
    """Loads environment variables from a `.env` file if present.

    Args:
        repo_root: Optional explicit repository root (directory containing `.env`).
    """
    if repo_root is not None:
        env_path = repo_root / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
        return

    env_path_str = find_dotenv(filename=".env", usecwd=True)
    if env_path_str:
        load_dotenv(dotenv_path=env_path_str, override=False)


def get_settings() -> Settings:
    """Builds Settings from process environment."""
    hf_token = os.environ.get("HF_TOKEN") or None
    return Settings(hf_token=hf_token)
 
