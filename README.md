## drau

Caches the Hugging Face dataset `geronimobasso/drone-audio-detection-samples` and provides tools for running acoustic drone-detection tests against external microphone systems.

### Requirements

- Python ≥ 3.11
- PortAudio: `sudo apt-get install libportaudio2` (Debian/Ubuntu) · `brew install portaudio` (macOS)

### Quickstart

```bash
make venv          # create .venv and install dependencies
make cache-data    # download and unpack the dataset (~6.6 GB)
make run-session SAMPLES=20 MICS=2 DIST_MAX=150
```

Run `make help` for all available targets and examples.

### Secrets

Copy `.env.example` to `.env` and set `HF_TOKEN` if the dataset requires authentication.
