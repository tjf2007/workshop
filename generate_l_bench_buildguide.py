"""
Generate a printable multi-page step-by-step build guide for the L-bench.

Output: l_bench_buildguide.svg - a tall SVG composed of letter-size
(8.5 x 11 in) pages stacked vertically. Most browsers and image viewers
will print each page as its own physical page when sent to a printer
(File -> Print, fit to page).

Layout per page:
  - Title bar at the top
  - Top-down diagram of the bench at this stage (parts built so far in
    light gray, new-this-step parts in highlight orange/red)
  - Instructions panel below the diagram
  - Tools / time / part-count sidebar

The first 3 pages are the cover/checklist and cut-day reference cards.
The remaining pages are one per construction step.
"""

from __future__ import annotations

import csv
import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Page / layout constants  (SVG uses px == inches via viewBox 1:1)
# ---------------------------------------------------------------------------

PAGE_W = 8.5
PAGE_H = 11.0
MARGIN = 0.5

# Bench dimensions (inches in shop coords)
BENCH_X_MIN, BENCH_X_MAX = 0, 144     # top leg X range
BENCH_Y_MIN, BENCH_Y_MAX = 0, 120     # full L Y range
BENCH_Z_MAX = 37

# Diagram window inside each page - now split into two halves
DIAG_Y = 1.2                           # below title bar
DIAG_H = 3.5                           # height of both diagrams
DIAG_GAP = 0.25                        # gap between left and right diagram
DIAG_W_HALF = (PAGE_W - 2 * MARGIN - DIAG_GAP) / 2

# LEFT diagram = top-down plan view
DIAG_PLAN_X = MARGIN
DIAG_PLAN_W = DIAG_W_HALF
PLAN_SCALE = min(DIAG_PLAN_W / (BENCH_X_MAX - BENCH_X_MIN),
                  DIAG_H / (BENCH_Y_MAX - BENCH_Y_MIN))
PLAN_OFFSET_X = (DIAG_PLAN_X
                  + (DIAG_PLAN_W - (BENCH_X_MAX - BENCH_X_MIN) * PLAN_SCALE) / 2)
PLAN_OFFSET_Y_REL = (DIAG_H - (BENCH_Y_MAX - BENCH_Y_MIN) * PLAN_SCALE) / 2

# RIGHT diagram = isometric view (camera at high X, high Y, high Z)
DIAG_ISO_X = MARGIN + DIAG_W_HALF + DIAG_GAP
DIAG_ISO_W = DIAG_W_HALF
# Isometric projection
ISO_COS = 0.8660254  # cos(30)
ISO_SIN = 0.5        # sin(30)

def iso_project(x: float, y: float, z: float) -> tuple[float, float]:
    """Isometric projection (camera at +X, +Y, +Z). Returns (sx, sy) in
    inches before scaling/offsetting."""
    sx = (x - y) * ISO_COS
    sy = -z + (x + y) * ISO_SIN
    return sx, sy

# Iso bench bounds in screen-coords
_iso_corners = [
    iso_project(0, 0, 0), iso_project(144, 0, 0),
    iso_project(0, 36, 0), iso_project(144, 36, 0),
    iso_project(0, 36, 0), iso_project(36, 120, 0),
    iso_project(0, 0, 37), iso_project(144, 0, 37),
    iso_project(0, 36, 37), iso_project(144, 36, 37),
    iso_project(0, 120, 37), iso_project(36, 120, 37),
    iso_project(36, 120, 0), iso_project(36, 36, 0),
]
ISO_X_MIN = min(c[0] for c in _iso_corners)
ISO_X_MAX = max(c[0] for c in _iso_corners)
ISO_Y_MIN = min(c[1] for c in _iso_corners)
ISO_Y_MAX = max(c[1] for c in _iso_corners)
ISO_W_RAW = ISO_X_MAX - ISO_X_MIN
ISO_H_RAW = ISO_Y_MAX - ISO_Y_MIN
ISO_SCALE = min(DIAG_ISO_W / ISO_W_RAW, DIAG_H / ISO_H_RAW)
ISO_OFFSET_X = (DIAG_ISO_X
                + (DIAG_ISO_W - ISO_W_RAW * ISO_SCALE) / 2
                - ISO_X_MIN * ISO_SCALE)
ISO_OFFSET_Y_REL = (DIAG_H - ISO_H_RAW * ISO_SCALE) / 2 - ISO_Y_MIN * ISO_SCALE


def iso_to_screen(x: float, y: float, z: float,
                   page_y0: float) -> tuple[float, float]:
    sx, sy = iso_project(x, y, z)
    return (ISO_OFFSET_X + sx * ISO_SCALE,
            page_y0 + DIAG_Y + ISO_OFFSET_Y_REL + sy * ISO_SCALE)


def plan_to_screen(x: float, y: float, page_y0: float) -> tuple[float, float]:
    return (PLAN_OFFSET_X + x * PLAN_SCALE,
            page_y0 + DIAG_Y + PLAN_OFFSET_Y_REL + y * PLAN_SCALE)


def darken(hex_color: str, factor: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"

# Palette: white page background (no toner waste), filled parts are OK.
COL_TEXT = "#000000"
COL_SUBTLE = "#555555"
COL_RULE = "#000000"
COL_RULE_LIGHT = "#777777"
COL_GRID = "#CCCCCC"

# Wood-tone fills for parts in the diagrams (light, easy on toner)
COL_BUILT_FILL = "#EFE6D2"      # light tan (already-built)
COL_BUILT_STROKE = "#9A8E70"
COL_NEW_FILL = "#F2B26A"        # warm highlight (new this step)
COL_NEW_STROKE = "#000000"
COL_NEW_HATCH = "#7A4A12"
COL_FOOTPRINT = "#AAAAAA"

# Iso-face shading: top brightest, front mid, right darkest
COL_BUILT_TOP = "#F4ECDA"
COL_BUILT_FRONT = "#E1D5B7"
COL_BUILT_RIGHT = "#CFC09A"
COL_NEW_TOP = "#F4BB70"
COL_NEW_FRONT = "#E89D45"
COL_NEW_RIGHT = "#CC7F20"

# Fonts (loaded via HTML wrapper for printing)
FONT_TITLE = "'Abel', 'Helvetica Neue', Helvetica, Arial, sans-serif"
FONT_BODY = "'Barlow', 'Helvetica Neue', Helvetica, Arial, sans-serif"


# ---------------------------------------------------------------------------
# Read parts
# ---------------------------------------------------------------------------

@dataclass
class Part:
    name: str
    category: str
    material: str
    shape: str
    x: float
    y: float
    z: float
    w: float
    d: float
    h: float
    cutlist_part: str
    lumber: str


def load_parts() -> list[Part]:
    parts: list[Part] = []
    with (OUT_DIR / "l_bench_objects.csv").open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                parts.append(Part(
                    name=row["name"],
                    category=row["category"],
                    material=row["material"],
                    shape=row["shape"],
                    x=float(row["x"]),
                    y=float(row["y"]),
                    z=float(row["z"]),
                    w=float(row["w_or_r"]),
                    d=float(row["d_or_axis"]) if row["d_or_axis"] not in ("x", "y", "z") else 0.0,
                    h=float(row["h"]),
                    cutlist_part=row["cutlist_part"],
                    lumber=row["lumber"],
                ))
            except ValueError:
                # Cylinders have non-numeric axis - skip for the plan view
                pass
    return parts


# ---------------------------------------------------------------------------
# Build steps - each step is a dict with patterns to match part names
# ---------------------------------------------------------------------------

STEPS = [
    {
        "kind": "cover",
        "title": "L-Bench Build Guide",
        "subtitle": "Step-by-step cut + assembly, no planer lift",
    },
    {
        "kind": "lumber_checklist",
        "title": "Materials: 2x4 SPF Lumber",
    },
    {
        "kind": "ply_checklist",
        "title": "Materials: Plywood + Hardware",
    },
    {
        "kind": "cut_day_lumber",
        "title": "Cut Day 1: 2x4 Lumber",
        "instructions": [
            "Cull bad boards first - reject visible twist, crown > 1/4 in,",
            "and knots larger than 1 in at edges.",
            "Cut longest pieces first to leave usable offcuts.",
            "Stamp each piece with its name (sharpie on the end grain).",
            "Stack by length, separated by 1/4 in spacers if storing > 1 day.",
        ],
        "tools": ["Miter saw", "Tape measure", "Pencil", "Sharpie"],
        "time": "3-4 hours",
    },
    {
        "kind": "cut_day_ply",
        "title": "Cut Day 2: Plywood Sheet Goods",
        "instructions": [
            "Print l_bench_partsheets.svg as a per-piece reference.",
            "Layout the cuts on each 4x8 sheet to minimize waste (see SVG).",
            "Cut largest panels first - small pieces from offcuts.",
            "Use a straight-edge guide or track saw for clean factory edges.",
            "Label every piece in sharpie as it comes off the saw.",
        ],
        "tools": ["Circular saw + straight edge OR track saw", "Tape", "Pencil"],
        "time": "4-6 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 1: Top Leg Back Wall Frame",
        "patterns": ["TopLeg_BackStud_", "TopLeg_BackTopRail", "TopLeg_BackBottomRail"],
        "instructions": [
            "Lay the 144 in bottom rail on the floor on its narrow edge.",
            "Mark stud positions on the rail: 0, 24, 46.5, 86, 104.5, 132, 140.5.",
            "Lay the top rail parallel, 28.5 in away.",
            "Stand 7 studs (28.5 in) vertically between the rails at marks.",
            "Glue + 2 screws per joint, toenailed through rail into stud end.",
            "CHECK SQUARE: measure both diagonals - match within 1/8 in.",
        ],
        "tools": ["Drill", "Impact driver", "Square", "Tape", "Glue", "Screws"],
        "time": "1 hour",
    },
    {
        "kind": "assembly",
        "title": "Step 2: Top Leg Front Wall Frame",
        "patterns": ["TopLeg_FrontStud_", "TopLeg_FrontTopRail", "TopLeg_FrontBottomRail"],
        "instructions": [
            "Identical procedure to back wall (same 7 stud positions).",
            "Lay flat on floor, glue + screw, check square.",
            "Set both wall frames aside vertically against a wall.",
            "Front face has cavity openings, but FRAMING is identical -",
            "the openings are in the top PANELS, not the studs.",
        ],
        "tools": ["Drill", "Impact driver", "Square", "Tape", "Glue", "Screws"],
        "time": "1 hour",
    },
    {
        "kind": "assembly",
        "title": "Step 3: Top Leg Cross Stretchers (Stand the Box)",
        "patterns": ["TopLeg_TopStretcher_", "TopLeg_BottomStretcher_"],
        "instructions": [
            "Stand both wall frames parallel, 36 in apart (outside-to-outside).",
            "Use 2 helpers OR right-angle clamps to hold vertical.",
            "Cut + install 14 cross stretchers (29 in each):",
            "  - 7 at the TOP rail level, between front + back rails",
            "  - 7 at the BOTTOM rail level, same X positions",
            "Glue + 2 screws per joint, into the rails (not the studs).",
            "Result: rigid 144 x 36 x 37 in box, ready for cavities.",
        ],
        "tools": ["Drill", "Impact driver", "Clamps", "Glue", "Screws"],
        "time": "1.5 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 4: Miter Recess Blocking",
        "patterns": ["Miter_Recess_Blocking"],
        "instructions": [
            "Inside the top leg between studs at X=46.5 and X=86,",
            "build the 4 in deep recess pocket for the miter saw.",
            "Front + back blocking: 2 x 36 in pieces along Y direction at",
            "the recess drop height (z = 33 in).",
            "Side blocking: 2 x 23 in pieces between front + back blocking.",
            "Result: 36 x 30 in opening, 4 in deep, all 4 sides framed.",
            "Miter saw bolts to the recess floor later.",
        ],
        "tools": ["Drill", "Square", "Glue", "Screws"],
        "time": "45 minutes",
    },
    {
        "kind": "assembly",
        "title": "Step 5: Router Cabinet (inside top leg)",
        "patterns": ["Router_Cabinet"],
        "instructions": [
            "Between studs at X=104.5 and X=132, build the router cabinet.",
            "Drop floor (32 x 24) at bottom-rail level. Screw to bottom rail.",
            "Stand 2 side panels (32 x 31.5) along inside faces of the studs.",
            "Glue + screw to studs.",
            "Drop back panel (31.5 x 24) against back wall studs. Glue + screw.",
            "Cabinet front is LEFT OPEN - you reach in to change router bits.",
        ],
        "tools": ["Drill", "Impact driver", "Clamps", "Glue", "Screws"],
        "time": "1 hour",
    },
    {
        "kind": "assembly",
        "title": "Step 6: Short Leg Side Walls",
        "patterns": ["LeftLeg_LeftSideStud_", "LeftLeg_RightSideStud_",
                     "LeftLeg_LeftTopRail", "LeftLeg_RightTopRail",
                     "LeftLeg_LeftBottomRail", "LeftLeg_RightBottomRail"],
        "instructions": [
            "Build the short leg as TWO side walls (left + right), each 84",
            "in long x 37 in tall, on the floor like the top leg walls.",
            "Each wall: bottom rail (84 in) + top rail (84 in) + 4 studs",
            "at Y positions 38.5, 72, 80.5, 116.",
            "Square each wall (diagonal check), set aside vertically.",
        ],
        "tools": ["Drill", "Square", "Tape", "Glue", "Screws"],
        "time": "1.5 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 7: Short Leg Cross Stretchers",
        "patterns": ["LeftLeg_TopStretcher_", "LeftLeg_BottomStretcher_"],
        "instructions": [
            "Stand both short-leg walls parallel, 36 in apart (outside-out).",
            "Connect with 8 cross stretchers (29 in each):",
            "  - 4 at TOP rail level at Y=38.5, 72, 80.5, 116",
            "  - 4 at BOTTOM rail level, same Y positions",
            "Glue + screw at each joint.",
            "Result: rigid 36 x 84 x 37 in box.",
        ],
        "tools": ["Drill", "Impact driver", "Clamps", "Glue", "Screws"],
        "time": "1 hour",
    },
    {
        "kind": "assembly",
        "title": "Step 8: Join + Anchor to Walls",
        "patterns": [],
        "highlight_zone": "wall_anchors",
        "instructions": [
            "Stand TOP LEG against back wall. Level it. Shim under bottom",
            "rail until perfectly level (garage floors are never flat).",
            "Lag-bolt back face to wall studs through back rails at 16 in OC.",
            "Stand SHORT LEG into position, mate top end to top leg's left",
            "end. Square the inside L corner (measure diagonals).",
            "Lag-bolt short leg's left side (X=0) to LHS wall studs.",
            "Screw the two frames together at corner: 4-6 screws through",
            "short leg's right-side stud into top leg's left-end stud.",
            "DO NOT install the top yet - you need open access for cavities.",
        ],
        "tools": ["Drill + 5/16 bit", "Impact driver", "Level", "Lag bolts",
                  "Shims", "Wood screws"],
        "time": "2 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 9: Toe Kicks (do BEFORE the top goes on)",
        "patterns": ["ToeKick"],
        "instructions": [
            "While you can still reach the bottom rails:",
            "TopLeg back: 144 x 4 against back face of bottom rail.",
            "TopLeg front: 144 x 4 recessed 3 in from front face.",
            "TopLeg right end: 36 x 4 capping the right end.",
            "Short leg left side: 84 x 4 against LHS wall.",
            "Short leg right (room-facing) side: 84 x 4 recessed 3 in.",
            "Short leg front end: 36 x 4 capping the front.",
            "All toe kicks: glue + screw to bottom rails / studs.",
        ],
        "tools": ["Drill", "Square", "Glue", "Screws"],
        "time": "1.5 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 10: Top Panels - Top Leg",
        "patterns": ["TopLeg_Top_", "Miter_Recess_Bottom"],
        "instructions": [
            "Each top panel is DOUBLED 3/4 in ply = 1.5 in finished thickness.",
            "Glue the 2 plies together BEFORE installing:",
            "  - PL Premium adhesive in a serpentine on the lower ply",
            "  - Drop upper ply, drive #8 x 1.25 screws at 6 in OC",
            "  - Clamp for 1 hour minimum before moving",
            "Install from corner outward:",
            "  1. TopLeg_Top_Left (50 x 36)",
            "  2. Miter recess floor (36 x 30) + lips (36 x 2 back, 36 x 4 front)",
            "  3. TopLeg_Top_MidRight (36 x 22)",
            "  4. Router area sub-panels (4 small pieces around insert plate)",
            "  5. TopLeg_Top_FarRight (36 x 12)",
        ],
        "tools": ["Clamps (8+)", "Drill", "Impact driver", "PL Premium",
                  "Wood glue", "Screws"],
        "time": "3 hours + glue cure",
    },
    {
        "kind": "assembly",
        "title": "Step 11: Top Panels - Short Leg (planer cavity OPEN)",
        "patterns": ["LeftLeg_Top_"],
        "instructions": [
            "Same doubling procedure as top leg.",
            "Install in this order:",
            "  1. LeftLeg_Top_AbovePlaner (36 x 6) at Y=36..42",
            "  2. PLANER CAVITY: leave fully open at Y=42..72.",
            "     Cavity floor / strips skip until lift install.",
            "     Drop a scrap 30 x 30 over the hole as a temporary cover.",
            "  3. LeftLeg_Top_BetweenCavities (36 x 12) at Y=72..84",
            "  4. Saw cavity strips (2 x 32 x 2) at the saw cavity sides",
            "  5. LeftLeg_Top_End (36 x 4) at Y=116..120",
        ],
        "tools": ["Clamps", "Drill", "PL Premium", "Wood glue", "Screws"],
        "time": "2 hours + glue cure",
    },
    {
        "kind": "assembly",
        "title": "Step 12: Saw Sled + Cleats",
        "patterns": ["Saw_Sled", "Saw_SledCleat_"],
        "instructions": [
            "Install 4 sled cleats inside the 32 x 32 saw cavity:",
            "  - 2 x 32 in cleats at front + back (Y=84 and Y=114)",
            "  - 2 x 25 in cleats at left + right (X=2 and X=32)",
            "Cleats sit at z = 23.25 in (so 3/4 sled lands at z=24).",
            "Bolt the DeWalt DWE7491 saw to the 30 x 30 sled using the",
            "saw's mounting holes. Center carefully - blade alignment > centering.",
            "Drop sled (with saw) onto cleats. Confirm deck flush at 37 in.",
            "Shim cleats if off; don't fasten the sled - it lifts out.",
        ],
        "tools": ["Drill", "Bolts (saw to sled)", "Level", "Shims"],
        "time": "1.5 hours",
    },
    {
        "kind": "assembly",
        "title": "Step 13: End Panels + Finish",
        "patterns": ["EndPanel"],
        "instructions": [
            "Install 2 end panels (36 x 33 plywood):",
            "  - TopLeg right end at X=144, facing the existing 3x8 bench",
            "  - Short leg front end at Y=120, facing into the room",
            "Glue + screw to end stud + rails.",
            "OPTIONAL: add 1/4 in skin over front + side faces for a clean",
            "finished look. Skip if you prefer exposed framing.",
            "FINISH: sand top to 120 grit, vacuum, apply BLO or Arm-R-Seal",
            "(2-3 coats, light sand between). Cure 24-48 hrs before tools.",
        ],
        "tools": ["Drill", "Sander", "Vacuum", "Brush / rag", "Finish"],
        "time": "2 hours + finish cure",
    },
    {
        "kind": "final_check",
        "title": "Final Sanity Check",
    },
]


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------

def svg_open(width_in: float, height_in: float) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_in}in" height="{height_in}in" '
        f'viewBox="0 0 {width_in} {height_in}">',
        # Font import for browser/HTML print context. Standalone SVG viewers
        # will silently fall back to sans-serif.
        '<defs><style type="text/css">'
        '@import url("https://fonts.googleapis.com/css2?'
        'family=Abel&amp;family=Barlow:wght@400;600;700&amp;display=swap");'
        '</style></defs>',
    ]


def rect(x, y, w, h, fill="none", stroke=None, stroke_w=0.005, opacity=1.0,
         rx=0.0, dasharray=None):
    s = (f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
         f'fill="{fill}" opacity="{opacity}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{stroke_w}"'
    if rx > 0:
        s += f' rx="{rx}" ry="{rx}"'
    if dasharray:
        s += f' stroke-dasharray="{dasharray}"'
    s += ' />'
    return s


def text(x, y, txt, size=0.14, fill=None, bold=False, anchor="start",
         family=None):
    f = fill if fill else COL_TEXT
    weight = "600" if bold else "400"
    fam = family if family else FONT_BODY
    txt = (str(txt).replace("&", "&amp;").replace("<", "&lt;")
           .replace(">", "&gt;"))
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" '
            f'fill="{f}" font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{fam}">{txt}</text>')


def line(x1, y1, x2, y2, stroke=COL_RULE, stroke_w=0.01, dasharray=None):
    s = (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
         f'stroke="{stroke}" stroke-width="{stroke_w}"')
    if dasharray:
        s += f' stroke-dasharray="{dasharray}"'
    s += ' />'
    return s


def polygon(points: list[tuple[float, float]], fill="none", stroke=COL_RULE,
            stroke_w=0.008, opacity=1.0, dasharray=None):
    pts = " ".join(f"{p[0]:.3f},{p[1]:.3f}" for p in points)
    s = (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
         f'stroke-width="{stroke_w}" opacity="{opacity}"')
    if dasharray:
        s += f' stroke-dasharray="{dasharray}"'
    s += ' />'
    return s


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------

def page_origin(page_idx: int) -> float:
    return page_idx * PAGE_H


def render_page_chrome(page_idx: int, title: str, subtitle: str = "",
                       total_pages: int = 0) -> list[str]:
    """Title (Abel) + thin rule + footer page number. No backgrounds."""
    y0 = page_origin(page_idx)
    out = []
    # Title (no background bar)
    out.append(text(MARGIN, y0 + MARGIN + 0.35, title,
                    size=0.34, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    if subtitle:
        out.append(text(PAGE_W - MARGIN, y0 + MARGIN + 0.35, subtitle,
                        size=0.14, fill=COL_SUBTLE, anchor="end",
                        family=FONT_BODY))
    # Rule under the title
    out.append(line(MARGIN, y0 + MARGIN + 0.55,
                     PAGE_W - MARGIN, y0 + MARGIN + 0.55,
                     COL_RULE, stroke_w=0.012))
    # Footer page number
    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.3,
                    f"{page_idx + 1} / {total_pages}",
                    size=0.11, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))
    return out


def render_bench_plan(page_idx: int, built_patterns: list[str],
                      new_patterns: list[str], parts: list[Part]) -> list[str]:
    """Top-down view (LEFT half of page). Outlines only, no fills.
    New parts: bold black outline + light diagonal hatch.
    Built parts: thin gray outline."""
    y0 = page_origin(page_idx)
    out = []
    # Caption
    out.append(text(DIAG_PLAN_X, y0 + DIAG_Y - 0.05,
                    "TOP-DOWN PLAN  (back wall = top)",
                    size=0.10, fill=COL_SUBTLE, family=FONT_TITLE))

    # 6-inch grid (very light)
    for gx in range(0, BENCH_X_MAX + 1, 12):
        sx, _ = plan_to_screen(gx, 0, y0)
        _, sy_end = plan_to_screen(0, BENCH_Y_MAX, y0)
        _, sy_start = plan_to_screen(0, 0, y0)
        out.append(line(sx, sy_start, sx, sy_end, COL_GRID, stroke_w=0.004))
    for gy in range(0, BENCH_Y_MAX + 1, 12):
        sx_start, sy = plan_to_screen(0, gy, y0)
        sx_end, _ = plan_to_screen(BENCH_X_MAX, gy, y0)
        out.append(line(sx_start, sy, sx_end, sy, COL_GRID, stroke_w=0.004))

    # L-bench footprint outline (thin dashed)
    fx, fy = plan_to_screen(0, 0, y0)
    out.append(rect(fx, fy, 144 * PLAN_SCALE, 36 * PLAN_SCALE,
                    fill="none", stroke=COL_FOOTPRINT, stroke_w=0.008,
                    dasharray="0.04,0.03"))
    fx, fy = plan_to_screen(0, 36, y0)
    out.append(rect(fx, fy, 36 * PLAN_SCALE, 84 * PLAN_SCALE,
                    fill="none", stroke=COL_FOOTPRINT, stroke_w=0.008,
                    dasharray="0.04,0.03"))

    def matches(name: str, patterns: list[str]) -> bool:
        return any(p in name for p in patterns)

    # Two-pass render: built first (light tan), then new (highlight on top)
    for want_new in [False, True]:
        for part in parts:
            if part.shape != "box" or part.category == "ghost":
                continue
            is_new = matches(part.name, new_patterns)
            is_built = matches(part.name, built_patterns)
            if want_new and not is_new:
                continue
            if (not want_new) and (is_new or not is_built):
                continue

            sx, sy = plan_to_screen(part.x, part.y, y0)
            sw = max(part.w * PLAN_SCALE, 0.015)
            sd = max(part.d * PLAN_SCALE, 0.015)
            if is_new:
                out.append(rect(sx, sy, sw, sd, fill=COL_NEW_FILL,
                                stroke=COL_NEW_STROKE, stroke_w=0.015))
            else:
                out.append(rect(sx, sy, sw, sd, fill=COL_BUILT_FILL,
                                stroke=COL_BUILT_STROKE, stroke_w=0.005))
    return out


def render_bench_iso(page_idx: int, built_patterns: list[str],
                     new_patterns: list[str], parts: list[Part]) -> list[str]:
    """Isometric view (RIGHT half of page). Camera at +X, +Y, +Z.
    Built parts in thin gray; new parts in bold black outline + hatch on
    top face."""
    y0 = page_origin(page_idx)
    out = []
    out.append(text(DIAG_ISO_X, y0 + DIAG_Y - 0.05,
                    "ISOMETRIC  (front-right view)",
                    size=0.10, fill=COL_SUBTLE, family=FONT_TITLE))

    # Ground-plane footprint of the L (faint dashed)
    def iso_pt(x, y, z):
        return iso_to_screen(x, y, z, y0)

    # L footprint at z=0
    out.append(polygon([iso_pt(0, 0, 0), iso_pt(144, 0, 0),
                         iso_pt(144, 36, 0), iso_pt(36, 36, 0),
                         iso_pt(36, 120, 0), iso_pt(0, 120, 0)],
                        fill="none", stroke=COL_FOOTPRINT,
                        stroke_w=0.006, dasharray="0.04,0.03"))

    def matches(name, patterns):
        return any(p in name for p in patterns)

    # Collect drawable parts and sort by depth (far first)
    def depth_key(p: Part) -> float:
        # Camera at +X, +Y, +Z. Larger sum = closer; smaller = farther.
        return (p.x + p.w / 2) + (p.y + p.d / 2) + (p.z + p.h / 2)

    drawable = []
    for p in parts:
        if p.shape != "box" or p.category == "ghost":
            continue
        is_new = matches(p.name, new_patterns)
        is_built = matches(p.name, built_patterns)
        if not (is_new or is_built):
            continue
        drawable.append((p, is_new))
    drawable.sort(key=lambda pn: depth_key(pn[0]))  # far first

    for p, is_new in drawable:
        x0, y0_, z0 = p.x, p.y, p.z
        x1, y1, z1 = p.x + p.w, p.y + p.d, p.z + p.h
        # 3 visible faces: top (z=z1), right (x=x1), front (y=y1)
        top = [iso_pt(x0, y0_, z1), iso_pt(x1, y0_, z1),
                iso_pt(x1, y1, z1), iso_pt(x0, y1, z1)]
        right = [iso_pt(x1, y0_, z0), iso_pt(x1, y1, z0),
                 iso_pt(x1, y1, z1), iso_pt(x1, y0_, z1)]
        front = [iso_pt(x0, y1, z0), iso_pt(x1, y1, z0),
                 iso_pt(x1, y1, z1), iso_pt(x0, y1, z1)]
        if is_new:
            out.append(polygon(right, fill=COL_NEW_RIGHT,
                                stroke=COL_NEW_STROKE, stroke_w=0.012))
            out.append(polygon(front, fill=COL_NEW_FRONT,
                                stroke=COL_NEW_STROKE, stroke_w=0.012))
            out.append(polygon(top, fill=COL_NEW_TOP,
                                stroke=COL_NEW_STROKE, stroke_w=0.012))
        else:
            out.append(polygon(right, fill=COL_BUILT_RIGHT,
                                stroke=COL_BUILT_STROKE, stroke_w=0.004))
            out.append(polygon(front, fill=COL_BUILT_FRONT,
                                stroke=COL_BUILT_STROKE, stroke_w=0.004))
            out.append(polygon(top, fill=COL_BUILT_TOP,
                                stroke=COL_BUILT_STROKE, stroke_w=0.004))
    return out


def render_instructions(page_idx: int, instructions: list[str],
                        tools: list[str] = None, time_est: str = "") -> list[str]:
    """Instructions block (no backgrounds). Vertical rule separates the
    instruction list from the tools/time sidebar."""
    y0 = page_origin(page_idx)
    out = []

    # Position: below diagrams
    instr_y = y0 + DIAG_Y + DIAG_H + 0.30
    instr_bottom = y0 + PAGE_H - 0.55
    instr_h = instr_bottom - instr_y

    # Sidebar split: right ~1.9in is tools/time
    sidebar_w = 1.9
    sidebar_x = PAGE_W - MARGIN - sidebar_w
    instr_text_w = sidebar_x - MARGIN - 0.2

    # Thin horizontal rule above the instructions
    out.append(line(MARGIN, instr_y - 0.10,
                     PAGE_W - MARGIN, instr_y - 0.10,
                     COL_RULE_LIGHT, stroke_w=0.006))

    # Vertical rule separating instructions and sidebar
    out.append(line(sidebar_x - 0.1, instr_y, sidebar_x - 0.1, instr_bottom,
                     COL_RULE_LIGHT, stroke_w=0.006))

    # Instructions heading (Abel)
    ix = MARGIN
    iy = instr_y + 0.22
    out.append(text(ix, iy, "INSTRUCTIONS",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    iy += 0.32
    for instr in instructions:
        out.append(text(ix, iy, instr, size=0.13, fill=COL_TEXT,
                        family=FONT_BODY))
        iy += 0.22

    # Sidebar: TOOLS heading + list
    sy = instr_y + 0.22
    out.append(text(sidebar_x, sy, "TOOLS",
                    size=0.13, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    sy += 0.26
    if tools:
        for t in tools:
            out.append(text(sidebar_x, sy, "- " + t,
                            size=0.12, fill=COL_TEXT, family=FONT_BODY))
            sy += 0.20
    sy += 0.18
    if time_est:
        out.append(text(sidebar_x, sy, "TIME",
                        size=0.13, fill=COL_TEXT, bold=True, family=FONT_TITLE))
        sy += 0.26
        out.append(text(sidebar_x, sy, time_est,
                        size=0.12, fill=COL_TEXT, family=FONT_BODY))

    # Legend at bottom-left of instructions area
    legend_y = instr_bottom - 0.10
    out.append(rect(ix, legend_y - 0.13, 0.14, 0.09,
                    fill=COL_NEW_FILL, stroke=COL_NEW_STROKE, stroke_w=0.014))
    out.append(text(ix + 0.20, legend_y - 0.05, "new this step",
                    size=0.10, fill=COL_TEXT, family=FONT_BODY))
    out.append(rect(ix + 1.4, legend_y - 0.13, 0.14, 0.09,
                    fill=COL_BUILT_FILL, stroke=COL_BUILT_STROKE,
                    stroke_w=0.005))
    out.append(text(ix + 1.6, legend_y - 0.05, "already built",
                    size=0.10, fill=COL_TEXT, family=FONT_BODY))

    return out


# ---------------------------------------------------------------------------
# Special pages: cover, materials checklists, cut day, final check
# ---------------------------------------------------------------------------

def render_cover(page_idx: int, total_pages: int) -> list[str]:
    y0 = page_origin(page_idx)
    out = []

    # Big title (Abel)
    out.append(text(PAGE_W / 2, y0 + 2.0, "L-BENCH",
                    size=1.1, fill=COL_TEXT, bold=True, anchor="middle",
                    family=FONT_TITLE))
    out.append(text(PAGE_W / 2, y0 + 2.7, "BUILD GUIDE",
                    size=0.55, fill=COL_TEXT, bold=True, anchor="middle",
                    family=FONT_TITLE))
    out.append(line(MARGIN + 1.5, y0 + 3.0, PAGE_W - MARGIN - 1.5, y0 + 3.0,
                    COL_RULE, stroke_w=0.02))
    out.append(text(PAGE_W / 2, y0 + 3.4,
                    "Step-by-step cut + assembly",
                    size=0.22, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))
    out.append(text(PAGE_W / 2, y0 + 3.7,
                    "(planer lift mechanism not included - leave cavity open)",
                    size=0.15, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))

    # Bench preview with wood-tone fills
    preview_y = y0 + 4.5
    scale = 0.028
    ox = PAGE_W / 2 - 144 * scale / 2
    oy = preview_y
    # Top leg
    out.append(rect(ox, oy, 144 * scale, 36 * scale,
                    fill=COL_BUILT_FILL, stroke=COL_RULE, stroke_w=0.015))
    # Short leg
    out.append(rect(ox, oy + 36 * scale, 36 * scale, 84 * scale,
                    fill=COL_BUILT_FILL, stroke=COL_RULE, stroke_w=0.015))
    # Tool cavities (highlighted fill)
    cavities = [
        (50, 2, 36, 30, "MITER"),
        (108, 4, 24, 32, "ROUTER"),
        (3, 42, 30, 30, "PLANER"),
        (2, 84, 32, 32, "SAW"),
    ]
    for cx, cy, cw, cd, label in cavities:
        out.append(rect(ox + cx * scale, oy + cy * scale,
                         cw * scale, cd * scale,
                         fill=COL_NEW_FILL, stroke=COL_RULE, stroke_w=0.008))
        out.append(text(ox + (cx + cw / 2) * scale,
                         oy + (cy + cd / 2 + 1) * scale,
                         label, size=0.10, fill=COL_TEXT, anchor="middle",
                         family=FONT_TITLE))

    # Stats
    stats_y = y0 + 8.6
    out.append(text(PAGE_W / 2, stats_y,
                    "144 in long  x  120 in deep  x  37 in tall",
                    size=0.20, fill=COL_TEXT, anchor="middle",
                    family=FONT_BODY))
    out.append(text(PAGE_W / 2, stats_y + 0.35,
                    "22 studs  /  22 stretchers  /  6 sheets 3/4 in plywood",
                    size=0.14, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))
    out.append(text(PAGE_W / 2, stats_y + 0.60,
                    "Build time: 6 weekend days (one person)",
                    size=0.14, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))

    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.5,
                    f"{total_pages} pages total - print the whole document",
                    size=0.11, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))
    return out


def render_lumber_checklist(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Materials: 2x4 SPF Lumber",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.6

    items = [
        ("2x4 x 8 ft SPF stud", "26", "Buy spares - cull bowed boards"),
        ("2x4 x 12 ft SPF", "2", "For 144 in top + bottom rails (top leg)"),
        ("Total board feet (approx)", "172 bf", "30% waste already included"),
    ]

    out.append(text(MARGIN, cy, "Quantity to buy",
                    size=0.20, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.4

    # Header row (rule only)
    out.append(text(MARGIN + 0.35, cy + 0.15, "Item",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    out.append(text(MARGIN + 4.0, cy + 0.15, "Qty",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    out.append(text(MARGIN + 4.8, cy + 0.15, "Note",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.30
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE, stroke_w=0.008))
    cy += 0.18

    for item, qty, note in items:
        # Checkbox (outline only)
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16,
                        fill="none", stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, item, size=0.13, fill=COL_TEXT,
                        family=FONT_BODY))
        out.append(text(MARGIN + 4.0, cy, qty, size=0.13, fill=COL_TEXT,
                        bold=True, family=FONT_BODY))
        out.append(text(MARGIN + 4.8, cy, note, size=0.11, fill=COL_SUBTLE,
                        family=FONT_BODY))
        cy += 0.36

    # Section divider
    cy += 0.25
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.30

    out.append(text(MARGIN, cy, "Pieces you will cut from this stock",
                    size=0.18, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.32

    cuts = [
        ("Stud, vertical (28.5 in)", "22"),
        ("Top + bottom rails (144 in)", "4"),
        ("Top + bottom rails (84 in)", "4"),
        ("Cross stretchers (29 in)", "14 + 8 = 22"),
        ("Miter recess blocking (36 in)", "2"),
        ("Miter recess blocking (23 in)", "2"),
        ("Saw sled cleats (32 in)", "2"),
        ("Saw sled cleats (25 in)", "2"),
    ]
    for desc, qty in cuts:
        out.append(text(MARGIN + 0.15, cy, "-",
                        size=0.13, fill=COL_TEXT, family=FONT_BODY))
        out.append(text(MARGIN + 0.35, cy, desc,
                        size=0.13, fill=COL_TEXT, family=FONT_BODY))
        out.append(text(MARGIN + 5.0, cy, qty, size=0.13,
                        fill=COL_TEXT, bold=True, family=FONT_BODY))
        cy += 0.24

    cy += 0.30
    out.append(text(MARGIN, cy,
                    "Pick straight boards from the middle of the stack.",
                    size=0.12, fill=COL_SUBTLE, family=FONT_BODY))
    cy += 0.20
    out.append(text(MARGIN, cy,
                    "Reject knots > 1 in. Reject any board with twist > 1/8 in.",
                    size=0.12, fill=COL_SUBTLE, family=FONT_BODY))
    return out


def render_ply_checklist(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Materials: Plywood + Hardware",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.6

    def section(title_text: str, items: list[tuple], cy: float) -> float:
        out.append(text(MARGIN, cy, title_text,
                        size=0.18, fill=COL_TEXT, bold=True,
                        family=FONT_TITLE))
        cy += 0.30
        out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                         stroke_w=0.006))
        cy += 0.20
        for item, qty in items:
            out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16,
                            fill="none", stroke=COL_RULE, stroke_w=0.01))
            out.append(text(MARGIN + 0.35, cy, item,
                            size=0.12, fill=COL_TEXT, family=FONT_BODY))
            out.append(text(MARGIN + 6.0, cy, qty,
                            size=0.12, fill=COL_TEXT, bold=True,
                            family=FONT_BODY))
            cy += 0.28
        return cy

    cy = section("Sheet goods", [
        ("3/4 in birch or sande plywood, 4 x 8 sheet", "6"),
        ("(Optional) 1/4 in skin plywood, 4 x 8 sheet", "1"),
    ], cy)
    cy += 0.20

    cy = section("Fasteners + adhesives", [
        ("#9 x 2.5 in construction screws (GRK or SPAX)", "1 lb"),
        ("#8 x 1.25 in wood screws", "1 lb"),
        ("1/4 x 3.5 in lag screws + washers", "8"),
        ("3/8 x 4 in lag screws (Husky tie-down)", "4"),
        ("Loctite PL Premium construction adhesive", "2 tubes"),
        ("Titebond II or III wood glue", "1 qt"),
    ], cy)
    cy += 0.20

    cy = section("Finish", [
        ("BLO or General Finishes Arm-R-Seal (1 qt)", "1"),
        ("Mineral spirits (1 qt)", "1"),
        ("Foam brushes / lint-free rags", "bulk"),
        ("Sandpaper 80, 120, 220 grit", "1 pack each"),
    ], cy)

    cy += 0.40
    out.append(text(MARGIN, cy,
                    "Approx total bench-only cost (no lift): $560 - $760",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.24
    out.append(text(MARGIN, cy,
                    "See SHOPPING_LIST.md for full breakdown and store routing.",
                    size=0.12, fill=COL_SUBTLE, family=FONT_BODY))
    return out


def render_final_check(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Final Sanity Check",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.6

    out.append(text(MARGIN, cy, "Before you declare the frame done:",
                    size=0.18, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.35
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.25

    checks = [
        "Bench top is level corner-to-corner within 1/8 in across 12 ft.",
        "Push hard on the front edge of the top leg - it should not move > 1/8 in.",
        "If it does, re-tighten wall lags or add a diagonal brace in a bay.",
        "Miter recess is exactly 36 x 30 in opening, 4 in deep. Saw sits flush.",
        "Router insert plate sits flush with the surrounding top.",
        "Saw sled drops in cleanly; deck flush at 37 in. Lifts out by hand.",
        "Planer cavity is FULLY OPEN - no obstructions in the 30 x 30 x 37 hole.",
        "Bottom of planer cavity is clear floor (no internal blocking).",
        "Toe kicks are recessed 3 in from front faces (left + right of L).",
        "All cavities have framed studs at every boundary - no cantilever.",
        "Top doubled panels are SCREWED + GLUED, not just screwed.",
        "End panels installed at the visible ends (X=144, Y=120).",
        "Finish has cured at least 24 hours before placing tools.",
    ]
    for c in checks:
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16,
                        fill="none", stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, c, size=0.12, fill=COL_TEXT,
                        family=FONT_BODY))
        cy += 0.28

    cy += 0.4
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE,
                     stroke_w=0.015))
    cy += 0.32
    out.append(text(MARGIN, cy, "NEXT UP: PLANER LIFT MECHANISM",
                    size=0.16, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.30
    out.append(text(MARGIN, cy,
                    "Drop a temporary 30 x 30 ply cover over the planer hole.",
                    size=0.13, fill=COL_TEXT, family=FONT_BODY))
    cy += 0.24
    out.append(text(MARGIN, cy,
                    "When ready, see planer_lift_bom.md for the BOM and",
                    size=0.13, fill=COL_TEXT, family=FONT_BODY))
    cy += 0.24
    out.append(text(MARGIN, cy,
                    "the scissor-stabilizer + drill mechanism build.",
                    size=0.13, fill=COL_TEXT, family=FONT_BODY))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def render_page(i: int, step: dict, parts: list[Part],
                built_patterns: list[str], total_pages: int) -> list[str]:
    """Render a single page worth of SVG fragments. Coords are in absolute
    multi-page space (page_origin(i) is the page top)."""
    kind = step["kind"]
    out: list[str] = []
    if kind == "cover":
        out.extend(render_cover(i, total_pages))
    elif kind == "lumber_checklist":
        out.extend(render_lumber_checklist(i, total_pages))
    elif kind == "ply_checklist":
        out.extend(render_ply_checklist(i, total_pages))
    elif kind == "cut_day_lumber":
        out.extend(render_page_chrome(i, step["title"], total_pages=total_pages))
        y0 = page_origin(i)
        cy = y0 + 1.5
        out.append(text(MARGIN + 0.2, cy, "Cross-cut order (longest first):",
                        size=0.16, fill=COL_TEXT, bold=True))
        cy += 0.35
        cuts = [
            ("4 x 144 in rails (top leg front + back)", "12 ft stock"),
            ("4 x 84 in rails (short leg sides)", "8 ft stock"),
            ("22 x 28.5 in studs (verticals)", "8 ft = 3 studs"),
            ("22 x 29 in cross stretchers", "8 ft = 3 stretchers"),
            ("2 x 32 in saw sled cleats", "scrap"),
            ("2 x 25 in saw sled cleats", "scrap"),
            ("2 x 36 in miter blocking", "scrap"),
            ("2 x 23 in miter blocking", "scrap"),
        ]
        for item, src in cuts:
            out.append(text(MARGIN + 0.4, cy, "-", size=0.13, fill=COL_TEXT))
            out.append(text(MARGIN + 0.6, cy, item, size=0.13, fill=COL_TEXT))
            out.append(text(MARGIN + 5.2, cy, f"({src})",
                            size=0.11, fill=COL_SUBTLE))
            cy += 0.30
        out.extend(render_instructions(i, step["instructions"],
                                        tools=step.get("tools"),
                                        time_est=step.get("time", "")))
    elif kind == "cut_day_ply":
        out.extend(render_page_chrome(i, step["title"], total_pages=total_pages))
        y0 = page_origin(i)
        cy = y0 + 1.5
        out.append(text(MARGIN + 0.2, cy,
                        "Print l_bench_partsheets.svg for per-piece diagrams.",
                        size=0.14, fill=COL_TEXT, bold=True))
        cy += 0.35
        out.append(text(MARGIN + 0.2, cy,
                        "Major panels (each doubled = 2 cut from 3/4):",
                        size=0.13, fill=COL_TEXT))
        cy += 0.25
        ply_panels = [
            "TopLeg_Top_Left (50 x 36)",
            "TopLeg_Top_MidRight (36 x 22)",
            "TopLeg_Top_FarRight (36 x 12)",
            "LeftLeg_Top_AbovePlaner (36 x 6)",
            "LeftLeg_Top_BetweenCavities (36 x 12)",
            "LeftLeg_Top_End (36 x 4)",
            "End panels (36 x 33, single ply)",
            "Toe kicks (144 x 4) and (84 x 4)",
            "Router cabinet sides (32 x 31.5)",
            "Saw sled (30 x 30) and Planer sled (28 x 28, set aside)",
        ]
        for p in ply_panels:
            out.append(text(MARGIN + 0.4, cy, "-", size=0.12, fill=COL_TEXT))
            out.append(text(MARGIN + 0.6, cy, p, size=0.12, fill=COL_TEXT))
            cy += 0.22
        out.extend(render_instructions(i, step["instructions"],
                                        tools=step.get("tools"),
                                        time_est=step.get("time", "")))
    elif kind == "assembly":
        out.extend(render_page_chrome(i, step["title"], total_pages=total_pages))
        out.extend(render_bench_plan(i, built_patterns,
                                      step.get("patterns", []), parts))
        out.extend(render_bench_iso(i, built_patterns,
                                     step.get("patterns", []), parts))
        out.extend(render_instructions(i, step["instructions"],
                                        tools=step.get("tools"),
                                        time_est=step.get("time", "")))
    elif kind == "final_check":
        out.extend(render_final_check(i, total_pages))
    return out


def write_html_wrapper(html_path: Path, total_pages: int):
    """Write an HTML file that embeds individual page SVGs with CSS page
    breaks. Open in browser, File -> Print -> Save as PDF for a clean
    multi-page PDF."""
    pages_html = []
    for i in range(total_pages):
        pages_html.append(
            f'<div class="page"><object data="l_bench_buildguide_page_{i+1:02d}.svg" '
            f'type="image/svg+xml" width="100%" height="100%"></object></div>')
    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>L-Bench Build Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Abel&amp;family=Barlow:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>
@page {{ size: 8.5in 11in; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{
    margin: 0; padding: 0; background: #DDD;
    font-family: 'Barlow', sans-serif;
}}
.page {{
    width: 8.5in;
    height: 11in;
    page-break-after: always;
    page-break-inside: avoid;
    margin: 0 auto 4px auto;
    background: white;
    overflow: hidden;
}}
.page:last-child {{ page-break-after: auto; }}
object {{ display: block; width: 100%; height: 100%; }}
@media print {{
    html, body {{ background: white; }}
    .page {{ margin: 0; background: white; }}
}}
</style></head><body>
{''.join(pages_html)}
</body></html>
"""
    html_path.write_text(html)


def main():
    parts = load_parts()
    total_pages = len(STEPS)
    total_h = PAGE_H * total_pages

    # 1) Build the single tall SVG (good for previewing in a browser)
    svg_parts = svg_open(PAGE_W, total_h)

    # Track which patterns are "built" cumulatively
    built_patterns: list[str] = []

    for i, step in enumerate(STEPS):
        page_svg = render_page(i, step, parts, built_patterns, total_pages)
        svg_parts.extend(page_svg)
        if step["kind"] == "assembly":
            built_patterns.extend(step.get("patterns", []))

    svg_parts.append("</svg>")
    out_path = OUT_DIR / "l_bench_buildguide.svg"
    out_path.write_text("\n".join(svg_parts))
    print(f"Wrote {out_path}  ({total_pages} pages stacked)")

    # 2) Build one SVG per page (for the HTML wrapper / clean PDF print)
    built_patterns = []
    for i, step in enumerate(STEPS):
        # Render the page in its own SVG with viewBox shifted so it starts at 0
        page_svg = render_page(i, step, parts, built_patterns, total_pages)
        if step["kind"] == "assembly":
            built_patterns.extend(step.get("patterns", []))

        # Wrap in an SVG that translates the content up by page_origin(i)
        y0 = page_origin(i)
        single = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{PAGE_W}in" height="{PAGE_H}in" '
            f'viewBox="0 {y0} {PAGE_W} {PAGE_H}">',
            '<defs><style type="text/css">'
            '@import url("https://fonts.googleapis.com/css2?'
            'family=Abel&amp;family=Barlow:wght@400;600;700&amp;display=swap");'
            '</style></defs>',
        ]
        single.extend(page_svg)
        single.append("</svg>")
        single_path = OUT_DIR / f"l_bench_buildguide_page_{i+1:02d}.svg"
        single_path.write_text("\n".join(single))

    # 3) Write the HTML wrapper for clean printing
    html_path = OUT_DIR / "l_bench_buildguide.html"
    write_html_wrapper(html_path, total_pages)
    print(f"Wrote {html_path}")
    print(f"  Open in browser, File -> Print -> Save as PDF.")
    print(f"  Each page breaks cleanly at the 8.5x11 boundary.")


if __name__ == "__main__":
    main()
