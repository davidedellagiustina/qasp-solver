'''Find the models of an ASP program using the naive Grover search algorithm.
'''

from src import qasp

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


def pause():
    '''Pause the program execution and wait for the user to press a key to continue.
    '''
    _ = input("Press the <ENTER> key to continue...")
    print()


def tab(lines: str, striplines: bool = False) -> str:
    '''Return a variant of the input string indented by one level.

    #### Arguments
        lines (str): Lines to be indented.
        striplines (bool): Whether to strip() individual lines before re-joining. Defaults to False.

    #### Return
        str: Indented variant of the provided string.
    '''
    return '\n'.join([
        '    ' + (line.strip() if striplines else line)
        for line in lines.splitlines(False)
    ])


if __name__ == '__main__':
    print(f'ASP program:\n{tab(PRGM.strip(), striplines=True)}\n')
    pause()

    # Program parameters
    N = len(STABLE_MODELS[0])
    M = len(STABLE_MODELS)
    print(f'Number of variables: {N}.')
    print(f'Number of stable models: {M}.')
    print()
    pause()

    # Initialization algorithm
    algorithm = qasp.problems.amplification.alg_grover(N)  # Walsh-Hadamard
    print(f'Initialization algorithm:\n{tab(str(algorithm.draw()))}\n')
    pause()

    # Oracle
    oracle = qasp.oracle.from_asp_stable_models(STABLE_MODELS)
    print(f'Quantum oracle:\n{tab(str(oracle[1].draw()))}\n')
    pause()

    # Simulation
    (circuit, iters, stable_model) = qasp.problems.amplification.exec_find_one_known_m(
        algorithm, oracle, M)
    print(f'Circuit:\n\n{circuit.draw()}')
    pause()
    print(f'Found stable model: {stable_model}.')
    print(f'Number of iterations: {iters}.')
    print()
