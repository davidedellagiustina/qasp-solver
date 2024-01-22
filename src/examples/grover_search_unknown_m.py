'''Find the models of an ASP program using the Grover search algorithm, but without knowing the \
    number M of solutions.
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
    [('p', True), ('q', False), ('r', True)],  # {p, r}
    [('p', False), ('q', True), ('r', True)],  # {q, r}
]


if __name__ == '__main__':
    print(f'ASP program:\n{tab(PRGM.strip(), striplines=True)}\n')
    pause()

    # Program parameters
    N = len(STABLE_MODELS[0])
    print(f'Number of variables: {N}.')
    print()
    pause()

    # Initialization algorithm
    algorithm = qasp.init_algorithm.alg_grover(N)  # Walsh-Hadamard
    print(f'Initialization algorithm:\n{tab(str(algorithm.draw()))}\n')
    pause()

    # Oracle
    oracle = qasp.oracle.from_asp_stable_models(STABLE_MODELS)
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