"""Select a fresh 12-qubit layout from the current Kingston calibration."""
from pathlib import Path
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

real = QiskitRuntimeService().backend("ibm_kingston")
candidates = {}
for max_readout in (0.02, 0.03, 0.05):
    for max_cz in (0.006, 0.01, 0.02):
        for min_t2 in (50e-6, 100e-6, 150e-6):
            cat = qats.best_tree_cat(real, 12, max_readout, max_cz, min_t2)
            if cat is not None:
                candidates.setdefault(tuple(hc.cat_qubits(cat)), ("tree", cat))

for i, line in enumerate(qats.line_candidates(real, 12, limit=16)):
    cat = generate_preset_pass_manager(
        optimization_level=3, backend=real, initial_layout=line, seed_transpiler=1
    ).run(qats.make_cat_from_middle(12))
    candidates.setdefault(tuple(hc.cat_qubits(cat)), (f"middle-{i}", cat))

defne = json.loads(subprocess.check_output(
    ["git", "show", "origin/defne:hardware_record.json"], text=True
))["team"]
defne_cat = hc.circuit_from_b64(defne["prep_qpy_b64"])
candidates.setdefault(tuple(defne["qubits"]), ("defne-saved", defne_cat))

rows = []
for qubits, (label, cat) in candidates.items():
    report = hc.cat_report(cat, real)
    rows.append({"label": label, "qubits": list(qubits), "report": report})
rows.sort(key=lambda row: (row["report"]["ESP"], -row["report"]["duration_us"]), reverse=True)
Path("teammate_review/live_extension_candidates.json").write_text(
    json.dumps(rows, indent=2) + "\n"
)
for row in rows[:12]:
    print(row["label"], f"ESP={row['report']['ESP']:.6f}",
          f"depth={row['report']['two_qubit_depth']}",
          f"duration={row['report']['duration_us']:.3f}us", row["qubits"])
winner = rows[0]
hc.save_circuit(candidates[tuple(winner["qubits"])][1], "qats_results/live_extension_cat.qpy")
Path("qats_results/live_extension_choice.json").write_text(
    json.dumps(winner, indent=2) + "\n"
)
print("SELECTED", winner)
