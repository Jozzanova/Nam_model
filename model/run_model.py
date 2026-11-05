"""One command for the whole model pipeline (the dashboard's "Update"):

    python -X utf8 model/run_model.py            # estimate + check + simulate + JS-twin test on the cached data
    python -X utf8 model/run_model.py --refresh  # refetch SSB / Norges Bank / ECB / Eurostat / OECD / World Bank data first

then rebuild the page with `python -X utf8 build.py` and deploy.  Options after `--` go to estimate.py
(e.g. `-- --u lfs --start 2001Q1`)."""
import os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
args = sys.argv[1:]; est_args = []
if "--" in args: i = args.index("--"); est_args = args[i + 1:]; args = args[:i]
py = [sys.executable, "-X", "utf8"]
def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)); r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode: sys.exit(f"step failed: {cmd[-1]}")
if "--refresh" in args: run(py + [str(HERE / "fetch_data.py"), "--refresh"])
run(py + [str(HERE / "estimate.py")] + est_args)
run(py + [str(HERE / "check_sim.py")])
run(py + [str(HERE / "simulate.py"), "--reps", "500"])
run(py + [str(HERE / "forecast_eval.py")])
run(py + [str(HERE / "robustness.py")])
node = os.environ.get("NODE") or next((p for p in [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "node-v22.23.3-win-x64" / "node.exe"] if p.exists()), None) or "node"
try: run([str(node), str(HERE / "js_twin_test.js")])
except FileNotFoundError: print("node not found; JS twin test skipped")
print("model pipeline done — now: python -X utf8 build.py")
