PYTHON_MODULE = tornado_retry_client

clean:
	find . -name "*.pyc" -exec rm '{}' ';'

test: test_unit flake8

test_unit:
	python setup.py test
	rm -Rf .coverage

flake8:
	flake8 ${PYTHON_MODULE}.py
	flake8 tests/

autopep8:
	autopep8 -r -i ${PYTHON_MODULE}.py
	autopep8 -r -i tests/

upload:
	python ./setup.py sdist upload -r pypi
