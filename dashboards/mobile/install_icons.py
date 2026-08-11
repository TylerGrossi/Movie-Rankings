"""Copy the generated tab icons into the PBIP and register them in report.json."""
import json, shutil
from pathlib import Path

SRC = Path(__file__).parent / "icons"
PROJ = Path(r"c:\Users\Owner\Desktop\Tyler\OneDrive\Projects\Movies\dashboards\Movie Dashboard.Report")
RES = PROJ / "StaticResources" / "RegisteredResources"
REPORT = PROJ / "definition" / "report.json"

RES.mkdir(parents=True, exist_ok=True)

pngs = sorted(SRC.glob("ic_*.png"))
assert len(pngs) == 10, f"expected 10 icons, found {len(pngs)}"

for p in pngs:
    shutil.copy2(p, RES / p.name)
    print(f"copied {p.name}")

report = json.loads(REPORT.read_text(encoding="utf-8"))
pkg = next(p for p in report["resourcePackages"] if p["type"] == "RegisteredResources")
existing = {i["name"] for i in pkg["items"]}

added = 0
for p in pngs:
    if p.name not in existing:
        pkg["items"].append({"name": p.name, "path": p.name, "type": "Image"})
        added += 1

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"\nregistered {added} images; package now has {len(pkg['items'])} items")
