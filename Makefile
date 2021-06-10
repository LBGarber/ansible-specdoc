test:
	pytest

lint:
	pylint ./tests ./ansible_specdoc

build:
	python setup.py build && python -m build

clean:
	python setup.py clean --all

.PHONY: lint test build