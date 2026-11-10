"""Reproducible circuit searches and experiment bookkeeping for team Qats."""
from collections import deque
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
import json
import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
import herding_cats as hc

OUT = Path("qats_results")
OUT.mkdir(exist_ok=True)

def dump(name, data):
    path = OUT / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
    temporary.replace(path)
    return path

def result_dict(result):
    return {**asdict(result), "certified": bool(result.certified)}

@lru_cache(maxsize=12)
def quality(backend):
    return hc.qubit_quality(backend)

def make_cat_from_middle(n):
    qc = QuantumCircuit(n)
    middle = n // 2
    qc.h(middle)
    left, right = middle, middle
    # The two root operations share a qubit; later branches can run in parallel.
    while left > 0 or right < n - 1:
        if left > 0:
            qc.cx(left, left - 1)
            left -= 1
        if right < n - 1:
            qc.cx(right, right + 1)
            right += 1
    return qc

def line_candidates(backend, n, limit=24):
    qinfo, errors = quality(backend)
    neighbours = {q: set() for q in range(backend.num_qubits)}
    for a, b in backend.coupling_map.get_edges():
        if tuple(sorted((a, b))) in errors:
            neighbours[a].add(b)
            neighbours[b].add(a)
    qcost = {q: -math.log(max(1e-9, 1 - v["readout"]))
             if np.isfinite(v["readout"]) else float("inf") for q, v in qinfo.items()}
    ecost = {e: -math.log(max(1e-9, 1 - error)) for e, error in errors.items()}
    ranked = []
    def dfs(path, cost):
        if len(ranked) >= limit and cost >= ranked[-1][0]:
            return
        if len(path) == n:
            ranked.append((cost, tuple(path)))
            ranked.sort()
            del ranked[limit:]
            return
        for q in sorted(neighbours[path[-1]], key=lambda x: qcost[x] + ecost[tuple(sorted((path[-1], x))) ]):
            if q not in path:
                dfs(path + [q], cost + qcost[q] + ecost[tuple(sorted((path[-1], q)))])
    for root in sorted(neighbours, key=qcost.get):
        dfs([root], qcost[root])
    return [list(p) for _, p in ranked]

def find_good_line(backend, n):
    candidates = line_candidates(backend, n, limit=1)
    return candidates[0] if candidates else None

def make_tree_cat(backend, root, n, max_readout=0.05, max_cz=0.02, min_t2=30e-6):
    qinfo, errors = quality(backend)
    good = {q for q, p in qinfo.items() if p["readout"] <= max_readout and (p["t2"] or 0) >= min_t2}
    if root not in good:
        return None
    adjacent = {q: set() for q in good}
    for (a, b), error in errors.items():
        if error <= max_cz and a in good and b in good:
            adjacent[a].add(b)
            adjacent[b].add(a)
    order, parents, seen = [root], [], {root}
    queue = deque([root])
    while queue and len(order) < n:
        parent = queue.popleft()
        candidates = sorted(adjacent[parent] - seen, key=lambda q:
            2 * errors[tuple(sorted((q, parent)))] + qinfo[q]["readout"] + 1e-6 / qinfo[q]["t2"])
        for child in candidates:
            if len(order) >= n:
                break
            seen.add(child)
            order.append(child)
            parents.append((parent, child))
            queue.append(child)
    if len(order) != n:
        return None
    logical = QuantumCircuit(n)
    index = {q: i for i, q in enumerate(order)}
    logical.h(0)
    for parent, child in parents:
        logical.cx(index[parent], index[child])
    return generate_preset_pass_manager(optimization_level=3, backend=backend,
        initial_layout=order, seed_transpiler=1).run(logical)

@lru_cache(maxsize=24)
def best_tree_cat(backend, n, max_readout=0.05, max_cz=0.02, min_t2=30e-6):
    best, best_esp = None, -1
    for root in range(backend.num_qubits):
        cat = make_tree_cat(backend, root, n, max_readout, max_cz, min_t2)
        if cat is not None:
            esp = hc.cat_report(cat, backend)["ESP"]
            if esp > best_esp:
                best, best_esp = cat, esp
    return best

def optimize_clean(backend, middle_cat, simulator):
    """Screen circuits/recipes, then select using fresh-seed conservative error."""
    tree = best_tree_cat(backend, 12)
    candidates = {"middle": middle_cat, "tree": tree}
    # Rank several distinct low-error chains using circuit timing as well as readout.
    timed = []
    for line in line_candidates(backend, 12, 12):
        cat = generate_preset_pass_manager(optimization_level=3, backend=backend,
            initial_layout=line, seed_transpiler=1).run(make_cat_from_middle(12))
        timed.append((hc.cat_report(cat, backend)["ESP"], cat))
    candidates["timing-aware middle"] = max(timed, key=lambda item: item[0])[1]
    recipes = {
        "TREX": hc.Recipe(readout_mitigation=True),
        "DD + TREX": hc.Recipe(dd="XX", readout_mitigation=True),
        "TREX + twirling": hc.Recipe(readout_mitigation=True, gate_twirling=True),
        "TREX + ZNE linear": hc.Recipe(readout_mitigation=True, zne_factors=(1,3), zne_extrapolator="linear"),
        "TREX + ZNE exponential": hc.Recipe(readout_mitigation=True, zne_factors=(1,3,5)),
        "DD + TREX + ZNE + twirling": hc.Recipe(dd="XX", readout_mitigation=True,
            gate_twirling=True, zne_factors=(1,3,5)),
    }
    rows = []
    for cname, cat in candidates.items():
        assert cat is not None and hc.verify_cat(cat)
        for rname, recipe in recipes.items():
            exp = hc.build_cat_experiment(cat, backend, recipe, seed=101)
            result = exp.run(simulator, total_shots=12_000)
            row = {"circuit": cname, "technique": rname, "recipe": asdict(recipe),
                   "result": result_dict(result), "eps_star": hc.conservative_error(result)}
            rows.append(row)
            dump("clean_screen.json", rows)
            print(f"screen {cname} / {rname}: {result}", flush=True)
    finalists = sorted(rows, key=lambda r: r["eps_star"])[:3]
    for row in finalists:
        cat = candidates[row["circuit"]]
        recipe = hc.Recipe(**row["recipe"])
        row["validation"] = []
        for seed in (701, 702):
            result = hc.measure_cat_quality(cat, hc.CatSimulator(backend, seed=seed),
                recipe, total_shots=24_000, seed=seed)
            row["validation"].append(result_dict(result))
            print(f"holdout {row['circuit']} / {row['technique']}, seed {seed}: {result}", flush=True)
        row["validation_error"] = float(np.mean([
            abs(1-r["F"]) + r["F_err"] for r in row["validation"]]))
    chosen = min(finalists, key=lambda r: r["validation_error"])
    dump("clean_validation.json", finalists)
    dump("clean_choice.json", chosen)
    best_cat = candidates[chosen["circuit"]]
    best_recipe = hc.Recipe(**chosen["recipe"])
    hc.save_circuit(best_cat, str(OUT / "clean_cat.qpy"))
    return best_cat, best_recipe, rows, finalists, chosen

def big_search(backend, simulator):
    recipe = hc.Recipe(dd="XX", readout_mitigation=True)
    rows, certified_candidates = [], []
    for n in (24, 36, 48, 64, 80, 96, 112, 128, 144, 156):
        cat = best_tree_cat(backend, n)
        if cat is None:
            continue
        assert hc.verify_cat(cat)
        exp = hc.build_cat_experiment(cat, backend, recipe, seed=903)
        result = exp.run(simulator, total_shots=8000)
        rows.append({"n": n, "result": result_dict(result), "qubits": hc.cat_qubits(cat)})
        dump("big_search.json", rows)
        print(f"big-cat screen: {result}", flush=True)
        if result.certified:
            certified_candidates.append(cat)
        elif certified_candidates:
            break
    if not certified_candidates:
        certified_candidates = [best_tree_cat(backend, 12)]
    # Confirm from largest to smallest on fresh data; keep a genuinely certified
    # smaller state if the screening winner does not survive independent checking.
    confirmations = []
    for cat in reversed(certified_candidates):
        exp = hc.build_cat_experiment(cat, backend, recipe, seed=1903)
        result = exp.run(hc.CatSimulator(backend, seed=1903), total_shots=24_000)
        print("big-cat independent confirmation:", result, flush=True)
        confirmations.append(result_dict(result))
        dump("big_confirmation.json", confirmations)
        if result.certified:
            return cat, exp, result, rows
    return cat, exp, result, rows

def assert_hardware_budget(circuits, shots, backend, limit=15):
    seconds = hc.estimate_qpu_seconds(circuits, shots, backend)
    if seconds > limit:
        raise ValueError(f"Estimated {seconds:.1f}s exceeds the {limit}s job budget")
    print(f"Estimated QPU use: {seconds:.1f}s", flush=True)
    return seconds

class BudgetRunner(hc.HardwareRunner):
    def _sampler(self):
        sampler = super()._sampler()
        sampler.options.max_execution_time = 30
        return sampler

def submit_once(name, circuits, shots, backend):
    """Resume a recorded job; never submit again after an ambiguous interruption."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    path = OUT / "hardware_jobs.json"
    manifest = json.loads(path.read_text()) if path.exists() else {}
    if name in manifest:
        entry = manifest[name]
        if entry.get("job_id"):
            print(f"Resuming {name}: {entry['job_id']}", flush=True)
            return QiskitRuntimeService().job(entry["job_id"])
        raise RuntimeError(f"Submission of {name} was interrupted. Check the IBM job list before retrying.")
    estimate = assert_hardware_budget(circuits, shots, backend)
    manifest[name] = {"state": "submitting", "circuits": len(circuits),
        "shots_per_circuit": shots, "estimated_seconds": estimate}
    dump("hardware_jobs.json", manifest)
    job = BudgetRunner(backend).submit(circuits, shots)
    manifest[name].update(state="submitted", job_id=job.job_id())
    dump("hardware_jobs.json", manifest)
    print(f"Submitted {name}: {job.job_id()}", flush=True)
    return job


# Local Aer compatibility only: the organizers' toolkit file is left unchanged.
import copy
from typing import Sequence
from qiskit.transpiler import PassManager

_OriginalSimulator = hc.CatSimulator

class StableCatSimulator(_OriginalSimulator):
    """Same noise model, with equivalent native Kraus idle channels on local Aer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._idle_kraus_cache = {}

    def run(self, circuits: QuantumCircuit | Sequence[QuantumCircuit], shots: int = 4000) -> list[dict]:
        """Simulate measured ISA circuits; returns one counts dict per circuit."""
        from qiskit_aer import AerSimulator

        single = isinstance(circuits, QuantumCircuit)
        circuits = [circuits] if single else list(circuits)
        shots = int(shots)
        # Every circuit is split into a few "noise batches" (fresh frequency noise each),
        # so that every measurement basis sees at least `noise_batches` noise draws.
        per_circuit = 1
        if self.detuning_khz > 0:
            per_circuit = max(1, math.ceil(self.noise_batches / max(1, len(circuits) // 3)))
            per_circuit = min(per_circuit, max(1, shots // 50))
        groups: dict = {}  # (phys, shots) -> list of (circuit index, compact circuit)
        for i, circ in enumerate(circuits):
            sched = hc.schedule_circuit(circ, self.backend)  # adds idle periods; keeps existing DD
            phys = tuple(hc._chain_order(sched))
            mp = {p: j for j, p in enumerate(phys)}
            split = [shots // per_circuit + (1 if b < shots % per_circuit else 0) for b in range(per_circuit)]
            for s in split:
                if s == 0:
                    continue
                det = (
                    self.rng.normal(0.0, self.detuning_khz * 1e3, size=len(phys))
                    if self.detuning_khz > 0
                    else None
                )
                groups.setdefault((phys, s), []).append((i, self._compact(sched, mp, det)))
        out: list[dict] = [dict() for _ in circuits]
        for (phys, s), items in groups.items():
            from qiskit.quantum_info import Kraus

            full_noise = self._compact_noise_model(phys)
            gate_readout_noise = copy.copy(full_noise)
            gate_readout_noise._custom_noise_passes = []
            bodies = [c for _, c in items]
            if full_noise._custom_noise_passes:
                bodies = PassManager(full_noise._custom_noise_passes).run(bodies)
            native_bodies = []
            for body in bodies:
                native = body.copy_empty_like()
                for inst in body.data:
                    op = inst.operation
                    if op.name == "quantum_channel":
                        channel = op._quantum_error.to_quantumchannel()
                        key = (channel.num_qubits, channel.data.tobytes())
                        if key not in self._idle_kraus_cache:
                            self._idle_kraus_cache[key] = Kraus(channel).to_instruction()
                        op = self._idle_kraus_cache[key]
                    native.append(op, inst.qubits, inst.clbits)
                native_bodies.append(native)
            sim = AerSimulator(method=self.method, noise_model=gate_readout_noise)
            res = sim.run(native_bodies, shots=s, seed_simulator=int(self.rng.integers(2**31))).result()
            if not res.success:
                raise RuntimeError(f"Aer simulation failed: {res.status}")
            for k, (i, _) in enumerate(items):
                for key, v in res.get_counts(k).items():
                    out[i][key] = out[i].get(key, 0) + v
        return out[0] if single else out
