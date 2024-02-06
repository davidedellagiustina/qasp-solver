'''Grover Search with a quantum oracle built from the classical procedure.

Example 4.2.1 in the thesis shows how to build a quantum oracle for a trivial ASP program using the
classical procedure. This example applies the Grover Search algorithm in order to demonstrate the
correctness of the built operator.
'''

import copy
from qiskit import QuantumCircuit, QuantumRegister
from src import qasp
from src.examples.util import tab, pause

# ASP program
PRGM = '''
    p :- not q.
    q.
'''


def build_oracle() -> tuple[qasp.oracle.Oracle, list[int]]:
    '''Build the quantum oracle shown in Example 4.1.1 in the thesis.

    #### Return
        tuple[QuantumCircuit, list[int]]: Circuit implementing the oracle and list of auxiliary \
            qubits used.
    '''
    # Build classical oracle
    def c_oracle(interp):
        m_p = {
            ('p', not ('q', True) in interp),
            ('q', True),
        }
        return interp == m_p

    # Build quantum oracle
    (p, q) = (QuantumRegister(1, 'p'), QuantumRegister(1, 'q'))
    p_if_not_q = QuantumRegister(1, 'p_if_not_q')
    p_in_reduct = QuantumRegister(1, 'p_in_reduct')
    q_in_reduct = QuantumRegister(1, 'q_in_reduct')
    p_equal = QuantumRegister(1, 'p_equal')
    q_equal = QuantumRegister(1, 'q_equal')
    equal = QuantumRegister(1, 'equal')
    q_oracle = QuantumCircuit(p, q, p_if_not_q, p_in_reduct,
                              q_in_reduct, p_equal, q_equal, equal, name='Oracle')
    aux_qubits = list(range(2, 8))

    # Step 1
    q_oracle.x(p_if_not_q)
    q_oracle.cx(q, p_if_not_q)
    q_oracle.barrier()

    # Step 2
    q_oracle.cx(p_if_not_q, p_in_reduct)
    q_oracle.x(q_in_reduct)
    q_oracle.barrier()

    # Step 3
    q_oracle.ccx(p, p_in_reduct, p_equal)
    q_oracle.ccx(p, p_in_reduct, p_equal, ctrl_state='00')
    q_oracle.ccx(q, q_in_reduct, q_equal)
    q_oracle.ccx(q, q_in_reduct, q_equal, ctrl_state='00')
    q_oracle.barrier()

    undo = copy.deepcopy(q_oracle).reverse_ops()

    # Step 4
    q_oracle.x(equal)
    q_oracle.h(equal)
    q_oracle.ccx(p_equal, q_equal, equal)
    q_oracle.h(equal)
    q_oracle.x(equal)
    q_oracle.barrier()

    # Undo steps
    q_oracle.compose(undo, q_oracle.qubits, inplace=True)

    return ((c_oracle, q_oracle), aux_qubits)


def main():
    '''Entrypoint.
    '''
    print(f'ASP program:\n{tab(PRGM.strip(), striplines=True)}\n')
    pause()

    # Program parameters
    n = 2
    n_aux = 6  # Number of auxiliary qubits
    m = 1
    print(f'Number of variables: {n}.')
    print(f'Number of stable models: {m}.')
    print()
    pause()

    # Initialization algorithm
    algorithm = qasp.init_algorithm.alg_grover(n)  # Walsh-Hadamard
    aux_reg = QuantumRegister(n_aux, 'aux')
    algorithm.add_register(aux_reg)
    algorithm.name += ' x Id'
    print(f'Initialization algorithm:\n{tab(str(algorithm.draw()))}\n')
    pause()

    # Oracle
    (oracle, aux_qubits) = build_oracle()
    print(f'Quantum oracle:\n{tab(str(oracle[1].draw()))}\n')
    pause()

    # Simulation
    (circuit, iters, stable_model) = qasp.problems.amplification.exec_find_one_known_m(
        algorithm, oracle, m, aux_qubits)
    print(f'Used circuit:\n{tab(str(circuit.draw()))}\n')
    pause()
    print(f'Found stable model: {stable_model}.')
    print(f'Number of iterations: {iters}.')
    print()


if __name__ == '__main__':
    main()
