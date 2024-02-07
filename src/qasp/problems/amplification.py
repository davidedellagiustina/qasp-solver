'''Amplitude amplification algorithms.
'''

import copy
import math
import random
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import GroverOperator
from ..oracle import Interpretation, QuantumOracle, Oracle
from ..simul import exec_circuit


# +-----------------------+
# | Amplification circuit |
# +-----------------------+

def __optimal_num_iters(n: int, m: int) -> int:
    '''Return the optimal number of iterations for amplitude amplification.
    Source: \
        https://github.com/Qiskit/qiskit/blob/stable/0.45/qiskit/algorithms/amplitude_amplifiers/grover.py#L381.

    #### Arguments
        n (int): Number of search qubits.
        m (int): (Known) number of solutions to the problem.

    #### Return
        int: Optimal number of iterations.
    '''
    amplitude = math.sqrt(m / 2**n)
    return round(math.acos(amplitude) / (2 * math.asin(amplitude)))


def circuit_optimal(
    algorithm: QuantumCircuit,
    oracle: QuantumOracle,
    m: int,
    aux_qubits: list[int] = None
) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude amplification algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (QuantumOracle): Circuit that implements the oracle.
        m (int): (Known) number of solutions.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.

    #### Returns
        QuantumCircuit: Built circuit.
    '''
    aux_qubits = [] if aux_qubits is None else aux_qubits

    assert algorithm.num_qubits == oracle.num_qubits
    assert len(aux_qubits) <= algorithm.num_qubits

    n = algorithm.num_qubits - len(aux_qubits)  # Search qubits only
    inc = m > 2**(n-1)
    num_iters = __optimal_num_iters(n, m)

    return circuit(algorithm, oracle, num_iters, inc, aux_qubits)


def circuit(
    algorithm: QuantumCircuit,
    oracle: QuantumOracle,
    num_iters: int,
    inc: bool = False,
    aux_qubits: list[int] = None
) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude amplification algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (QuantumOracle): Circuit that implements the oracle.
        num_iters (int): Number of iterations to perform.
        inc (bool): Whether to use an additional qubit for searching (necessary if m > n/2). \
            Defaults to False.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.

    #### Returns
        QuantumCircuit: Built circuit.
    '''
    aux_qubits = [] if aux_qubits is None else aux_qubits

    assert algorithm.num_qubits == oracle.num_qubits
    assert len(aux_qubits) <= algorithm.num_qubits

    n_all = algorithm.num_qubits
    n_aux = len(aux_qubits)
    n_search = n_all - n_aux

    # Add a qubit if there are too many solutions
    if inc:
        n_all += 1
        n_search += 1

        # Algorithm
        algorithm.name = 'AlgorithmAug'
        aug = QuantumRegister(1, 'aug')
        algorithm.add_register(aug)
        algorithm.h(aug)  # Equiprobable superposition
        assert algorithm.num_qubits == n_all

        # Oracle
        c_oracle = oracle.control()
        c_oracle.name = 'OracleAug'
        oracle.data = []
        aug = QuantumRegister(1, 'aug')
        oracle.add_register(aug)
        oracle.compose(
            c_oracle,
            [n_all-1] + list(range(n_all-1)),
            inplace=True,
        )
        assert oracle.num_qubits == n_all

    # Copy qubit strucure of oracle
    circ = copy.deepcopy(oracle)
    circ.data = []
    circ.name = 'Amp'

    # Qubit partitioning
    qubits_search = list(filter(
        lambda x: not x in aux_qubits,
        list(range(n_all))
    ))
    qubits_measure = list(filter(
        lambda x: not x in aux_qubits,
        list(range(n_all - (1 if inc else 0)))
    ))

    # Initialization
    circ.append(algorithm, circ.qubits)

    # Iterations
    op = GroverOperator(oracle, state_preparation=algorithm,
                        reflection_qubits=qubits_search).decompose()
    op.name = "Q"
    for _ in range(num_iters):
        circ.append(op, circ.qubits)

    # Measurements
    result = ClassicalRegister(len(qubits_measure), name='result')
    circ.add_register(result)
    # Reverse order to match natural expectation
    circ.measure(list(reversed(qubits_measure)), result)

    return circ


# +----------------------+
# | Algorithm simulation |
# +----------------------+

def __measure_to_model(measurements: str, var_names: list[str]) -> Interpretation:
    '''Convert the result of a measurement to a human-readable format with variable names.

    #### Arguments
        measurements (str): Measured bits.
        var_names (list[str]): Ordered list of variable names that the measurements refer to.

    #### Return
        Interpretation: Solution representation.
    '''
    assert len(measurements) == len(var_names)

    model = set()
    for (name, value) in zip(var_names, measurements):
        assert value in ('0', '1')
        bool_value = value == '1'
        model.add((name, bool_value))
    return model


def exec_find_one_known_m(
    algorithm: QuantumCircuit,
    oracle: Oracle,
    m: int,
    aux_qubits: list[int] = None
) -> tuple[QuantumCircuit, int, Interpretation]:
    '''Simulate the amplitude amplification circuit to find one solution to the problem.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        m (int): (Known) number of solutions.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.

    #### Return
        tuple[QuantumCircuit, int, Interpretation]: Used circuit, number of iterations performed, \
            and found solution.
    '''
    # pylint: disable=too-many-locals

    aux_qubits = [] if aux_qubits is None else aux_qubits
    (c_oracle, q_oracle) = oracle

    # Extract variable names associated to search qubits (from oracle circuit)
    var_names = []
    qubits = q_oracle.qubits
    for (idx, qubit) in zip(range(len(qubits)), qubits):
        if not idx in aux_qubits:
            reg = q_oracle.find_bit(qubit).registers[0][0]
            var_names = var_names + [reg.name]

    # Build circuit
    circ = circuit_optimal(algorithm, q_oracle, m, aux_qubits)

    # Run simulation
    model, iters = None, 0
    while True:
        iters += 1
        result = exec_circuit(circ, shots=1)
        measurements = list(result.get_counts(circ).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

    # Map output to readable format
    return (circ, iters, model)


def exec_find_one_unknown_m(
    algorithm: QuantumCircuit,
    oracle: Oracle,
    aux_qubits: list[int] = None,
    c: float = 1.5
) -> tuple[list[QuantumCircuit], int, Interpretation]:
    '''Exponentially guess the value of m to find one solution to the problem.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        aux_qubits (list[int]): List of indices of auxiliary qubits (e.g. used by the oracle) \
            that should not be used for the search procedure. Defaults to the empty list.
        c (float): Base of the exponential defining the guess for m.

    #### Return
        tuple[list[QuantumCircuit], int, Interpretation]: List of used circuits, number of \
            iterations performed, and found solution.
    '''
    # pylint: disable=too-many-locals

    aux_qubits = [] if aux_qubits is None else aux_qubits
    (c_oracle, q_oracle) = oracle
    inc = True  # Since we do not know m, we must be the most general possible
    random.seed()

    # Extract variable names associated to search qubits (from oracle circuit)
    var_names = []
    qubits = q_oracle.qubits
    for (idx, qubit) in zip(range(len(qubits)), qubits):
        if not idx in aux_qubits:
            reg = q_oracle.find_bit(qubit).registers[0][0]
            var_names = var_names + [reg.name]

    # Prepare circuit with no amplification iterations
    circ_noiter = circuit(copy.deepcopy(algorithm),
                          copy.deepcopy(q_oracle), 0, inc, aux_qubits)
    circs = [circ_noiter]

    # Run simulation
    model, iters = None, 0
    while True:
        iters += 1  # `l' in the paper
        m = math.ceil(c**iters)

        # Step 3
        result = exec_circuit(circ_noiter, shots=1)
        measurements = list(result.get_counts(circ_noiter).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

        # Steps 4-7
        j = random.randint(1, m)
        circ = circuit(copy.deepcopy(algorithm),
                       copy.deepcopy(q_oracle), j, inc, aux_qubits)
        circs.append(circ)
        result = exec_circuit(circ, shots=1)
        measurements = list(result.get_counts(circ).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

    return (circs, iters, model)
