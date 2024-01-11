'''Initialization algorithms for amplitude-related problems.
'''

import math
from qiskit import QuantumCircuit


def alg_grover(n: int) -> QuantumCircuit:
    '''Return an instance of the Grover initialization algorithm.

    #### Arguments
        n (int): Number of search qubits.

    #### Return
        QuantumCircuit: Built circuit.
    '''
    circ = QuantumCircuit(n)
    circ.name = 'WH'
    circ.h(circ.qubits)
    return circ


def alg_from_weights(weights: list[float]) -> QuantumCircuit:
    '''Return an instance of the Rot initialization algorithm defined by Riguzzi.

    #### Arguments
        weights(list[float]): Weight of each bit evaluating to 1. Complementary is computed \
            assuming normalization constraint.

    #### Return
        QuantumCircuit: Built circuit.
    '''
    n = len(weights)
    circ = QuantumCircuit(n)
    circ.name = 'Rot'

    for (i, weight) in zip(range(n), weights):
        theta = 2 * math.acos(math.sqrt(1 - weight))
        circ.ry(theta, i)

    return circ
