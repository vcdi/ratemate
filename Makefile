targs = --cov-report term-missing --cov ratemate

check: clean fmt test lint

test:
	pytest $(targs)

lint:
	flake8 .

fmt:
	isort -rc . --skip .venv
	black .

clean:
	find . -name \*.pyc -delete
	rm -rf .cache
