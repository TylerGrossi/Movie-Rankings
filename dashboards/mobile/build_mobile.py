"""Build the mobile experience for the Movie Dashboard.

Web/mobile separation
---------------------
Power BI Mobile hides `HiddenInViewMode` pages from its page list, so the entry
point cannot itself be hidden. The Home layout therefore lives on the EXISTING
"Movie Dashboard" page (already page 1, already visible on web) as mobile-only
visuals parked off-canvas at x >= 1700. A 1600x900 FitToPage page clips to its
canvas, so those visuals never render on web, but mobile.json places them
correctly on the phone.

The other four tabs are new pages, all HiddenInViewMode, reachable only by
tapping the bar. Nothing new appears on the web report.

Viewport
--------
iPhone 15 Pro: 393x852pt. Minus status bar (59), PBI top bar (~44), page-nav
footer + home indicator (~78) leaves ~671pt of device height. The phone canvas
is ~324 units wide and scales to device width, so 671 / (393/324) ~= 553 canvas
units are visible. Everything is built to 540 for margin — that is what keeps
the tab bar on screen, since the phone canvas scrolls as one unit and nothing
in Power BI mobile can be sticky.

    y   0..34    header
    y  38..466   content (one visual scrolls internally)
    y 472..540   tab bar (5 image tiles, 64x68 each)
"""
import json, shutil, time, os, stat, sys
from pathlib import Path


def rmtree(path, attempts=8):
    """OneDrive transiently locks folders it is syncing; retry rather than fail."""
    def on_error(func, p, exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    for i in range(attempts):
        try:
            shutil.rmtree(path, onexc=on_error)
            return
        except (PermissionError, OSError):
            if i == attempts - 1:
                raise
            time.sleep(0.4 * (i + 1))

REPORT = Path(r"c:\Users\Owner\Desktop\Tyler\OneDrive\Projects\Movies"
              r"\dashboards\Movie Dashboard.Report\definition")
PAGES = REPORT / "pages"
DASHBOARD_PAGE = "2cec21eda0ac65e6e68a"        # "Movie Dashboard" — the mobile entry point
OFFSCREEN_X = 1700                              # beyond the 1600-wide canvas

S_VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.11.0/schema.json"
S_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
S_MOB = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainerMobileState/2.5.0/schema.json"

W, H = 320, 540
BAR_Y, BAR_H, SLOT = 472, 68, 64
CONTENT_BOTTOM = 466

BG, PANEL, FG = "#31394C", "#262D3C", "#FFFFFF"
MUTED, ACCENT = "#8A93A6", "#00DEFF"

MR, MTW = "Movie Rankings", "Movies to Watch"
DR, AR, GR = "Director Rankings", "Actor Rankings", "Genre Rankings"
M_ACT, M_DIR = "Movie_Actors", "Movie_Directors"


# ------------------------------------------------------------------ helpers
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def num(v): return lit(f"{v}D")
def txt(v): return lit(f"'{v}'")
def solid(h): return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{h}'"}}}}}
def col(e, p): return {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}
def mea(e, p): return {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}


def proj(field, e, p, display=None, active=False):
    d = {"field": field, "queryRef": f"{e}.{p}", "nativeQueryRef": p}
    if active:
        d["active"] = True
    if display:
        d["displayName"] = display
    return d


def pcol(e, p, display=None, active=False): return proj(col(e, p), e, p, display, active)
def pmea(e, p, display=None): return proj(mea(e, p), e, p, display)


NO_CHROME = {
    "border": [{"properties": {"show": lit("false")}}],
    "background": [{"properties": {"show": lit("false")}}],
    "visualHeader": [{"properties": {"show": lit("false")}}],
    "title": [{"properties": {"show": lit("false")}}],
}


def visual(name, vtype, x, y, w, h, z, *, objects=None, vco=None, query=None, sort=None):
    v = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if query:
        v["query"] = {"queryState": query}
        if sort:
            v["query"]["sortDefinition"] = {"sort": sort}
    if objects:
        v["objects"] = objects
    v["visualContainerObjects"] = {**NO_CHROME, **(vco or {})}
    return {"$schema": S_VC, "name": name,
            "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
            "visual": v}


def sort_by(field, direction): return [{"field": field, "direction": direction}]


# ------------------------------------------------------------------ pieces
def label(name, text, x, y, w, h, z, size=9.5, color=MUTED, bold=False):
    """Static text via actionButton — the report has no textbox to copy, and
    inventing paragraph JSON risks a blank visual."""
    props = {"text": txt(text), "fontSize": num(size), "fontColor": solid(color),
             "horizontalAlignment": txt("left"),
             "leftMargin": lit("0L"), "topMargin": lit("0L"), "bottomMargin": lit("0L")}
    if bold:
        props["bold"] = lit("true")
    return visual(name, "actionButton", x, y, w, h, z, objects={
        "text": [{"properties": {"show": lit("true")}},
                 {"properties": props, "selector": {"id": "default"}}],
        "fill": [{"properties": {"show": lit("false")}}],
        "outline": [{"properties": {"show": lit("false")}}],
        "icon": [{"properties": {"shapeType": txt("blank")}, "selector": {"id": "default"}}],
    })


def table(name, cols, x, y, w, h, z, widths, sort=None):
    projections = [pcol(e, c, d) for e, c, d in cols]
    assert sum(widths) <= 305, f"{name}: widths sum {sum(widths)} > 305"
    return visual(name, "tableEx", x, y, w, h, z,
                  query={"Values": {"projections": projections}}, sort=sort,
                  objects={
                      "columnHeaders": [{"properties": {
                          "fontSize": num(9), "autoSizeColumnWidth": lit("true"),
                          "fontColor": solid(MUTED), "backColor": solid(PANEL),
                          "wordWrap": lit("false")}}],
                      "values": [{"properties": {
                          "fontSize": num(9), "fontColor": solid(FG),
                          "backColor": solid(BG), "backColorSecondary": solid(PANEL),
                          "wordWrap": lit("false")}}],
                      "grid": [{"properties": {"rowPadding": num(2),
                                               "gridVertical": lit("false")}}],
                      "columnWidth": [
                          {"properties": {"value": num(wd)},
                           "selector": {"metadata": p["queryRef"]}}
                          for p, wd in zip(projections, widths)],
                  })


def stat_card(name, measures, x, y, w, h, z, rows, cols, value_size, label_size):
    return visual(name, "cardVisual", x, y, w, h, z,
                  query={"Data": {"projections": measures}},
                  objects={
                      "layout": [{"properties": {
                          "style": txt("Table"), "orientation": num(2),
                          "rowCount": lit(f"{rows}L"), "columnCount": lit(f"{cols}L")}}],
                      "value": [{"properties": {"fontSize": num(value_size),
                                                "fontColor": solid(FG)},
                                 "selector": {"id": "default"}}],
                      "label": [{"properties": {"fontSize": num(label_size),
                                                "fontColor": solid(MUTED)},
                                 "selector": {"id": "default"}}],
                  })


def slicer(name, entity, prop, x, y, w, h, z, search=True, sort=None):
    """`sort` matters more than it looks. Movie_Directors[Director] and
    Movie_Actors[Actors] carry a model-level sortByColumn (their *Sort Score*
    columns), and a slicer defaults to ascending — which lists the worst-rated
    people first. Passing Descending puts the best at the top.

    Going alphabetical instead would mean dropping sortByColumn in the model,
    which changes every visual using those columns, so it is not done here."""
    o = {"data": [{"properties": {"mode": txt("Dropdown")}}],
         "header": [{"properties": {"show": lit("false")}}],
         "items": [{"properties": {"textSize": num(9.5), "fontColor": solid(FG),
                                   "background": solid(PANEL)}}]}
    if search:
        o["general"] = [{"properties": {"selfFilterEnabled": lit("true")}}]
    return visual(name, "slicer", x, y, w, h, z,
                  query={"Values": {"projections": [pcol(entity, prop, active=True)]}},
                  sort=sort_by(col(entity, prop), sort) if sort else None,
                  objects=o)


def chart(name, vtype, category, values, x, y, w, h, z, sort=None):
    return visual(name, vtype, x, y, w, h, z,
                  query={"Category": {"projections": [category]},
                         "Y": {"projections": values}}, sort=sort,
                  objects={
                      "categoryAxis": [{"properties": {"showAxisTitle": lit("false"),
                                                       "fontSize": num(9),
                                                       "labelColor": solid(MUTED)}}],
                      "valueAxis": [{"properties": {"show": lit("false"),
                                                    "showAxisTitle": lit("false")}}],
                      "legend": [{"properties": {"show": lit("false")}}],
                      # No dataPoint override on purpose: 13 of the 15 charts on
                      # the desktop pages set none and inherit the theme's
                      # dataColors[0] (#018DA2). Setting a colour here is what
                      # made these two charts not match the rest of the report.
                      "labels": [{"properties": {"show": lit("true"), "fontSize": num(9),
                                                 "color": solid(MUTED)}}],
                  })


TABS = [("home", DASHBOARD_PAGE), ("films", "pgMob02Films"),
        ("watchlist", "pgMob03Watchlist"), ("people", "pgMob04People"),
        ("stats", "pgMob05Stats")]


def bar(active_slug, prefix=""):
    out = []
    for i, (slug, target) in enumerate(TABS):
        active = slug == active_slug
        v = visual(f"{prefix or 'v'}90Tab{i+1}{slug.capitalize()}", "image",
                   i * SLOT, BAR_Y, SLOT, BAR_H, 9000 + i,
                   objects={
                       "general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
                           "PackageName": "RegisteredResources", "PackageType": 1,
                           "ItemName": f"ic_{slug}_{'on' if active else 'off'}.png"}}}}}],
                       "imageScaling": [{"properties": {"imageScalingType": txt("Fit")}}]})
        if not active:
            v["visual"]["visualContainerObjects"]["visualLink"] = [{"properties": {
                "show": lit("true"), "type": txt("PageNavigation"),
                "navigationSection": txt(target), "showDefaultTooltip": lit("false")}}]
        out.append(v)
    return out


# ------------------------------------------------------------------ layouts
def home_visuals():
    """Lives on the existing Movie Dashboard page; prefixed to avoid collisions."""
    p = "vMob"
    return [
        label(f"{p}Title", "Movie Diary", 14, 4, 240, 28, 100, size=16, color=FG, bold=True),
        # Three stats across one row (Hours dropped). The 2x2 grid it replaces
        # gave each label ~150pt and still truncated "Avg Score" to "Avg Sc...";
        # one row of three gives ~106pt each but drops the second row entirely,
        # returning 26pt to the list below.
        stat_card(f"{p}Stats", [
            pmea(MR, "Films Watched", "Films"),
            pmea(MR, "Avg Score", "Avg Score"),
            pmea(MTW, "Watchlist Count", "Watchlist"),
        ], 0, 36, 320, 92, 200, rows=1, cols=3, value_size=20, label_size=9),
        label(f"{p}RecentLabel", "RECENTLY WATCHED", 14, 136, 240, 16, 300),
        table(f"{p}Recent", [(MR, "Movie", None), (MR, "Score", None),
                             (MR, "Date Watched", "Watched")],
              0, 156, 320, CONTENT_BOTTOM - 156, 400, widths=[168, 52, 80],
              sort=sort_by(col(MR, "Date Watched"), "Descending")),
    ] + bar("home", prefix=p)


def page_films():
    return [
        label("v01Title", "Films", 14, 4, 240, 28, 100, size=16, color=FG, bold=True),
        slicer("v02Search", MR, "Movie", 0, 36, 320, 38, 200),
        slicer("v03Director", M_DIR, "Director", 0, 78, 157, 38, 210, sort="Descending"),
        slicer("v04Actor", M_ACT, "Actors", 163, 78, 157, 38, 220, sort="Descending"),
        table("v05Ranked", [(MR, "Rank", None), (MR, "Movie", None),
                            (MR, "Score", None), (MR, "Critics", None)],
              0, 120, 320, CONTENT_BOTTOM - 120, 400, widths=[38, 152, 52, 58],
              sort=sort_by(col(MR, "Rank"), "Ascending")),
    ] + bar("films")


def page_watchlist():
    return [
        label("v01Title", "Watchlist", 14, 4, 240, 28, 100, size=16, color=FG, bold=True),
        label("v02Label", "TONIGHT'S PICK", 14, 36, 240, 15, 150),
        stat_card("v03Pick", [pmea(MTW, "Top Pick", "Top Pick"),
                              pmea(MTW, "Top Pick Score", "Predicted")],
                  0, 53, 320, 70, 200, rows=1, cols=2, value_size=13, label_size=9),
        slicer("v04Genre", MTW, "Genre1", 0, 127, 320, 38, 300),
        table("v05Queue", [(MTW, "Movie", None), (MTW, "Year", None),
                           (MTW, "Predicted Score", "Pred"), (MTW, "Star", None)],
              0, 169, 320, CONTENT_BOTTOM - 169, 400, widths=[150, 40, 60, 48],
              sort=sort_by(col(MTW, "Predicted Score"), "Descending")),
    ] + bar("watchlist")


def page_people():
    return [
        label("v01Title", "People", 14, 4, 240, 28, 100, size=16, color=FG, bold=True),
        label("v02LabelDir", "TOP DIRECTORS", 14, 36, 240, 15, 150),
        table("v03Directors", [(DR, "Rank", None), (DR, "Director", None),
                               (DR, "Rating", None), (DR, "Movies", None),
                               (DR, "Average", "Avg")],
              0, 53, 320, 190, 300, widths=[30, 116, 52, 50, 52],
              sort=sort_by(col(DR, "Rank"), "Ascending")),
        label("v04LabelAct", "TOP ACTORS", 14, 251, 240, 15, 350),
        # actors use +Rating, not Rating (directors keep Rating)
        table("v05Actors", [(AR, "Rank", None), (AR, "Best Actors", "Actor"),
                            (AR, "+Rating", None), (AR, "Movies", None),
                            (AR, "Average", "Avg")],
              0, 268, 320, CONTENT_BOTTOM - 268, 400, widths=[40, 106, 52, 50, 52],
              sort=sort_by(col(AR, "Rank"), "Ascending")),
    ] + bar("people")


def page_stats():
    return [
        label("v01Title", "Stats", 14, 4, 240, 28, 100, size=16, color=FG, bold=True),
        label("v02LabelDist", "SCORE DISTRIBUTION", 14, 36, 240, 15, 150),
        chart("v03Distribution", "clusteredColumnChart",
              pcol(MR, "Score (bins)", "Score"), [pmea(MR, "Films Watched", "Films")],
              0, 53, 320, 160, 200),
        label("v04LabelGenre", "AVG SCORE BY GENRE", 14, 221, 240, 15, 250),
        chart("v05Genres", "clusteredBarChart",
              pcol(GR, "Genres", "Genre"), [pmea(GR, "Genre Avg", "Avg")],
              0, 238, 320, 160, 300,
              sort=sort_by(mea(GR, "Genre Avg"), "Descending")),
        stat_card("v06Compare", [pmea(MR, "Avg Score", "Your Avg"),
                                 pmea(MR, "Avg vs Critics", "vs Critics")],
                  0, 404, 320, CONTENT_BOTTOM - 404, 400, rows=1, cols=2,
                  value_size=16, label_size=9),
    ] + bar("stats")


NEW_PAGES = [("pgMob02Films", "Films", page_films),
             ("pgMob03Watchlist", "Watchlist", page_watchlist),
             ("pgMob04People", "People", page_people),
             ("pgMob05Stats", "Stats", page_stats)]


# ------------------------------------------------------------------ write
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check(pname, visuals):
    names = [v["name"] for v in visuals]
    assert len(names) == len(set(names)), f"{pname}: duplicate visual names"
    for v in visuals:
        p = v["position"]
        assert p["x"] + p["width"] <= W, f"{pname}/{v['name']} wider than {W}"
        assert p["y"] + p["height"] <= H, f"{pname}/{v['name']} past {H}"
        if p["y"] < BAR_Y:
            assert p["y"] + p["height"] <= CONTENT_BOTTOM, \
                f"{pname}/{v['name']} collides with tab bar"


def guard_against_desktop_edits(force):
    """Refuse to clobber work done in Power BI Desktop.

    This script deletes and regenerates whole visual folders. Once the report
    has been opened and edited in Desktop, the live files carry things the
    builder has no idea about — filterConfig blocks, retuned column widths,
    changed sorts. Rebuilding would silently discard them.

    A filterConfig is the reliable tell: the builder never emits one, so its
    presence means a human has been here. Patch surgically instead (see
    patch_actors_rating.py) or pass --force if you genuinely mean to reset.
    """
    edited = []
    for pname in [DASHBOARD_PAGE] + [p for p, _, _ in NEW_PAGES]:
        vdir = PAGES / pname / "visuals"
        if not vdir.exists():
            continue
        for d in vdir.iterdir():
            if pname == DASHBOARD_PAGE and not d.name.startswith("vMob"):
                continue
            f = d / "visual.json"
            if f.exists() and "filterConfig" in json.loads(f.read_text(encoding="utf-8")):
                edited.append(f"{pname}/{d.name}")
    if edited and not force:
        print("REFUSING TO REBUILD — these visuals carry Desktop edits:\n")
        for e in edited:
            print(f"    {e}")
        print("\nRegenerating would discard their filters, sorts and column widths.")
        print("Patch the specific file instead, or re-run with --force to reset.")
        raise SystemExit(1)
    if edited:
        print(f"--force: discarding Desktop edits on {len(edited)} visuals\n")


def main():
    force = "--force" in sys.argv
    guard_against_desktop_edits(force)

    meta_path = PAGES / "pages.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    # --- retire the old visible Home page -----------------------------------
    old = PAGES / "pgMob01Home"
    if old.exists():
        rmtree(old)
        print("removed pgMob01Home (Home now lives on the Movie Dashboard page)")
    meta["pageOrder"] = [p for p in meta["pageOrder"] if p != "pgMob01Home"]

    # --- Home onto the existing dashboard page ------------------------------
    dash = PAGES / DASHBOARD_PAGE / "visuals"
    for d in dash.iterdir():                       # drop the ad-hoc legacy phone layout
        m = d / "mobile.json"
        if m.exists() and not d.name.startswith("vMob"):
            m.unlink()
            print(f"removed legacy mobile.json from {d.name}")
    for d in list(dash.iterdir()):                 # clear our own previous run
        if d.name.startswith("vMob"):
            rmtree(d)

    home = home_visuals()
    check("MovieDashboard", home)
    for v in home:
        p = v["position"]
        mobile_pos = dict(p)
        # park off-canvas on web; a 1600x900 FitToPage page clips to its canvas
        v["position"] = {**p, "x": OFFSCREEN_X + p["x"]}
        vdir = dash / v["name"]
        write(vdir / "visual.json", v)
        write(vdir / "mobile.json", {"$schema": S_MOB, "position": mobile_pos})
    print(f"Movie Dashboard   +{len(home)} mobile-only visuals parked at x>={OFFSCREEN_X}")

    # --- the four hidden tab pages ------------------------------------------
    for pname, display, builder in NEW_PAGES:
        pdir = PAGES / pname
        if pdir.exists():
            rmtree(pdir)
        write(pdir / "page.json", {
            "$schema": S_PAGE, "name": pname, "displayName": display,
            "displayOption": "FitToPage", "width": W, "height": H,
            "visibility": "HiddenInViewMode",
            "objects": {"background": [{"properties": {"color": solid(BG),
                                                       "transparency": num(0)}}]}})
        visuals = builder()
        check(pname, visuals)
        for v in visuals:
            vdir = pdir / "visuals" / v["name"]
            write(vdir / "visual.json", v)
            write(vdir / "mobile.json", {"$schema": S_MOB, "position": dict(v["position"])})
        if pname not in meta["pageOrder"]:
            meta["pageOrder"].append(pname)
        print(f"{pname:18} {display:10} {len(visuals):>2} visuals  (hidden on web)")

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\npages.json -> {len(meta['pageOrder'])} pages")


if __name__ == "__main__":
    main()
