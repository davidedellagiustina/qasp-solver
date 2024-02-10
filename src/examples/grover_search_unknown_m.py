'''Find the stable models of an ASP program using QSearch on the naive Grover Search algorithm, \
without requiring the number M of solutions to be known in advance.

Reference: Example 5.2.1 in the thesis.
'''

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
    (circuits, iters, stable_model) = qasp.problems.amplification.exec_find_one_unknown_m(
        algorithm, oracle)
    print('All used circuits:')
    for circuit in circuits:
        print(f'{tab(str(circuit.draw()))}\n')
    pause()
    print(f'Found stable model: {stable_model}.')
    print(f'Number of iterations: {iters}.')
    print()


if __name__ == '__main__':
    main()
