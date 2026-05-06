# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules

- Never create git commits.
- Never use `from __future__ import annotations`.
- Never put Python files in `scripts/` and never embed inline Python inside shell scripts. All Python logic belongs in `src/drau/` (or a subpackage of it); shell scripts only invoke `python -m drau.<module>`.

## Setup

```bash
make venv      # or: bash scripts/setup.sh [--recreate]
```

Copy `.env.example` to `.env` and set `HF_TOKEN` (optional for public datasets).
`pyproject.toml` is the single source of truth for all dependencies.

## Commands

Primary interface: `make help`.  Direct script access (each script self-installs via `pip install -e .`):

```bash
./scripts/cache_audio_data.sh
./scripts/run_session.sh --samples-num N --mic-num N --dist-max N
./scripts/analyse_detection.sh <csv-path>
```

## Architecture

`src/drau/` top-level modules:

- `env.py` — loads `.env`, exposes frozen `Settings` dataclass (`hf_token`).
- `cache_audio_data.py` — downloads the HF dataset, saves Arrow files via `DatasetDict.save_to_disk()`. Skips if directory exists.
- `unpack_audio_data.py` — writes raw WAV bytes from Arrow into `drone-audio/` and `non-drone-audio/` subdirs. Skips if both dirs are populated.
- `analyse_detection.py` — reads a session CSV and prints accuracy / precision / recall / F1 / FPR / FNR tables per mic, per distance grade, and per sound class.

`src/drau/detection_test/` subpackage (`python -m drau.detection_test`):

- `calibrate.py` — plays a 1 kHz tone and records the computer mic to establish a `Calibration` (reference scale for distance-gain math).
- `player.py` — loads WAV via stdlib `wave`, normalises RMS, applies inverse-distance gain, plays via `sounddevice`.
- `sampler.py` — picks N files with a 50/50 drone/non-drone split.
- `form.py` — rich terminal UI: shows sample info panel, collects y/n per mic.
- `run.py` — orchestrates calibration → sample loop → CSV write.
- `__main__.py` — CLI entry point (`--samples-num`, `--mic-num`, `--dist-max`).

All audio is 16 kHz mono 16-bit PCM (native dataset rate); no resampling is needed.  
Session CSVs are written to `.data/detection-tests/session_YYYYMMDD_HHMMSS.csv`.  
System dependency: `libportaudio2` (`sudo apt-get install libportaudio2`).
