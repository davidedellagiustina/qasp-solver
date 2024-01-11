'''Amplitude amplification algorithms.
'''

import copy
import math
import random
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit.library import GroverOperator
from qiskit_aer import Aer, AerJob
from ..oracle import Model, QuantumOracle, Oracle

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


def circuit_optimal(algorithm: QuantumCircuit, oracle: QuantumOracle, m: int) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude amplification algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (QuantumOracle): Circuit that implements the oracle.
        m (int): (Known) number of solutions.

    #### Returns
        QuantumCircuit: Built circuit.
    '''
    assert algorithm.num_qubits == oracle.num_qubits

    n = algorithm.num_qubits
    inc = m > (2**n)/2
    num_iters = __optimal_num_iters(n, m)

    return circuit(algorithm, oracle, num_iters, inc)


def circuit(
    algorithm: QuantumCircuit,
    oracle: QuantumOracle,
    num_iters: int,
    inc: bool = False
) -> QuantumCircuit:
    '''Build a quantum circuit implementing the amplitude amplification algorithm.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (QuantumOracle): Circuit that implements the oracle.
        num_iters (int): Number of iterations to perform.
        inc (bool): Whether to use an additional qubit for searching (necessary if m > n/2). \
            Defaults to False.

    #### Returns
        QuantumCircuit: Built circuit.
    '''
    assert algorithm.num_qubits == oracle.num_qubits

    n = algorithm.num_qubits
    n_orig = n

    # Add a qubit if there are too many solutions
    if inc:
        n += 1

        # Algorithm
        algorithm.name = 'AlgorithmAug'
        aux = QuantumRegister(1, 'aux')
        algorithm.add_register(aux)
        algorithm.h(aux)
        assert algorithm.num_qubits == n

        # Oracle
        c_oracle = oracle.control()
        c_oracle.name = 'OracleAug'
        oracle.data = []
        aux = QuantumRegister(1, 'aux')
        oracle.add_register(aux)
        oracle.compose(
            c_oracle,
            [n-1] + list(range(n-1)),
            inplace=True,
        )
        assert oracle.num_qubits == n

    # Copy qubit strucure of oracle
    circ = copy.deepcopy(oracle)
    circ.data = []
    circ.name = 'Amp'

    # Initialization
    circ.append(algorithm, circ.qubits)

    # Iterations
    op = GroverOperator(oracle, state_preparation=algorithm).decompose()
    op.name = "Op"
    for _ in range(num_iters):
        circ.append(op, circ.qubits)

    # Measurements
    result = ClassicalRegister(n_orig, name="result")
    circ.add_register(result)
    # Reverse order to match natural expectation
    circ.measure([*range(n_orig-1, -1, -1)], result)

    return circ

# +----------------------+
# | Algorithm simulation |
# +----------------------+


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


def __measure_to_model(measurements: str, var_names: str) -> Model:
    '''Convert the result of a measurement to a human-readable format with variable names.

    #### Arguments
        measurements (str): Measured bits.
        var_names (str): Ordered list of variable namess that the measurements refer to.

    #### Return
        Model: Solution representation.
    '''
    assert len(measurements) == len(var_names)

    model = []
    for (name, value) in zip(var_names, measurements):
        assert value in ('0', '1')
        bool_value = value == '1'
        model += [(name, bool_value)]
    return model


def exec_find_one_known_m(algorithm: QuantumCircuit, oracle: Oracle, m: int) -> tuple[int, Model]:
    '''Simulate the amplitude amplification circuit to find one solution to the problem.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        m (int): (Known) number of solutions.

    #### Return
        tuple[int, Model]: Found solution and number of iterations performed.
    '''
    (c_oracle, q_oracle) = oracle

    # Extract variable names
    var_names = ''
    for qubit in q_oracle.qubits:
        reg = q_oracle.find_bit(qubit).registers[0][0]
        var_names = var_names + reg.name

    # Build circuit
    circ = circuit_optimal(algorithm, q_oracle, m)
    print(f'Circuit:\n{circ.draw()}\n')

    # Run simulation
    model, iters = None, 0
    while True:
        iters += 1
        result = __exec_circuit(circ, shots=1)
        measurements = list(result.get_counts(circ).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

    # Map output to readable format
    return (iters, model)


def exec_find_one_unknown_m(
    algorithm: QuantumCircuit,
    oracle: Oracle,
    c: float = 1.5
) -> tuple[int, Model]:
    '''Exponentially guess the value of m to find one solution to the problem.

    #### Arguments
        algorithm (QuantumCircuit): Circuit that implements the initialization algorithm.
        oracle (Oracle): Pair of classical and quantum oracles.
        c (float): Base of the exponential defining the guess for m.

    #### Return
        tuple[int, Model]: Found solution and number of iterations performed.
    '''
    (c_oracle, q_oracle) = oracle
    inc = True  # Since we do not know m, we must be the most general possible
    random.seed()

    # Extract variable names
    var_names = ''
    for qubit in q_oracle.qubits:
        reg = q_oracle.find_bit(qubit).registers[0][0]
        var_names = var_names + reg.name

    # Prepare circuit with no amplification iterations
    circ_noiter = circuit(copy.deepcopy(algorithm),
                          copy.deepcopy(q_oracle), 0, inc)
    print(f'Circuit without amplification iterations:\n{circ_noiter.draw()}\n')

    # Run simulation
    model, iters = None, 0
    while True:
        iters += 1  # `l' in the paper
        m = math.ceil(c**iters)

        # Step 3
        result = __exec_circuit(circ_noiter, shots=1)
        measurements = list(result.get_counts(circ_noiter).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

        # Steps 4-7
        j = random.randint(1, m)
        circ = circuit(copy.deepcopy(algorithm),
                       copy.deepcopy(q_oracle), j, inc)
        print(f'Circuit with {j} amplification iterations:\n{circ.draw()}\n')
        result = __exec_circuit(circ, shots=1)
        measurements = list(result.get_counts(circ).keys())[0]
        model = __measure_to_model(measurements, var_names)
        if c_oracle(model):
            break

    return (iters, model)

# +---------------------------------+
# | Known initialization algorithms |
# +---------------------------------+


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
