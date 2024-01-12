'''Amplitude estimation algorithms.
'''

from qiskit import QuantumCircuit
from ..oracle import QuantumOracle


# +--------------------+
# | Estimation circuit |
# +--------------------+

def circuit(algorithm: QuantumCircuit, oracle: QuantumOracle, t: int) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude estimation algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Ciruit that implements the initialization algorithm.
        oracle (QuantumOracle): Citcuit that implements the oracle.
        t (int): Number of decimal (binary) digits to estimate.

    #### Return
        QuantumCircuit: Built circuit.
    '''
    assert t > 0
    assert algorithm.num_qubits == oracle.num_qubits
    # TODO
