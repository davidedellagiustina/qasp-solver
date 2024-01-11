'''Utility functions for simulating quantum circuits.
'''

from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer, AerJob


def __exec_circuit(circ: QuantumCircuit, shots: int = 1) -> AerJob:
    '''Execute a quantum circuit and retrieve the execution result.

    #### Arguments
        circ (QuantumCircuit): Circuit to simulate.
        shots (int): Number of experiment repetitions to simulate. Defaults to 1.

    #### Return
        AerJob: Result of the simulation.
    '''
    simulator = Aer.get_backend('aer_simulator')
    circ = transpile(circ, simulator)
    result = simulator.run(circ, shots=shots).result()
    return result
