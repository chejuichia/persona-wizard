.PHONY: setup dev test clean models bundle

setup:              ## init submodules, install deps, pre-gen sample
	python -m pip install -r requirements.txt || true
	npm --prefix frontend install
	git submodule update --init --recursive || true
	python scripts/prepare_asr_models.py --model tiny --onnx
	python scripts/pre_generate_samples.py

dev:                ## run frontend + backend + foundry local with hot reload
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Foundry Local: http://127.0.0.1:53224"
	@echo "Press Ctrl+C to stop all servers"
	@trap 'kill %1; kill %2; kill %3' INT; \
	scripts/start_services.sh & \
	npm --prefix frontend run dev &

test:               ## run backend + frontend tests
	pytest backend/tests/ -v
	npm --prefix frontend test

models:             ## optional: download TTS/LLM/lip-sync extras
	python scripts/download_models.py

bundle:             ## export latest persona bundle
	python scripts/download_models.py --minimal
	# call builder endpoint or direct script

clean:              ## cleanup data/tmp
	rm -rf data/tmp/* data/outputs/*

help:               ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
