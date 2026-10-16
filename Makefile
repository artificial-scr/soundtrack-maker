# Shortcuts for the common workflows. Run `make` or `make help` to see them.
#
# Variables (override on the command line, e.g. `make level LEVEL=volcano SEEDS=9-20`):
#   LEVEL   level name, comma-separated list, or all     (see `make list`)
#   SEEDS   seed range or list, e.g. 1-8 or 1,4,7          (default 1-8)
#   CUES    limit to some cues, e.g. action or calm,boss   (default: all cues of the level)
#   JOBS    parallel worker processes                      (default: limited by CPUs and free RAM)
#   PICK    for `make export`: LEVEL:SEED or LEVEL.CUE:SEED, space-separated
#   OUT     for `make export`: destination folder          (default export/)
#   WAV     for `make export`: set WAV=1 to copy the WAV masters too

PY    := .venv/bin/python
SEEDS ?= 1-8
LEVEL ?=
CUES  ?=
JOBS  ?=
PICK  ?=
OUT   ?=
WAV   ?=

GEN_ARGS = --seeds $(SEEDS) $(if $(CUES),--cues $(CUES)) $(if $(JOBS),--jobs $(JOBS))

.DEFAULT_GOAL := help
.PHONY: help setup list music level check check-full test export clean venv

help:  ## show this help
	@echo "Usage: make <target> [LEVEL=...] [SEEDS=...] [CUES=...] [JOBS=...]"
	@echo
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-11s %s\n", $$1, $$2}'
	@echo
	@echo "Examples:"
	@echo "  make level LEVEL=volcano SEEDS=1-20"
	@echo "  make export PICK=\"volcano:3 keep.boss:7\""

setup:  ## one-time setup: venv, Python packages, soundfont
	@scripts/setup.sh

venv:
	@test -x $(PY) || { echo "Run 'make setup' first."; exit 1; }

list: venv  ## list levels, keys, tempos and cues
	@$(PY) -m render.make_stems --list

music: venv  ## generate SEEDS for every level (all cues)
	$(PY) -m render.make_stems --area all $(GEN_ARGS)

level: venv  ## generate SEEDS for LEVEL (required)
	@test -n "$(LEVEL)" || { echo "usage: make level LEVEL=volcano [SEEDS=1-8] [CUES=action]"; exit 2; }
	$(PY) -m render.make_stems --area $(LEVEL) $(GEN_ARGS)

check: venv  ## technical checks on built stems (LEVEL optional, default all)
	$(PY) -m checks.run --area $(or $(LEVEL),all) $(if $(filter command line,$(origin SEEDS)),--seeds $(SEEDS))

check-full: venv  ## checks plus a rebuild-and-compare determinism test
	$(PY) -m checks.run --area $(or $(LEVEL),all) --determinism

test: venv  ## unit tests
	$(PY) -m pytest -q tests

export: venv  ## copy chosen seeds to OUT with stable names, e.g. PICK="volcano:3"
	@test -n "$(PICK)" || { echo "usage: make export PICK=\"volcano:3 meadow.action:5\" [OUT=path] [WAV=1]"; exit 2; }
	$(PY) -m render.export $(PICK) $(if $(OUT),--out $(OUT)) $(if $(WAV),--wav)

clean:  ## remove Python caches (never touches stems/ or export/)
	find . -path ./.venv -prune -o -type d \( -name __pycache__ -o -name .pytest_cache \) -print -exec rm -rf {} +
