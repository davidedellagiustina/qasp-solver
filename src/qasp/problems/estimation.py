'''Amplitude estimation algorithms.
'''

import copy
import math
from typing import Callable
import intervals as interval
from intervals import Interval
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import GroverOperator, QFT
from ..oracle import Oracle, QuantumOracle
from ..simul import exec_circuit


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
    # pylint: disable=too-many-locals

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
        c_pow_g = copy.deepcopy(pow_g).control()
        circ.compose(c_pow_g, [t-idx-1] + list(range(t, t+n)), inplace=True)
        # Next power of G
        pow_g.compose(pow_g, pow_g.qubits, inplace=True)
        pow_g.name = f'Q^(2^{idx+1})'

    # Inverse QFT
    # NOTE: Qiskit's QFT has the opposite bit order w.r.t. the one used in the thesis, hence why \
    #       we disable the swaps.
    iqft = QFT(t, inverse=True, do_swaps=False)
    circ.append(iqft, qr0)

    # Measurements
    result = ClassicalRegister(m, name='result')
    circ.add_register(result)
    circ.measure(list(range(t-m, t)), result)  # Only requested m bits

    return circ


# +-----------------------+
# | Algoroithm simulation |
# +-----------------------+

def __phase_to_count(n: int, phase: float) -> float:
    '''Compute the number M of solutions of a search problem given an estimate of the rotation \
        angle phi of the respective Grover Operator.

    #### Arguments
        N (int): Number of search qubits.
        phase (float): Estimate value of the phase phi.

    #### Return
        float: Estimated value of M.
    '''
    return 2**n * math.sin(phase/2)**2


def __measure_to_count(
    measurements: str,
    num_search_qubits: int,
    count_fn: Callable[[float], float] = None
) -> tuple[Interval, Interval]:
    '''Convert the result of a measurement to estimation intervals for the respective phase and \
        for the solutions count.

    #### Arguments
        measurements (str): Measured bits.
        num_search_qubits (int): Number of search qubits.
        count_fn (Callable[[float], float]): Function that, given an estimate for phi, computes \
            the solutions count (or any other needed value). Defaults to N * sin^2(theta/2).

    #### Return
        tuple[Interval, Interval]: Estimation intervals for the measured phase and the solutions \
            count, respectively.
    '''
    count_fn = (
        lambda phase: __phase_to_count(num_search_qubits, phase)
    ) if count_fn is None else count_fn

    m = len(measurements)
    phi = 0.0
    for (idx, bit) in zip(range(m), measurements):
        phi += int(bit) * 2**(-idx-1)
    phases = [2 * math.pi * (phi + delta) for delta in [0, 2**(-m)]]

    if phi <= 1/2:  # If theta was measured
        interval_type = interval.closedopen
    else:  # If (2 pi - theta) was measured
        interval_type = interval.openclosed
        phases = [2 * math.pi - phase for phase in reversed(phases)]

    phase_estimate = interval_type(phases[0], phases[1])
    counts = [count_fn(phase) for phase in phases]
    count_estimate = interval_type(counts[0], counts[1])

    return (phase_estimate, count_estimate)


def exec_count(
    algorithm: QuantumCircuit,
    oracle: Oracle,
    m: int,
    eps: float,
    aux_qubits: list[int] = None,
    count_fn: Callable[[float], float] = None
) -> tuple[QuantumCircuit, Interval, Interval]:
    '''Simulate the amplitude estimation circuit to approximate the number of solutions of the \
        problem.

    #### Arguments
        algorithm (QuantumCircuit): Ciruit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        m (int): Desired number of binary digits to be estimated.
        eps (float): Complement of the desired success probability.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.
        count_fn (Callable[[float], float]): Function that, given an estimate for phi, computes \
            the solutions count (or any other needed value). Defaults to N * sin^2(theta/2).

    #### Return
        tuple[QuantumCircuit, Interval, Interval]: Used circuit, estimation interval for the \
            measured phase, and estimation interval for the solutions count.
    '''
    # pylint: disable=too-many-arguments

    aux_qubits = [] if aux_qubits is None else aux_qubits
    (_, q_oracle) = oracle  # Classical oracle is unused

    n = len(q_oracle.qubits) - len(aux_qubits) + 1  # Account for `aug`

    # Build circuit
    circ = circuit(algorithm, q_oracle, m, eps, aux_qubits)

    # Run simulation and compute results
    result = exec_circuit(circ, shots=1)
    measurements = list(result.get_counts().keys())[0]
    (phase, count) = __measure_to_count(measurements, n, count_fn)

    return (circ, phase, count)
