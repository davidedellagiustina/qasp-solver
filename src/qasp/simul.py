'''Utility functions for simulating quantum circuits.
'''

from qiskit import QuantumCircuit, transpile
from qiskit.synthesis import generate_basic_approximations
from qiskit.transpiler.passes.synthesis import SolovayKitaev
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


def transpile_into_clifford_t_basis(
    circ: QuantumCircuit,
    approx_depth: int = 3,
    sk_rec: int = 2,
    opt_lv: int = 3,
) -> QuantumCircuit:
    '''Transpile and decompose a given circuit into the Clifford+T basis.

    #### Arguments
        circ (QuantumCircuit): Quantum circuit to be transpiled.
        approx_depth (int): Gates approximation depth. Defaults to 3.
        sk_rec (int): Recursion degree for the Solovay-Kitaev decomposition algorithm. Defaults to
            2.
        opt_lv (int): Optimization level for the transpiling process. Defaults to 3.

    #### Return
        QuantumCircuit: Transpiled circuit.
    '''
    universal_basis = ['u1', 'u2', 'u3', 'cx']
    clifford_t_basis = ['h', 's', 't']
    basis = generate_basic_approximations(clifford_t_basis, depth=approx_depth)
    skd = SolovayKitaev(recursion_degree=sk_rec, basic_approximations=basis)
    transpiled = transpile(
        circ, basis_gates=universal_basis, optimization_level=opt_lv)
    decomposed = skd(transpiled)
    return decomposed
