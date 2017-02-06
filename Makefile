
DOCKER_IMAGE=elasticsearch:5.1.2

setup:
	pip install -r requirements-dev.txt
	pip install -Ue .

flake:
	flake8 asynces tests 

test: flake
	pytest -s --no-print-logs --docker-image $(DOCKER_IMAGE) $(FLAGS) tests

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -rf docs/_build/
	rm -rf cover
	rm -rf build
	rm -rf dist
