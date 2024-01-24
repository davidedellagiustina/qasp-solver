'''Utility functions for building classical and quantum oracles.
'''

from typing import Callable
from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import PhaseOracle


# +-------+
# | Types |
# +-------+

Literal = tuple[str, bool]  # Either atom or negated atom
Model = list[Literal]  # Complete (!) list of literals
ClassicalOracle = Callable[[Model], bool]
QuantumOracle = QuantumCircuit
Oracle = tuple[ClassicalOracle, QuantumOracle]


# +-----------------+
# | Formulas syntax |
# +-----------------+

def __literal_to_formula(literal: Literal) -> str:
    '''Build a logical formula whose only model is the given literal.

    #### Arguments
        literal (Literal): Input literal.

    #### Returns
        str: Built logical formula.
    '''
    (atom, value) = literal
    return ('' if value else '~') + f'{atom}'


def __model_to_formula(model: Model) -> str:
    '''Build a logical formula whose only model is the given one.

    #### Arguments
        model (Model): Input model.

    #### Returns
        str: Built logical formula.
    '''
    pieces = map(__literal_to_formula, model)
    return '(' + ' & '.join(pieces) + ')'


# +---------------------+
# | Oracle construction |
# +---------------------+

def from_asp_stable_models(stable_models: list[Model], var_order: list[str] = None) -> Oracle:
    '''Build an oracle solving an ASP program.

    #### Arguments
        stable_models (list[Model]): List of the stable models of the considered ASP program.
        var_order (list[str], optional): Explicit ordering of the variables. Defaults to `None` \
            (i.e. appearence order).

    #### Returns
        Oracle: Built oracle.
    '''
    atoms = [
        atom for (atom, _) in stable_models[0]
    ] if var_order is None else var_order

    # Build classical oracle
    def c_oracle(model):
        return model in stable_models

    # Build quantum oracle
    clauses = map(__model_to_formula, stable_models)
    formula = ' | '.join(clauses)
    oracle_gate = PhaseOracle(formula, var_order=atoms)

    # Wrap quantum oracle in a circuit with proper qubit labels
    regs = [QuantumRegister(1, f'{atom}') for atom in atoms]
    q_oracle = QuantumCircuit(*regs, name='Oracle')
    q_oracle.compose(oracle_gate, q_oracle.qubits, inplace=True)

    return (c_oracle, q_oracle)
