"""Add the KPI measures the mobile pages need.

All DAX is single-line on purpose: multi-line VAR/RETURN in TMDL depends on
exact indentation relative to the properties that follow, and fails silently —
the measure is dropped and every visual bound to it shows "Something's wrong
with one or more fields."
"""
import re, uuid
from pathlib import Path

TABLES = Path(r"c:\Users\Owner\Desktop\Tyler\OneDrive\Projects\Movies"
              r"\dashboards\Movie Dashboard.SemanticModel\definition\tables")

MEASURES = {
    "Movie Rankings": [
        ("Films Watched",  "COUNTROWS('Movie Rankings')", "0"),
        ("Avg Score",      "AVERAGE('Movie Rankings'[Score])", "0.0"),
        ("Hours Watched",  "DIVIDE(SUM('Movie Rankings'[Runtime]), 60)", "#,0"),
        ("Avg vs Critics", "AVERAGE('Movie Rankings'[Score]) - AVERAGE('Movie Rankings'[Critics])",
                           "+0.0;-0.0;0.0"),
    ],
    # chart Y-axes need a measure: a bare column would require an Aggregation
    # wrapper, and a wrong Function code silently blanks the visual.
    "Genre Rankings": [
        ("Genre Avg", "AVERAGE('Genre Rankings'[Average])", "0.0"),
    ],
    "Movies to Watch": [
        ("Watchlist Count", "COUNTROWS('Movies to Watch')", "0"),
        ("Top Pick", "CALCULATE(MAX('Movies to Watch'[Movie]), TOPN(1, ALLSELECTED('Movies to Watch'), "
                     "'Movies to Watch'[Predicted Score], DESC))", None),
        ("Top Pick Score", "MAXX(ALLSELECTED('Movies to Watch'), 'Movies to Watch'[Predicted Score])", "0.0"),
    ],
}


def block(name, dax, fmt):
    out = [f"\tmeasure '{name}' = {dax}"]
    if fmt:
        out.append(f"\t\tformatString: {fmt}")
    out.append(f"\t\tlineageTag: {uuid.uuid4()}")
    out.append("")
    return "\n".join(out) + "\n"


for table, defs in MEASURES.items():
    path = TABLES / f"{table}.tmdl"
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{table}: unexpected BOM"
    text = raw.decode("utf-8")

    # insert immediately before the first column definition
    m = re.search(r"^\tcolumn ", text, re.M)
    assert m, f"{table}: no column found"
    at = m.start()

    added = []
    chunk = ""
    for name, dax, fmt in defs:
        if re.search(r"^\tmeasure '?" + re.escape(name) + r"'?\s*=", text, re.M):
            print(f"  skip (exists): {table}[{name}]")
            continue
        chunk += block(name, dax, fmt)
        added.append(name)

    if not added:
        continue

    text = text[:at] + chunk + text[at:]
    path.write_bytes(text.encode("utf-8"))   # UTF-8, no BOM
    print(f"{table}: added {', '.join(added)}")
