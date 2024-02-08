'''Count the number of stable models of an ASP program after some navigation steps, using the QWMC \
circuit.

This example implements Example 5.1.1 in the thesis document, where we use the Quanutm WMC circuit \
to estimate the number of solutions to a program after navigating its solution space using a route \
delta.
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
    {('p', True), ('q', False), ('r', True)},  # {p, r}
    {('p', False), ('q', True), ('r', True)},  # {q, r}
]

# Hardcoded navigation route and relative weight function
DELTA = [('p', True)]
WEIGHTS = [1, 1/2, 1/2]  # Order: p < q < r


def count_fn(phase: float) -> float:
    '''Estimate the number of solutions to PRGM from the value of the estimated phase.

    #### Arguments
        phase (float): Estimated phase.

    #### Return
        float: Estimated number of solutions.
    '''
    n = len(STABLE_MODELS[0])
    k = len(DELTA)
    coeff = 2**(n-k)
    return coeff * 2 * math.sin(phase/2)**2


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

    # Route
    route = ', '.join(
        [('' if value else 'not ') + f'{atom}' for (atom, value) in DELTA]
    )
    print(f'Route delta: <{route}>')
    print()
    pause()

    # Initialization algorithm
    algorithm = qasp.init_algorithm.alg_from_weights(WEIGHTS)  # Rot gate
    print(f'Initialization algorithm:\n{tab(str(algorithm.draw()))}\n')
    pause()

    # Oracle
    oracle = qasp.oracle.from_asp_stable_models(
        STABLE_MODELS, var_order=['p', 'q', 'r'])
    print(f'Quantum oracle:\n{tab(str(oracle[1].draw()))}\n')
    pause()

    # Simulation
    m = 5  # NOTE: This is the only change from `quantum_counting' example
    eps = 1/6
    # pylint: disable=invalid-name
    (circuit, _, M) = qasp.problems.estimation.exec_count(
        algorithm, oracle, m, eps, count_fn=count_fn)
    print(f'Used circuit:\n{tab(str(circuit.draw()))}\n')
    pause()
    print(
        f'Estimated number of solutions: {M.lower:.2f} <= M <= {M.upper:.2f}.')
    print()


if __name__ == '__main__':
    main()
