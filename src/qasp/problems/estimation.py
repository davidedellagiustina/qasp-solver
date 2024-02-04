'''Amplitude estimation algorithms.
'''

import copy
import math
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import GroverOperator, QFT
from ..oracle import Oracle, QuantumOracle
from ..simul import __exec_circuit


# +--------------------+
# | Estimation circuit |
# +--------------------+

def circuit(
    algorithm: QuantumCircuit,
    oracle: QuantumOracle,
    m: int,
    eps: float,
    aux_qubits: list[int] = None
) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude estimation algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Ciruit that implements the initialization algorithm.
        oracle (QuantumOracle): Citcuit that implements the oracle.
        m (int): Desired number of binary digits to be estimated.
        eps (float): Complement of the desired success probability.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.

    #### Return
        QuantumCircuit: Built circuit.
    '''
    aux_qubits = [] if aux_qubits is None else aux_qubits

    assert m > 0 and eps > 0
    assert algorithm.num_qubits == oracle.num_qubits

    n = algorithm.num_qubits + 1  # Also counting `aug` qubit
    t = m + math.ceil(math.log2(2 + 1/(2*eps)))

    # Add `aug` qubit to algorithm
    algorithm.name = 'AlgorithmAug'
    aug = QuantumRegister(1, 'aug')
    algorithm.add_register(aug)
    algorithm.h(aug)  # Equiprobable superposition
    assert algorithm.num_qubits == n

    # Add `aug` qubit to oracle
    c_oracle = oracle.control()
    c_oracle.name = 'OracleAug'
    oracle.data = []
    aug = QuantumRegister(1, 'aug')
    oracle.add_register(aug)
    oracle.compose(
        c_oracle,
        [n-1] + list(range(n-1)),
        inplace=True,
    )
    assert oracle.num_qubits == n

    # Circuit structure
    qr0 = QuantumRegister(t)
    qr_others = list(  # Clone qubit labels from oracle
        dict.fromkeys(  # Remove duplicates while maintaining order
            map(lambda q: oracle.find_bit(q).registers[0][0], oracle.qubits)
        )
    )
    circ = QuantumCircuit(qr0, *qr_others)
    circ.name = 'Est'

    # Qubit partitioning
    qubits_search = list(filter(
        lambda x: not x in aux_qubits,
        list(range(n))
    ))

    # Initialization
    circ.h(qr0)
    circ.append(algorithm, qr_others)

    # Iterations
    pow_g = GroverOperator(
        oracle, state_preparation=algorithm, reflection_qubits=qubits_search)
    pow_g.name = 'Q^(2^0)'
    for idx in range(t):
        ctrl = t - idx - 1
        c_pow_g = copy.deepcopy(pow_g).control()
        circ.compose(c_pow_g, [ctrl] +
                     list(range(t, t+n)), inplace=True)
        # Next power of G
        pow_g.compose(pow_g, pow_g.qubits, inplace=True)
        pow_g.name = f'Q^(2^{idx+1})'

    # Inverse QFT
    iqft = QFT(t, inverse=True)
    circ.append(iqft, qr0)

    # Measurements
    result = ClassicalRegister(m, name='result')
    circ.add_register(result)
    circ.measure(list(range(t-m, t)), result)  # Only m bits

    return circ


# +-----------------------+
# | Algoroithm simulation |
# +-----------------------+

def __measure_to_count(measurements: str, num_search_qubits: int) -> tuple[float, int]:
    '''Convert the result of a measurement to to actual phase factor and the resulting solutions \
        count.

    #### Arguments
        measurements (str): Measured bits.
        num_search_qubits (int): Number of search qubits.

    #### Return
        tuple[float, int]: Phase factor and solutions count.
    '''
    phi = 0.0
    for (idx, bit) in zip(range(len(measurements)), measurements):
        phi += int(bit) * 2**(-idx-1)
    print(measurements, phi)
    phase = 2 * math.pi * phi
    count = 2**num_search_qubits * (math.sin(phase / 2))**2

    return (phase, count)


def exec_count(
    algorithm: QuantumCircuit,
    oracle: Oracle,
    m: int,
    eps: float,
    aux_qubits: list[int] = None
) -> tuple[QuantumCircuit, float, int]:
    '''Simulate the amplitude estimation circuit to approximate the number of solutions of the \
        problem.

    #### Arguments
        algorithm (QuantumCircuit): Ciruit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        m (int): Desired number of binary digits to be estimated.
        eps (float): Complement of the desired success probability.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.

    #### Return
        tuple[QuantumCircuit, float, int]: Used circuit, measured phase, and estimated number \
            of solutions.
    '''
    aux_qubits = [] if aux_qubits is None else aux_qubits
    (_, q_oracle) = oracle  # Classical oracle is unused

    n = len(q_oracle.qubits) - len(aux_qubits) + 1  # Account for `aug`

    # Build circuit
    circ = circuit(algorithm, q_oracle, m, eps, aux_qubits)

    # Run simulation
    result = __exec_circuit(circ, shots=10000)
    measurements = list(result.get_counts(circ).keys())[0]
    print(result.get_counts())

    # Compute results
    (phase, count) = __measure_to_count(measurements, n)

    return (circ, phase, count)
