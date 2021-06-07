test:
	pytest

lint:
	pylint ./tests ./ansible_specdoc

.PHONY: lint test