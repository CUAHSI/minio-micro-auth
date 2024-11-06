.DEFAULT_GOAL := all
isort = python3 -m isort api
black = python3 -m black -S -l 120 --target-version py38 api

.PHONY: format
format:
	$(isort)
	$(black)
