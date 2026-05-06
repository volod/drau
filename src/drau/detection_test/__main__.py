"""Entry point: python -m drau.detection_test."""

import argparse
import sys
from pathlib import Path

from drau.detection_test.session import run


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="drau-detection-test",
        description="Run a drone-sound detection test with external microphone systems.",
    )
    parser.add_argument("--samples-num", type=int, required=True,
                        help="Number of audio samples to play.")
    parser.add_argument("--mic-num", type=int, required=True,
                        help="Number of external microphone systems under test.")
    parser.add_argument("--dist-max", type=float, required=True,
                        help="Maximum simulated drone distance in metres.")
    parser.add_argument("--audio-dir",
                        default=".data/drone-audio-detection-samples/audio",
                        help="Parent dir with drone-audio/ and non-drone-audio/ (default: %(default)s).")
    parser.add_argument("--output-dir",
                        default=".data/detection-tests",
                        help="Directory for session CSV files (default: %(default)s).")
    parser.add_argument("--audio-duration-min", type=float, default=None,
                        metavar="SECONDS",
                        help="Exclude samples shorter than this duration in seconds (default: no filter).")
    parser.add_argument("--reliable-range", type=float, default=100.0,
                        metavar="METRES",
                        help="Distance beyond which a warning is shown in the form (default: %(default)s m).")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run(
        samples_num=args.samples_num,
        mic_num=args.mic_num,
        dist_max=args.dist_max,
        audio_dir=Path(args.audio_dir),
        output_dir=Path(args.output_dir),
        min_duration_s=args.audio_duration_min,
        reliable_range=args.reliable_range,
    ))
