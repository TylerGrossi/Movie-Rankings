# dashboards/

All Power BI artifacts live here.

```text
dashboards/
├── Movie Dashboard.pbix        # the working binary — edited in Power BI Desktop
└── Movie Dashboard.pbip        # PBIP export — diffable PBIR JSON + TMDL
    Movie Dashboard.Report/     #   report layer: pages, visuals, mobile.json
    Movie Dashboard.SemanticModel/  #   model layer: tables, measures (TMDL)
```

## Why both

The `.pbix` is a binary that agents cannot read or edit. The `.pbip` is the same
report exported as plain-text JSON/TMDL, which agents *can* edit — that is what
the **pbir-report-builder** skill writes into.

They are not kept in sync automatically. Power BI Desktop opens one or the
other; whichever you save is the one that carries your changes forward.

## Creating the .pbip

1. Open `Movie Dashboard.pbix` in Power BI Desktop
2. File → Save As → **Power BI Project (.pbip)**
3. Save into this folder

## Rules when an agent is editing the .pbip

- **Power BI Desktop must be closed.** Files cannot be written while Desktop has
  the project open, and Desktop will overwrite agent changes on save.
- Reopen the `.pbip` afterwards to see new pages and visuals.

A previous PBIP (`Movie BI/` at repo root) was deleted on 2026-07-19. It is
recoverable from git history at commit `8ee2338` and is a useful reference for
the semantic model, the custom theme (`Seppirus Dark Mode 1.1`), and a working
page-navigation `actionButton`.

## The mobile layout was GENERATED — but Desktop is now the source of truth

`build_mobile.py` **bootstrapped** the phone layout. The report has since been
edited in Power BI Desktop, and those edits are the real thing: filter configs,
retuned column widths, changed sorts. The builder knows nothing about them.

**Editing in Desktop is expected and fine. Rebuilding is what's dangerous.**
`build_mobile.py` deletes and regenerates whole visual folders, so it now
refuses to run when it detects Desktop edits (a `filterConfig` on any generated
visual is the tell — the builder never emits one). Pass `--force` only if you
genuinely want to reset the layout and lose that tuning.

To change one thing, **patch it** — see `patch_actors_rating.py` for the shape:
read the file, change the one projection, remap the `columnWidth` selector that
points at it, assert nothing else referenced the old column, write it back.
Column widths are keyed by `queryRef`, so renaming a column without remapping
its selector silently orphans the width.

```bash
cd dashboards/mobile
python gen_icons.py ./icons     # 10 tab-bar tiles (5 tabs x on/off)
python install_icons.py ./icons # copy into StaticResources + register in report.json
python add_measures.py          # KPI measures (idempotent — skips existing)
python build_mobile.py          # the five phone layouts
```

### How web and mobile are kept apart

Power BI Mobile hides `HiddenInViewMode` pages from its page list, so the entry
point cannot itself be hidden. Therefore:

- **Home** lives on the existing **Movie Dashboard** page (page 1, already
  visible on web) as mobile-only visuals named `vMob*`, parked at **x ≥ 1700**.
  A 1600×900 `FitToPage` page clips to its canvas, so they never render on web;
  their `mobile.json` places them correctly on the phone.
- **Films / Watchlist / People / Stats** are separate pages, all
  `HiddenInViewMode`, reachable only by tapping the tab bar.

Net effect: the web report gains nothing visible. Deleting a visual's
`mobile.json` is the *only* way to hide it on phone.

### Why every page stops at y=640

Nothing in Power BI mobile can be sticky — the phone canvas scrolls as one unit.
Keeping every page inside one viewport is what makes the tab bar *look* fixed.
The one long list per page scrolls **inside its own table** instead. Both
`build_mobile.py` and `reflow_640.py` assert this; if a page overflows, the bar
drops below the fold.

**640 is measured, not calculated.** The first build used 540, derived from
subtracting assumed Power BI chrome from the iPhone 15 Pro's 393×852 — that
estimate was too conservative and left roughly a sixth of the screen empty below
the bar. Don't re-derive this number from device specs; it depends on Power BI's
own chrome, which the docs don't publish. Check it on a real phone and adjust
the one constant.

    y   0..34    header
    y  38..566   content (one visual scrolls internally)
    y 572..640   tab bar (5 transparent 64×68 tiles)

Tab tiles have **transparent** backgrounds so the page colour shows through;
only a faint top hairline marks the bar. `gen_icons.py` must save RGBA — calling
`.convert("RGB")` before save silently reintroduces the opaque block.

### Changing the layout after Desktop edits

`reflow_640.py` is the worked example: it rewrites `position` and page height
across every visual and touches nothing else, so filters, sorts and column
widths survive. Copy that shape for future layout changes rather than reaching
for `build_mobile.py --force`.
