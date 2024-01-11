lint:
    autopep8 -rd --exit-code ./src
    PYTHONPATH=. pylint ./src
