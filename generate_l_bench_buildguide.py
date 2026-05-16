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

# Diagram window inside each page
DIAG_X = MARGIN
DIAG_Y = 1.2                           # below title bar
DIAG_W = PAGE_W - 2 * MARGIN
DIAG_H = 4.5                           # plenty for the L shape

# Scale: fit bench into diagram window
SCALE = min(DIAG_W / (BENCH_X_MAX - BENCH_X_MIN),
            DIAG_H / (BENCH_Y_MAX - BENCH_Y_MIN))
# Center the diagram in the window
DIAG_OFFSET_X = DIAG_X + (DIAG_W - (BENCH_X_MAX - BENCH_X_MIN) * SCALE) / 2
DIAG_OFFSET_Y = DIAG_Y + (DIAG_H - (BENCH_Y_MAX - BENCH_Y_MIN) * SCALE) / 2

# Colors
COL_BG = "#FBFAF6"
COL_PAGE_RULE = "#DDD8C8"
COL_TITLE_BAR = "#2E2A26"
COL_TITLE_TEXT = "#FFFFFF"
COL_TEXT = "#1A1A1A"
COL_SUBTLE = "#555"
COL_BUILT_FILL = "#E4DECF"
COL_BUILT_STROKE = "#BBB2A0"
COL_NEW_FILL = "#F18F4C"
COL_NEW_STROKE = "#9A3F0A"
COL_CAVITY = "#D8D8D8"
COL_SHADOW = "#00000010"
COL_INSTR_BG = "#FFFFFF"
COL_INSTR_BORDER = "#E0DCC8"
COL_SIDEBAR_BG = "#F2EFE2"
COL_TOOL_TAG = "#4A6FA5"
COL_TIME_TAG = "#6C8C3B"


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
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_in}in" height="{height_in}in" '
        f'viewBox="0 0 {width_in} {height_in}" '
        f'style="background:{COL_BG};font-family:Helvetica,Arial,sans-serif;">',
        # Light page-break ruler lines drawn at each page boundary later
    ]
    return parts


def rect(x, y, w, h, fill, stroke=None, stroke_w=0.005, opacity=1.0,
         rx=0.0):
    s = (f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
         f'fill="{fill}" opacity="{opacity}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{stroke_w}"'
    if rx > 0:
        s += f' rx="{rx}" ry="{rx}"'
    s += ' />'
    return s


def text(x, y, txt, size=0.14, fill=None, bold=False, anchor="start",
         family="Helvetica,Arial,sans-serif"):
    f = fill if fill else COL_TEXT
    weight = "bold" if bold else "normal"
    # Escape special XML
    txt = (str(txt).replace("&", "&amp;").replace("<", "&lt;")
           .replace(">", "&gt;"))
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" '
            f'fill="{f}" font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{family}">{txt}</text>')


def line(x1, y1, x2, y2, stroke, stroke_w=0.01, dasharray=None):
    s = (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
         f'stroke="{stroke}" stroke-width="{stroke_w}"')
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
    """Title bar + page-number footer; returns SVG string fragments."""
    y0 = page_origin(page_idx)
    out = []
    # Page background
    out.append(rect(0, y0, PAGE_W, PAGE_H, COL_BG))
    # Title bar
    out.append(rect(MARGIN, y0 + MARGIN, PAGE_W - 2 * MARGIN, 0.55,
                    COL_TITLE_BAR, rx=0.06))
    out.append(text(MARGIN + 0.18, y0 + MARGIN + 0.4, title,
                    size=0.26, fill=COL_TITLE_TEXT, bold=True))
    if subtitle:
        out.append(text(PAGE_W - MARGIN - 0.18, y0 + MARGIN + 0.4, subtitle,
                        size=0.15, fill=COL_TITLE_TEXT, anchor="end"))
    # Footer page number
    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.3,
                    f"Page {page_idx + 1} of {total_pages}",
                    size=0.12, fill=COL_SUBTLE, anchor="middle"))
    # Page-break rule between pages
    if page_idx > 0:
        out.append(line(0, y0, PAGE_W, y0, COL_PAGE_RULE,
                        stroke_w=0.015, dasharray="0.08,0.08"))
    return out


def render_bench_plan(page_idx: int, built_patterns: list[str],
                      new_patterns: list[str], parts: list[Part]) -> list[str]:
    """Top-down view of the bench, with built parts gray + new parts highlighted."""
    y0 = page_origin(page_idx)
    out = []
    # Diagram window border
    out.append(rect(DIAG_X, y0 + DIAG_Y, DIAG_W, DIAG_H, "#FFF",
                    stroke=COL_INSTR_BORDER, stroke_w=0.01, rx=0.05))

    # Light grid every 6 in
    for gx in range(0, BENCH_X_MAX + 1, 6):
        sx = DIAG_OFFSET_X + gx * SCALE
        out.append(line(sx, y0 + DIAG_OFFSET_Y, sx,
                        y0 + DIAG_OFFSET_Y + BENCH_Y_MAX * SCALE,
                        "#EEE7D3", stroke_w=0.005))
    for gy in range(0, BENCH_Y_MAX + 1, 6):
        sy = y0 + DIAG_OFFSET_Y + gy * SCALE
        out.append(line(DIAG_OFFSET_X, sy,
                        DIAG_OFFSET_X + BENCH_X_MAX * SCALE, sy,
                        "#EEE7D3", stroke_w=0.005))

    # L-bench overall outline (top leg + short leg) as a faint "footprint"
    out.append(rect(DIAG_OFFSET_X + 0 * SCALE,
                    y0 + DIAG_OFFSET_Y + 0 * SCALE,
                    144 * SCALE, 36 * SCALE,
                    "#F8F4E3", stroke="#D8D0B0", stroke_w=0.005))
    out.append(rect(DIAG_OFFSET_X + 0 * SCALE,
                    y0 + DIAG_OFFSET_Y + 36 * SCALE,
                    36 * SCALE, 84 * SCALE,
                    "#F8F4E3", stroke="#D8D0B0", stroke_w=0.005))

    def matches(name: str, patterns: list[str]) -> bool:
        return any(p in name for p in patterns)

    # Render parts: built first (gray), then new (highlight) on top
    for part in parts:
        if part.shape != "box":
            continue
        if part.category == "ghost":
            continue
        is_new = matches(part.name, new_patterns)
        is_built = matches(part.name, built_patterns)
        if not (is_new or is_built):
            continue
        if is_new and is_built:
            is_built = False  # new wins

        # Position + size in inches, scaled
        x = DIAG_OFFSET_X + part.x * SCALE
        y = y0 + DIAG_OFFSET_Y + part.y * SCALE
        w = max(part.w * SCALE, 0.015)
        d = max(part.d * SCALE, 0.015)
        if is_new:
            fill = COL_NEW_FILL
            stroke = COL_NEW_STROKE
            opacity = 0.95
        else:
            fill = COL_BUILT_FILL
            stroke = COL_BUILT_STROKE
            opacity = 0.7
        out.append(rect(x, y, w, d, fill, stroke=stroke,
                        stroke_w=0.008, opacity=opacity))

    # Axis labels (small)
    out.append(text(DIAG_OFFSET_X, y0 + DIAG_OFFSET_Y - 0.06,
                    "X = back wall (in)", size=0.09, fill=COL_SUBTLE))
    out.append(text(DIAG_OFFSET_X - 0.05,
                    y0 + DIAG_OFFSET_Y + BENCH_Y_MAX * SCALE + 0.12,
                    "Y = depth into room (in)", size=0.09, fill=COL_SUBTLE))

    # Compass / orientation note
    out.append(text(DIAG_X + DIAG_W - 0.18,
                    y0 + DIAG_Y + 0.18,
                    "BACK WALL (windows) is at TOP of plan",
                    size=0.09, fill=COL_SUBTLE, anchor="end"))
    out.append(text(DIAG_X + DIAG_W - 0.18,
                    y0 + DIAG_Y + 0.32,
                    "LHS wall (garage door side) is at LEFT",
                    size=0.09, fill=COL_SUBTLE, anchor="end"))
    return out


def render_instructions(page_idx: int, instructions: list[str],
                        tools: list[str] = None, time_est: str = "") -> list[str]:
    """Render the instruction block below the diagram."""
    y0 = page_origin(page_idx)
    out = []
    # Instructions panel
    instr_y = y0 + DIAG_Y + DIAG_H + 0.25
    instr_h = PAGE_H - DIAG_Y - DIAG_H - 0.25 - 0.6 - MARGIN
    out.append(rect(MARGIN, instr_y, PAGE_W - 2 * MARGIN, instr_h,
                    COL_INSTR_BG, stroke=COL_INSTR_BORDER,
                    stroke_w=0.01, rx=0.05))

    # Sidebar with tools / time
    sidebar_w = 1.9
    sidebar_x = PAGE_W - MARGIN - sidebar_w - 0.1
    sidebar_y = instr_y + 0.1
    sidebar_h = instr_h - 0.2
    out.append(rect(sidebar_x, sidebar_y, sidebar_w, sidebar_h,
                    COL_SIDEBAR_BG, rx=0.04))

    # Sidebar content
    sy = sidebar_y + 0.25
    out.append(text(sidebar_x + 0.12, sy, "TOOLS",
                    size=0.11, fill=COL_TOOL_TAG, bold=True))
    sy += 0.18
    if tools:
        for t in tools:
            out.append(text(sidebar_x + 0.12, sy, f"- {t}",
                            size=0.11, fill=COL_TEXT))
            sy += 0.18
    sy += 0.18
    if time_est:
        out.append(text(sidebar_x + 0.12, sy, "TIME",
                        size=0.11, fill=COL_TIME_TAG, bold=True))
        sy += 0.18
        out.append(text(sidebar_x + 0.12, sy, time_est,
                        size=0.11, fill=COL_TEXT))

    # Instructions content (text wrapped lines)
    ix = MARGIN + 0.25
    iy = instr_y + 0.4
    line_h = 0.20
    out.append(text(ix, iy, "Instructions",
                    size=0.16, fill=COL_TEXT, bold=True))
    iy += 0.30
    for instr in instructions:
        out.append(text(ix, iy, instr, size=0.13, fill=COL_TEXT))
        iy += line_h

    # Legend at bottom of instructions panel
    legend_y = instr_y + instr_h - 0.25
    out.append(rect(ix, legend_y - 0.12, 0.18, 0.10,
                    COL_NEW_FILL, stroke=COL_NEW_STROKE, stroke_w=0.005))
    out.append(text(ix + 0.24, legend_y - 0.04, "New this step",
                    size=0.10, fill=COL_TEXT))
    out.append(rect(ix + 1.5, legend_y - 0.12, 0.18, 0.10,
                    COL_BUILT_FILL, stroke=COL_BUILT_STROKE, stroke_w=0.005))
    out.append(text(ix + 1.74, legend_y - 0.04, "Already built",
                    size=0.10, fill=COL_TEXT))

    return out


# ---------------------------------------------------------------------------
# Special pages: cover, materials checklists, cut day, final check
# ---------------------------------------------------------------------------

def render_cover(page_idx: int, total_pages: int) -> list[str]:
    y0 = page_origin(page_idx)
    out = []
    out.append(rect(0, y0, PAGE_W, PAGE_H, COL_BG))

    # Big title
    out.append(text(PAGE_W / 2, y0 + 2.0, "L-BENCH",
                    size=0.9, fill=COL_TEXT, bold=True, anchor="middle"))
    out.append(text(PAGE_W / 2, y0 + 2.7, "BUILD GUIDE",
                    size=0.5, fill=COL_TITLE_BAR, bold=True, anchor="middle"))
    out.append(line(MARGIN + 1.5, y0 + 3.0, PAGE_W - MARGIN - 1.5, y0 + 3.0,
                    COL_TITLE_BAR, stroke_w=0.02))
    out.append(text(PAGE_W / 2, y0 + 3.4,
                    "Step-by-step cut + assembly",
                    size=0.22, fill=COL_SUBTLE, anchor="middle"))
    out.append(text(PAGE_W / 2, y0 + 3.7,
                    "(Planer lift mechanism not included - leave cavity open)",
                    size=0.16, fill=COL_SUBTLE, anchor="middle"))

    # Bench preview (drawn iso-like as top-down)
    preview_y = y0 + 4.5
    scale = 0.025
    ox = PAGE_W / 2 - 144 * scale / 2
    oy = preview_y
    # Top leg
    out.append(rect(ox, oy, 144 * scale, 36 * scale,
                    "#D4C8A5", stroke="#8E7E55", stroke_w=0.015))
    # Short leg
    out.append(rect(ox, oy + 36 * scale, 36 * scale, 84 * scale,
                    "#D4C8A5", stroke="#8E7E55", stroke_w=0.015))
    # Tool cavities
    out.append(rect(ox + 50 * scale, oy + 2 * scale,
                    36 * scale, 30 * scale,
                    "#E8B97A", stroke="#7C5530", stroke_w=0.01))
    out.append(text(ox + 68 * scale, oy + 18 * scale, "MITER",
                    size=0.1, fill="#333", anchor="middle"))
    out.append(rect(ox + 108 * scale, oy + 4 * scale,
                    24 * scale, 32 * scale,
                    "#AAA", stroke="#444", stroke_w=0.01))
    out.append(text(ox + 120 * scale, oy + 22 * scale, "ROUTER",
                    size=0.09, fill="#333", anchor="middle"))
    out.append(rect(ox + 3 * scale, oy + 42 * scale,
                    30 * scale, 30 * scale,
                    "#E8D26A", stroke="#7A6520", stroke_w=0.01))
    out.append(text(ox + 18 * scale, oy + 60 * scale, "PLANER",
                    size=0.09, fill="#333", anchor="middle"))
    out.append(rect(ox + 2 * scale, oy + 84 * scale,
                    32 * scale, 32 * scale,
                    "#E8D26A", stroke="#7A6520", stroke_w=0.01))
    out.append(text(ox + 18 * scale, oy + 102 * scale, "SAW",
                    size=0.10, fill="#333", anchor="middle"))

    # Stats
    stats_y = y0 + 8.5
    out.append(text(PAGE_W / 2, stats_y, "144 in long  x  120 in deep  x  37 in tall",
                    size=0.18, fill=COL_TEXT, anchor="middle"))
    out.append(text(PAGE_W / 2, stats_y + 0.4,
                    "22 studs  /  16 stretchers  /  6 sheets 3/4 in plywood",
                    size=0.14, fill=COL_SUBTLE, anchor="middle"))
    out.append(text(PAGE_W / 2, stats_y + 0.7,
                    "Build time: 6 weekend days (one person)",
                    size=0.14, fill=COL_SUBTLE, anchor="middle"))

    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.5,
                    f"{total_pages} pages total - print this whole document",
                    size=0.12, fill=COL_SUBTLE, anchor="middle"))
    return out


def render_lumber_checklist(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Materials: 2x4 SPF Lumber",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    items = [
        ("2x4 x 8 ft SPF stud", "26", "Buy 26 to have spares - cull bowed boards"),
        ("2x4 x 12 ft SPF", "2", "For the 144 in top + bottom rails on top leg"),
        ("Total board feet (approx)", "172 bf", "30% waste already included"),
    ]

    out.append(text(MARGIN + 0.2, cy, "Quantity to buy",
                    size=0.20, fill=COL_TEXT, bold=True))
    cy += 0.45

    # Header row
    out.append(rect(MARGIN, cy, PAGE_W - 2 * MARGIN, 0.35,
                    "#E8E1C8", rx=0.04))
    out.append(text(MARGIN + 0.15, cy + 0.23, "Item",
                    size=0.13, fill=COL_TEXT, bold=True))
    out.append(text(MARGIN + 4.0, cy + 0.23, "Qty",
                    size=0.13, fill=COL_TEXT, bold=True))
    out.append(text(MARGIN + 4.8, cy + 0.23, "Note",
                    size=0.13, fill=COL_TEXT, bold=True))
    cy += 0.45

    for item, qty, note in items:
        out.append(rect(MARGIN, cy - 0.15, 0.20, 0.22, "#FFF",
                        stroke="#999", stroke_w=0.01))  # checkbox
        out.append(text(MARGIN + 0.35, cy, item, size=0.13, fill=COL_TEXT))
        out.append(text(MARGIN + 4.0, cy, qty, size=0.13, fill=COL_TEXT,
                        bold=True))
        out.append(text(MARGIN + 4.8, cy, note, size=0.11, fill=COL_SUBTLE))
        cy += 0.4

    # Subtotal cut list
    cy += 0.3
    out.append(text(MARGIN + 0.2, cy, "Pieces you will cut from this stock",
                    size=0.16, fill=COL_TEXT, bold=True))
    cy += 0.35

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
        out.append(text(MARGIN + 0.4, cy, "-", size=0.13, fill=COL_TEXT))
        out.append(text(MARGIN + 0.6, cy, desc, size=0.13, fill=COL_TEXT))
        out.append(text(MARGIN + 5.0, cy, qty, size=0.13, fill=COL_TEXT,
                        bold=True))
        cy += 0.24

    cy += 0.3
    out.append(text(MARGIN + 0.2, cy, "Pick straight boards from the middle "
                                       "of the stack. Reject knots > 1 in.",
                    size=0.13, fill=COL_SUBTLE))
    return out


def render_ply_checklist(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Materials: Plywood + Hardware",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    out.append(text(MARGIN + 0.2, cy, "Sheet goods",
                    size=0.18, fill=COL_TEXT, bold=True))
    cy += 0.35

    sheets = [
        ("3/4 in birch or sande plywood, 4 x 8 sheet", "6"),
        ("(Optional) 1/4 in skin plywood, 4 x 8 sheet", "1"),
    ]
    for item, qty in sheets:
        out.append(rect(MARGIN, cy - 0.15, 0.20, 0.22, "#FFF",
                        stroke="#999", stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, item, size=0.13, fill=COL_TEXT))
        out.append(text(MARGIN + 6.5, cy, qty, size=0.13, fill=COL_TEXT,
                        bold=True))
        cy += 0.35

    cy += 0.2
    out.append(text(MARGIN + 0.2, cy, "Fasteners + adhesives",
                    size=0.18, fill=COL_TEXT, bold=True))
    cy += 0.35

    fast = [
        ("#9 x 2.5 in construction screws (GRK or SPAX)", "1 lb"),
        ("#8 x 1.25 in wood screws", "1 lb"),
        ("1/4 x 3.5 in lag screws + washers", "8"),
        ("3/8 x 4 in lag screws (Husky tie-down)", "4"),
        ("Loctite PL Premium construction adhesive", "2 tubes"),
        ("Titebond II or III wood glue", "1 qt"),
    ]
    for item, qty in fast:
        out.append(rect(MARGIN, cy - 0.15, 0.20, 0.22, "#FFF",
                        stroke="#999", stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, item, size=0.12, fill=COL_TEXT))
        out.append(text(MARGIN + 6.0, cy, qty, size=0.12, fill=COL_TEXT,
                        bold=True))
        cy += 0.3

    cy += 0.2
    out.append(text(MARGIN + 0.2, cy, "Finish",
                    size=0.18, fill=COL_TEXT, bold=True))
    cy += 0.35

    finish = [
        ("BLO or General Finishes Arm-R-Seal (1 qt)", "1"),
        ("Mineral spirits (1 qt)", "1"),
        ("Foam brushes / lint-free rags", "bulk"),
        ("Sandpaper 80, 120, 220 grit", "1 pack each"),
    ]
    for item, qty in finish:
        out.append(rect(MARGIN, cy - 0.15, 0.20, 0.22, "#FFF",
                        stroke="#999", stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, item, size=0.12, fill=COL_TEXT))
        out.append(text(MARGIN + 6.0, cy, qty, size=0.12, fill=COL_TEXT,
                        bold=True))
        cy += 0.3

    cy += 0.4
    out.append(text(MARGIN + 0.2, cy, "Approx total bench-only cost (no lift): $560 - $760",
                    size=0.14, fill=COL_TEXT, bold=True))
    out.append(text(MARGIN + 0.2, cy + 0.25,
                    "See SHOPPING_LIST.md for full breakdown and store routing.",
                    size=0.12, fill=COL_SUBTLE))
    return out


def render_final_check(page_idx: int, total_pages: int) -> list[str]:
    out = render_page_chrome(page_idx, "Final Sanity Check",
                             total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    out.append(text(MARGIN + 0.2, cy,
                    "Before you declare the frame done:",
                    size=0.18, fill=COL_TEXT, bold=True))
    cy += 0.4

    checks = [
        "Bench top is level corner-to-corner within 1/8 in across 12 ft.",
        "Push hard on the front edge of the top leg - it should not move > 1/8 in.",
        "If it does, re-tighten wall lags or add a diagonal brace in a bay.",
        "Miter recess is exactly 36 x 30 in opening, 4 in deep. Saw sits flush.",
        "Router insert plate sits flush with the surrounding top - no proud edges.",
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
        out.append(rect(MARGIN, cy - 0.15, 0.20, 0.22, "#FFF",
                        stroke="#666", stroke_w=0.012, rx=0.02))
        out.append(text(MARGIN + 0.4, cy, c, size=0.12, fill=COL_TEXT))
        cy += 0.32

    cy += 0.4
    out.append(rect(MARGIN, cy, PAGE_W - 2 * MARGIN, 1.3,
                    "#FFF6E0", stroke="#D6BA60", stroke_w=0.01, rx=0.05))
    out.append(text(MARGIN + 0.2, cy + 0.3,
                    "Next up: planer lift mechanism",
                    size=0.16, fill=COL_TEXT, bold=True))
    out.append(text(MARGIN + 0.2, cy + 0.6,
                    "Drop a temporary 30 x 30 ply cover over the planer hole.",
                    size=0.12, fill=COL_TEXT))
    out.append(text(MARGIN + 0.2, cy + 0.85,
                    "When ready, see planer_lift_bom.md for the BOM and",
                    size=0.12, fill=COL_TEXT))
    out.append(text(MARGIN + 0.2, cy + 1.10,
                    "the scissor-stabilizer + drill mechanism build.",
                    size=0.12, fill=COL_TEXT))
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
<style>
@page {{ size: 8.5in 11in; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #888; }}
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
object {{ display: block; }}
@media print {{
    html, body {{ background: white; }}
    .page {{ margin: 0; }}
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
            f'viewBox="0 {y0} {PAGE_W} {PAGE_H}" '
            f'style="background:{COL_BG};'
            f'font-family:Helvetica,Arial,sans-serif;">',
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
