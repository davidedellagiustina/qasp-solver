python_path := '.'

# Dummy default recipe, just to avoid running undesired commands if no argument is supplied
_default:
    @echo "Run \`just -l' to list the available recipies"

# Run format and lint checks corresponding to those run by the GitHub CI action
ci:
    autopep8 -rd --exit-code ./src
    PYTHONPATH={{python_path}} pylint ./src

# List the available examples
list:
    @ls -lA ./src/examples/ | tail -n +2 | awk '{print $9}' | sed 's/.py//'

# Run a selected example from the examples folder
run example:
    PYTHONPATH={{python_path}} python ./src/examples/{{example}}.py
