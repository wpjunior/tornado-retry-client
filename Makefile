PYTHON_MODULE = tornado_retry_client
.PHONY: setup clean test test_unit flake8 autopep8 upload

setup:
	pip install -e .\[tests\]

clean:
	find . -name "*.pyc" -exec rm '{}' ';'

coverage:
	@coverage report -m --fail-under=10

unit test:
	@coverage run --branch `which nosetests` -v --with-yanc -s tests/
	$(MAKE) coverage
	$(MAKE) flake8

flake8:
	flake8 ${PYTHON_MODULE}
	flake8 tests/

autopep8:
	autopep8 -r -i ${PYTHON_MODULE}
	autopep8 -r -i tests/

upload:
	python ./setup.py sdist upload -r pypi

bump bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

bump_major:
	bumpversion minor
