"""Unpack cached Arrow dataset into plain WAV files sorted by label."""

from pathlib import Path

from datasets import Audio, load_from_disk

DRONE_SUBDIR     = "drone-audio"
NON_DRONE_SUBDIR = "non-drone-audio"

_LABEL_TO_SUBDIR = {0: NON_DRONE_SUBDIR, 1: DRONE_SUBDIR}


def _dirs_populated(output_dir: Path) -> bool:
    for subdir in _LABEL_TO_SUBDIR.values():
        p = output_dir / subdir
        if not p.is_dir() or not any(p.iterdir()):
            return False
    return True


def unpack_dataset(dataset_dir: Path, output_dir: Path, *, force: bool) -> Path:
    """Write one WAV file per row into drone-audio/ or non-drone-audio/.

    Skips extraction if both output subdirectories are already populated, unless force=True.
    Returns the resolved output_dir path.
    """
    output_dir = output_dir.resolve()

    if not force and _dirs_populated(output_dir):
        return output_dir

    for subdir in _LABEL_TO_SUBDIR.values():
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    ds    = load_from_disk(str(dataset_dir.resolve()))
    split = ds["train"].cast_column("audio", Audio(decode=False))
    total = len(split)

    for i, row in enumerate(split):
        subdir   = _LABEL_TO_SUBDIR[row["label"]]
        filename = Path(row["audio"]["path"]).name
        dest     = output_dir / subdir / filename
        if not force and dest.exists():
            continue
        dest.write_bytes(row["audio"]["bytes"])
        if (i + 1) % 10_000 == 0:
            print(f"  {i + 1}/{total} files written...")

    return output_dir
