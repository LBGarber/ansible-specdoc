test:
	pytest

lint:
	pylint ./tests ./ansible_specdoc

build:
	python -m build

.PHONY: lint test build