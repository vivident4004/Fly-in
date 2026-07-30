#MAP = ./maps/custom/02_feedback_loop_puzzle.txt
MAP = ./maps/easy/02_simple_fork.txt

install:
	uv sync

run:
	uv run python -m src

bonus:
	uv run python -m src --ws

bonus-plot:
	uv run python -m src --plot

debug:
	uv run python -m pdb -m src $(MAP)

clean:
	rm -rf __pycache__ */__pycache__ .mypy_cache .ruff_cache

lint:
	uv run flake8 src/
	uv run mypy src/

lint-strict:
	uv run flake8 src/
	uv run mypy src/ --strict

ruff:
	uv run ruff check .
	uv run ruff format --check .

ty:
	uv run ty check src/

format:
	uv run ruff format .

.PHONY: install run debug bonus bonus-plot clean lint lint-strict ruff ty format
