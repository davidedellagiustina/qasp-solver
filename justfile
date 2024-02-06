python_path := '.'

_default:
    @ just -l

# Run format and lint checks corresponding to those run by the GitHub CI action
ci:
    autopep8 -rd --exit-code ./src
    PYTHONPATH={{python_path}} pylint ./src

# List the available examples
list:
    @ ls -lA ./src/examples/ | tail -n +2 | awk '{print $9}' | sed 's/\.py//' | sed '/__/d'

# Run a selected example from the examples folder
run example:
    @ ( \
        export PYTHONPATH={{python_path}}; \
        export NAME=`echo {{example}} | sed 's/\.py//'`; \
        python ./src/examples/$NAME.py \
    )
