"""Swap Actor Rankings[Rating] -> [+Rating] on the People page actors table.

Surgical on purpose. The live files now carry hand edits made in Desktop
(filterConfig blocks, sort changes, tuned column widths) that build_mobile.py
does not know about, so a rebuild would discard them. This touches only the one
projection and the columnWidth selector that points at it, leaving every other
byte of the file alone.
"""
import json
from pathlib import Path

TARGET = Path(r"c:\Users\Owner\Desktop\Tyler\OneDrive\Projects\Movies\dashboards"
              r"\Movie Dashboard.Report\definition\pages\pgMob04People"
              r"\visuals\v05Actors\visual.json")

ENTITY = "Actor Rankings"
OLD, NEW = "Rating", "+Rating"

doc = json.loads(TARGET.read_text(encoding="utf-8"))
projections = doc["visual"]["query"]["queryState"]["Values"]["projections"]

old_ref, new_ref = f"{ENTITY}.{OLD}", f"{ENTITY}.{NEW}"
hits = 0
for p in projections:
    if p.get("queryRef") == old_ref:
        p["field"]["Column"]["Property"] = NEW
        p["queryRef"] = new_ref
        p["nativeQueryRef"] = NEW
        hits += 1
assert hits == 1, f"expected 1 Rating projection, found {hits}"

# the width selector is keyed by queryRef; leave the tuned VALUE untouched
widths = doc["visual"]["objects"].get("columnWidth", [])
moved = 0
for w in widths:
    if w.get("selector", {}).get("metadata") == old_ref:
        w["selector"]["metadata"] = new_ref
        moved += 1

# a sort or filter still pointing at the old column would silently break
sort = doc["visual"]["query"].get("sortDefinition", {}).get("sort", [])
for s in sort:
    assert s["field"].get("Column", {}).get("Property") != OLD, \
        "sort targets Rating; update it too"
for f in doc.get("filterConfig", {}).get("filters", []):
    assert f["field"].get("Column", {}).get("Property") != OLD, \
        f"filter {f.get('name')} targets Rating; update it too"

TARGET.write_text(json.dumps(doc, indent=2), encoding="utf-8")
print(f"projection  {old_ref} -> {new_ref}")
print(f"columnWidth selectors remapped: {moved}")
print("columns now:", [p["nativeQueryRef"] for p in projections])
print("sorted by:", sort[0]["field"]["Column"]["Property"], sort[0]["direction"] if sort else "-")
