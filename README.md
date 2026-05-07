## drau

Caches the Hugging Face dataset `geronimobasso/drone-audio-detection-samples` and provides tools for running acoustic drone-detection tests against external microphone systems.

### Requirements

- Python ≥ 3.11
- PortAudio — installed automatically by `make venv` on Debian/Ubuntu; on macOS: `brew install portaudio`

### Quickstart

Copy `.env.example` to `.env` and set `HF_TOKEN` if the dataset requires authentication.

```bash
cp .env.example .env
nano .env
```

Create a token at https://huggingface.co/settings/tokens, set and save:

```
HF_TOKEN=hf_****************
```

Then:

```bash
make venv          # create .venv, install dependencies, and install libportaudio2
make cache-data    # download and unpack the dataset (~6.6 GB)
```

Run `make help` for all available targets and examples.

### run-session

Runs a calibrated detection test session and auto-analyses the results.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `SAMPLES` | yes | Number of audio samples to play |
| `MICS` | yes (unless `PLAY_SAMPLE=1`) | Number of microphone systems under test |
| `DIST_MAX` | yes | Maximum simulated drone distance in metres |
| `PLAY_SAMPLE` | no | Play samples continuously without collecting results |

```bash
# Full detection test session
make run-session SAMPLES=20 MICS=2 DIST_MAX=150

# Play-only preview — no mic input or CSV written
make run-session SAMPLES=20 DIST_MAX=100 PLAY_SAMPLE=1
```

Play-only mode uses the same 50/50 drone/non-drone selection and distance simulation as a full session, but auto-advances through samples without waiting for mic identefication input.
