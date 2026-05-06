"""Entry point: python -m drau.data — download, unpack, and analyse audio dataset."""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from drau.data.analytics import run_analytics
from drau.data.cache import cache_dataset
from drau.data.unpack import unpack_dataset
from drau.settings.env import get_settings, load_env


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    load_env(repo_root=repo_root)
    settings = get_settings()

    parser = argparse.ArgumentParser(
        prog="drau-data",
        description=(
            "Download and cache the drone audio dataset, unpack WAV files, "
            "and (by default) run acoustic analytics."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        default=settings.data_cache_dir,
        help="Target directory for cached Arrow dataset (default: %(default)s).",
    )
    parser.add_argument(
        "--audio-dir",
        default=settings.data_audio_dir,
        help="Output directory for unpacked WAV files (default: %(default)s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the cache directory and re-download before processing.",
    )
    parser.add_argument(
        "--analytics",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Run acoustic analytics after unpacking (default: enabled).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args      = _parse_args(argv)
    repo_root = Path(__file__).resolve().parents[3]
    load_env(repo_root=repo_root)
    settings  = get_settings()
    console   = Console()

    cache_path = cache_dataset(
        Path(args.cache_dir), hf_token=settings.hf_token, force=bool(args.force)
    )
    console.print(f"Cached dataset to: [cyan]{cache_path}[/cyan]")

    audio_dir   = Path(args.audio_dir)
    output_path = unpack_dataset(cache_path, audio_dir, force=bool(args.force))
    console.print(f"Audio files unpacked to: [cyan]{output_path}[/cyan]")

    if args.analytics:
        run_analytics(audio_dir, console)

    return 0


if __name__ == "__main__":
    sys.exit(main())
