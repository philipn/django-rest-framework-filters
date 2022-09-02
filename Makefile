
build:
	python -m build

publish: build
	python -m twine upload --repository ubidots dist/*