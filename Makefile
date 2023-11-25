
build:
	python -m build

code_artifact_login:
	./twine_aws_login.sh

publish: build code_artifact_login
	python -m twine upload --repository codeartifact dist/*

