import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "scripts/verify_v2.py",
    "scripts/football_v2_ablation.py",
    "scripts/verify_goal_markets.py",
    "scripts/verify_dixon_coles.py",
    "scripts/verify_poisson_market.py",
    "scripts/market_structure_test.py",
]

REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report = REPORT_DIR / f"research_{timestamp}.txt"

with report.open("w", encoding="utf-8") as out:

    out.write("BAgent RESEARCH REPORT\n")
    out.write("=" * 70 + "\n")
    out.write(f"DATE: {datetime.now().isoformat()}\n\n")

    for relative in SCRIPTS:

        script = ROOT / relative

        out.write("\n")
        out.write("#" * 70 + "\n")
        out.write(f"SCRIPT: {relative}\n")
        out.write("#" * 70 + "\n\n")

        if not script.exists():
            out.write("SKIPPED: FILE NOT FOUND\n")
            continue

        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            out.write(result.stdout)

            if result.stderr:
                out.write("\n--- STDERR ---\n")
                out.write(result.stderr)

            out.write(
                f"\nEXIT CODE: {result.returncode}\n"
            )

        except Exception as exc:
            out.write(
                f"ERROR RUNNING SCRIPT: {exc}\n"
            )

print()
print("RESEARCH COMPLETE")
print("REPORT:")
print(report)
