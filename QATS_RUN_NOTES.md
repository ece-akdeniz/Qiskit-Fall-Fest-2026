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

## Defne comparison (team repository commit 3d61bb8)

Defne reports a 12-qubit hardware result F=0.965±0.014, same-job baseline 0.592±0.008, R=8.31 (about 11.46/15 hardware points). The verified raw counts for Kingston job dbpjq25t7fqc7389ijj0 are included in `submission_Qats.json`; the frozen figures are in Final scoring freeze below. Her inspected notebook had no completed Biggest Cat result. The team submission keeps the certified 40-qubit hardware cat.

We replicated three candidates with equal nominal26,880-shot budgets on fresh paired seeds8101–8103. Original tree recipe: mean F0.975998, mean sigma0.017074, mean conservative error0.041076. Defne’s middle-chain recipe:0.979067,0.013270,0.034203. Our tree plus Defne’s TREX/exponential-ZNE(1,5), DDoff, gate-twirlingoff:0.983309,0.013920,0.030611. Differences in mean fidelity are small; the combined recipe chiefly reduces shot uncertainty. Independent seed9101 gave F0.974094±0.013789, score24.2/25; this is the final reported simulator result.

One follow-up Kingston run uses the saved live tree plus that two-factor recipe: job dbpk88c4148s739up4d0, F0.942735±0.014250, same-job baseline0.604513±0.007198. It improves recorded hardware points to about9.25/15; the fidelity difference from the prior0.920±0.015 does not meet a two-sigma significance test. The certified40-qubit hardware result is retained. Raw counts, experiment definitions and independent comparisons are saved. The original toolkit file is restored byte-for-byte; compatibility is external in qats.py.

## Final 0.99 simulator refinement

The earlier combined recipe prioritized conservative error and produced
F=0.974094±0.013789 on independent seed 9101. A new suppression ablation on
paired seed 9501 isolated gate twirling as the useful final change:
TREX+ZNE gave 0.978±0.014; adding DD gave 0.970±0.013; adding gate twirling
without DD gave 1.000±0.014; and DD+twirling gave 0.974±0.014. The selected
recipe is therefore TREX + gate twirling + exponential ZNE factors (1,3,5),
with DD disabled.

The final held-out grader-scale run used simulator and experiment seed 9601,
which was absent from all layout and recipe screening. At a nominal 100,000
shots it returned F=0.998651±0.008625 (displayed as 0.999±0.009), P=1.000599
and X=0.996105. The result and per-factor measurements are stored in
`teammate_review/final_verify_099.json`; the executable verification is
`teammate_review/final_verify_099.py`. This meets the requested 0.99 simulator
fidelity target. It is a zero-noise estimate for Cleanest Cat and is not used
for Biggest Cat certification.


## Final scoring freeze
Verified Defne hardware job dbpjq25t7fqc7389ijj0: F=0.964540±0.013669, baseline=0.591590±0.007638, epsilon*=0.049128, R=8.313, estimated 11.46/15. Raw counts included. Biggest Cat remains certified N=40 hardware without ZNE.


## Biggest Cat certification matrix
### Complete Biggest Cat certification audit

Certification uses the published rule **F − 2σ > 0.5**, with raw or TREX-corrected data and **no ZNE**.

| Qubits | Environment | Fidelity | F−2σ | Certified |
|---:|---|---:|---:|:---:|
| 16 | simulator | 0.922751±0.005939 | 0.910872 | **YES** |
| 24 | simulator | 0.843953±0.007295 | 0.829362 | **YES** |
| 32 | simulator | 0.802746±0.009804 | 0.783138 | **YES** |
| 40 | hardware | 0.567877±0.018907 | 0.530062 | **YES** |
| 48 | simulator | 0.675638±0.028458 | 0.618722 | **YES** |
| 48 | hardware-pooled audit | 0.510445±0.013827 | 0.482791 | **NO** |
| 64 | simulator stretch | 0.555862±0.033947 | 0.487968 | **NO** |

Every leaderboard size tier (16, 24, 32, 40 and 48+) has a certified result. The largest certified
**hardware** result remains 40 qubits, worth 12/15 Biggest Cat points. The 48-qubit simulator result
certifies that size, but simulator scores receive half hardware points. Three 48-qubit hardware trials
did not certify. Pooling the two experiments with identical preparation, recipe, seed, masks and circuit
order produced F=0.510445±0.013827, with
F−2σ=0.482791; this is still below 0.5 and is reported honestly.
The 64-qubit stretch result also remains uncertified. Its uncertainty cannot be relabelled as evidence.

