"""Entry point: python -m drau.analysis."""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from drau.analysis import analyse


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="drau-analyse-detection",
        description="Analyse a detection test session CSV and print statistics.",
    )
    parser.add_argument("csv_file", type=Path, help="Path to the session CSV file.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    analyse(args.csv_file, Console())
    sys.exit(0)
