'''Count the number of stable models of an ASP program using the naive Quantum Counting algorithm.

Example 4.1.2 in the thesis shows how to use the Quantum Counting algorithm to count the stable \
models of a given ASP program. This example implements that technique.
'''

import math
from src import qasp
from src.examples.util import tab, pause

# ASP program
PRGM = '''
    p :- not q.
    q :- not p.
    r :- p.
    r :- q.
'''

# Hardcoded list of stable models
STABLE_MODELS = [
    [('p', True), ('q', False), ('r', True)],  # {p, r}
    [('p', False), ('q', True), ('r', True)],  # {q, r}
]


def main():
    '''Entrypoint.
    '''
    print(f'ASP program:\n{tab(PRGM.strip(), striplines=True)}\n')
    pause()

    # Program parameters
    n = len(STABLE_MODELS[0])
    print(f'Number of variables: {n}.')
    print()
    pause()

    # Initialization algorithm
    algorithm = qasp.init_algorithm.alg_grover(n)  # Walsh-Hadamard
    print(f'Initialization algorithm:\n{tab(str(algorithm.draw()))}\n')
    pause()

    # Oracle
    oracle = qasp.oracle.from_asp_stable_models(
        STABLE_MODELS, var_order=['p', 'q', 'r'])
    print(f'Quantum oracle:\n{tab(str(oracle[1].draw()))}\n')
    pause()

    # Simulation
    m = math.ceil(n/2)
    eps = 1/6
    # pylint: disable=invalid-name
    (circuit, _, M) = qasp.problems.estimation.exec_count(algorithm, oracle, m, eps)
    print(f'Used circuit:\n{tab(str(circuit.draw()))}\n')
    pause()
    print(
        f'Estimated number of solutions: {M.lower:.2f} <= M <= {M.upper:.2f}.')
    print()


if __name__ == '__main__':
    main()