"""PEC stretch experiment on a learned, deliberately simple simulator noise model.

This is not a calibrated model of ibm_kingston and is not a leaderboard result.
For E=(1-p)I+pZ, E^-1=((1-p)I-pZ)/(1-2p). We learn p from
an independent Bell-parity calibration and sample the signed inverse after each CX.
"""
from itertools import product
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error
import qats

rng = np.random.default_rng(4026)
injected_p = 0.08
noise = NoiseModel()
noise.add_all_qubit_quantum_error(pauli_error([("IZ", injected_p), ("II", 1-injected_p)]), "cx")
simulator = AerSimulator(method="stabilizer", noise_model=noise)

def measured(circuit):
    c = circuit.copy()
    c.h(range(c.num_qubits))
    c.measure_all()
    return c

def parity(counts):
    shots = sum(counts.values())
    return sum((-1)**bits.count("1") * count for bits,count in counts.items()) / shots

calibration = QuantumCircuit(2)
calibration.h(0); calibration.cx(0,1)
calibration_shots = 8000
cal_counts = simulator.run(measured(calibration), shots=calibration_shots, seed_simulator=11).result().get_counts()
p_hat = (1-parity(cal_counts))/2
patterns = list(product((0,1), repeat=2))

def coefficients(p):
    return np.array([(-1)**sum(pattern) * (1-p)**(2-sum(pattern)) * p**sum(pattern)
                     / (1-2*p)**2 for pattern in patterns])

weights = coefficients(p_hat)
gamma = float(np.abs(weights).sum())
allocated = rng.multinomial(16_000, np.abs(weights)/gamma)
counts = []
for pattern, shots in zip(patterns, allocated):
    c = QuantumCircuit(3)
    c.h(0); c.cx(0,1)
    if pattern[0]: c.z(0)
    c.cx(1,2)
    if pattern[1]: c.z(1)
    counts.append(simulator.run(measured(c), shots=int(shots), seed_simulator=100+2*pattern[0]+pattern[1]).result().get_counts())
means = np.array([parity(c) for c in counts])
corrected_X = float(weights @ means)
raw_X = float(means[0])
bootstrap = []
for _ in range(1000):
    learned = rng.binomial(calibration_shots, p_hat)/calibration_shots
    sampled_means = np.array([2*rng.binomial(int(n), (1+m)/2)/n-1 for n,m in zip(allocated,means)])
    bootstrap.append((1+coefficients(learned) @ sampled_means)/2)
result = {
    "scope": "three-qubit toy Pauli-Z gate-noise model; NOT IBM hardware or a leaderboard claim",
    "injected_p": injected_p, "learned_p": p_hat, "calibration_shots": calibration_shots,
    "experiment_shots": int(allocated.sum()), "raw_F": (1+raw_X)/2,
    "pec_F": (1+corrected_X)/2, "pec_standard_error": float(np.std(bootstrap, ddof=1)),
    "gamma": gamma, "sampling_overhead_bound": gamma**2,
    "explanation": "P=1 exactly in this phase-only model. Error bar includes calibration and measurement resampling.",
}
qats.dump("pec_demo.json", result)
print("PEC stretch demonstration (toy model, not calibrated Kingston):")
print(f"Learned p={p_hat:.4f}; injected p={injected_p:.4f}")
print(f"Raw F={result['raw_F']:.4f}; PEC F={result['pec_F']:.4f} ± {result['pec_standard_error']:.4f}")
print(f"Sampling overhead bound γ²={gamma**2:.2f}; additional calibration shots={calibration_shots}")
