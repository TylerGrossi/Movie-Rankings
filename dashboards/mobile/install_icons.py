"""Sync the generated tab icons into the PBIP and register them in report.json.

Syncs rather than adds: icons that no longer exist in icons/ are deleted from
StaticResources and deregistered, so retiring a tab (Stats -> Series) doesn't
leave orphans behind. Only ic_*.png is touched — the custom theme registration
in the same package is left alone.
"""
import json, shutil
from pathlib import Path

SRC = Path(__file__).parent / "icons"
PROJ = Path(__file__).resolve().parents[1] / "Movie Dashboard.Report"
RES = PROJ / "StaticResources" / "RegisteredResources"
REPORT = PROJ / "definition" / "report.json"

RES.mkdir(parents=True, exist_ok=True)

wanted = {p.name for p in SRC.glob("ic_*.png")}
assert wanted, "no icons generated — run gen_icons.py first"

for p in sorted(SRC.glob("ic_*.png")):
    shutil.copy2(p, RES / p.name)

stale = {p.name for p in RES.glob("ic_*.png")} - wanted
for name in sorted(stale):
    (RES / name).unlink()
    print(f"removed stale {name}")

report = json.loads(REPORT.read_text(encoding="utf-8"))
pkg = next(p for p in report["resourcePackages"] if p["type"] == "RegisteredResources")

kept = [i for i in pkg["items"]
        if not i["name"].startswith("ic_") or i["name"] in wanted]
have = {i["name"] for i in kept}
for name in sorted(wanted - have):
    kept.append({"name": name, "path": name, "type": "Image"})

dropped = len(pkg["items"]) - len([i for i in kept if i["name"] in have or i["name"] in wanted])
pkg["items"] = kept
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(f"synced {len(wanted)} icons; package has {len(pkg['items'])} items "
      f"({len(stale)} stale removed)")
