"""Generate the mobile tab-bar tiles for the Movie Dashboard.

Each PNG is a COMPLETE bar slot: TRANSPARENT background, line glyph,
baked text label, and (active variant) the cyan top indicator. Five tiles laid
edge to edge form a seamless 320pt bar, so the bar costs 5 image visuals per
page instead of a background + icons + buttons + indicators.

Text is rasterised here, so nothing depends on a font being present on the phone.

Palette comes from the report's own theme (Seppirus Dark Mode 1.1):
  page background #31394C   foreground #FFFFFF   dataColors[1] #00DEFF
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

SLOT_W, SLOT_H = 64, 68        # pt, as placed on the phone canvas
SS = 8                          # supersample
GLYPH = 26                      # glyph box, pt
GLYPH_TOP = 11                  # pt from tile top
LABEL_BASE = 47                 # pt from tile top to label ascender

BAR_BG = (0, 0, 0, 0)          # transparent — the page background shows through
INACTIVE = (0xFF, 0xFF, 0xFF, 140)
ACTIVE = (0x00, 0xDE, 0xFF, 255)
HAIRLINE = (0xFF, 0xFF, 0xFF, 22)   # faint divider so the bar still reads as a bar

VB = 100                        # glyph viewbox
STROKE = 8.0

FONT_PATH = r"C:\Windows\Fonts\segoeui.ttf"
FONT_PATH_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


# ------------------------------------------------------------------ glyphs
# drawn in a 100x100 viewbox on their own transparent layer, then pasted

def _s(v, scale):
    return v * scale


def mk_stroker(d, scale):
    def stroke(pts, color, w=STROKE, closed=False, caps=True):
        p = [(_s(x, scale), _s(y, scale)) for x, y in pts]
        if closed:
            p = p + [p[0]]
        d.line(p, fill=color, width=int(_s(w, scale)), joint="curve")
        if caps:
            r = _s(w, scale) / 2.0
            for x, y in (p if closed else [p[0], p[-1]]):
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    return stroke


def home(d, c, scale):
    st = mk_stroker(d, scale)
    st([(12, 52), (50, 18), (88, 52)], c)
    st([(23, 47), (23, 86), (77, 86), (77, 47)], c)
    st([(40, 86), (40, 65), (60, 65), (60, 86)], c)


def films(d, c, scale):
    st = mk_stroker(d, scale)
    st([(14, 24), (86, 24), (86, 82), (14, 82)], c, closed=True)
    st([(32, 24), (32, 82)], c, w=6, caps=False)
    st([(68, 24), (68, 82)], c, w=6, caps=False)
    for y in (36, 53, 70):
        for x in (23, 77):
            r = _s(4.2, scale)
            d.ellipse([_s(x, scale) - r, _s(y, scale) - r,
                       _s(x, scale) + r, _s(y, scale) + r], fill=c)


def watchlist(d, c, scale):
    st = mk_stroker(d, scale)
    st([(28, 14), (28, 88), (50, 68), (72, 88), (72, 14)], c, closed=True)


def people(d, c, scale):
    r = 15
    d.ellipse([_s(50 - r, scale), _s(30 - r, scale),
               _s(50 + r, scale), _s(30 + r, scale)],
              outline=c, width=int(_s(STROKE, scale)))
    d.arc([_s(19, scale), _s(56, scale), _s(81, scale), _s(112, scale)],
          start=180, end=360, fill=c, width=int(_s(STROKE, scale)))
    cap = _s(STROKE, scale) / 2.0
    for x in (_s(19, scale) + cap, _s(81, scale) - cap):
        d.ellipse([x - cap, _s(84, scale) - cap, x + cap, _s(84, scale) + cap], fill=c)


def stats(d, c, scale):
    st = mk_stroker(d, scale)
    for x, top in ((26, 66), (50, 42), (74, 24)):
        st([(x, top), (x, 84)], c, w=11)


def series(d, c, scale):
    """2x2 grid — a collection/library, deliberately unlike the filmstrip so the
    Films and Series tabs never read as the same icon at 26pt."""
    st = mk_stroker(d, scale)
    for x0, y0 in ((16, 18), (54, 18), (16, 52), (54, 52)):
        st([(x0, y0), (x0 + 30, y0), (x0 + 30, y0 + 30), (x0, y0 + 30)],
           c, w=7, closed=True)


TABS = [
    ("home", "Home", home),
    ("films", "Films", films),
    ("watchlist", "Watchlist", watchlist),
    ("people", "People", people),
    ("series", "Series", series),
]


def render(slug, label, glyph_fn, active):
    color = ACTIVE if active else INACTIVE
    W, H = SLOT_W * SS, SLOT_H * SS
    tile = Image.new("RGBA", (W, H), BAR_BG)
    d = ImageDraw.Draw(tile)

    # hairline along the top edge of the bar
    d.rectangle([0, 0, W, max(1, SS // 8)], fill=HAIRLINE)

    # active indicator: a short cyan bar centred on the top edge
    if active:
        w = 22 * SS
        d.rectangle([(W - w) // 2, 0, (W + w) // 2, 3 * SS], fill=ACTIVE)

    # glyph on its own layer so the 100-unit viewbox maps onto GLYPH pt
    gpx = GLYPH * SS
    layer = Image.new("RGBA", (gpx, gpx), (0, 0, 0, 0))
    glyph_fn(ImageDraw.Draw(layer), color, gpx / VB)
    tile.alpha_composite(layer, ((W - gpx) // 2, GLYPH_TOP * SS))

    # label
    font = ImageFont.truetype(FONT_PATH_BOLD if active else FONT_PATH, int(9.5 * SS))
    tw = d.textbbox((0, 0), label, font=font)[2]
    d.text(((W - tw) // 2, LABEL_BASE * SS), label, font=font, fill=color)

    tile = tile.resize((SLOT_W * 4, SLOT_H * 4), Image.LANCZOS)   # 4x asset
    path = OUT / f"ic_{slug}_{'on' if active else 'off'}.png"
    tile.save(path, "PNG", optimize=True)   # keep alpha
    return path


for slug, label, fn in TABS:
    for active in (False, True):
        p = render(slug, label, fn, active)
        print(f"{p.name:24} {p.stat().st_size:>6} bytes")
