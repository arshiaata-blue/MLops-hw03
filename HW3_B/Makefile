# HW3_B Makefile — orchestrate the 5 scripts.
# Typical first run:   make run   (builds image, starts compose, runs smoke)
# Typical day-2:       make test
# Cleanup:             make clean

PYTHON ?= python
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

IMAGE ?= qbc12-hw03-b-encoder:dev
COMPOSE := docker compose

.PHONY: help all build run stop test smoke load clean

help:
	@echo "Targets:"
	@echo "  make build   - build the HW3_B image (with bundle baked in)"
	@echo "  make run     - start Qdrant + PG + API via compose"
	@echo "  make stop    - stop the compose stack"
	@echo "  make smoke   - curl-based smoke test against running API"
	@echo "  make test    - run pytest (unit tests, no compose needed)"
	@echo "  make load    - concurrent /embed load test"
	@echo "  make all     - build + run + smoke + test"
	@echo "  make clean   - remove bundle symlink, stop compose, prune image"

all: build run smoke test

build:
	bash scripts/01_build_image.sh

run:
	bash scripts/02_run_local.sh

stop:
	$(COMPOSE) down

smoke:
	bash scripts/04_smoke_test.sh

test:
	TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
		PYTHONPATH=. python -m pytest tests/ -v

load:
	bash scripts/05_load_test.sh

clean:
	$(COMPOSE) down -v
	rm -rf bundle
	docker rmi $(IMAGE) 2>/dev/null || true
	@echo "Cleaned."
