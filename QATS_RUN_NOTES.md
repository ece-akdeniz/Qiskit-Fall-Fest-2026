# Qats experiment notes

The completed challenge is `team_Qats.ipynb`. `team_Qats_simulator.ipynb` preserves
the full simulator pass before hardware results were collected. The generated
grading payload is `submission_Qats.json`. Team members: Ece Akdeniz, Defne Tufan,
Kerem Akın, Ömer Melik Sazak and Eren Yozbilir.

## What is measured

The experiment uses the organizers' Z/X fidelity lower bound, with bootstrap
uncertainties when mitigation is applied. Cleanest Cat has exactly 12 qubits.
ZNE results are zero-noise estimates and can fall outside [0,1]; they are never
clipped or used for Biggest Cat certification. Biggest Cat requires
`F - 2*standard_error > 0.5` without ZNE.

The clean-cat search compares connected chains, middle growth and breadth-first
trees, then compares DD, Pauli twirling, TREX and ZNE recipes. Screening uses the
same nominal 12,000-shot budget per candidate. The top three are evaluated again
with 24,000 shots on independent simulator seeds 701 and 702. Selection minimizes
mean `abs(1-F)+standard_error`. Additional scorecard seeds provide independent
checks. Exact shot totals may round down to a multiple of the circuit count.

`qats_results/` stores the screening, validation, evidence and raw hardware
counts. The live layout is re-searched using current Kingston calibration.
Hardware jobs compare the baseline and improved circuit in the same job.

The initially inconclusive 64-qubit simulator screen gets an independent
32k-shot follow-up. The initially inconclusive 48-qubit hardware result gets one
predeclared 48k-shot precision check; if necessary a smaller simulator-validated
hardware cat is used as a fallback. These results are retained separately. The
submission selects the strongest certified record using the published hardware
versus simulator points, breaking ties by size.

## Simulator compatibility fix

The original Aer 0.18 execution crashed on some layouts when gate noise and
idle-time relaxation `QuantumError` channels were combined. The local
`qats.StableCatSimulator` subclass materializes those same idle channels as native
Kraus instructions. The organizers' `herding_cats.py` is unchanged. Gate noise,
readout noise, slow detuning and the original T1/T2
parameters remain in place. Twelve channel-equivalence checks passed, and the
baseline stayed at about 0.442. The submitted circuit and recipe use only the
original toolkit's scoring features; the workaround is local execution plumbing.

## Hardware safeguards

Hardware is opt-in via `QATS_RUN_HARDWARE=1`. `qats.submit_once` records intent
and job IDs in `qats_results/hardware_jobs.json` and resumes recorded jobs.
It refuses to retry an ambiguous submission automatically. Each submitted job
must have an estimated QPU duration at most 15 seconds, and the sampler has a
30-second execution limit. Job IDs and raw counts are retained for recovery.

Do not delete the hardware job manifest to rerun the notebook. Keep IBM
credentials in Qiskit's local account storage, outside the submission files.

## PEC stretch

`pec_demo.py` separately learns a simple Pauli-Z gate-noise model and samples
its signed inverse. This illustrates PEC, its calibration cost and sampling
overhead. It is not a calibrated Kingston model and is not a leaderboard or
hardware fidelity claim. The notebook includes the executed demonstration.
