.DEFAULT_GOAL := all
isort = python3 -m isort app
black = python3 -m black -S -l 120 --target-version py38 app

.PHONY: format
format:
	$(isort)
	$(black)
