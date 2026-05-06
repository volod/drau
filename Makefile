SHELL  := /usr/bin/env bash
PYTHON := .venv/bin/python

.DEFAULT_GOAL := help
.PHONY: help venv venv-clean install cache-data run-session analyse

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@printf "drau — drone audio detection test toolkit\n\n"
	@printf "Usage: make <target> [VAR=value ...]\n\n"
	@printf "  %-22s %s\n" "venv"        "Create .venv and install requirements"
	@printf "  %-22s %s\n" "venv-clean"  "Delete and recreate .venv"
	@printf "  %-22s %s\n" "install"     "Re-install requirements into existing .venv"
	@printf "  %-22s %s\n" "cache-data"  "Download and unpack drone audio dataset (~6.6 GB)"
	@printf "  %-22s %s\n" "run-session" "Run detection test then auto-analyse results"
	@printf "  %-22s %s\n" ""            "  Required: SAMPLES=<n>  MICS=<n>  DIST_MAX=<m>"
	@printf "  %-22s %s\n" "analyse"     "Analyse a session CSV"
	@printf "  %-22s %s\n" ""            "  Required: CSV=<path>"
	@printf "\nExamples:\n"
	@printf "  make venv\n"
	@printf "  make cache-data\n"
	@printf "  make run-session SAMPLES=20 MICS=2 DIST_MAX=30\n"
	@printf "  make analyse CSV=.data/detection-tests/session_20240101_120000.csv\n"

# ── Environment ───────────────────────────────────────────────────────────────

venv:
	@bash scripts/setup.sh

venv-clean:
	@bash scripts/setup.sh --recreate

install:
	@test -d .venv || { echo "Run 'make venv' first."; exit 1; }
	$(PYTHON) -m pip install -e . -q
	@echo "Requirements installed."

# ── Data ──────────────────────────────────────────────────────────────────────

cache-data:
	@bash scripts/cache_audio_data.sh

# ── Detection test ────────────────────────────────────────────────────────────

run-session:
ifndef SAMPLES
	$(error SAMPLES is required — usage: make run-session SAMPLES=20 MICS=2 DIST_MAX=30)
endif
ifndef MICS
	$(error MICS is required — usage: make run-session SAMPLES=20 MICS=2 DIST_MAX=30)
endif
ifndef DIST_MAX
	$(error DIST_MAX is required — usage: make run-session SAMPLES=20 MICS=2 DIST_MAX=30)
endif
	@bash scripts/run_session.sh --samples-num $(SAMPLES) --mic-num $(MICS) \
	  --dist-max $(DIST_MAX) --audio-duration-min 2; \
	 code=$$?; [ $$code -eq 130 ] && exit 0 || exit $$code

analyse:
ifndef CSV
	$(error CSV is required — usage: make analyse CSV=.data/detection-tests/session_xxx.csv)
endif
	@bash scripts/analyse_detection.sh $(CSV)
