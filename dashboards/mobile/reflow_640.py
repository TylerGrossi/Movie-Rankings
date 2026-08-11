"""Reflow the phone layout from a 540-unit canvas to 640, and add the third Stats chart.

Position-only, by design. The live files carry Desktop edits — filterConfig
blocks, retuned column widths, changed sorts — so this rewrites `position`
(and page height) and nothing else. Everything under `visual.objects`,
`visual.query` and `filterConfig` is left exactly as found.

The 540 budget was a deliberate underestimate; on an iPhone 15 Pro it left about
a sixth of the screen empty below the bar. 640 puts the bar near the bottom edge
and returns ~100 units to the content region.

    y   0..34    header
    y  38..566   content (one visual scrolls internally)
    y 572..640   tab bar
"""
import json, importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("bm", Path(__file__).parent / "build_mobile.py")
bm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)

PAGES = bm.PAGES
DASH = bm.DASHBOARD_PAGE
H, BAR_Y, BAR_H, SLOT = 640, 572, 68, 64
CONTENT_BOTTOM = 566

MR = bm.MR

BAR = {f"v90Tab{i+1}{s.capitalize()}": (i * SLOT, BAR_Y, SLOT, BAR_H)
       for i, (s, _) in enumerate(bm.TABS)}

LAYOUT = {
    DASH: {
        "vMobTitle":       (14, 4, 240, 28),
        "vMobStats":       (0, 36, 320, 92),
        "vMobRecentLabel": (14, 136, 240, 16),
        "vMobRecent":      (0, 156, 320, CONTENT_BOTTOM - 156),      # +100 rows
        # dashboard-page tiles are vMob90Tab1Home, not vMobv90Tab1Home
        **{"vMob" + k[1:]: v for k, v in BAR.items()},
    },
    "pgMob02Films": {
        "v01Title":    (14, 4, 240, 28),
        "v02Search":   (0, 36, 320, 38),
        "v03Director": (0, 78, 157, 38),
        "v04Actor":    (163, 78, 157, 38),
        "v05Ranked":   (0, 120, 320, CONTENT_BOTTOM - 120),          # +100
        **BAR,
    },
    "pgMob03Watchlist": {
        "v01Title": (14, 4, 240, 28),
        "v02Label": (14, 36, 240, 15),
        "v03Pick":  (0, 53, 320, 70),
        "v04Genre": (0, 127, 320, 38),
        "v05Queue": (0, 169, 320, CONTENT_BOTTOM - 169),             # +100
        **BAR,
    },
    "pgMob04People": {
        "v01Title":     (14, 4, 240, 28),
        "v02LabelDir":  (14, 36, 240, 15),
        "v03Directors": (0, 53, 320, 240),                           # +50
        "v04LabelAct":  (14, 301, 240, 15),
        "v05Actors":    (0, 318, 320, CONTENT_BOTTOM - 318),         # +50
        **BAR,
    },
    "pgMob05Stats": {
        "v01Title":       (14, 4, 240, 28),
        "v06Compare":     (0, 36, 320, 56),      # summary moves to the top
        "v02LabelDist":   (14, 98, 240, 15),
        "v03Distribution": (0, 115, 320, 133),
        "v04LabelGenre":  (14, 254, 240, 15),
        "v05Genres":      (0, 271, 320, 133),
        "v07LabelWhere":  (14, 410, 240, 15),    # new
        "v08Where":       (0, 427, 320, 133),    # new
        **BAR,
    },
}


def new_stats_visuals():
    """Third chart: where you watch. Built with the shared helpers so it picks up
    the same chrome-stripping and theme-inherited colours as the other two."""
    lbl = bm.label("v07LabelWhere", "WHERE YOU WATCH", 14, 410, 240, 15, 260)
    ch = bm.chart("v08Where", "clusteredBarChart",
                  bm.pcol(MR, "Watch Location", "Location", active=True),
                  [bm.pmea(MR, "Films Watched", "Films")],
                  0, 427, 320, 133, 320,
                  sort=bm.sort_by(bm.mea(MR, "Films Watched"), "Descending"))
    return [lbl, ch]


def reflow():
    touched = created = 0

    for pname, names in LAYOUT.items():
        pdir = PAGES / pname
        vdir = pdir / "visuals"

        # page height (the dashboard page keeps its 1600x900 desktop canvas)
        if pname != DASH:
            pj = pdir / "page.json"
            page = json.loads(pj.read_text(encoding="utf-8"))
            if page.get("height") != H:
                page["height"] = H
                pj.write_text(json.dumps(page, indent=2), encoding="utf-8")

        for vname, (x, y, w, h) in names.items():
            d = vdir / vname
            vf, mf = d / "visual.json", d / "mobile.json"
            if not vf.exists():
                continue
            doc = json.loads(vf.read_text(encoding="utf-8"))
            pos = doc["position"]
            # desktop x is parked off-canvas for the dashboard-page visuals
            doc["position"] = {**pos, "x": (bm.OFFSCREEN_X + x) if pname == DASH else x,
                               "y": y, "width": w, "height": h}
            vf.write_text(json.dumps(doc, indent=2), encoding="utf-8")

            mob = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else \
                {"$schema": bm.S_MOB, "position": {}}
            mob["position"] = {**mob.get("position", {}), **pos,
                               "x": x, "y": y, "width": w, "height": h}
            mf.write_text(json.dumps(mob, indent=2), encoding="utf-8")
            touched += 1

    # the new Stats visuals
    sdir = PAGES / "pgMob05Stats" / "visuals"
    for v in new_stats_visuals():
        d = sdir / v["name"]
        if (d / "visual.json").exists():
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
        (d / "mobile.json").write_text(
            json.dumps({"$schema": bm.S_MOB, "position": dict(v["position"])}, indent=2),
            encoding="utf-8")
        created += 1

    # nothing may cross the bar or the canvas
    for pname, names in LAYOUT.items():
        for vname, (x, y, w, h) in names.items():
            if not (PAGES / pname / "visuals" / vname / "visual.json").exists():
                continue
            assert x + w <= 320, f"{pname}/{vname} wider than 320"
            assert y + h <= H, f"{pname}/{vname} past {H}"
            if y < BAR_Y:
                assert y + h <= CONTENT_BOTTOM, f"{pname}/{vname} collides with the bar"

    print(f"repositioned {touched} visuals, created {created}")


if __name__ == "__main__":
    reflow()
