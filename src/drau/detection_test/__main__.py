"""Entry point: python -m drau.detection_test."""

import argparse
import sys
from pathlib import Path

from drau.detection_test.session import run
from drau.settings.env import get_settings, load_env


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    load_env(repo_root=repo_root)
    settings = get_settings()

    parser = argparse.ArgumentParser(
        prog="drau-detection-test",
        description="Run a drone-sound detection test with external microphone systems.",
    )
    parser.add_argument("--samples-num", type=int, default=None,
                        help="Number of audio samples to play.")
    parser.add_argument("--mic-num", type=int, default=None,
                        help="Number of external microphone systems under test.")
    parser.add_argument("--dist-max", type=float, default=None,
                        help="Maximum simulated drone distance in metres.")
    parser.add_argument("--audio-dir",
                        default=settings.detection_audio_dir,
                        help="Parent dir with drone-audio/ and non-drone-audio/ (default: %(default)s).")
    parser.add_argument("--output-dir",
                        default=settings.detection_output_dir,
                        help="Directory for session CSV files (default: %(default)s).")
    parser.add_argument("--audio-duration-min", type=float,
                        default=settings.audio_duration_min_s,
                        metavar="SECONDS",
                        help="Exclude samples shorter than this duration in seconds (default: no filter).")
    parser.add_argument("--audio-duration-max", type=float,
                        default=settings.audio_duration_max_s,
                        metavar="SECONDS",
                        help="Clip samples longer than this duration in seconds (default: %(default)s).")
    parser.add_argument("--reliable-range", type=float,
                        default=settings.detection_reliable_range_m,
                        metavar="METRES",
                        help="Distance beyond which a warning is shown in the form (default: %(default)s m).")
    parser.add_argument("--mic-detect-max", type=float,
                        default=settings.mic_detect_max_m,
                        metavar="METRES",
                        help="Distance beyond which detection is not expected; analysis splits at this boundary (default: %(default)s m).")

    args = parser.parse_args(argv)

    missing = [flag for flag, val in [
        ("--samples-num", args.samples_num),
        ("--mic-num",     args.mic_num),
        ("--dist-max",    args.dist_max),
    ] if val is None]
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)}")

    return args


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
        audio_duration_max_s=args.audio_duration_max,
        mic_detect_max_m=args.mic_detect_max,
    ))
