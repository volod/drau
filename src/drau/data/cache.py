"""Download and cache the drone audio HuggingFace dataset."""

import shutil
from pathlib import Path

from datasets import DownloadConfig, load_dataset

DATASET_ID = "geronimobasso/drone-audio-detection-samples"


def cache_dataset(cache_dir: Path, *, hf_token: str | None, force: bool) -> Path:
    """Download the dataset and write it to disk as Arrow files.

    Skips download if cache_dir already exists unless force=True.
    Returns the resolved cache_dir path.
    """
    cache_dir = cache_dir.resolve()
    if cache_dir.exists():
        if force:
            shutil.rmtree(cache_dir)
        else:
            return cache_dir

    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    download_config = DownloadConfig(token=hf_token) if hf_token else DownloadConfig()
    dataset_dict = load_dataset(DATASET_ID, download_config=download_config)
    dataset_dict.save_to_disk(str(cache_dir))
    return cache_dir
