'''Dummy example used for testing purposes.
'''

from src.qasp import oracle
from src.qasp.problems import amplification as amp_problem

if __name__ == '__main__':
    # ASP program
    PROG = '''
        p :- not q.
        q :- not p.
        r :- p.
        r :- q.
    '''

    # Oracle
    stable_models = [
        [('p', True), ('q', False), ('r', True)],  # {p,r}
        [('p', False), ('q', True), ('r', True)],  # {q,r}
    ]
    o = oracle.from_asp_stable_models(stable_models)

    # Grover search
    N = len(stable_models[0])
    M = len(stable_models)
    a = amp_problem.alg_grover(N)

    # With known m
    print('\n+---------+\n| Known m |\n+---------+\n')
    result = amp_problem.exec_find_one_known_m(a, o, M)
    print(f'Simulation result ({result[0]} iterations): {result[1]}')

    # With unknown m
    print('\n+-----------+\n| Unknown m |\n+-----------+\n')
    result = amp_problem.exec_find_one_unknown_m(a, o)
    print(f'Simulation result ({result[0]} iterations): {result[1]}')
