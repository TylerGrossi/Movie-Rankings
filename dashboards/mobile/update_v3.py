"""v3: Series tab replaces Stats, Films becomes a filter hub, Home gains a chart.

Preserves Desktop edits. Slicers already carry hand-built filterConfig blocks
and the People tables carry retuned widths and sorts; anything rebuilt here has
its existing filterConfig lifted off the old file and re-attached, and anything
not mentioned is left untouched.

Changes
-------
Home      recent list shortened to make room for a score-distribution chart
          (no data labels — the bars are the point, the numbers are noise)
Films     four labelled filters: FILM / DIRECTOR / ACTOR / GENRE, each with a
          Select All checkbox. Genre comes from Movie_Genres[Genre], which is
          bothDirections to Movie Rankings so it matches any of a film's three
          genre slots rather than just Genre1.
Watchlist genre slicer gains a title and Select All
Series    NEW page, replaces Stats. Series picker + per-series summary +
          the films of the selected series in running order.
Bar       Stats tile swapped for Series across all five pages.
"""
import json, importlib.util, shutil
from pathlib import Path

_spec = importlib.util.spec_from_file_location("bm", Path(__file__).parent / "build_mobile.py")
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)

PAGES, DASH = bm.PAGES, bm.DASHBOARD_PAGE
H, BAR_Y, BAR_H, SLOT, CONTENT_BOTTOM = 640, 572, 68, 64, 566
MR, MTW, DR, AR = bm.MR, bm.MTW, bm.DR, bm.AR
M_ACT, M_DIR = bm.M_ACT, bm.M_DIR
M_GEN, SERIES = "Movie_Genres", "All Series Mapping"

OLD_STATS, NEW_SERIES = "pgMob05Stats", "pgMob05Series"
TABS = [("home", DASH), ("films", "pgMob02Films"), ("watchlist", "pgMob03Watchlist"),
        ("people", "pgMob04People"), ("series", NEW_SERIES)]

lit, num, txt, solid = bm.lit, bm.num, bm.txt, bm.solid
col, mea, pcol, pmea = bm.col, bm.mea, bm.pcol, bm.pmea
label, table, chart, stat_card, sort_by = bm.label, bm.table, bm.chart, bm.stat_card, bm.sort_by


# ------------------------------------------------------------------ helpers
def keep_filters(page, vname, doc):
    """Carry a hand-built filterConfig across a rebuild of the same visual."""
    old = PAGES / page / "visuals" / vname / "visual.json"
    if old.exists():
        prev = json.loads(old.read_text(encoding="utf-8"))
        if "filterConfig" in prev:
            doc["filterConfig"] = prev["filterConfig"]
    return doc


def filter_slicer(page, name, entity, prop, x, y, w, h, z, search=False):
    """Slicer with Select All. `selection.selectAllCheckboxEnabled` is the
    property Desktop itself uses elsewhere in this report — not invented."""
    v = bm.slicer(name, entity, prop, x, y, w, h, z, search=search)
    v["visual"]["objects"]["selection"] = [{"properties": {
        "selectAllCheckboxEnabled": lit("true")}}]
    return keep_filters(page, name, v)


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")


def place(page, visuals, offscreen=False):
    vdir = PAGES / page / "visuals"
    for v in visuals:
        pos = v["position"]
        d = vdir / v["name"]
        doc = json.loads(json.dumps(v))
        if offscreen:
            doc["position"] = {**pos, "x": bm.OFFSCREEN_X + pos["x"]}
        write(d / "visual.json", doc)
        write(d / "mobile.json", {"$schema": bm.S_MOB, "position": dict(pos)})


def bar(active, prefix="v"):
    out = []
    for i, (slug, target) in enumerate(TABS):
        on = slug == active
        v = bm.visual(f"{prefix}90Tab{i+1}{slug.capitalize()}", "image",
                      i * SLOT, BAR_Y, SLOT, BAR_H, 9000 + i,
                      objects={
                          "general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
                              "PackageName": "RegisteredResources", "PackageType": 1,
                              "ItemName": f"ic_{slug}_{'on' if on else 'off'}.png"}}}}}],
                          "imageScaling": [{"properties": {"imageScalingType": txt("Fit")}}]})
        if not on:
            v["visual"]["visualContainerObjects"]["visualLink"] = [{"properties": {
                "show": lit("true"), "type": txt("PageNavigation"),
                "navigationSection": txt(target), "showDefaultTooltip": lit("false")}}]
        out.append(v)
    return out


# ------------------------------------------------------------------ pages
def home():
    p = "vMob"
    v = [
        label(f"{p}Title", "Movie Diary", 14, 4, 240, 28, 100, size=16, color=bm.FG, bold=True),
        stat_card(f"{p}Stats", [pmea(MR, "Films Watched", "Films"),
                                pmea(MR, "Avg Score", "Avg Score"),
                                pmea(MTW, "Watchlist Count", "Watchlist")],
                  0, 36, 320, 92, 200, rows=1, cols=3, value_size=20, label_size=9),
        label(f"{p}RecentLabel", "RECENTLY WATCHED", 14, 136, 240, 16, 300),
        table(f"{p}Recent", [(MR, "Movie", None), (MR, "Score", None),
                             (MR, "Date Watched", "Watched")],
              0, 156, 320, 232, 400, widths=[168, 52, 80],
              sort=sort_by(col(MR, "Date Watched"), "Descending")),
        label(f"{p}DistLabel", "YOUR RATINGS", 14, 396, 240, 16, 500),
        chart(f"{p}Dist", "clusteredColumnChart",
              pcol(MR, "Score (bins)", "Score", active=True),
              [pmea(MR, "Films Watched", "Films")],
              0, 416, 320, CONTENT_BOTTOM - 416, 600),
    ]
    # data labels off: at 320pt the numbers collide with the bars
    v[-1]["visual"]["objects"]["labels"] = [{"properties": {"show": lit("false")}}]
    for x in v:
        x["name"] = x["name"]
    return v


def films():
    pg = "pgMob02Films"
    return [
        label("v01Title", "Films", 14, 4, 240, 28, 100, size=16, color=bm.FG, bold=True),
        label("v06LabelFilm", "FILM", 14, 36, 200, 13, 150, size=9),
        filter_slicer(pg, "v02Search", MR, "Movie", 0, 51, 320, 36, 200, search=True),
        label("v07LabelDir", "DIRECTOR", 14, 93, 140, 13, 160, size=9),
        label("v08LabelAct", "ACTOR", 177, 93, 140, 13, 170, size=9),
        filter_slicer(pg, "v03Director", M_DIR, "Director", 0, 108, 157, 36, 210, search=True),
        filter_slicer(pg, "v04Actor", M_ACT, "Actors", 163, 108, 157, 36, 220, search=True),
        label("v09LabelGenre", "GENRE", 14, 150, 200, 13, 180, size=9),
        filter_slicer(pg, "v10Genre", M_GEN, "Genre", 0, 165, 320, 36, 230, search=True),
        table("v05Ranked", [(MR, "Rank", None), (MR, "Movie", None),
                            (MR, "Score", None), (MR, "Critics", None)],
              0, 207, 320, CONTENT_BOTTOM - 207, 400, widths=[38, 152, 52, 58],
              sort=sort_by(col(MR, "Rank"), "Ascending")),
    ] + bar("films")


def watchlist():
    pg = "pgMob03Watchlist"
    return [
        label("v01Title", "Watchlist", 14, 4, 240, 28, 100, size=16, color=bm.FG, bold=True),
        label("v02Label", "TONIGHT'S PICK", 14, 36, 240, 15, 150),
        stat_card("v03Pick", [pmea(MTW, "Top Pick", "Top Pick"),
                              pmea(MTW, "Top Pick Score", "Predicted")],
                  0, 53, 320, 70, 200, rows=1, cols=2, value_size=13, label_size=9),
        label("v06LabelGenre", "GENRE", 14, 129, 200, 13, 250, size=9),
        filter_slicer(pg, "v04Genre", MTW, "Genre1", 0, 144, 320, 36, 300, search=True),
        table("v05Queue", [(MTW, "Movie", None), (MTW, "Year", None),
                           (MTW, "Predicted Score", "Pred"), (MTW, "Star", None)],
              0, 186, 320, CONTENT_BOTTOM - 186, 400, widths=[150, 40, 60, 48],
              sort=sort_by(col(MTW, "Predicted Score"), "Descending")),
    ] + bar("watchlist")


def series():
    pg = NEW_SERIES
    return [
        label("v01Title", "Series", 14, 4, 240, 28, 100, size=16, color=bm.FG, bold=True),
        label("v02LabelPick", "SERIES", 14, 36, 200, 13, 150, size=9),
        filter_slicer(pg, "v03Slicer", SERIES, "Series", 0, 51, 320, 36, 200, search=True),
        label("v04LabelAll", "ALL SERIES", 14, 95, 240, 15, 250),
        table("v05Summary", [(SERIES, "Series", None)],
              0, 112, 320, 190, 300, widths=[150],
              sort=sort_by(mea(SERIES, "Series Avg"), "Descending")),
        label("v06LabelFilms", "FILMS IN ORDER", 14, 310, 240, 15, 350),
        table("v07Films", [(SERIES, "Series Order", "#"), (SERIES, "Movie", None),
                           (SERIES, "Score", None), (SERIES, "Year", None)],
              0, 327, 320, CONTENT_BOTTOM - 327, 400, widths=[28, 158, 52, 52],
              sort=sort_by(col(SERIES, "Series Order"), "Ascending")),
    ] + bar("series")


def main():
    # the summary table mixes a column with two measures, which `table` cannot express
    s = series()
    summary = next(v for v in s if v["name"] == "v05Summary")
    q = summary["visual"]["query"]["queryState"]["Values"]["projections"]
    q.append(pmea(SERIES, "Series Films", "Films"))
    q.append(pmea(SERIES, "Series Avg", "Avg"))
    summary["visual"]["objects"]["columnWidth"] = [
        {"properties": {"value": num(w)}, "selector": {"metadata": p["queryRef"]}}
        for p, w in zip(q, [150, 60, 60])]
    # only films that actually belong to a series
    summary["filterConfig"] = {"filters": [{
        "name": "seriesnotblank0001",
        "field": col(SERIES, "Series"),
        "type": "Categorical",
        "filter": {"Version": 2,
                   "From": [{"Name": "s", "Entity": SERIES, "Type": 0}],
                   "Where": [{"Condition": {"Not": {"Expression": {"In": {
                       "Expressions": [{"Column": {
                           "Expression": {"SourceRef": {"Source": "s"}}, "Property": "Series"}}],
                       "Values": [[{"Literal": {"Value": "null"}}]]}}}}}]}}]}

    place(DASH, home(), offscreen=True)
    place(DASH, bar("home", prefix="vMob"), offscreen=True)
    place("pgMob02Films", films())
    place("pgMob03Watchlist", watchlist())
    place("pgMob04People", bar("people"))          # People content untouched

    sdir = PAGES / NEW_SERIES
    write(sdir / "page.json", {
        "$schema": bm.S_PAGE, "name": NEW_SERIES, "displayName": "Series",
        "displayOption": "FitToPage", "width": 320, "height": H,
        "visibility": "HiddenInViewMode",
        "objects": {"background": [{"properties": {"color": solid(bm.BG),
                                                   "transparency": num(0)}}]}})
    place(NEW_SERIES, s)

    # retire Stats and its now-orphaned tiles
    if (PAGES / OLD_STATS).exists():
        bm.rmtree(PAGES / OLD_STATS)
    for pname in [DASH, "pgMob02Films", "pgMob03Watchlist", "pgMob04People", NEW_SERIES]:
        for d in (PAGES / pname / "visuals").iterdir():
            if d.name.endswith("Stats") and "Tab" in d.name:
                bm.rmtree(d)

    meta_path = PAGES / "pages.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["pageOrder"] = [p for p in meta["pageOrder"] if p != OLD_STATS]
    if NEW_SERIES not in meta["pageOrder"]:
        meta["pageOrder"].append(NEW_SERIES)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for pname in [DASH, "pgMob02Films", "pgMob03Watchlist", "pgMob04People", NEW_SERIES]:
        for d in (PAGES / pname / "visuals").iterdir():
            f = d / "mobile.json"
            if not f.exists():
                continue
            p = json.loads(f.read_text(encoding="utf-8"))["position"]
            assert p["x"] + p["width"] <= 320, f"{pname}/{d.name} too wide"
            assert p["y"] + p["height"] <= H, f"{pname}/{d.name} past {H}"
            if p["y"] < BAR_Y:
                assert p["y"] + p["height"] <= CONTENT_BOTTOM, f"{pname}/{d.name} hits the bar"
    print("v3 applied")


if __name__ == "__main__":
    main()
