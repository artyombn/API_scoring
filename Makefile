startlinters:
	black . --exclude '\.venv|test_unittest\.py'
	isort . --skip .venv --skip test_unittest.py
	pylint . --ignore=.venv,test_unittest.py
	mypy . --exclude '(\.venv|test_unittest\.py)'

startpytest:
	pytest -s -v