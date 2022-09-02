# Steps required to publish the package to pypi

## Install required dependencies

    python3 -m pip install --upgrade pip
    python3 -m pip install --upgrade build
    python3 -m pip install --upgrade twine

## Edit file ~/.pypirc with

    [distutils]
        index-servers =
            ubidots

    [ubidots]
    repository = http://169.53.160.59:8080
    username = ubidots_dev
    password = $UBIDOTS_PYPI_PASSWORD

* Replace $UBIDOTS_PYPI_PASSWORD with the pypi server password of the user ubidots_dev.

## To build the library

    python3 -m build

## To upload the library to the pypi server

    python3 -m twine upload --repository ubidots dist/*
