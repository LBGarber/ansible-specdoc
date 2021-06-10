test:
	pytest

lint:
	pylint ./tests ./ansible_specdoc

build:
	python setup.py build && python -m build

clean_dist:
	python setup.py clean --dist

.PHONY: lint test build