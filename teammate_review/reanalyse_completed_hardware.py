"""Compare allowed extrapolators on already completed 1,3,5 hardware counts."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats

record = json.loads(Path("qats_results/hardware_defne_layout_twirling_record.json").read_text())
backend = hc.fake_kingston()
rows = []
for kind in ("linear", "exponential", "quadratic"):
    rec = record["team"]
    exp = hc.experiment_from_record(rec, backend)
    exp.recipe.zne_extrapolator = kind
    result = exp.analyze(rec["counts"])
    eps = hc.conservative_error(result)
    ratio = abs(1 - record["baseline"]["result"]["F"]) / eps
    row = {
        "extrapolator": kind, "result": qats.result_dict(result),
        "eps_star": eps, "error_reduction": ratio,
    }
    rows.append(row)
    print(kind, result, "epsilon*=", eps, "R=", ratio)
Path("teammate_review/hardware_extrapolator_comparison.json").write_text(
    json.dumps(rows, indent=2) + "\n"
)
