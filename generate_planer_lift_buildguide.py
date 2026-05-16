"""
Generate a printable multi-page step-by-step build guide for the PLANER
LIFT mechanism (scissor stabilizer + drill motor design).

Outputs:
  - planer_lift_buildguide.svg          (tall preview, all pages stacked)
  - planer_lift_buildguide_page_NN.svg  (one per page)
  - planer_lift_buildguide.html         (print wrapper)

Style matches l_bench_buildguide: white page, Abel/Barlow fonts, no
toner-burning backgrounds. Each assembly step gets a PLAN view (top-down
into the cavity from above) and an ISO view (front-right-above). Bolts
and screws are marked with solid dots / X marks at their actual XY
positions; sizes are listed on the page legend.

For the wiring step and the drill-bracket detail step we draw custom
schematics instead of the cavity-plan/iso pair.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Page constants (same letter-size geometry as the L-bench guide)
# ---------------------------------------------------------------------------

PAGE_W = 8.5
PAGE_H = 11.0
MARGIN = 0.5

# Cavity local coordinates: X=0..30 wide, Y=0..30 deep, Z=0..37 tall.
CAV_W, CAV_D, CAV_H = 30.0, 30.0, 37.0

# Diagram window (two halves: PLAN on left, ISO on right)
DIAG_Y = 1.20
DIAG_H = 3.80
DIAG_GAP = 0.30
DIAG_W_HALF = (PAGE_W - 2 * MARGIN - DIAG_GAP) / 2

# LEFT diagram - top-down PLAN view
DIAG_PLAN_X = MARGIN
PLAN_SCALE = min(DIAG_W_HALF / CAV_W, DIAG_H / CAV_D)
PLAN_OFFSET_X = DIAG_PLAN_X + (DIAG_W_HALF - CAV_W * PLAN_SCALE) / 2
PLAN_OFFSET_Y_REL = (DIAG_H - CAV_D * PLAN_SCALE) / 2

# RIGHT diagram - ISO view (camera at +X, +Y, +Z)
DIAG_ISO_X = MARGIN + DIAG_W_HALF + DIAG_GAP
ISO_COS = 0.8660254
ISO_SIN = 0.5


def iso_project(x: float, y: float, z: float) -> tuple[float, float]:
    return ((x - y) * ISO_COS, -z + (x + y) * ISO_SIN)


# Compute iso bounding box for the cavity envelope
_iso_corners = [
    iso_project(0, 0, 0), iso_project(CAV_W, 0, 0),
    iso_project(0, CAV_D, 0), iso_project(CAV_W, CAV_D, 0),
    iso_project(0, 0, CAV_H), iso_project(CAV_W, 0, CAV_H),
    iso_project(0, CAV_D, CAV_H), iso_project(CAV_W, CAV_D, CAV_H),
]
ISO_X_MIN = min(c[0] for c in _iso_corners)
ISO_X_MAX = max(c[0] for c in _iso_corners)
ISO_Y_MIN = min(c[1] for c in _iso_corners)
ISO_Y_MAX = max(c[1] for c in _iso_corners)
ISO_W_RAW = ISO_X_MAX - ISO_X_MIN
ISO_H_RAW = ISO_Y_MAX - ISO_Y_MIN
ISO_SCALE = min(DIAG_W_HALF / ISO_W_RAW, DIAG_H / ISO_H_RAW)
ISO_OFFSET_X = (DIAG_ISO_X
                + (DIAG_W_HALF - ISO_W_RAW * ISO_SCALE) / 2
                - ISO_X_MIN * ISO_SCALE)
ISO_OFFSET_Y_REL = (DIAG_H - ISO_H_RAW * ISO_SCALE) / 2 - ISO_Y_MIN * ISO_SCALE


def iso_to_screen(x, y, z, page_y0):
    sx, sy = iso_project(x, y, z)
    return (ISO_OFFSET_X + sx * ISO_SCALE,
            page_y0 + DIAG_Y + ISO_OFFSET_Y_REL + sy * ISO_SCALE)


def plan_to_screen(x, y, page_y0):
    return (PLAN_OFFSET_X + x * PLAN_SCALE,
            page_y0 + DIAG_Y + PLAN_OFFSET_Y_REL + y * PLAN_SCALE)


def page_origin(idx):
    return idx * PAGE_H


# ---------------------------------------------------------------------------
# Palette + fonts (matches L-bench guide)
# ---------------------------------------------------------------------------

COL_TEXT = "#000000"
COL_SUBTLE = "#555555"
COL_RULE = "#000000"
COL_RULE_LIGHT = "#777777"
COL_GRID = "#CCCCCC"
COL_FOOTPRINT = "#AAAAAA"

# Materials
COL_PLY_FILL = "#EFE6D2"
COL_PLY_STROKE = "#9A8E70"
COL_PLY_FRONT = "#E1D5B7"
COL_PLY_RIGHT = "#CFC09A"

COL_STEEL_FILL = "#B8B8C2"
COL_STEEL_STROKE = "#3A3A48"
COL_STEEL_FRONT = "#9C9CA8"
COL_STEEL_RIGHT = "#7C7C88"

COL_DRILL_FILL = "#444444"
COL_DRILL_STROKE = "#000000"
COL_DRILL_FRONT = "#333333"
COL_DRILL_RIGHT = "#222222"

COL_PLANER_FILL = "#F4C84A"
COL_PLANER_STROKE = "#5A4500"
COL_PLANER_FRONT = "#E0B232"
COL_PLANER_RIGHT = "#B8901A"

COL_HIGHLIGHT_STROKE = "#000000"
COL_HIGHLIGHT_FILL = "#F2B26A"
COL_HIGHLIGHT_TOP = "#F4BB70"
COL_HIGHLIGHT_FRONT = "#E89D45"
COL_HIGHLIGHT_RIGHT = "#CC7F20"

COL_BOLT = "#000000"
COL_SCREW = "#000000"

FONT_TITLE = "'Abel', 'Helvetica Neue', Helvetica, Arial, sans-serif"
FONT_BODY = "'Barlow', 'Helvetica Neue', Helvetica, Arial, sans-serif"


# ---------------------------------------------------------------------------
# Parts model - every named hardware item that ends up in the cavity
# ---------------------------------------------------------------------------

@dataclass
class Part:
    name: str
    x: float
    y: float
    z: float
    w: float
    d: float
    h: float
    kind: str = "ply"   # ply, steel, drill, planer
    note: str = ""


# Build sequence: each step lists which parts get added. The "new" parts
# at step N are the highlighted ones; parts from steps < N are "built".
# Geometry is approximate - meant to communicate placement, not be a
# precise CAD model. Always verify against the parts in hand.

PARTS: dict[str, Part] = {
    # Step 4 - plywood platform on cavity floor
    "Platform": Part("Platform_28x28_ply", 1, 1, 3.25, 28, 28, 0.75, "ply",
                      "3/4 ply platform, sits 4in above cavity floor"),

    # Step 6 - scissor jack (HF #96406 approx footprint)
    "Jack_Base": Part("Jack_Base", 10, 12, 4.0, 10, 6, 1.0, "steel",
                       "Scissor jack base, 4 lag bolts through to platform"),
    "Jack_Linkage": Part("Jack_Linkage", 11, 13, 5.0, 8, 4, 2.0, "steel",
                          "Stowed scissor linkage (compressed)"),
    "Jack_Top_Stowed": Part("Jack_Top_Stowed", 11, 13, 7.0, 8, 4, 1.0, "steel",
                              "Top plate at min height (8in from cavity floor)"),

    # Step 7 - steel angle drill bracket
    "Drill_Angle": Part("Drill_Angle_2x2x1/8", 8, 6, 4.0, 12, 2, 0.125,
                          "steel",
                          "2x2x1/8 steel angle, mounts to platform + holds drill cradle"),
    "Drill_Cradle": Part("Drill_Cradle_2x4", 10, 7, 4.125, 5, 4, 2.0, "ply",
                          "2x4 scrap with pistol-grip cutout"),

    # Step 8 - drill body in cradle, chuck pointing UP at jack input shaft
    "Drill_Body": Part("Drill_Body", 10.5, 8, 6.125, 4, 2.5, 8, "drill",
                        "Cordless drill, body horizontal in cradle"),
    "Drill_Chuck": Part("Drill_Chuck", 12, 9, 14.0, 1, 1, 2.5, "steel",
                         "Drill chuck holds hex-to-socket adapter"),
    "Socket_Adapter": Part("Socket_Adapter", 12.3, 9.3, 16.5, 0.4, 0.4, 1.5,
                            "steel",
                            "1/4in hex to 3/4in socket adapter, on jack input"),

    # Step 9 - reed switches on cavity walls + magnets on sled
    "Reed_Switch_Bottom": Part("Reed_Switch_Bottom", 0.0, 14, 8.0, 0.5, 2, 1,
                                  "steel",
                                  "Cuts drill power when sled fully DOWN"),
    "Reed_Switch_Top": Part("Reed_Switch_Top", 0.0, 14, 32.0, 0.5, 2, 1,
                              "steel",
                              "Cuts drill power when sled at WORKING height"),
    "Magnet_Bottom": Part("Magnet_Bottom", 1, 14, 8.0, 0.5, 1, 0.5,
                            "steel",
                            "Magnet on sled edge - aligns with bottom reed"),
    "Magnet_Top": Part("Magnet_Top", 1, 14, 24.0, 0.5, 1, 0.5,
                         "steel",
                         "Magnet on sled edge - aligns with top reed"),

    # Step 11 - pin lock receivers in cavity wall + sled edge
    "Pin_Receiver_Wall": Part("Pin_Receiver_Wall_Coupling", 0.0, 7, 24.0,
                                 0.5, 1, 1, "steel",
                                 "1/2in pipe coupling in cavity wall"),
    "Pin_Receiver_Sled": Part("Pin_Receiver_Sled_Coupling", 1.0, 7, 24.0,
                                 0.5, 1, 1, "steel",
                                 "1/2in pipe coupling in sled edge"),

    # Step 12 - planer sled (separate from L-bench cut, sits on jack top)
    "Sled": Part("Planer_Sled_28x28", 1, 1, 24.0, 28, 28, 0.75, "ply",
                  "Planer bolts to this; sits on jack top plate"),

    # Step 13 - planer mounted on sled
    "Planer": Part("Planer_DeWalt", 3, 4, 24.75, 22, 16, 12, "planer",
                    "DeWalt planer, bolted to sled through base"),
}


# Fastener positions (in cavity local coords). Step assignment matches
# the step where the fastener gets installed.
@dataclass
class Fastener:
    x: float
    y: float
    z: float
    kind: str  # "lag", "screw", "bolt", "hose_clamp"
    note: str = ""


FASTENERS_BY_STEP: dict[int, list[Fastener]] = {
    5: [  # Platform to bench framing
        Fastener(3, 3, 3.625, "lag", "Platform to bench bottom rail"),
        Fastener(27, 3, 3.625, "lag", "Platform to bench bottom rail"),
        Fastener(3, 27, 3.625, "lag", "Platform to bench bottom rail"),
        Fastener(27, 27, 3.625, "lag", "Platform to bench bottom rail"),
    ],
    6: [  # Jack base to platform
        Fastener(11, 13, 4.5, "lag", "Jack base to platform"),
        Fastener(19, 13, 4.5, "lag", "Jack base to platform"),
        Fastener(11, 17, 4.5, "lag", "Jack base to platform"),
        Fastener(19, 17, 4.5, "lag", "Jack base to platform"),
    ],
    7: [  # Steel angle to platform + cradle to angle
        Fastener(9, 7, 4.0, "lag", "Steel angle to platform"),
        Fastener(19, 7, 4.0, "lag", "Steel angle to platform"),
        Fastener(11, 8, 6.0, "screw", "Cradle to steel angle"),
        Fastener(14, 8, 6.0, "screw", "Cradle to steel angle"),
    ],
    8: [  # Hose clamps for drill body
        Fastener(11, 8.5, 7.0, "hose_clamp", "Hose clamp on drill body"),
        Fastener(14, 8.5, 7.0, "hose_clamp", "Hose clamp on drill body"),
    ],
    9: [  # Reed switches + magnets (held by adhesive + 2 screws each)
        Fastener(0.25, 14, 7.5, "screw", "Bottom reed switch mounting"),
        Fastener(0.25, 14, 8.5, "screw", "Bottom reed switch mounting"),
        Fastener(0.25, 14, 31.5, "screw", "Top reed switch mounting"),
        Fastener(0.25, 14, 32.5, "screw", "Top reed switch mounting"),
    ],
    11: [  # Pin couplings - epoxied into drilled receiver holes
        Fastener(0.5, 7, 24, "bolt", "Wall coupling - epoxied into wall hole"),
        Fastener(1, 7, 24, "bolt", "Sled coupling - epoxied into sled edge"),
    ],
    12: [  # Planer to sled
        Fastener(5, 6, 25, "bolt", "Planer base bolt #1 (M8 typ)"),
        Fastener(23, 6, 25, "bolt", "Planer base bolt #2"),
        Fastener(5, 18, 25, "bolt", "Planer base bolt #3"),
        Fastener(23, 18, 25, "bolt", "Planer base bolt #4"),
    ],
}

# Map parts to the step where they get installed.
PART_STEP: dict[str, int] = {
    "Platform": 4,
    "Jack_Base": 6, "Jack_Linkage": 6, "Jack_Top_Stowed": 6,
    "Drill_Angle": 7, "Drill_Cradle": 7,
    "Drill_Body": 8, "Drill_Chuck": 8, "Socket_Adapter": 8,
    "Reed_Switch_Bottom": 9, "Reed_Switch_Top": 9,
    "Magnet_Bottom": 9, "Magnet_Top": 9,
    "Pin_Receiver_Wall": 11, "Pin_Receiver_Sled": 11,
    "Sled": 12,
    "Planer": 13,
}


# ---------------------------------------------------------------------------
# Build steps
# ---------------------------------------------------------------------------

STEPS = [
    {"kind": "cover"},
    {"kind": "materials"},
    {"kind": "tools_check"},

    # Step 1 - cavity prep
    {"kind": "assembly", "title": "Step 1: Prepare the Cavity",
     "step_n": 1,
     "instructions": [
         "Open up the L-bench's planer cavity (X=3..33, Y=42..72 in shop coords).",
         "Vacuum out any sawdust. Check that the cavity floor is clear -",
         "no cleats, no internal blocking. Cavity should be a 30 x 30 in",
         "hole, fully open from z=0 to z=37 in.",
         "Verify the bench bottom rails frame the cavity at z=0..4 (toe-kick zone).",
         "Verify the bench top opening is exactly 30 x 30 in (no overhang).",
     ],
     "tools": ["Shop vac", "Tape measure", "Square", "Flashlight"],
     "time": "20 minutes"},

    # Step 2 - build platform
    {"kind": "assembly", "title": "Step 2: Cut the Platform",
     "step_n": 2,
     "instructions": [
         "Cut a 28 x 28 in piece of 3/4 in plywood (already cut during",
         "L-bench build, labeled 'Planer_Sled' - use the FIRST 28x28 piece",
         "as the platform; cut a SECOND 28x28 for the sled in step 9).",
         "Drill 4 lag-bolt clearance holes at the corners (1/4 in dia),",
         "located 2 in in from each edge (4 corners, 4 holes total).",
         "Dry-fit into the cavity at z=4. Confirm 1 in clearance all around.",
     ],
     "tools": ["Circular saw", "Drill + 1/4 in bit", "Square"],
     "time": "30 minutes"},

    # Step 3 - install platform
    {"kind": "assembly", "title": "Step 3: Install the Platform",
     "step_n": 3,
     "patterns": ["Platform"],
     "instructions": [
         "Lower the platform into the cavity, resting on the bench's bottom",
         "rails (at z=4 in). Center it - 1 in clearance to each cavity wall.",
         "Mark the 4 corner hole positions onto the rails through the",
         "platform's pilot holes.",
         "Lift the platform out, pre-drill the rails (3/16 in pilot bit).",
         "Replace platform, drive 4 x (1/4 x 1.5 in) lag bolts with washers.",
         "Confirm platform is solid - push down hard, should not flex.",
     ],
     "tools": ["Drill + 3/16 in bit", "Socket wrench 7/16 in",
               "4 lag bolts 1/4 x 1.5 in", "4 washers"],
     "time": "30 minutes",
     "fastener_step": 5},

    # Step 4 - mount scissor jack
    {"kind": "assembly", "title": "Step 4: Mount the Scissor Jack",
     "step_n": 4,
     "patterns": ["Jack_Base", "Jack_Linkage", "Jack_Top_Stowed"],
     "instructions": [
         "Open the HF #96406 jack in fully-collapsed position.",
         "Identify the input shaft side - this is where the drill mounts.",
         "Orient jack so input shaft points toward the FRONT of the cavity",
         "(toward Y=0 in local coords = the room-facing side).",
         "Center jack on platform: 10 in left margin, 12 in front margin.",
         "Mark the 4 base bolt holes on the platform through the jack base.",
         "Pre-drill platform (3/16 in pilot, do NOT drill all the way through).",
         "Bolt jack to platform with 4 x (5/16 x 2 in) lag bolts.",
     ],
     "tools": ["Drill + 3/16 in bit", "Socket wrench 1/2 in",
               "Pencil + square"],
     "time": "30 minutes",
     "fastener_step": 6},

    # Step 5 - build drill bracket
    {"kind": "drill_bracket_detail",
     "title": "Step 5: Build the Drill Bracket"},

    # Step 5 cont - install bracket
    {"kind": "assembly", "title": "Step 6: Install the Drill Bracket",
     "step_n": 6,
     "patterns": ["Drill_Angle", "Drill_Cradle"],
     "instructions": [
         "Cut the 2x2x1/8 in steel angle to 12 in length. Deburr.",
         "Drill 2 mounting holes through one leg of the angle, 9 in apart",
         "(use 5/16 in bit, slot or oversize for adjustment).",
         "Cut a 5 in piece of 2x4 to use as drill cradle. With a 1.5 in",
         "Forstner bit, drill 2 shallow craters in the top face of the 2x4",
         "to receive the drill body. (Adjust to fit YOUR drill - mock-up first.)",
         "Bolt the cradle to the standing leg of the steel angle with 2",
         "wood screws.",
         "Position the bracket on the platform, lag-bolt the base leg.",
     ],
     "tools": ["Hacksaw", "Drill + bits", "Forstner 1.5 in",
                "Wood screws #10 x 1.5", "2 lag bolts 5/16 x 1.5"],
     "time": "1 hour",
     "fastener_step": 7},

    # Step 7 - mount drill
    {"kind": "assembly", "title": "Step 7: Mount the Drill",
     "step_n": 7,
     "patterns": ["Drill_Body", "Drill_Chuck", "Socket_Adapter"],
     "instructions": [
         "Set the drill in the cradle, chuck facing UP toward the jack input",
         "shaft. Drill body horizontal. Confirm the chuck is RIGHT BELOW the",
         "jack's input hex - within 1/4 in alignment.",
         "Insert the 1/4 in hex to 3/4 in socket adapter into the drill chuck.",
         "Snap a 3/4 in socket onto the adapter (verify your jack's hex size",
         "first - some are 13/16 in).",
         "Push the socket up onto the jack's input shaft.",
         "Wrap 2 hose clamps around the drill body to hold it tight in cradle.",
         "Verify the drill's clutch is set to a LOW torque (start at 5-10).",
     ],
     "tools": ["Drill", "Hex-to-socket adapter", "3/4 socket OR 13/16",
                "2 hose clamps", "Hose clamp screwdriver"],
     "time": "20 minutes",
     "fastener_step": 8},

    # Step 8 - reed switches
    {"kind": "assembly", "title": "Step 8: Install Reed Switches",
     "step_n": 8,
     "patterns": ["Reed_Switch_Bottom", "Reed_Switch_Top",
                  "Magnet_Bottom", "Magnet_Top"],
     "instructions": [
         "Mark switch positions on the LEFT cavity wall (X=0 side, local):",
         "  - BOTTOM switch at z=8 (sled rests here when fully down)",
         "  - TOP switch at z=32 (sled here when planer at working height)",
         "Stick the reed switches to the wall with 3M VHB tape + 2 screws each.",
         "Wire leads go down to the relay (next step).",
         "Glue 2 small neodymium magnets to the LEFT edge of the planer sled,",
         "centered to align with each reed switch when sled is at limit.",
         "Test: bring magnet near each switch with a multimeter - confirm",
         "continuity when magnet is within ~0.5 in.",
     ],
     "tools": ["Multimeter", "Drill + 1/16 in bit",
                "VHB double-sided tape", "Super glue (for magnets)"],
     "time": "1 hour",
     "fastener_step": 9},

    # Step 9 - wiring schematic
    {"kind": "wiring_schematic", "title": "Step 9: Wire the Cutoff Circuit"},

    # Step 10 - install pin lock receivers
    {"kind": "assembly", "title": "Step 10: Install Pin Lock",
     "step_n": 10,
     "patterns": ["Pin_Receiver_Wall", "Pin_Receiver_Sled"],
     "instructions": [
         "Determine working height: with planer mounted on sled (next step",
         "you'll re-check), where does the sled bottom land for the planer",
         "BED to be at 37 in? Mark this Z height on the cavity LEFT wall.",
         "At that mark, drill a 1/2 in hole horizontally through the cavity",
         "wall stud. Epoxy a 1/2 in pipe coupling into the hole, flush with",
         "the inside wall.",
         "On the LEFT edge of the planer sled, drill a matching 1/2 in hole.",
         "Epoxy a second pipe coupling into the sled edge.",
         "Test: raise the sled to working height, slide the 1/2 in hitch pin",
         "through wall coupling into sled coupling. Pin should slide easily.",
         "If pin binds, ream the sled coupling until it slides clean.",
     ],
     "tools": ["Drill + 1/2 in bit", "5-minute epoxy", "1/2 in pipe couplings",
                "1/2 x 6 in hitch pin", "Round file"],
     "time": "1 hour + epoxy cure",
     "fastener_step": 11},

    # Step 11 - mount planer to sled
    {"kind": "assembly", "title": "Step 11: Mount Planer to Sled",
     "step_n": 11,
     "patterns": ["Sled"],
     "instructions": [
         "Cut a second 28 x 28 x 3/4 in plywood sled (or use the spare you",
         "set aside during L-bench Step 13).",
         "Place the planer ON TOP of the sled. Center it, with infeed/outfeed",
         "tables oriented to face the front of the cavity (toward Y=0 local).",
         "Mark the 4 planer base bolt holes onto the sled.",
         "Drill 4 clearance holes (5/16 in usually, check your planer manual).",
         "Bolt the planer to the sled with M8 x 50mm hex bolts (or per planer",
         "manual). Use washers + nylock nuts on the underside.",
         "DO NOT yet place the sled on the jack - test the jack alone first.",
     ],
     "tools": ["Drill + 5/16 in bit", "Wrench set",
                "4 M8 x 50 bolts + washers + nylock nuts"],
     "time": "45 minutes",
     "fastener_step": 12},

    # Step 12 - test cycle (no planer)
    {"kind": "assembly", "title": "Step 12: Test Cycle (No Planer Yet)",
     "step_n": 12,
     "instructions": [
         "Set the empty sled on the jack top plate (no planer yet).",
         "Plug in / power the drill through the relay circuit. Run the drill",
         "in EXTEND direction (CW typ).",
         "Watch the sled rise. Verify:",
         "  - sled rises smoothly without binding",
         "  - reed switch + relay CUTS DRILL POWER at top of travel",
         "  - magnet alignment with switches is correct",
         "Reverse drill direction. Watch sled lower. Verify bottom cutoff.",
         "Test the hitch pin at top - it should slide in cleanly.",
         "REPEAT 3 full cycles before adding the planer.",
     ],
     "tools": ["Multimeter (for verifying cutoff)"],
     "time": "30 minutes"},

    # Step 13 - first test with planer
    {"kind": "assembly", "title": "Step 13: First Cycle WITH Planer",
     "step_n": 13,
     "patterns": ["Planer"],
     "instructions": [
         "With the sled lowered (drill OFF, sled at the bottom stop):",
         "Set the planer-on-sled assembly onto the jack top plate.",
         "Connect the planer's power cord with enough slack for full travel.",
         "Run the drill SLOWLY in EXTEND direction. Listen for binding.",
         "Stop at WORKING HEIGHT - verify the planer BED is at exactly 37 in",
         "above the floor (use a level on the bench top + ruler).",
         "If bed is too low, add 1-4 in of plywood spacers between sled and jack.",
         "If too high, remove material from sled bottom.",
         "Once height is right, INSERT THE HITCH PIN. Always.",
     ],
     "tools": ["Level", "Tape measure", "Plywood spacers (cut to fit)"],
     "time": "1 hour + iteration"},

    {"kind": "safety_check"},
]


# ---------------------------------------------------------------------------
# SVG primitives
# ---------------------------------------------------------------------------

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


def circle(cx, cy, r, fill="none", stroke=None, stroke_w=0.005):
    s = (f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{fill}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{stroke_w}"'
    s += ' />'
    return s


def text(x, y, txt, size=0.13, fill=None, bold=False, anchor="start",
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


def polygon(points, fill="none", stroke=COL_RULE, stroke_w=0.008,
            opacity=1.0):
    pts = " ".join(f"{p[0]:.3f},{p[1]:.3f}" for p in points)
    s = (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
         f'stroke-width="{stroke_w}" opacity="{opacity}" />')
    return s


def path(d, fill="none", stroke=COL_RULE, stroke_w=0.01, dasharray=None):
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"'
    if dasharray:
        s += f' stroke-dasharray="{dasharray}"'
    s += ' />'
    return s


# Fastener markers
def fastener_marker(cx, cy, kind):
    out = []
    if kind == "lag":
        # Hex bolt head - hexagon with a dot in center
        r = 0.05
        out.append(polygon(
            [(cx + r * math.cos(math.radians(60 * i)),
              cy + r * math.sin(math.radians(60 * i))) for i in range(6)],
            fill="#000", stroke="#000", stroke_w=0.004))
    elif kind == "screw":
        # Cross / + symbol
        r = 0.04
        out.append(line(cx - r, cy, cx + r, cy, COL_SCREW, stroke_w=0.012))
        out.append(line(cx, cy - r, cx, cy + r, COL_SCREW, stroke_w=0.012))
    elif kind == "bolt":
        # Round dot with ring
        out.append(circle(cx, cy, 0.05, fill="#000", stroke="#000",
                          stroke_w=0.004))
    elif kind == "hose_clamp":
        # Open circle
        out.append(circle(cx, cy, 0.06, fill="#FFF", stroke="#000",
                          stroke_w=0.012))
    return out


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def page_chrome(page_idx, title, subtitle="", total_pages=0):
    y0 = page_origin(page_idx)
    out = [
        text(MARGIN, y0 + MARGIN + 0.35, title,
              size=0.32, fill=COL_TEXT, bold=True, family=FONT_TITLE),
    ]
    if subtitle:
        out.append(text(PAGE_W - MARGIN, y0 + MARGIN + 0.35, subtitle,
                         size=0.14, fill=COL_SUBTLE, anchor="end"))
    out.append(line(MARGIN, y0 + MARGIN + 0.55,
                     PAGE_W - MARGIN, y0 + MARGIN + 0.55,
                     COL_RULE, stroke_w=0.012))
    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.3,
                     f"{page_idx + 1} / {total_pages}",
                     size=0.11, fill=COL_SUBTLE, anchor="middle"))
    return out


def part_color(kind, new):
    """Return (top_fill, front_fill, right_fill, stroke, stroke_w)."""
    if new:
        return (COL_HIGHLIGHT_TOP, COL_HIGHLIGHT_FRONT, COL_HIGHLIGHT_RIGHT,
                COL_HIGHLIGHT_STROKE, 0.012)
    if kind == "ply":
        return (COL_PLY_FILL, COL_PLY_FRONT, COL_PLY_RIGHT,
                COL_PLY_STROKE, 0.004)
    if kind == "steel":
        return (COL_STEEL_FILL, COL_STEEL_FRONT, COL_STEEL_RIGHT,
                COL_STEEL_STROKE, 0.004)
    if kind == "drill":
        return (COL_DRILL_FILL, COL_DRILL_FRONT, COL_DRILL_RIGHT,
                COL_DRILL_STROKE, 0.004)
    if kind == "planer":
        return (COL_PLANER_FILL, COL_PLANER_FRONT, COL_PLANER_RIGHT,
                COL_PLANER_STROKE, 0.004)
    return (COL_PLY_FILL, COL_PLY_FRONT, COL_PLY_RIGHT,
            COL_PLY_STROKE, 0.004)


def render_cavity_plan(page_idx, built_names, new_names, fastener_step=None):
    y0 = page_origin(page_idx)
    out = []
    out.append(text(DIAG_PLAN_X, y0 + DIAG_Y - 0.05,
                    "TOP-DOWN PLAN  (looking into the cavity from above)",
                    size=0.09, fill=COL_SUBTLE, family=FONT_TITLE))

    # 6-inch grid
    for gx in range(0, int(CAV_W) + 1, 6):
        sx, _ = plan_to_screen(gx, 0, y0)
        _, sy0 = plan_to_screen(0, 0, y0)
        _, sy1 = plan_to_screen(0, CAV_D, y0)
        out.append(line(sx, sy0, sx, sy1, COL_GRID, stroke_w=0.004))
    for gy in range(0, int(CAV_D) + 1, 6):
        sx0, sy = plan_to_screen(0, gy, y0)
        sx1, _ = plan_to_screen(CAV_W, gy, y0)
        out.append(line(sx0, sy, sx1, sy, COL_GRID, stroke_w=0.004))

    # Cavity outline
    sx, sy = plan_to_screen(0, 0, y0)
    out.append(rect(sx, sy, CAV_W * PLAN_SCALE, CAV_D * PLAN_SCALE,
                    fill="none", stroke=COL_RULE, stroke_w=0.012))

    # Render parts: built first then new (both as rects in plan view)
    for want_new in [False, True]:
        for pname, part in PARTS.items():
            is_new = pname in new_names
            is_built = pname in built_names
            if want_new and not is_new:
                continue
            if (not want_new) and (is_new or not is_built):
                continue
            top, front, right, stroke, sw = part_color(part.kind, is_new)
            sx, sy = plan_to_screen(part.x, part.y, y0)
            sw_ = max(part.w * PLAN_SCALE, 0.015)
            sd_ = max(part.d * PLAN_SCALE, 0.015)
            out.append(rect(sx, sy, sw_, sd_, fill=top, stroke=stroke,
                             stroke_w=sw))

    # Fasteners for this step
    if fastener_step and fastener_step in FASTENERS_BY_STEP:
        for f in FASTENERS_BY_STEP[fastener_step]:
            sx, sy = plan_to_screen(f.x, f.y, y0)
            out.extend(fastener_marker(sx, sy, f.kind))

    # Axis labels
    out.append(text(DIAG_PLAN_X, y0 + DIAG_Y + DIAG_H + 0.18,
                    "Y = depth (in)   <- room side at Y=0",
                    size=0.08, fill=COL_SUBTLE))

    return out


def render_cavity_iso(page_idx, built_names, new_names):
    y0 = page_origin(page_idx)
    out = []
    out.append(text(DIAG_ISO_X, y0 + DIAG_Y - 0.05,
                    "ISOMETRIC  (front-right view, walls partial)",
                    size=0.09, fill=COL_SUBTLE, family=FONT_TITLE))

    # Cavity floor outline (dashed)
    def ipt(x, y, z):
        return iso_to_screen(x, y, z, y0)
    out.append(polygon([ipt(0, 0, 0), ipt(CAV_W, 0, 0),
                         ipt(CAV_W, CAV_D, 0), ipt(0, CAV_D, 0)],
                        fill="none", stroke=COL_FOOTPRINT,
                        stroke_w=0.006))
    # Bench top opening (dashed at z=37)
    out.append(polygon([ipt(0, 0, CAV_H), ipt(CAV_W, 0, CAV_H),
                         ipt(CAV_W, CAV_D, CAV_H), ipt(0, CAV_D, CAV_H)],
                        fill="none", stroke=COL_FOOTPRINT,
                        stroke_w=0.006))
    # Left wall (X=0) and back wall (Y=0) - draw as see-through outlines
    for face in [
        [ipt(0, 0, 0), ipt(0, CAV_D, 0), ipt(0, CAV_D, CAV_H), ipt(0, 0, CAV_H)],
        [ipt(0, 0, 0), ipt(CAV_W, 0, 0), ipt(CAV_W, 0, CAV_H), ipt(0, 0, CAV_H)],
    ]:
        out.append(polygon(face, fill="none", stroke=COL_FOOTPRINT,
                            stroke_w=0.005, opacity=0.6))

    # Sort parts by depth (far first)
    def depth(p):
        return (p.x + p.w / 2) + (p.y + p.d / 2) + (p.z + p.h / 2)

    drawables = []
    for pname, p in PARTS.items():
        if pname in built_names or pname in new_names:
            drawables.append((pname, p, pname in new_names))
    drawables.sort(key=lambda t: depth(t[1]))

    for pname, p, is_new in drawables:
        top_c, front_c, right_c, stroke, sw = part_color(p.kind, is_new)
        x0, y0_, z0 = p.x, p.y, p.z
        x1, y1, z1 = p.x + p.w, p.y + p.d, p.z + p.h
        top = [ipt(x0, y0_, z1), ipt(x1, y0_, z1),
                ipt(x1, y1, z1), ipt(x0, y1, z1)]
        right = [ipt(x1, y0_, z0), ipt(x1, y1, z0),
                  ipt(x1, y1, z1), ipt(x1, y0_, z1)]
        front = [ipt(x0, y1, z0), ipt(x1, y1, z0),
                  ipt(x1, y1, z1), ipt(x0, y1, z1)]
        out.append(polygon(right, fill=right_c, stroke=stroke, stroke_w=sw))
        out.append(polygon(front, fill=front_c, stroke=stroke, stroke_w=sw))
        out.append(polygon(top, fill=top_c, stroke=stroke, stroke_w=sw))

    return out


def render_instructions(page_idx, instructions, tools=None, time_est="",
                         fastener_legend=False):
    y0 = page_origin(page_idx)
    out = []
    instr_y = y0 + DIAG_Y + DIAG_H + 0.30
    instr_bottom = y0 + PAGE_H - 0.55

    sidebar_w = 1.9
    sidebar_x = PAGE_W - MARGIN - sidebar_w

    out.append(line(MARGIN, instr_y - 0.10,
                     PAGE_W - MARGIN, instr_y - 0.10,
                     COL_RULE_LIGHT, stroke_w=0.006))
    out.append(line(sidebar_x - 0.1, instr_y, sidebar_x - 0.1, instr_bottom,
                     COL_RULE_LIGHT, stroke_w=0.006))

    ix = MARGIN
    iy = instr_y + 0.22
    out.append(text(ix, iy, "INSTRUCTIONS",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    iy += 0.30
    for instr in instructions:
        out.append(text(ix, iy, instr, size=0.12, fill=COL_TEXT,
                        family=FONT_BODY))
        iy += 0.20

    sy = instr_y + 0.22
    out.append(text(sidebar_x, sy, "TOOLS",
                    size=0.13, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    sy += 0.24
    if tools:
        for t in tools:
            out.append(text(sidebar_x, sy, "- " + t,
                            size=0.11, fill=COL_TEXT, family=FONT_BODY))
            sy += 0.18
    sy += 0.18
    if time_est:
        out.append(text(sidebar_x, sy, "TIME",
                        size=0.13, fill=COL_TEXT, bold=True,
                        family=FONT_TITLE))
        sy += 0.24
        out.append(text(sidebar_x, sy, time_est,
                        size=0.11, fill=COL_TEXT, family=FONT_BODY))

    # Legend (parts + fasteners) at bottom left
    legend_y = instr_bottom - 0.18
    # Materials legend
    swatches = [
        (COL_PLY_FILL, COL_PLY_STROKE, "ply"),
        (COL_STEEL_FILL, COL_STEEL_STROKE, "steel"),
        (COL_DRILL_FILL, COL_DRILL_STROKE, "drill"),
        (COL_PLANER_FILL, COL_PLANER_STROKE, "planer"),
        (COL_HIGHLIGHT_FILL, COL_HIGHLIGHT_STROKE, "new this step"),
    ]
    sw_x = ix
    for fill, stroke, label in swatches:
        out.append(rect(sw_x, legend_y - 0.10, 0.13, 0.08,
                        fill=fill, stroke=stroke, stroke_w=0.005))
        out.append(text(sw_x + 0.17, legend_y - 0.03, label,
                        size=0.09, fill=COL_TEXT, family=FONT_BODY))
        sw_x += 1.0

    if fastener_legend:
        # Fastener legend on a second row
        legend2_y = legend_y - 0.30
        fx = ix
        for kind, label in [("lag", "lag bolt"), ("screw", "wood screw"),
                            ("bolt", "machine bolt"),
                            ("hose_clamp", "hose clamp")]:
            out.extend(fastener_marker(fx + 0.08, legend2_y - 0.05, kind))
            out.append(text(fx + 0.20, legend2_y - 0.03, label,
                            size=0.09, fill=COL_TEXT, family=FONT_BODY))
            fx += 1.0

    return out


# ---------------------------------------------------------------------------
# Special pages
# ---------------------------------------------------------------------------

def render_cover(page_idx, total_pages):
    y0 = page_origin(page_idx)
    out = []
    out.append(text(PAGE_W / 2, y0 + 1.9, "PLANER",
                    size=1.0, fill=COL_TEXT, bold=True, anchor="middle",
                    family=FONT_TITLE))
    out.append(text(PAGE_W / 2, y0 + 2.6, "LIFT",
                    size=1.0, fill=COL_TEXT, bold=True, anchor="middle",
                    family=FONT_TITLE))
    out.append(text(PAGE_W / 2, y0 + 3.1, "BUILD GUIDE",
                    size=0.42, fill=COL_TEXT, bold=True, anchor="middle",
                    family=FONT_TITLE))
    out.append(line(MARGIN + 1.5, y0 + 3.4, PAGE_W - MARGIN - 1.5, y0 + 3.4,
                     COL_RULE, stroke_w=0.02))
    out.append(text(PAGE_W / 2, y0 + 3.8,
                    "Scissor stabilizer + drill motor mechanism",
                    size=0.20, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))
    out.append(text(PAGE_W / 2, y0 + 4.1,
                    "(install after the L-bench frame is complete)",
                    size=0.14, fill=COL_SUBTLE, anchor="middle",
                    family=FONT_BODY))

    # Quick exploded-view sketch
    cx = PAGE_W / 2
    cy = y0 + 6.5
    # Drawing: vertical stack of components
    # Cavity outline
    out.append(rect(cx - 1.2, cy - 1.8, 2.4, 3.6,
                    fill="none", stroke=COL_RULE, stroke_w=0.012,
                    dasharray="0.06,0.04"))
    out.append(text(cx, cy - 2.0, "(cavity, 30 x 30 x 37 in)",
                    size=0.10, fill=COL_SUBTLE, anchor="middle"))

    # Planer at top
    out.append(rect(cx - 0.9, cy - 1.7, 1.8, 0.3,
                    fill=COL_PLANER_FILL, stroke=COL_PLANER_STROKE,
                    stroke_w=0.01))
    out.append(text(cx, cy - 1.50, "PLANER",
                    size=0.10, fill=COL_TEXT, anchor="middle", bold=True))

    # Sled
    out.append(rect(cx - 1.0, cy - 1.35, 2.0, 0.15,
                    fill=COL_PLY_FILL, stroke=COL_PLY_STROKE, stroke_w=0.008))
    out.append(text(cx, cy - 1.22, "sled (28 x 28 x 3/4)",
                    size=0.09, fill=COL_TEXT, anchor="middle"))

    # Jack (scissor) - simple X
    out.append(line(cx - 0.5, cy - 1.15, cx + 0.5, cy - 0.45,
                     COL_STEEL_STROKE, stroke_w=0.015))
    out.append(line(cx + 0.5, cy - 1.15, cx - 0.5, cy - 0.45,
                     COL_STEEL_STROKE, stroke_w=0.015))
    out.append(rect(cx - 0.55, cy - 0.45, 1.1, 0.10,
                    fill=COL_STEEL_FILL, stroke=COL_STEEL_STROKE,
                    stroke_w=0.008))
    out.append(text(cx + 0.7, cy - 0.8, "scissor",
                    size=0.09, fill=COL_TEXT, anchor="start"))
    out.append(text(cx + 0.7, cy - 0.65, "jack",
                    size=0.09, fill=COL_TEXT, anchor="start"))

    # Drill bracket + drill
    out.append(rect(cx - 0.8, cy - 0.35, 0.1, 0.2,
                    fill=COL_STEEL_FILL, stroke=COL_STEEL_STROKE,
                    stroke_w=0.008))
    out.append(rect(cx - 0.7, cy - 0.25, 0.5, 0.1,
                    fill=COL_DRILL_FILL, stroke=COL_DRILL_STROKE,
                    stroke_w=0.008))
    out.append(text(cx - 1.3, cy - 0.20, "drill",
                    size=0.09, fill=COL_TEXT, anchor="end"))

    # Platform
    out.append(rect(cx - 1.0, cy - 0.10, 2.0, 0.12,
                    fill=COL_PLY_FILL, stroke=COL_PLY_STROKE, stroke_w=0.008))
    out.append(text(cx, cy + 0.04, "platform (28 x 28 x 3/4)",
                    size=0.09, fill=COL_TEXT, anchor="middle"))

    # Floor
    out.append(line(cx - 1.2, cy + 0.5, cx + 1.2, cy + 0.5,
                     COL_RULE, stroke_w=0.012))
    out.append(text(cx, cy + 0.65, "cavity floor (bench bottom rails)",
                    size=0.09, fill=COL_SUBTLE, anchor="middle"))

    # Stats
    stats_y = y0 + 9.0
    out.append(text(PAGE_W / 2, stats_y,
                    "~$90 in parts  +  one old drill",
                    size=0.18, fill=COL_TEXT, anchor="middle"))
    out.append(text(PAGE_W / 2, stats_y + 0.30,
                    "Build time: 1 weekend (5-7 hours)",
                    size=0.13, fill=COL_SUBTLE, anchor="middle"))

    out.append(text(PAGE_W / 2, y0 + PAGE_H - 0.5,
                    f"{total_pages} pages total - print the whole document",
                    size=0.11, fill=COL_SUBTLE, anchor="middle"))
    return out


def render_materials(page_idx, total_pages):
    out = page_chrome(page_idx, "Materials Checklist",
                      total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    items = [
        ("HAUL-MASTER 2.5 Ton Scissor Stabilizer", "HF #96406", "1", "$38"),
        ("Old corded or cordless drill", "shelf", "1", "$0"),
        ("1/4 hex to 3/4 in socket adapter", "HD / Amazon", "1", "$5"),
        ("3/4 in socket (verify YOUR jack input)", "HD", "1", "$3"),
        ("Magnetic reed switch + magnet", "Amazon", "2", "$20"),
        ("12V relay, 10A rated", "Amazon", "1", "$8"),
        ("1/2 x 6 in steel hitch pin", "HD #660429", "1", "$4"),
        ("1/2 in pipe coupling (pin receiver)", "HD #392104", "2", "$6"),
        ("2 in x 2 in x 1/8 in steel angle (1 ft)", "HD / local steel", "1", "$5"),
        ("Lag bolts 5/16 x 2 in (jack to platform)", "HD", "8", "$4"),
        ("Lag bolts 1/4 x 1.5 in (platform to bench)", "HD", "4", "$2"),
        ("Wood screws #10 x 1.5 in", "HD bulk", "10", "$2"),
        ("Hose clamps 2 in (drill body)", "HD", "2", "$6"),
        ("3M VHB tape (reed switch mounting)", "HD", "1 roll", "$8"),
        ("5-minute epoxy (pin coupling install)", "HD", "1 pkg", "$5"),
        ("16 ga wire (relay + reed switch leads)", "HD", "20 ft", "$8"),
        ("Wire nuts / butt connectors", "HD", "1 pack", "$5"),
        ("Foot pedal switch (optional)", "Amazon", "1", "$15"),
    ]

    # Header
    out.append(text(MARGIN + 0.35, cy + 0.15, "Item",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    out.append(text(MARGIN + 3.8, cy + 0.15, "Source",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    out.append(text(MARGIN + 5.5, cy + 0.15, "Qty",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    out.append(text(MARGIN + 6.3, cy + 0.15, "$",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.30
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE, stroke_w=0.008))
    cy += 0.18

    total = 0
    for item, src, qty, cost in items:
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16, fill="none",
                        stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, item,
                        size=0.11, fill=COL_TEXT, family=FONT_BODY))
        out.append(text(MARGIN + 3.8, cy, src,
                        size=0.10, fill=COL_SUBTLE, family=FONT_BODY))
        out.append(text(MARGIN + 5.5, cy, qty,
                        size=0.11, fill=COL_TEXT, bold=True, family=FONT_BODY))
        out.append(text(MARGIN + 6.3, cy, cost,
                        size=0.11, fill=COL_TEXT, family=FONT_BODY))
        cy += 0.26

    cy += 0.15
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE, stroke_w=0.008))
    cy += 0.22
    out.append(text(PAGE_W - MARGIN, cy, "Approx total: $130-150",
                    size=0.15, fill=COL_TEXT, bold=True, anchor="end",
                    family=FONT_TITLE))
    cy += 0.30
    out.append(text(MARGIN, cy,
                    "Verify the jack input shaft hex size (3/4 vs 13/16 in)",
                    size=0.11, fill=COL_SUBTLE, family=FONT_BODY))
    cy += 0.18
    out.append(text(MARGIN, cy,
                    "BEFORE buying the socket adapter. Open the HF box in-store.",
                    size=0.11, fill=COL_SUBTLE, family=FONT_BODY))
    return out


def render_tools_check(page_idx, total_pages):
    out = page_chrome(page_idx, "Tools + Pre-Build Verification",
                      total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    out.append(text(MARGIN, cy, "Tools you need",
                    size=0.18, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.32
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.20
    tools = [
        "Drill / driver + bits (1/16, 3/16, 5/16, 1/2 in)",
        "Hacksaw (for cutting steel angle)",
        "Forstner bit 1.5 in (drill body cradle)",
        "Socket wrench set (1/2 in for lag bolts)",
        "Multimeter (continuity test for reed switches)",
        "Soldering iron + solder OR wire nuts",
        "Wire strippers, side cutters",
        "Tape measure, square, pencil",
        "Level (4 ft minimum)",
        "Shop vac",
        "Safety glasses, ear protection",
    ]
    for t in tools:
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16, fill="none",
                        stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, t,
                        size=0.12, fill=COL_TEXT, family=FONT_BODY))
        cy += 0.26

    cy += 0.25
    out.append(text(MARGIN, cy,
                    "Pre-build verification (do these BEFORE Step 1)",
                    size=0.16, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.32
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.20
    verify = [
        "Open the HF #96406 box in-store. MEASURE the input hex shaft.",
        "Compare to 3/4 in vs 13/16 in socket - buy the matching one.",
        "Measure the jack collapsed-height and extended-height in person.",
        "Confirm your drill clutch goes low enough (5-10 setting min).",
        "Identify which direction on your drill is JACK EXTEND (usually CW).",
        "Inventory all bolts, screws, magnets - everything on shopping list.",
        "Confirm L-bench planer cavity is fully open + framing rails clear.",
        "Plan the relay + wire routing inside the bench (where does power come from?)",
    ]
    for v in verify:
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16, fill="none",
                        stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, v,
                        size=0.12, fill=COL_TEXT, family=FONT_BODY))
        cy += 0.26
    return out


def render_drill_bracket_detail(page_idx, total_pages):
    """Custom detail page for the drill bracket fabrication."""
    out = page_chrome(page_idx, "Step 5: Build the Drill Bracket",
                      subtitle="DETAIL DRAWING", total_pages=total_pages)
    y0 = page_origin(page_idx)

    # Main detail area: 6 in wide x 3.5 in tall, centered
    cx0 = MARGIN + 0.3
    cy0 = y0 + 1.4
    cw = 7.4
    ch = 3.6

    # Title for the detail
    out.append(text(cx0, cy0, "STEEL ANGLE 2 x 2 x 1/8 in  -  cut to 12 in",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))

    # Draw the steel angle in 3 views: top, front, side
    # Use a local scale, 0.25 in/in
    s = 0.20
    angle_y = cy0 + 0.4

    # ---- TOP VIEW (looking down at the bracket lying flat) ----
    tx = cx0
    out.append(text(tx, angle_y, "TOP VIEW (looking down)",
                    size=0.10, fill=COL_SUBTLE))
    # Horizontal leg of the angle (12 in long x 2 in wide)
    out.append(rect(tx, angle_y + 0.1, 12 * s, 2 * s,
                    fill=COL_STEEL_FILL, stroke=COL_STEEL_STROKE,
                    stroke_w=0.012))
    # Mounting holes (5/16 in) at 1.5 and 10.5 in from left end
    for hx in [1.5, 10.5]:
        out.extend(fastener_marker(tx + hx * s, angle_y + 0.1 + 1.0 * s,
                                    "lag"))
    # Dimension lines
    out.append(line(tx, angle_y + 0.1 + 2 * s + 0.08,
                     tx + 12 * s, angle_y + 0.1 + 2 * s + 0.08,
                     COL_TEXT, stroke_w=0.006))
    out.append(text(tx + 6 * s, angle_y + 0.1 + 2 * s + 0.20, "12 in",
                    size=0.10, fill=COL_TEXT, anchor="middle"))
    # Hole spacing dimension
    out.append(line(tx + 1.5 * s, angle_y + 0.04,
                     tx + 10.5 * s, angle_y + 0.04,
                     COL_TEXT, stroke_w=0.006))
    out.append(text(tx + 6 * s, angle_y - 0.06, "9 in (hole spacing)",
                    size=0.09, fill=COL_TEXT, anchor="middle"))

    # ---- FRONT VIEW (looking at the standing leg) ----
    fx = cx0
    fy = angle_y + 0.1 + 2 * s + 0.5
    out.append(text(fx, fy, "FRONT VIEW (looking at the standing leg)",
                    size=0.10, fill=COL_SUBTLE))
    fy += 0.10
    # Standing leg: 12 in x 2 in tall (L-cross-section: thin vertical leg)
    out.append(rect(fx, fy + 2 * s - 0.04, 12 * s, 0.04,
                    fill=COL_STEEL_FILL, stroke=COL_STEEL_STROKE,
                    stroke_w=0.008))
    out.append(rect(fx, fy, 0.04, 2 * s,
                    fill=COL_STEEL_FILL, stroke=COL_STEEL_STROKE,
                    stroke_w=0.008))
    # The 90 deg angle hatched
    out.append(line(fx, fy, fx + 0.04, fy + 0.04, COL_STEEL_STROKE,
                     stroke_w=0.006))
    out.append(text(fx + 12 * s + 0.05, fy + 1 * s,
                    "1/8 in thick", size=0.09, fill=COL_TEXT))
    out.append(text(fx - 0.05, fy + 2 * s + 0.04, "2 in",
                    size=0.09, fill=COL_TEXT, anchor="end"))

    # ---- CRADLE DETAIL (the 2x4 with the Forstner crater) ----
    bx = cx0 + 4.5
    by = cy0 + 0.4
    out.append(text(bx, by, "DRILL CRADLE (cut from 2x4 scrap)",
                    size=0.10, fill=COL_SUBTLE))
    by += 0.10
    cs = 0.30
    # Side view of cradle: 5 in long x 3.5 in tall (2x4 dimensions)
    out.append(rect(bx, by, 5 * cs, 3.5 * cs,
                    fill=COL_PLY_FILL, stroke=COL_PLY_STROKE, stroke_w=0.012))
    # 1.5 in diameter half-circle crater for drill body
    crater_cx = bx + 2.5 * cs
    crater_cy = by
    out.append(path(
        f"M {crater_cx - 0.75 * cs:.3f} {crater_cy:.3f} "
        f"A {0.75 * cs:.3f} {0.75 * cs:.3f} 0 0 0 "
        f"{crater_cx + 0.75 * cs:.3f} {crater_cy:.3f}",
        fill="white", stroke=COL_PLY_STROKE, stroke_w=0.012))
    out.append(text(crater_cx, crater_cy - 0.10,
                    "1.5 in dia Forstner",
                    size=0.09, fill=COL_TEXT, anchor="middle"))
    # Mounting hole for screw into steel angle
    out.append(text(bx + 0.5 * cs, by + 3.0 * cs, "screw",
                    size=0.08, fill=COL_TEXT))
    out.extend(fastener_marker(bx + 0.5 * cs, by + 3.2 * cs, "screw"))
    out.append(text(bx + 5 * cs + 0.1, by + 1 * cs, "5 in long",
                    size=0.09, fill=COL_TEXT))

    # Instructions below
    instr_y = y0 + 6.5
    out.append(line(MARGIN, instr_y, PAGE_W - MARGIN, instr_y,
                     COL_RULE_LIGHT, stroke_w=0.006))
    instr_y += 0.30
    out.append(text(MARGIN, instr_y, "FABRICATION",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    instr_y += 0.30

    steps = [
        "1. Cut the 2 x 2 x 1/8 steel angle to 12 in length with a hacksaw.",
        "   Deburr both ends with a file.",
        "2. Mark 2 hole positions on the HORIZONTAL leg, 1.5 and 10.5 in",
        "   from one end, centered along the 2 in width.",
        "3. Drill 2 x 5/16 in clearance holes at the marks.",
        "4. Cut a 5 in piece of 2x4 scrap for the drill cradle.",
        "5. With a 1.5 in Forstner bit, drill a SHALLOW (about 1/2 in deep)",
        "   half-circle crater across the top face of the 2x4 to receive",
        "   the drill body. The crater axis should run perpendicular to",
        "   the 2x4's long dimension.",
        "6. Adjust crater diameter to match YOUR drill body. Mock-fit the",
        "   drill into it - should sit snug, no play, no binding.",
        "7. Pre-drill 2 holes in the cradle for #10 wood screws.",
        "8. Screw the cradle to the STANDING leg of the steel angle.",
        "",
        "When done you have an L-shaped bracket: horizontal leg lag-bolts",
        "to the platform; standing leg holds the drill cradle facing UP.",
    ]
    for s in steps:
        out.append(text(MARGIN, instr_y, s, size=0.12, fill=COL_TEXT,
                         family=FONT_BODY))
        instr_y += 0.20
    return out


def render_wiring_schematic(page_idx, total_pages):
    out = page_chrome(page_idx, "Step 9: Wire the Cutoff Circuit",
                      subtitle="ELECTRICAL SCHEMATIC", total_pages=total_pages)
    y0 = page_origin(page_idx)

    # Centered schematic area
    sx0 = MARGIN + 0.5
    sy0 = y0 + 1.6
    sw_total = 7.0
    sh_total = 4.5

    # Labels
    out.append(text(sx0, sy0, "120V AC power flow with two reed-switch end stops",
                    size=0.12, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    sy0 += 0.20

    # Draw schematic
    # AC source on left
    ac_x = sx0 + 0.3
    ac_y = sy0 + 1.0
    out.append(circle(ac_x, ac_y, 0.20, fill="none", stroke=COL_RULE,
                       stroke_w=0.012))
    out.append(text(ac_x, ac_y + 0.05, "~", size=0.18, fill=COL_TEXT,
                     anchor="middle", bold=True))
    out.append(text(ac_x, ac_y + 0.35, "120V AC", size=0.10, fill=COL_TEXT,
                     anchor="middle"))

    # Wire from AC to relay
    out.append(line(ac_x + 0.2, ac_y, ac_x + 1.2, ac_y, COL_RULE,
                     stroke_w=0.012))

    # Relay box
    relay_x = ac_x + 1.2
    relay_y = ac_y - 0.6
    out.append(rect(relay_x, relay_y, 1.5, 1.2, fill="none",
                    stroke=COL_RULE, stroke_w=0.012))
    out.append(text(relay_x + 0.75, relay_y - 0.06, "RELAY",
                    size=0.11, fill=COL_TEXT, bold=True, anchor="middle"))
    out.append(text(relay_x + 0.75, relay_y + 0.20, "12V coil",
                    size=0.09, fill=COL_TEXT, anchor="middle"))
    out.append(text(relay_x + 0.75, relay_y + 0.50, "10A contacts",
                    size=0.09, fill=COL_TEXT, anchor="middle"))
    out.append(text(relay_x + 0.75, relay_y + 0.80, "(NO + NC)",
                    size=0.09, fill=COL_TEXT, anchor="middle"))

    # Wire from relay to drill
    out.append(line(relay_x + 1.5, ac_y, relay_x + 2.6, ac_y, COL_RULE,
                     stroke_w=0.012))

    # Drill on right
    drill_x = relay_x + 2.6
    out.append(rect(drill_x, ac_y - 0.25, 1.4, 0.5,
                    fill=COL_DRILL_FILL, stroke=COL_DRILL_STROKE,
                    stroke_w=0.012))
    out.append(text(drill_x + 0.7, ac_y + 0.05, "DRILL",
                    size=0.12, fill="white", bold=True, anchor="middle"))
    out.append(text(drill_x + 0.7, ac_y - 0.40, "trigger zip-tied DOWN",
                    size=0.09, fill=COL_TEXT, anchor="middle"))

    # 12V relay coil control: separate small loop with reed switches in series
    # Coil power source (e.g. AC adapter)
    c_y = relay_y + 1.7
    cs_x = sx0 + 0.3
    out.append(text(cs_x, c_y - 0.20,
                    "RELAY COIL CONTROL (12V DC, low current)",
                    size=0.11, fill=COL_TEXT, bold=True, family=FONT_TITLE))

    # 12V battery / wallwart
    out.append(rect(cs_x, c_y, 0.6, 0.5, fill="none", stroke=COL_RULE,
                    stroke_w=0.012))
    out.append(text(cs_x + 0.3, c_y + 0.18, "12V", size=0.11, fill=COL_TEXT,
                     bold=True, anchor="middle"))
    out.append(text(cs_x + 0.3, c_y + 0.40, "wallwart",
                    size=0.08, fill=COL_TEXT, anchor="middle"))

    # Wire from + to reed switch 1 (top of travel)
    w_y = c_y + 0.10
    out.append(line(cs_x + 0.6, w_y, cs_x + 1.4, w_y, COL_RULE,
                     stroke_w=0.012))
    # Reed switch 1 (normally closed - opens when sled magnet present)
    reed1_x = cs_x + 1.4
    out.append(rect(reed1_x, w_y - 0.15, 0.8, 0.30,
                    fill="none", stroke=COL_STEEL_STROKE, stroke_w=0.012))
    # NC contact symbol (line crossing through)
    out.append(line(reed1_x + 0.1, w_y, reed1_x + 0.7, w_y,
                     COL_STEEL_STROKE, stroke_w=0.012))
    out.append(line(reed1_x + 0.4, w_y - 0.10, reed1_x + 0.7, w_y - 0.10,
                     COL_STEEL_STROKE, stroke_w=0.012))
    out.append(text(reed1_x + 0.4, w_y - 0.25, "REED TOP",
                    size=0.08, fill=COL_TEXT, anchor="middle"))
    out.append(text(reed1_x + 0.4, w_y + 0.30, "(NC)",
                    size=0.08, fill=COL_TEXT, anchor="middle"))

    # Wire to reed switch 2
    out.append(line(reed1_x + 0.8, w_y, reed1_x + 1.5, w_y, COL_RULE,
                     stroke_w=0.012))
    reed2_x = reed1_x + 1.5
    out.append(rect(reed2_x, w_y - 0.15, 0.8, 0.30,
                    fill="none", stroke=COL_STEEL_STROKE, stroke_w=0.012))
    out.append(line(reed2_x + 0.1, w_y, reed2_x + 0.7, w_y,
                     COL_STEEL_STROKE, stroke_w=0.012))
    out.append(line(reed2_x + 0.4, w_y - 0.10, reed2_x + 0.7, w_y - 0.10,
                     COL_STEEL_STROKE, stroke_w=0.012))
    out.append(text(reed2_x + 0.4, w_y - 0.25, "REED BOTTOM",
                    size=0.08, fill=COL_TEXT, anchor="middle"))
    out.append(text(reed2_x + 0.4, w_y + 0.30, "(NC)",
                    size=0.08, fill=COL_TEXT, anchor="middle"))

    # Wire to relay coil
    out.append(line(reed2_x + 0.8, w_y, reed2_x + 1.4, w_y, COL_RULE,
                     stroke_w=0.012))
    out.append(line(reed2_x + 1.4, w_y, reed2_x + 1.4, w_y + 0.5,
                     COL_RULE, stroke_w=0.012))
    # Relay coil indicator
    out.append(rect(reed2_x + 1.25, w_y + 0.5, 0.3, 0.3,
                    fill="none", stroke=COL_RULE, stroke_w=0.012))
    out.append(text(reed2_x + 1.40, w_y + 0.70, "C",
                    size=0.10, fill=COL_TEXT, bold=True, anchor="middle"))
    # Return to -
    out.append(line(reed2_x + 1.4, w_y + 0.8, reed2_x + 1.4, w_y + 1.0,
                     COL_RULE, stroke_w=0.012))
    out.append(line(reed2_x + 1.4, w_y + 1.0, cs_x + 0.3, w_y + 1.0,
                     COL_RULE, stroke_w=0.012))
    out.append(line(cs_x + 0.3, w_y + 1.0, cs_x + 0.3, c_y + 0.5,
                     COL_RULE, stroke_w=0.012))

    # Explanation
    exp_y = y0 + 7.8
    out.append(line(MARGIN, exp_y, PAGE_W - MARGIN, exp_y,
                     COL_RULE_LIGHT, stroke_w=0.006))
    exp_y += 0.30
    out.append(text(MARGIN, exp_y, "HOW IT WORKS",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    exp_y += 0.30
    notes = [
        "Both reed switches are NORMALLY CLOSED. When neither magnet is near,",
        "current flows through both switches in series, energizing the relay coil.",
        "Relay closes the AC contacts -> drill has power.",
        "",
        "When the sled reaches EITHER end of travel, the magnet on the sled edge",
        "comes near its matching reed switch. The reed OPENS, breaking the coil",
        "circuit. Relay drops out, AC contacts open, DRILL LOSES POWER.",
        "",
        "Operator reverses the drill direction by hand (the direction switch on",
        "the drill body is still accessible) and runs again. Magnet leaves the",
        "switch zone, reed closes, relay re-energizes, drill spins again.",
        "",
        "OPTIONAL: add a foot-pedal switch in series with the 12V supply so the",
        "operator can KILL the drill instantly without leaning over the planer.",
    ]
    for n in notes:
        out.append(text(MARGIN, exp_y, n, size=0.11, fill=COL_TEXT,
                         family=FONT_BODY))
        exp_y += 0.18
    return out


def render_safety_check(page_idx, total_pages):
    out = page_chrome(page_idx, "Final Safety Check + Operation",
                      total_pages=total_pages)
    y0 = page_origin(page_idx)
    cy = y0 + 1.5

    out.append(text(MARGIN, cy, "Before every use",
                    size=0.18, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.32
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.22
    checks = [
        "Hitch pin is OUT before you raise or lower (cycling against pin = damage).",
        "All cables clear of the moving sled travel path.",
        "Planer power cord has slack for full travel (don't yank from outlet).",
        "Drill clutch set to LOW torque (5-10) - clutch should slip before damage.",
        "Reed switches respond to magnets (test with multimeter occasionally).",
    ]
    for c in checks:
        out.append(rect(MARGIN, cy - 0.13, 0.16, 0.16, fill="none",
                        stroke=COL_RULE, stroke_w=0.01))
        out.append(text(MARGIN + 0.35, cy, c, size=0.12, fill=COL_TEXT,
                        family=FONT_BODY))
        cy += 0.28

    cy += 0.25
    out.append(text(MARGIN, cy, "Operation sequence",
                    size=0.18, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.32
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE_LIGHT,
                     stroke_w=0.006))
    cy += 0.22
    seq = [
        "1. Verify hitch pin is OUT.",
        "2. Set drill direction to EXTEND (CW).",
        "3. Pull foot-pedal / engage relay - drill spins, jack rises.",
        "4. Drill cuts out automatically when top reed engages.",
        "5. SLIDE THE HITCH PIN through wall + sled couplings.",
        "6. Plug in planer, do your planing work.",
        "7. When done: unplug planer, REMOVE hitch pin.",
        "8. Set drill direction to RETRACT (CCW).",
        "9. Engage relay - drill spins backward, jack lowers.",
        "10. Drill cuts out automatically at bottom reed.",
        "11. Drop a 30 x 30 cover panel over the cavity opening.",
    ]
    for s in seq:
        out.append(text(MARGIN + 0.1, cy, s, size=0.12, fill=COL_TEXT,
                         family=FONT_BODY))
        cy += 0.22

    cy += 0.30
    out.append(line(MARGIN, cy, PAGE_W - MARGIN, cy, COL_RULE,
                     stroke_w=0.015))
    cy += 0.30
    out.append(text(MARGIN, cy, "MAINTENANCE",
                    size=0.14, fill=COL_TEXT, bold=True, family=FONT_TITLE))
    cy += 0.26
    out.append(text(MARGIN, cy,
                    "After first 10 cycles: re-tighten all lag bolts (initial settling).",
                    size=0.12, fill=COL_TEXT, family=FONT_BODY))
    cy += 0.20
    out.append(text(MARGIN, cy,
                    "Annually: lube jack screw with white lithium grease.",
                    size=0.12, fill=COL_TEXT, family=FONT_BODY))
    cy += 0.20
    out.append(text(MARGIN, cy,
                    "If drill bogs or stalls during lift: increase clutch ONE step.",
                    size=0.12, fill=COL_TEXT, family=FONT_BODY))
    cy += 0.20
    out.append(text(MARGIN, cy,
                    "Replace drill brushes after ~1 year of regular use.",
                    size=0.12, fill=COL_TEXT, family=FONT_BODY))
    return out


# ---------------------------------------------------------------------------
# Page dispatch
# ---------------------------------------------------------------------------

def render_page(i, step, built_names, total_pages):
    kind = step["kind"]
    out = []
    if kind == "cover":
        out.extend(render_cover(i, total_pages))
    elif kind == "materials":
        out.extend(render_materials(i, total_pages))
    elif kind == "tools_check":
        out.extend(render_tools_check(i, total_pages))
    elif kind == "drill_bracket_detail":
        out.extend(render_drill_bracket_detail(i, total_pages))
    elif kind == "wiring_schematic":
        out.extend(render_wiring_schematic(i, total_pages))
    elif kind == "safety_check":
        out.extend(render_safety_check(i, total_pages))
    elif kind == "assembly":
        out.extend(page_chrome(i, step["title"], total_pages=total_pages))
        new_names = step.get("patterns", [])
        fast_step = step.get("fastener_step")
        out.extend(render_cavity_plan(i, built_names, new_names, fast_step))
        out.extend(render_cavity_iso(i, built_names, new_names))
        out.extend(render_instructions(
            i, step["instructions"],
            tools=step.get("tools"),
            time_est=step.get("time", ""),
            fastener_legend=bool(fast_step)))
    return out


def write_html_wrapper(html_path, total_pages):
    pages_html = []
    for i in range(total_pages):
        pages_html.append(
            f'<div class="page"><object data="planer_lift_buildguide_page_{i+1:02d}.svg" '
            f'type="image/svg+xml" width="100%" height="100%"></object></div>')
    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Planer Lift Build Guide</title>
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
    total_pages = len(STEPS)
    total_h = PAGE_H * total_pages

    # Build single tall SVG
    big = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{PAGE_W}in" height="{total_h}in" '
        f'viewBox="0 0 {PAGE_W} {total_h}">',
        '<defs><style type="text/css">'
        '@import url("https://fonts.googleapis.com/css2?'
        'family=Abel&amp;family=Barlow:wght@400;600;700&amp;display=swap");'
        '</style></defs>',
    ]
    built_names: set[str] = set()
    for i, step in enumerate(STEPS):
        big.extend(render_page(i, step, built_names, total_pages))
        if step["kind"] == "assembly":
            for pname in step.get("patterns", []):
                built_names.add(pname)
    big.append("</svg>")
    (OUT_DIR / "planer_lift_buildguide.svg").write_text("\n".join(big))
    print(f"Wrote planer_lift_buildguide.svg  ({total_pages} pages stacked)")

    # Per-page SVGs
    built_names = set()
    for i, step in enumerate(STEPS):
        page_svg = render_page(i, step, built_names, total_pages)
        if step["kind"] == "assembly":
            for pname in step.get("patterns", []):
                built_names.add(pname)
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
        (OUT_DIR / f"planer_lift_buildguide_page_{i+1:02d}.svg").write_text(
            "\n".join(single))

    write_html_wrapper(OUT_DIR / "planer_lift_buildguide.html", total_pages)
    print(f"Wrote planer_lift_buildguide.html")
    print(f"  {total_pages} pages, open in browser, Print -> Save as PDF.")


if __name__ == "__main__":
    main()
