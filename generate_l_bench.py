"""
L-Bench detailed CAD model for SketchUp.

Stick-frame construction with every 2x4 and panel modeled as a separate
named part so SketchUp can produce a cut list. Includes the planer
vertical lift mechanism, miter saw recess, router table cutout, and
table saw drop-in cavity.

Outputs (written next to this script):
  - l_bench.dae          Collada model. Drag into SketchUp.
  - l_bench.svg          Top-down plan.
  - l_bench_cutlist.csv  Aggregated cut list (parts grouped by type).
  - l_bench_objects.csv  Flat list of every modeled object.

Coordinate system matches the parent shop model:
  - Origin (0,0,0) = back-left corner of the L-bench footprint, floor.
  - X = along the 12 ft back-wall leg, 0..144 in
  - Y = depth from back wall, 0..36 in for top leg, 0..120 in overall
  - Z = height, 0..37 in nominal bench top
  - up axis = Z, units = inches

Construction summary:
  - Frame: 2x4 SPF studs (1.5 x 3.5 actual). 28.5 in tall studs.
  - Top: 2 layers of 3/4 in plywood = 1.5 in total. Glued + screwed.
  - Toe kick: 4 in tall, 3 in recessed from front face. 3/4 in ply.
  - End panels: 3/4 in ply on visible ends. Back panel skipped (bench
    sits against the back wall).
  - Husky chests sit under the top leg, free-standing, slide-in.
  - Planer lift: 4x heavy-duty 24 in drawer slides + 4x gas struts
    (one beside each slide for balanced near-neutral lift force) + a
    1/2 in steel pin lock at the top position.
  - Table saw: drops into a 32 x 32 cavity in the lower left leg, deck
    flush at 37 in. Saw bolts to a sled inside the cavity.
"""

from __future__ import annotations

import csv
import math
import os
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass, field

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Material:
    name: str
    rgb: tuple[float, float, float]
    alpha: float = 1.0

    @property
    def hex(self) -> str:
        r, g, b = self.rgb
        return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))


MATERIALS: dict[str, Material] = {
    "stud":         Material("stud",         (0.82, 0.68, 0.45)),  # SPF tan
    "rail":         Material("rail",         (0.78, 0.62, 0.40)),  # slightly darker
    "stretcher":    Material("stretcher",    (0.74, 0.58, 0.36)),
    "blocking":     Material("blocking",     (0.70, 0.55, 0.32)),
    "ply_top":      Material("ply_top",      (0.88, 0.74, 0.50)),  # bench top
    "ply_panel":    Material("ply_panel",    (0.80, 0.66, 0.42)),  # side / toe kick
    "ply_recess":   Material("ply_recess",   (0.92, 0.78, 0.55)),  # miter recess bottom
    "ply_router":   Material("ply_router",   (0.55, 0.42, 0.25)),  # router cabinet
    "router_insert": Material("router_insert", (0.55, 0.55, 0.58)),
    "saw_sled":     Material("saw_sled",     (0.85, 0.70, 0.45)),
    "saw_body":     Material("saw_body",     (0.95, 0.78, 0.05)),  # DeWalt yellow
    "planer_sled":  Material("planer_sled",  (0.85, 0.70, 0.45)),
    "planer_body":  Material("planer_body",  (0.95, 0.78, 0.05)),
    "drawer_slide": Material("drawer_slide", (0.55, 0.55, 0.58)),
    "gas_strut":    Material("gas_strut",    (0.30, 0.30, 0.32)),
    "lock_pin":     Material("lock_pin",     (0.85, 0.30, 0.20)),
    "lock_recv":    Material("lock_recv",    (0.45, 0.45, 0.50)),
    "husky":        Material("husky",        (0.10, 0.10, 0.12)),
    "ghost":        Material("ghost",        (0.30, 0.55, 0.95), 0.18),
    "ghost_cavity": Material("ghost_cavity", (0.95, 0.30, 0.30), 0.12),
    "label":        Material("label",        (0.05, 0.05, 0.05)),
}


# ---------------------------------------------------------------------------
# Object model
# ---------------------------------------------------------------------------

@dataclass
class Box:
    name: str
    x: float
    y: float
    z: float
    w: float
    d: float
    h: float
    material: str
    note: str = ""
    category: str = "object"
    cutlist_part: str = ""   # "Stud, top leg corner" - groups identical parts
    lumber: str = ""         # "2x4 SPF", "3/4 ply", etc.


@dataclass
class Cylinder:
    name: str
    cx: float
    cy: float
    base_z: float
    radius: float
    height: float
    material: str
    axis: str = "z"
    note: str = ""
    category: str = "object"
    cutlist_part: str = ""
    lumber: str = ""


@dataclass
class Scene:
    boxes: list[Box] = field(default_factory=list)
    cylinders: list[Cylinder] = field(default_factory=list)

    def box(self, *args, **kwargs) -> Box:
        b = Box(*args, **kwargs)
        self.boxes.append(b)
        return b

    def cyl(self, *args, **kwargs) -> Cylinder:
        c = Cylinder(*args, **kwargs)
        self.cylinders.append(c)
        return c


# ---------------------------------------------------------------------------
# Lumber / construction constants
# ---------------------------------------------------------------------------

LUM_25 = 1.5    # 2x stock thickness (1.5" actual)
LUM_4 = 3.5     # 2x4 width (3.5" actual)
PLY_34 = 0.75   # 3/4 in plywood
PLY_TOP = 1.5   # doubled 3/4 in top

BENCH_H = 37.0
TOE_H = 4.0
TOE_RECESS = 3.0
RAIL_T = LUM_25
STUD_H = BENCH_H - TOE_H - 2 * RAIL_T - PLY_TOP    # 28.5"

# L-bench overall footprint
TOP_LEG_X0, TOP_LEG_Y0 = 0.0, 0.0
TOP_LEG_W, TOP_LEG_D = 144.0, 36.0   # 12 ft x 3 ft

LEFT_LEG_X0, LEFT_LEG_Y0 = 0.0, 36.0
LEFT_LEG_W, LEFT_LEG_D = 36.0, 84.0  # 3 ft x 7 ft (corner is part of top leg)

# Cavity geometry (in shop coordinates)
MITER_X0, MITER_W = 50.0, 36.0
MITER_Y0, MITER_D = 2.0,  30.0
MITER_RECESS_DROP = 4.0          # recess depth below bench top

ROUTER_X0, ROUTER_W = 108.0, 24.0
ROUTER_Y0, ROUTER_D = 4.0,  32.0
ROUTER_INSERT_W, ROUTER_INSERT_D = 11.75, 9.25   # standard router insert

PLANER_X0, PLANER_W = 3.0, 30.0
PLANER_Y0, PLANER_D = 42.0, 30.0

SAW_X0, SAW_W = 2.0, 32.0
SAW_Y0, SAW_D = 84.0, 32.0
SAW_DECK_DROP = 13.0    # DWE7491 saw body height below deck (approx)


# ---------------------------------------------------------------------------
# Helpers for adding common parts
# ---------------------------------------------------------------------------

def add_stud(s: Scene, name: str, x: float, y: float, *,
             face: str, cutlist_part: str = "Stud") -> Box:
    """Vertical 2x4 stud with face orientation specified.

    face = "front_or_back"  -> 3.5" along X, 1.5" along Y
    face = "side"           -> 1.5" along X, 3.5" along Y
    """
    if face == "front_or_back":
        w, d = LUM_4, LUM_25
    elif face == "side":
        w, d = LUM_25, LUM_4
    else:
        raise ValueError(face)
    return s.box(name, x, y, TOE_H + RAIL_T, w, d, STUD_H,
                 "stud", category="frame",
                 cutlist_part=cutlist_part, lumber="2x4 SPF",
                 note=f"Vertical 2x4, {STUD_H:.1f}in long")


def add_horiz_2x4(s: Scene, name: str, x: float, y: float, z: float,
                  length: float, axis: str, *,
                  cutlist_part: str, material: str = "rail") -> Box:
    """Horizontal 2x4 rail / stretcher / blocking.

    axis="x" -> length along X, 3.5" along Y, 1.5" tall
    axis="y" -> length along Y, 3.5" along X, 1.5" tall
    """
    if axis == "x":
        w, d, h = length, LUM_4, LUM_25
    elif axis == "y":
        w, d, h = LUM_4, length, LUM_25
    else:
        raise ValueError(axis)
    return s.box(name, x, y, z, w, d, h, material, category="frame",
                 cutlist_part=cutlist_part, lumber="2x4 SPF",
                 note=f"Horizontal 2x4, {length:.1f}in long")


def add_panel(s: Scene, name: str, x: float, y: float, z: float,
              w: float, d: float, h: float, *,
              cutlist_part: str, material: str = "ply_panel") -> Box:
    return s.box(name, x, y, z, w, d, h, material, category="panel",
                 cutlist_part=cutlist_part, lumber="3/4 in plywood",
                 note=f"Panel {w:.1f} x {d:.1f} x {h:.2f}")


# ---------------------------------------------------------------------------
# Build the scene
# ---------------------------------------------------------------------------

def build_scene() -> Scene:
    s = Scene()

    # =========================================================================
    # TOP LEG FRAME (12 ft along back wall x 3 ft deep)
    # =========================================================================
    # Front face is at Y=36 (toward room). Back face is at Y=0 (against wall).
    # Studs distributed along X at cavity boundaries with mid-span studs in
    # large open bays.

    # Stud X-positions along the front face (face="front_or_back" -> 3.5" wide
    # along X). The list is the LEFT EDGE of each stud's 3.5" footprint, so
    # adjacent studs sit edge-to-edge against cavity boundaries.
    top_front_stud_x = [
        0.0,                              # left end
        24.0,                             # mid-span left bay
        MITER_X0 - LUM_4,                 # left of miter recess
        MITER_X0 + MITER_W,               # right of miter recess
        ROUTER_X0 - LUM_4,                # left of router cutout
        ROUTER_X0 + ROUTER_W,             # right of router cutout
        TOP_LEG_W - LUM_4,                # right end
    ]

    # Front studs at Y=36-1.5 (1.5" deep, flush to front face at Y=36)
    for i, sx in enumerate(top_front_stud_x):
        add_stud(s, f"TopLeg_FrontStud_{i}", sx, TOP_LEG_D - LUM_25,
                 face="front_or_back",
                 cutlist_part="Stud, frame vertical (28.5in)")

    # Back studs at Y=0 (3.5" along X, 1.5" deep, flush to back face)
    for i, sx in enumerate(top_front_stud_x):
        add_stud(s, f"TopLeg_BackStud_{i}", sx, 0.0,
                 face="front_or_back",
                 cutlist_part="Stud, frame vertical (28.5in)")

    # Top + bottom rails along the front face (one continuous run on each).
    # Rail height: 1.5" thick, 3.5" tall, but here laid FLAT (3.5" wide along Y).
    # For simplicity model rails as: along X length, 3.5" along Y, 1.5" tall.
    add_horiz_2x4(s, "TopLeg_FrontTopRail", 0, TOP_LEG_D - LUM_4,
                  BENCH_H - PLY_TOP - RAIL_T,
                  TOP_LEG_W, axis="x",
                  cutlist_part="Top rail, top leg front (144in)")
    add_horiz_2x4(s, "TopLeg_FrontBottomRail", 0, TOP_LEG_D - LUM_4,
                  TOE_H,
                  TOP_LEG_W, axis="x",
                  cutlist_part="Bottom rail, top leg front (144in)")
    add_horiz_2x4(s, "TopLeg_BackTopRail", 0, 0,
                  BENCH_H - PLY_TOP - RAIL_T,
                  TOP_LEG_W, axis="x",
                  cutlist_part="Top rail, top leg back (144in)")
    add_horiz_2x4(s, "TopLeg_BackBottomRail", 0, 0,
                  TOE_H,
                  TOP_LEG_W, axis="x",
                  cutlist_part="Bottom rail, top leg back (144in)")

    # Cross stretchers (front-to-back) at top and bottom, between every pair
    # of front+back studs. Length = TOP_LEG_D - 2*LUM_4 = 36 - 7 = 29 in.
    stretcher_len = TOP_LEG_D - 2 * LUM_4
    for i, sx in enumerate(top_front_stud_x):
        # Center the stretcher on the stud's 3.5" face
        sx_centered = sx + (LUM_4 - LUM_4) / 2  # already 3.5" wide -> use sx
        # Top stretcher at the same Z as the top rails
        add_horiz_2x4(s, f"TopLeg_TopStretcher_{i}",
                      sx_centered, LUM_4,
                      BENCH_H - PLY_TOP - RAIL_T,
                      stretcher_len, axis="y",
                      cutlist_part="Cross stretcher, top leg (29in)",
                      material="stretcher")
        add_horiz_2x4(s, f"TopLeg_BottomStretcher_{i}",
                      sx_centered, LUM_4,
                      TOE_H,
                      stretcher_len, axis="y",
                      cutlist_part="Cross stretcher, top leg (29in)",
                      material="stretcher")

    # Miter recess support frame: 2x4 blocking around the recess opening at
    # z = BENCH_H - MITER_RECESS_DROP - LUM_25 (so recess panel sits on top of it).
    miter_block_z = BENCH_H - MITER_RECESS_DROP - LUM_25
    # Front blocking
    add_horiz_2x4(s, "Miter_Recess_BlockingFront",
                  MITER_X0, MITER_Y0 + MITER_D - LUM_4, miter_block_z,
                  MITER_W, axis="x",
                  cutlist_part="Blocking, miter recess (36in)",
                  material="blocking")
    # Back blocking
    add_horiz_2x4(s, "Miter_Recess_BlockingBack",
                  MITER_X0, MITER_Y0, miter_block_z,
                  MITER_W, axis="x",
                  cutlist_part="Blocking, miter recess (36in)",
                  material="blocking")
    # Side blocking
    add_horiz_2x4(s, "Miter_Recess_BlockingLeft",
                  MITER_X0, MITER_Y0 + LUM_4, miter_block_z,
                  MITER_D - 2 * LUM_4, axis="y",
                  cutlist_part="Blocking, miter recess sides (22in)",
                  material="blocking")
    add_horiz_2x4(s, "Miter_Recess_BlockingRight",
                  MITER_X0 + MITER_W - LUM_4, MITER_Y0 + LUM_4, miter_block_z,
                  MITER_D - 2 * LUM_4, axis="y",
                  cutlist_part="Blocking, miter recess sides (22in)",
                  material="blocking")

    # Router cabinet: a 3-sided box inside the bench under the router cutout.
    # Sides + back of router enclosure.
    add_panel(s, "Router_Cabinet_Left",
              ROUTER_X0, ROUTER_Y0, TOE_H,
              PLY_34, ROUTER_D, BENCH_H - TOE_H - PLY_TOP,
              cutlist_part="Router cabinet side panel",
              material="ply_router")
    add_panel(s, "Router_Cabinet_Right",
              ROUTER_X0 + ROUTER_W - PLY_34, ROUTER_Y0, TOE_H,
              PLY_34, ROUTER_D, BENCH_H - TOE_H - PLY_TOP,
              cutlist_part="Router cabinet side panel",
              material="ply_router")
    add_panel(s, "Router_Cabinet_Back",
              ROUTER_X0, ROUTER_Y0, TOE_H,
              ROUTER_W, PLY_34, BENCH_H - TOE_H - PLY_TOP,
              cutlist_part="Router cabinet back panel",
              material="ply_router")
    add_panel(s, "Router_Cabinet_Floor",
              ROUTER_X0, ROUTER_Y0, TOE_H,
              ROUTER_W, ROUTER_D, PLY_34,
              cutlist_part="Router cabinet floor panel",
              material="ply_router")

    # =========================================================================
    # LEFT LEG FRAME (3 ft x 7 ft, perpendicular to top leg)
    # =========================================================================
    # Front face is at X=36 (toward room). Back face is at X=0 (left wall).
    # Studs distributed along Y at cavity boundaries.

    left_face_stud_y = [
        PLANER_Y0 - LUM_4,                        # left of planer (38.5)
        PLANER_Y0 + PLANER_D,                     # right of planer (72)
        SAW_Y0 - LUM_4,                           # left of saw (80.5)
        SAW_Y0 + SAW_D,                           # right of saw (116)
    ]
    # Note: the corner stud (y=36) is provided by the TOP LEG's front studs at
    # x=0, which butt against the left leg. The front-end edge (y=120) is
    # framed by the saw-boundary stud at y=116 plus the end panel.
    for i, sy in enumerate(left_face_stud_y):
        # Left-leg studs face into Y direction (3.5" along Y, 1.5" along X)
        add_stud(s, f"LeftLeg_LeftSideStud_{i}", 0.0, sy,
                 face="side",
                 cutlist_part="Stud, frame vertical (28.5in)")
        add_stud(s, f"LeftLeg_RightSideStud_{i}", LEFT_LEG_W - LUM_25, sy,
                 face="side",
                 cutlist_part="Stud, frame vertical (28.5in)")

    # Top + bottom rails along the LEFT and RIGHT (long) faces of the left leg.
    add_horiz_2x4(s, "LeftLeg_LeftTopRail",
                  0, LEFT_LEG_Y0,
                  BENCH_H - PLY_TOP - RAIL_T,
                  LEFT_LEG_D, axis="y",
                  cutlist_part="Top rail, left leg sides (84in)")
    add_horiz_2x4(s, "LeftLeg_RightTopRail",
                  LEFT_LEG_W - LUM_4, LEFT_LEG_Y0,
                  BENCH_H - PLY_TOP - RAIL_T,
                  LEFT_LEG_D, axis="y",
                  cutlist_part="Top rail, left leg sides (84in)")
    add_horiz_2x4(s, "LeftLeg_LeftBottomRail",
                  0, LEFT_LEG_Y0,
                  TOE_H,
                  LEFT_LEG_D, axis="y",
                  cutlist_part="Bottom rail, left leg sides (84in)")
    add_horiz_2x4(s, "LeftLeg_RightBottomRail",
                  LEFT_LEG_W - LUM_4, LEFT_LEG_Y0,
                  TOE_H,
                  LEFT_LEG_D, axis="y",
                  cutlist_part="Bottom rail, left leg sides (84in)")

    # Cross stretchers between left and right side rails of the left leg.
    cross_len = LEFT_LEG_W - 2 * LUM_4   # 36 - 7 = 29 in
    for i, sy in enumerate(left_face_stud_y):
        add_horiz_2x4(s, f"LeftLeg_TopStretcher_{i}",
                      LUM_4, sy, BENCH_H - PLY_TOP - RAIL_T,
                      cross_len, axis="x",
                      cutlist_part="Cross stretcher, left leg (29in)",
                      material="stretcher")
        add_horiz_2x4(s, f"LeftLeg_BottomStretcher_{i}",
                      LUM_4, sy, TOE_H,
                      cross_len, axis="x",
                      cutlist_part="Cross stretcher, left leg (29in)",
                      material="stretcher")

    # =========================================================================
    # BENCH TOP PANELS (1.5 in doubled 3/4 ply, with cutouts)
    # =========================================================================
    # Top consists of multiple panels around cavities so cavities remain open.
    top_z = BENCH_H - PLY_TOP

    # Top leg top: solid up to miter, recessed at miter (drops 4"),
    # solid between miter and router, cutout at router insert, solid after.
    add_panel(s, "TopLeg_Top_Left",
              0, 0, top_z,
              MITER_X0, TOP_LEG_D, PLY_TOP,
              cutlist_part="Top panel, top leg sections",
              material="ply_top")
    # Miter recess panel (sits LOWER, supported by blocking)
    miter_panel_z = BENCH_H - MITER_RECESS_DROP
    add_panel(s, "Miter_Recess_Bottom",
              MITER_X0, MITER_Y0, miter_panel_z,
              MITER_W, MITER_D, PLY_34,
              cutlist_part="Miter recess bottom panel (36 x 30 x 3/4)",
              material="ply_recess")
    # Top edges around the miter recess (front lip + back lip + side lips at full top height)
    # Back lip
    add_panel(s, "TopLeg_Top_MiterBackLip",
              MITER_X0, 0, top_z,
              MITER_W, MITER_Y0, PLY_TOP,
              cutlist_part="Top panel, top leg sections",
              material="ply_top")
    # Front lip (between recess and front edge)
    add_panel(s, "TopLeg_Top_MiterFrontLip",
              MITER_X0, MITER_Y0 + MITER_D, top_z,
              MITER_W, TOP_LEG_D - (MITER_Y0 + MITER_D), PLY_TOP,
              cutlist_part="Top panel, top leg sections",
              material="ply_top")
    # Between miter and router
    add_panel(s, "TopLeg_Top_MidRight",
              MITER_X0 + MITER_W, 0, top_z,
              ROUTER_X0 - (MITER_X0 + MITER_W), TOP_LEG_D, PLY_TOP,
              cutlist_part="Top panel, top leg sections",
              material="ply_top")
    # Over router area, with insert cutout (modeled as panel minus insert hole)
    # Approximated as: 4 panels around the insert hole + the insert plate.
    insert_x0 = ROUTER_X0 + (ROUTER_W - ROUTER_INSERT_W) / 2
    insert_y0 = ROUTER_Y0 + (ROUTER_D - ROUTER_INSERT_D) / 2
    # Back strip
    add_panel(s, "TopLeg_Top_RouterBack",
              ROUTER_X0, 0, top_z,
              ROUTER_W, insert_y0, PLY_TOP,
              cutlist_part="Top panel, router area (4 sub-panels around insert)",
              material="ply_top")
    # Front strip
    add_panel(s, "TopLeg_Top_RouterFront",
              ROUTER_X0, insert_y0 + ROUTER_INSERT_D, top_z,
              ROUTER_W, TOP_LEG_D - (insert_y0 + ROUTER_INSERT_D), PLY_TOP,
              cutlist_part="Top panel, router area (4 sub-panels around insert)",
              material="ply_top")
    # Left strip
    add_panel(s, "TopLeg_Top_RouterLeft",
              ROUTER_X0, insert_y0, top_z,
              insert_x0 - ROUTER_X0, ROUTER_INSERT_D, PLY_TOP,
              cutlist_part="Top panel, router area (4 sub-panels around insert)",
              material="ply_top")
    # Right strip
    add_panel(s, "TopLeg_Top_RouterRight",
              insert_x0 + ROUTER_INSERT_W, insert_y0, top_z,
              ROUTER_X0 + ROUTER_W - (insert_x0 + ROUTER_INSERT_W),
              ROUTER_INSERT_D, PLY_TOP,
              cutlist_part="Top panel, router area (4 sub-panels around insert)",
              material="ply_top")
    # Router insert plate (phenolic / aluminum, 3/8" usually - shown as 1/2")
    s.box("Router_Insert_Plate",
          insert_x0, insert_y0, top_z + PLY_TOP - 0.5,
          ROUTER_INSERT_W, ROUTER_INSERT_D, 0.5,
          "router_insert", category="tool",
          note="Phenolic/aluminum router insert plate (commercial)")
    # Right of router to right end
    add_panel(s, "TopLeg_Top_FarRight",
              ROUTER_X0 + ROUTER_W, 0, top_z,
              TOP_LEG_W - (ROUTER_X0 + ROUTER_W), TOP_LEG_D, PLY_TOP,
              cutlist_part="Top panel, top leg sections",
              material="ply_top")

    # Left leg top: solid except for planer + saw cavities.
    # From corner (Y=36) down to start of planer cavity (Y=42).
    add_panel(s, "LeftLeg_Top_AbovePlaner",
              0, LEFT_LEG_Y0, top_z,
              LEFT_LEG_W, PLANER_Y0 - LEFT_LEG_Y0, PLY_TOP,
              cutlist_part="Top panel, left leg sections",
              material="ply_top")
    # Sides of the planer cavity (between cavity and bench edge along X)
    add_panel(s, "LeftLeg_Top_PlanerLeftStrip",
              0, PLANER_Y0, top_z,
              PLANER_X0, PLANER_D, PLY_TOP,
              cutlist_part="Top panel, planer cavity strips",
              material="ply_top")
    add_panel(s, "LeftLeg_Top_PlanerRightStrip",
              PLANER_X0 + PLANER_W, PLANER_Y0, top_z,
              LEFT_LEG_W - (PLANER_X0 + PLANER_W), PLANER_D, PLY_TOP,
              cutlist_part="Top panel, planer cavity strips",
              material="ply_top")
    # Between planer and saw cavities
    add_panel(s, "LeftLeg_Top_BetweenCavities",
              0, PLANER_Y0 + PLANER_D, top_z,
              LEFT_LEG_W, SAW_Y0 - (PLANER_Y0 + PLANER_D), PLY_TOP,
              cutlist_part="Top panel, left leg sections",
              material="ply_top")
    # Sides of the saw cavity
    add_panel(s, "LeftLeg_Top_SawLeftStrip",
              0, SAW_Y0, top_z,
              SAW_X0, SAW_D, PLY_TOP,
              cutlist_part="Top panel, saw cavity strips",
              material="ply_top")
    add_panel(s, "LeftLeg_Top_SawRightStrip",
              SAW_X0 + SAW_W, SAW_Y0, top_z,
              LEFT_LEG_W - (SAW_X0 + SAW_W), SAW_D, PLY_TOP,
              cutlist_part="Top panel, saw cavity strips",
              material="ply_top")
    # End strip past saw
    add_panel(s, "LeftLeg_Top_End",
              0, SAW_Y0 + SAW_D, top_z,
              LEFT_LEG_W, LEFT_LEG_Y0 + LEFT_LEG_D - (SAW_Y0 + SAW_D),
              PLY_TOP,
              cutlist_part="Top panel, left leg sections",
              material="ply_top")

    # =========================================================================
    # TOE KICK BOARDS (3/4 ply)
    # =========================================================================
    # Top leg front toe kick (recessed 3" from front face)
    add_panel(s, "TopLeg_ToeKick_Front",
              0, TOP_LEG_D - TOE_RECESS - PLY_34, 0,
              TOP_LEG_W, PLY_34, TOE_H,
              cutlist_part="Toe kick board (4in tall)",
              material="ply_panel")
    # Top leg back toe kick (against wall, full back)
    add_panel(s, "TopLeg_ToeKick_Back",
              0, 0, 0,
              TOP_LEG_W, PLY_34, TOE_H,
              cutlist_part="Toe kick board (4in tall)",
              material="ply_panel")
    # Top leg right end toe kick
    add_panel(s, "TopLeg_ToeKick_RightEnd",
              TOP_LEG_W - PLY_34, 0, 0,
              PLY_34, TOP_LEG_D, TOE_H,
              cutlist_part="Toe kick end cap (4 x 36)",
              material="ply_panel")
    # Left leg front toe kick (right side of leg, facing into room)
    add_panel(s, "LeftLeg_ToeKick_Right",
              LEFT_LEG_W - TOE_RECESS - PLY_34, LEFT_LEG_Y0, 0,
              PLY_34, LEFT_LEG_D, TOE_H,
              cutlist_part="Toe kick board (4in tall)",
              material="ply_panel")
    # Left leg back toe kick (left side, against wall or curtain edge)
    add_panel(s, "LeftLeg_ToeKick_Left",
              0, LEFT_LEG_Y0, 0,
              PLY_34, LEFT_LEG_D, TOE_H,
              cutlist_part="Toe kick board (4in tall)",
              material="ply_panel")
    # Left leg front-end toe kick
    add_panel(s, "LeftLeg_ToeKick_FrontEnd",
              0, LEFT_LEG_Y0 + LEFT_LEG_D - PLY_34, 0,
              LEFT_LEG_W, PLY_34, TOE_H,
              cutlist_part="Toe kick end cap (4 x 36)",
              material="ply_panel")

    # =========================================================================
    # END / BACK PANELS (3/4 ply skin on visible faces)
    # =========================================================================
    # Right end of top leg (visible end past existing bench area)
    add_panel(s, "TopLeg_EndPanel_Right",
              TOP_LEG_W - PLY_34, 0, TOE_H,
              PLY_34, TOP_LEG_D, BENCH_H - TOE_H,
              cutlist_part="End panel (33 x 36 x 3/4)",
              material="ply_panel")
    # Front end of left leg (visible front face past saw cavity)
    add_panel(s, "LeftLeg_EndPanel_Front",
              0, LEFT_LEG_Y0 + LEFT_LEG_D - PLY_34, TOE_H,
              LEFT_LEG_W, PLY_34, BENCH_H - TOE_H,
              cutlist_part="End panel (33 x 36 x 3/4)",
              material="ply_panel")

    # =========================================================================
    # PLANER VERTICAL LIFT MECHANISM
    # =========================================================================
    # Cavity inside the left leg at PLANER_X0..+W, PLANER_Y0..+D, full bench
    # height. Hardware:
    #   - 4 heavy-duty drawer slides, mounted vertically on left + right cavity
    #     walls (2 per wall, at front and back corners of the cavity).
    #   - 1 sled (3/4 ply) inside cavity, planer bolts to the sled.
    #   - 4 gas struts, one beside each drawer slide for balanced lift.
    #   - 1 steel pin lock at the top position (pin + receiver).

    SLIDE_TRAVEL = 24.0   # heavy-duty 24in vertical drawer slide
    SLIDE_W = 1.0         # slide profile width
    SLIDE_T = 1.5         # slide projection from wall

    # Cavity inner walls
    cav_left_x = PLANER_X0
    cav_right_x = PLANER_X0 + PLANER_W
    cav_back_y = PLANER_Y0
    cav_front_y = PLANER_Y0 + PLANER_D

    # Slides on the LEFT cavity wall (mounted to a ledger on the wall)
    s.box("Planer_Slide_LeftBack",
          cav_left_x, cav_back_y + 1.0, TOE_H,
          SLIDE_T, SLIDE_W, SLIDE_TRAVEL,
          "drawer_slide", category="hardware",
          note="HD drawer slide #1 (left-back) - 24in travel, 220lb rated")
    s.box("Planer_Slide_LeftFront",
          cav_left_x, cav_front_y - 1.0 - SLIDE_W, TOE_H,
          SLIDE_T, SLIDE_W, SLIDE_TRAVEL,
          "drawer_slide", category="hardware",
          note="HD drawer slide #2 (left-front) - 24in travel, 220lb rated")
    s.box("Planer_Slide_RightBack",
          cav_right_x - SLIDE_T, cav_back_y + 1.0, TOE_H,
          SLIDE_T, SLIDE_W, SLIDE_TRAVEL,
          "drawer_slide", category="hardware",
          note="HD drawer slide #3 (right-back) - 24in travel, 220lb rated")
    s.box("Planer_Slide_RightFront",
          cav_right_x - SLIDE_T, cav_front_y - 1.0 - SLIDE_W, TOE_H,
          SLIDE_T, SLIDE_W, SLIDE_TRAVEL,
          "drawer_slide", category="hardware",
          note="HD drawer slide #4 (right-front) - 24in travel, 220lb rated")

    # Gas struts: 4 total, one beside each slide, mounted at slight angle for
    # balanced near-neutral lift force across travel.
    # Strut: bottom mount on cavity floor near corner, top mount on sled
    # underside near opposite corner. Modeled as a thin cylinder.
    STRUT_R = 0.5  # rod radius approximation
    # Each strut runs from a low corner (cavity floor) to a high corner (sled)
    # diagonally to provide an angle that yields a smooth lift profile.
    strut_corners = [
        # name, lower (x,y,z), upper (x,y,z)
        ("Planer_GasStrut_LeftBack",
         (cav_left_x + 2.5, cav_back_y + 2.5, TOE_H),
         (cav_left_x + 4.5, cav_back_y + 4.5, TOE_H + SLIDE_TRAVEL)),
        ("Planer_GasStrut_LeftFront",
         (cav_left_x + 2.5, cav_front_y - 2.5, TOE_H),
         (cav_left_x + 4.5, cav_front_y - 4.5, TOE_H + SLIDE_TRAVEL)),
        ("Planer_GasStrut_RightBack",
         (cav_right_x - 2.5, cav_back_y + 2.5, TOE_H),
         (cav_right_x - 4.5, cav_back_y + 4.5, TOE_H + SLIDE_TRAVEL)),
        ("Planer_GasStrut_RightFront",
         (cav_right_x - 2.5, cav_front_y - 2.5, TOE_H),
         (cav_right_x - 4.5, cav_front_y - 4.5, TOE_H + SLIDE_TRAVEL)),
    ]
    for name, lo, hi in strut_corners:
        # Approximate the strut as an axis-aligned thin box from lower to upper.
        x_lo, y_lo, z_lo = lo
        x_hi, y_hi, z_hi = hi
        s.box(name,
              min(x_lo, x_hi) - STRUT_R, min(y_lo, y_hi) - STRUT_R, z_lo,
              abs(x_hi - x_lo) + 2 * STRUT_R,
              abs(y_hi - y_lo) + 2 * STRUT_R,
              z_hi - z_lo,
              "gas_strut", category="hardware",
              note=("Gas strut, ~50lb force, mounted at angle. 4 total give "
                    "near-neutral buoyancy across travel"))

    # Planer sled (3/4 ply) - planer bolts to top of sled
    SLED_INSET = 1.0
    sled_w = PLANER_W - 2 * SLED_INSET
    sled_d = PLANER_D - 2 * SLED_INSET
    add_panel(s, "Planer_Sled",
              PLANER_X0 + SLED_INSET, PLANER_Y0 + SLED_INSET,
              TOE_H + SLIDE_TRAVEL,    # shown at TOP of travel (working position)
              sled_w, sled_d, PLY_34,
              cutlist_part=f"Planer sled ({sled_w:.0f} x {sled_d:.0f} x 3/4)",
              material="planer_sled")

    # Pin lock at top position
    # Receiver bracket on cavity right wall, near top
    s.box("Planer_LockReceiver",
          cav_right_x - 1.5, cav_back_y + PLANER_D / 2 - 1.0,
          TOE_H + SLIDE_TRAVEL - 1.0,
          1.5, 2.0, 1.5,
          "lock_recv", category="hardware",
          note="Lock receiver bracket. Pin engages here at top position.")
    # 1/2 in steel locking pin (cylinder along X)
    s.cyl("Planer_LockPin",
          cav_right_x - 3.0, cav_back_y + PLANER_D / 2,
          TOE_H + SLIDE_TRAVEL - 0.25,
          0.25, 6.0,
          "lock_pin", axis="x",
          note="1/2in steel locking pin. POSITIVE engagement - do NOT rely on struts.",
          category="hardware")

    # Planer body (in working / raised position, sitting on sled, deck flush at 37)
    PLANER_BASE_H = 4.0    # planer chassis below the bed
    PLANER_BODY_H = 17.0   # total planer height
    s.box("Planer_Body_Working",
          PLANER_X0 + 2.0, PLANER_Y0 + 4.0,
          BENCH_H - PLANER_BASE_H,
          PLANER_W - 4.0, PLANER_D - 8.0, PLANER_BODY_H,
          "planer_body", category="tool",
          note="DeWalt planer in working position - bed flush at 37in")

    # Ghost outline at lowered/stored position
    s.box("Planer_Body_Stored_Ghost",
          PLANER_X0 + 2.0, PLANER_Y0 + 4.0,
          TOE_H + 0.5,
          PLANER_W - 4.0, PLANER_D - 8.0, PLANER_BODY_H,
          "ghost_cavity", category="ghost",
          note="Planer in stored/lowered position (ghost). Cover with insert panel.")

    # =========================================================================
    # TABLE SAW DROP-IN CAVITY (saw lives in cavity, deck flush at 37)
    # =========================================================================
    # Saw bolts to a sled inside the cavity. Sled height set so the saw deck
    # comes out flush at z=37.
    saw_sled_z = BENCH_H - SAW_DECK_DROP - PLY_34
    add_panel(s, "Saw_Sled",
              SAW_X0 + 1.0, SAW_Y0 + 1.0, saw_sled_z,
              SAW_W - 2.0, SAW_D - 2.0, PLY_34,
              cutlist_part="Saw sled (30 x 30 x 3/4)",
              material="saw_sled")
    # Sled support cleats: 2x4 ledgers on the cavity walls that the sled
    # rests on. 4 cleats, one per wall.
    cleat_z = saw_sled_z - LUM_25
    add_horiz_2x4(s, "Saw_SledCleat_Back",
                  SAW_X0, SAW_Y0, cleat_z,
                  SAW_W, axis="x",
                  cutlist_part="Saw sled cleat (32in)",
                  material="blocking")
    add_horiz_2x4(s, "Saw_SledCleat_Front",
                  SAW_X0, SAW_Y0 + SAW_D - LUM_4, cleat_z,
                  SAW_W, axis="x",
                  cutlist_part="Saw sled cleat (32in)",
                  material="blocking")
    add_horiz_2x4(s, "Saw_SledCleat_Left",
                  SAW_X0, SAW_Y0 + LUM_4, cleat_z,
                  SAW_D - 2 * LUM_4, axis="y",
                  cutlist_part="Saw sled cleat (25in)",
                  material="blocking")
    add_horiz_2x4(s, "Saw_SledCleat_Right",
                  SAW_X0 + SAW_W - LUM_4, SAW_Y0 + LUM_4, cleat_z,
                  SAW_D - 2 * LUM_4, axis="y",
                  cutlist_part="Saw sled cleat (25in)",
                  material="blocking")
    # Saw body (deck flush at 37)
    s.box("Saw_Body",
          SAW_X0 + 1.5, SAW_Y0 + 1.5, BENCH_H - SAW_DECK_DROP,
          SAW_W - 3.0, SAW_D - 3.0, SAW_DECK_DROP,
          "saw_body", category="tool",
          note="DeWalt DWE7491 jobsite saw, stand removed, deck flush at 37in")
    # Saw deck (flush with bench top)
    s.box("Saw_Deck",
          SAW_X0 + 1.5, SAW_Y0 + 1.5, BENCH_H - 0.25,
          SAW_W - 3.0, SAW_D - 3.0, 0.25,
          "saw_body", category="tool",
          note="Saw cast deck - flush with bench top")

    # =========================================================================
    # HUSKY CHESTS (free-standing, sit under top leg, slide-in)
    # =========================================================================
    # Tall Husky between left end of bench and miter recess (50in clear bay).
    HUSKY_TALL_W = 40.0
    HUSKY_TALL_D = 18.0
    HUSKY_TALL_H = 36.0
    HUSKY_SHORT_H = 20.0
    HUSKY_SHORT_PLINTH = 16.0  # sits on a plinth so its top reaches under the bench top
    # Tall Husky in left bay of top leg (clear width 50, fit 40W in middle)
    husky_tall_x = 5.0
    husky_tall_y = TOP_LEG_D - HUSKY_TALL_D - 1.0   # slide-in from front
    s.box("Tall_Husky_40x18x36",
          husky_tall_x, husky_tall_y, 0,
          HUSKY_TALL_W, HUSKY_TALL_D, HUSKY_TALL_H,
          "husky", category="cabinet",
          note="Tall Husky chest, slides in from front (no wheels)")
    # Short Husky between miter and router (only 22in clear - short Husky 40in
    # too wide). Place it ELSE: under far-right past router cutout.
    # Far-right bay is x=132..144 = 12in wide (too narrow). Best home for the
    # short Husky is under the existing 3x8 bench, OR rotated 90 degrees in
    # the gap. For now, place inside the left leg's between-cavities bay
    # (x=0..36, y=72..84 = 12in deep, too shallow).
    # Compromise: place short Husky on its 16in plinth at the right end of the
    # top leg, tucked into the 12in slot - which doesn't fit either.
    # Better: locate at the CORNER of the L (under the 36 x 36 corner area),
    # where there is clear room (no cavity). Slide in from the front of the
    # top leg.
    husky_short_x = LEFT_LEG_W + 4.0   # past the left leg into the top leg corner
    husky_short_y = TOP_LEG_D - HUSKY_TALL_D - 1.0
    # Plinth for short Husky
    s.box("Short_Husky_Plinth",
          husky_short_x, husky_short_y, 0,
          HUSKY_TALL_W, HUSKY_TALL_D, HUSKY_SHORT_PLINTH,
          "husky", category="cabinet",
          note="16in plinth for short Husky chest")
    s.box("Short_Husky_40x18x20",
          husky_short_x, husky_short_y, HUSKY_SHORT_PLINTH,
          HUSKY_TALL_W, HUSKY_TALL_D, HUSKY_SHORT_H,
          "husky", category="cabinet",
          note="Short Husky chest, slides in from front (sits on plinth)")

    # =========================================================================
    # GHOST: working zones above the bench
    # =========================================================================
    # Miter saw outline (8 in tall) for visualization at the recess
    s.box("Miter_Saw_Body_Ghost",
          MITER_X0 + 3, MITER_Y0 + 3, BENCH_H - MITER_RECESS_DROP,
          MITER_W - 6, MITER_D - 6, 12,
          "ghost_cavity", category="ghost",
          note="DeWalt 10in miter saw body sitting in recess (ghost)")
    # Router under-bench access ghost
    s.box("Router_Motor_Ghost",
          insert_x0 + 1, insert_y0 + 1, top_z - 8,
          ROUTER_INSERT_W - 2, ROUTER_INSERT_D - 2, 8,
          "ghost_cavity", category="ghost",
          note="Router motor hanging from insert plate (ghost)")

    return s


# ---------------------------------------------------------------------------
# Mesh helpers (box + cylinder tessellation)
# ---------------------------------------------------------------------------

def box_mesh(b: Box):
    x0, y0, z0 = b.x, b.y, b.z
    x1, y1, z1 = x0 + b.w, y0 + b.d, z0 + b.h
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2), (0, 2, 1), (4, 5, 6), (4, 6, 7),
         (0, 1, 5), (0, 5, 4), (2, 3, 7), (2, 7, 6),
         (1, 2, 6), (1, 6, 5), (3, 0, 4), (3, 4, 7)]
    return v, f


def cylinder_mesh(c: Cylinder, segments: int = 16):
    verts, tris = [], []
    bottom_ring, top_ring = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        bottom_ring.append((c.radius * math.cos(a), c.radius * math.sin(a), 0.0))
        top_ring.append((c.radius * math.cos(a), c.radius * math.sin(a), c.height))

    def transform(p):
        x, y, z = p
        if c.axis == "z":
            return (c.cx + x, c.cy + y, c.base_z + z)
        elif c.axis == "x":
            return (c.base_z + z, c.cy + x, c.cx + y)
        elif c.axis == "y":
            return (c.cx + x, c.base_z + z, c.cy + y)
        raise ValueError(c.axis)

    base_idx = len(verts)
    for p in bottom_ring + top_ring:
        verts.append(transform(p))
    bot, top = base_idx, base_idx + segments
    for i in range(segments):
        j = (i + 1) % segments
        tris.append((bot + i, bot + j, top + j))
        tris.append((bot + i, top + j, top + i))
    bc = len(verts); verts.append(transform((0, 0, 0)))
    tc = len(verts); verts.append(transform((0, 0, c.height)))
    for i in range(segments):
        j = (i + 1) % segments
        tris.append((bc, bot + j, bot + i))
        tris.append((tc, top + i, top + j))
    return verts, tris


# ---------------------------------------------------------------------------
# Collada (.dae) writer
# ---------------------------------------------------------------------------

NS = "http://www.collada.org/2005/11/COLLADASchema"


def write_dae(scene: Scene, dae_path: str) -> None:
    ET.register_namespace("", NS)
    root = ET.Element(f"{{{NS}}}COLLADA", attrib={"version": "1.4.1"})
    asset = ET.SubElement(root, f"{{{NS}}}asset")
    contributor = ET.SubElement(asset, f"{{{NS}}}contributor")
    ET.SubElement(contributor, f"{{{NS}}}author").text = "generate_l_bench"
    ET.SubElement(contributor, f"{{{NS}}}authoring_tool").text = "generate_l_bench.py"
    ET.SubElement(asset, f"{{{NS}}}created").text = "2026-05-03T00:00:00"
    ET.SubElement(asset, f"{{{NS}}}modified").text = "2026-05-03T00:00:00"
    unit = ET.SubElement(asset, f"{{{NS}}}unit")
    unit.set("name", "inch"); unit.set("meter", "0.0254")
    ET.SubElement(asset, f"{{{NS}}}up_axis").text = "Z_UP"

    lib_effects = ET.SubElement(root, f"{{{NS}}}library_effects")
    for m in MATERIALS.values():
        eff = ET.SubElement(lib_effects, f"{{{NS}}}effect", id=f"{m.name}-effect")
        prof = ET.SubElement(eff, f"{{{NS}}}profile_COMMON")
        tech = ET.SubElement(prof, f"{{{NS}}}technique", sid="common")
        lam = ET.SubElement(tech, f"{{{NS}}}lambert")
        diff = ET.SubElement(lam, f"{{{NS}}}diffuse")
        color = ET.SubElement(diff, f"{{{NS}}}color")
        r, g, b = m.rgb
        color.text = f"{r:.4f} {g:.4f} {b:.4f} {m.alpha:.4f}"
        if m.alpha < 1.0:
            tr = ET.SubElement(lam, f"{{{NS}}}transparency")
            tf = ET.SubElement(tr, f"{{{NS}}}float"); tf.text = f"{m.alpha:.4f}"
            tp = ET.SubElement(lam, f"{{{NS}}}transparent", opaque="A_ONE")
            tc = ET.SubElement(tp, f"{{{NS}}}color")
            tc.text = f"1 1 1 {m.alpha:.4f}"

    lib_materials = ET.SubElement(root, f"{{{NS}}}library_materials")
    for m in MATERIALS.values():
        mat = ET.SubElement(lib_materials, f"{{{NS}}}material",
                            id=f"{m.name}-material", name=m.name)
        ET.SubElement(mat, f"{{{NS}}}instance_effect", url=f"#{m.name}-effect")

    lib_geoms = ET.SubElement(root, f"{{{NS}}}library_geometries")
    geoms: list[tuple[str, str, str]] = []
    used_ids: set[str] = set()

    def safe(name: str) -> str:
        return "".join(c if c.isalnum() or c in "_-" else "_" for c in name)

    def unique(base: str) -> str:
        gid = base; n = 1
        while gid in used_ids:
            n += 1; gid = f"{base}_{n}"
        used_ids.add(gid); return gid

    def add_geometry(geom_id, name, material, verts, tris):
        geom = ET.SubElement(lib_geoms, f"{{{NS}}}geometry", id=geom_id, name=name)
        mesh = ET.SubElement(geom, f"{{{NS}}}mesh")
        pos_id = f"{geom_id}-positions"
        src = ET.SubElement(mesh, f"{{{NS}}}source", id=pos_id)
        flat = [v for vert in verts for v in vert]
        fa = ET.SubElement(src, f"{{{NS}}}float_array",
                           id=f"{pos_id}-array", count=str(len(flat)))
        fa.text = " ".join(f"{x:.4f}" for x in flat)
        tc = ET.SubElement(src, f"{{{NS}}}technique_common")
        acc = ET.SubElement(tc, f"{{{NS}}}accessor",
                            source=f"#{pos_id}-array",
                            count=str(len(verts)), stride="3")
        for ax in ("X", "Y", "Z"):
            ET.SubElement(acc, f"{{{NS}}}param", name=ax, type="float")
        ve = ET.SubElement(mesh, f"{{{NS}}}vertices", id=f"{geom_id}-vertices")
        ET.SubElement(ve, f"{{{NS}}}input", semantic="POSITION", source=f"#{pos_id}")
        tr = ET.SubElement(mesh, f"{{{NS}}}triangles",
                           count=str(len(tris)), material="mat_symbol")
        ET.SubElement(tr, f"{{{NS}}}input", semantic="VERTEX",
                      source=f"#{geom_id}-vertices", offset="0")
        p = ET.SubElement(tr, f"{{{NS}}}p")
        p.text = " ".join(f"{a} {b} {c}" for (a, b, c) in tris)
        geoms.append((geom_id, material, name))

    for box in scene.boxes:
        v, t = box_mesh(box)
        add_geometry(unique(f"geom_{safe(box.name)}"), box.name, box.material, v, t)
    for cyl in scene.cylinders:
        v, t = cylinder_mesh(cyl)
        add_geometry(unique(f"geom_{safe(cyl.name)}"), cyl.name, cyl.material, v, t)

    lib_scenes = ET.SubElement(root, f"{{{NS}}}library_visual_scenes")
    vs = ET.SubElement(lib_scenes, f"{{{NS}}}visual_scene",
                       id="LBenchScene", name="LBench")
    for gid, mat, name in geoms:
        node = ET.SubElement(vs, f"{{{NS}}}node", id=f"node_{gid}", name=name, type="NODE")
        inst = ET.SubElement(node, f"{{{NS}}}instance_geometry", url=f"#{gid}")
        bm = ET.SubElement(inst, f"{{{NS}}}bind_material")
        tc = ET.SubElement(bm, f"{{{NS}}}technique_common")
        ET.SubElement(tc, f"{{{NS}}}instance_material",
                      symbol="mat_symbol", target=f"#{mat}-material")
    se = ET.SubElement(root, f"{{{NS}}}scene")
    ET.SubElement(se, f"{{{NS}}}instance_visual_scene", url="#LBenchScene")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(dae_path, xml_declaration=True, encoding="utf-8")


# ---------------------------------------------------------------------------
# Wavefront OBJ + MTL writer
# ---------------------------------------------------------------------------

def write_obj_mtl(scene: Scene, obj_path: str, mtl_path: str) -> None:
    """Write geometry as Wavefront OBJ with a sibling MTL.

    OBJ does NOT carry units, so importers default to meters / their own
    scene units. The bench is in inches; in tools like FreeCAD / Blender /
    Tinkercad you need to import-as-inches or scale by 0.0254 to get meters.
    """
    with open(mtl_path, "w") as f:
        for m in MATERIALS.values():
            r, g, b = m.rgb
            f.write(f"newmtl {m.name}\n")
            f.write(f"Ka {r:.3f} {g:.3f} {b:.3f}\n")
            f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
            f.write("Ks 0.05 0.05 0.05\nNs 16\n")
            f.write(f"d {m.alpha:.3f}\nillum 2\n\n")

    with open(obj_path, "w") as f:
        f.write(f"# L-bench geometry. Units: inches.\n")
        f.write(f"# Importing into a tool that assumes meters? Scale by 0.0254.\n")
        f.write(f"mtllib {os.path.basename(mtl_path)}\n")
        vertex_offset = 1
        for box in scene.boxes:
            v, t = box_mesh(box)
            f.write(f"\no {box.name}\nusemtl {box.material}\n")
            for vx, vy, vz in v:
                f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
            for a, b_, c_ in t:
                f.write(f"f {a + vertex_offset} {b_ + vertex_offset} {c_ + vertex_offset}\n")
            vertex_offset += len(v)
        for cyl in scene.cylinders:
            v, t = cylinder_mesh(cyl)
            f.write(f"\no {cyl.name}\nusemtl {cyl.material}\n")
            for vx, vy, vz in v:
                f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
            for a, b_, c_ in t:
                f.write(f"f {a + vertex_offset} {b_ + vertex_offset} {c_ + vertex_offset}\n")
            vertex_offset += len(v)


# ---------------------------------------------------------------------------
# 2D top-down SVG plan
# ---------------------------------------------------------------------------

ROOM_X = 144.0   # full L-bench bounding length
ROOM_Y = 120.0   # full L-bench bounding depth


def write_svg(scene: Scene, svg_path: str) -> None:
    px = 5
    margin = 60
    width = int(ROOM_X * px + 2 * margin)
    height = int(ROOM_Y * px + 2 * margin + 80)

    def sx(x): return margin + x * px
    def sy(y): return margin + y * px

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="9">',
        '<style>'
        '.label{font-size:8px;fill:#222;}'
        '.title{font-size:14px;font-weight:bold;fill:#111;}'
        '.note{font-size:9px;fill:#333;}'
        '</style>',
        '<rect x="0" y="0" width="100%" height="100%" fill="#fafafa"/>',
        f'<text class="title" x="{margin}" y="{margin - 30}">'
        f'L-Bench Stick Frame Plan - top-down - units = inches</text>',
        f'<text class="note" x="{margin}" y="{margin - 14}">'
        f'X = back wall (12ft top leg). Y = depth (3ft top leg, 7ft left leg). '
        f'1 grid = 6in.</text>',
    ]

    # Grid
    for ix in range(0, int(ROOM_X) + 1, 6):
        x = sx(ix)
        parts.append(f'<line x1="{x}" y1="{sy(0)}" x2="{x}" y2="{sy(ROOM_Y)}" '
                     f'stroke="#e8e8e8" stroke-width="0.5"/>')
    for iy in range(0, int(ROOM_Y) + 1, 6):
        y = sy(iy)
        parts.append(f'<line x1="{sx(0)}" y1="{y}" x2="{sx(ROOM_X)}" y2="{y}" '
                     f'stroke="#e8e8e8" stroke-width="0.5"/>')

    # L-bench outline
    parts.append(f'<rect x="{sx(0)}" y="{sy(0)}" width="{TOP_LEG_W * px}" '
                 f'height="{TOP_LEG_D * px}" fill="none" stroke="#888" stroke-width="1.5" stroke-dasharray="4 2"/>')
    parts.append(f'<rect x="{sx(0)}" y="{sy(LEFT_LEG_Y0)}" '
                 f'width="{LEFT_LEG_W * px}" height="{LEFT_LEG_D * px}" '
                 f'fill="none" stroke="#888" stroke-width="1.5" stroke-dasharray="4 2"/>')

    layer_order = ["frame", "panel", "cabinet", "hardware", "tool", "ghost"]
    for cat in layer_order:
        for box in scene.boxes:
            if box.category != cat:
                continue
            mat = MATERIALS[box.material]
            x = sx(box.x); y = sy(box.y)
            w = box.w * px; h = box.d * px
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" '
                         f'height="{h:.2f}" fill="{mat.hex}" '
                         f'fill-opacity="{mat.alpha:.2f}" '
                         f'stroke="#333" stroke-width="0.4"/>')

    # Cavity outlines (red dashed)
    for name, x0, y0, w, d in [
        ("Miter recess", MITER_X0, MITER_Y0, MITER_W, MITER_D),
        ("Router cutout", ROUTER_X0, ROUTER_Y0, ROUTER_W, ROUTER_D),
        ("Planer cavity", PLANER_X0, PLANER_Y0, PLANER_W, PLANER_D),
        ("Saw cavity", SAW_X0, SAW_Y0, SAW_W, SAW_D),
    ]:
        parts.append(f'<rect x="{sx(x0):.2f}" y="{sy(y0):.2f}" '
                     f'width="{w * px:.2f}" height="{d * px:.2f}" '
                     f'fill="none" stroke="#c0392b" stroke-width="1.2" '
                     f'stroke-dasharray="3 2"/>')
        parts.append(f'<text class="label" x="{sx(x0 + w / 2):.2f}" '
                     f'y="{sy(y0 + d / 2):.2f}" text-anchor="middle">'
                     f'{name}</text>')

    # Legend
    legend_y = sy(ROOM_Y) + 24
    items = [
        ("2x4 stud", MATERIALS["stud"].hex),
        ("2x4 rail / stretcher", MATERIALS["rail"].hex),
        ("2x4 blocking / cleat", MATERIALS["blocking"].hex),
        ("3/4 ply top", MATERIALS["ply_top"].hex),
        ("3/4 ply panel", MATERIALS["ply_panel"].hex),
        ("Husky chest (slides in)", MATERIALS["husky"].hex),
        ("Drawer slide", MATERIALS["drawer_slide"].hex),
        ("Gas strut", MATERIALS["gas_strut"].hex),
        ("Lock pin", MATERIALS["lock_pin"].hex),
        ("Cavity outline", "#c0392b"),
    ]
    for i, (text, color) in enumerate(items):
        col = i % 4; row = i // 4
        lx = margin + col * 180; ly = legend_y + row * 18
        parts.append(f'<rect x="{lx}" y="{ly - 9}" width="14" height="10" '
                     f'fill="{color}" stroke="#222" stroke-width="0.4"/>')
        parts.append(f'<text class="label" x="{lx + 18}" y="{ly}">{text}</text>')

    parts.append('</svg>')
    with open(svg_path, "w") as f:
        f.write("\n".join(parts))


# ---------------------------------------------------------------------------
# Cut list CSV (aggregated)
# ---------------------------------------------------------------------------

def write_cutlist(scene: Scene, csv_path: str) -> None:
    """Group identical parts by (lumber, cutlist_part, dims) and report
    quantity. Parts with the same name but different dimensions get separate
    rows so the cut list is actually usable.
    """
    def round_dim(v: float) -> float:
        return round(v, 2)

    groups: OrderedDict[tuple, dict] = OrderedDict()
    for b in scene.boxes:
        if not b.cutlist_part:
            continue
        # Cut-list dimension = the LONGEST dimension is the "length" of the
        # piece; the other two are width and thickness.
        dims = sorted([b.w, b.d, b.h], reverse=True)
        key = (b.lumber, b.cutlist_part,
               round_dim(dims[0]), round_dim(dims[1]), round_dim(dims[2]))
        if key not in groups:
            groups[key] = {
                "lumber": b.lumber,
                "part": b.cutlist_part,
                "qty": 0,
                "length": dims[0],
                "width": dims[1],
                "thickness": dims[2],
                "examples": [],
            }
        g = groups[key]
        g["qty"] += 1
        if len(g["examples"]) < 3:
            g["examples"].append(b.name)

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lumber", "part", "quantity",
                    "length_in", "width_in", "thickness_in",
                    "example_names"])
        for g in groups.values():
            w.writerow([g["lumber"], g["part"], g["qty"],
                        f"{g['length']:.2f}", f"{g['width']:.2f}",
                        f"{g['thickness']:.2f}",
                        "; ".join(g["examples"])])


def write_objects_csv(scene: Scene, csv_path: str) -> None:
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "category", "material", "shape",
                    "x", "y", "z", "w_or_r", "d_or_axis", "h",
                    "cutlist_part", "lumber", "note"])
        for b in scene.boxes:
            w.writerow([b.name, b.category, b.material, "box",
                        b.x, b.y, b.z, b.w, b.d, b.h,
                        b.cutlist_part, b.lumber, b.note])
        for c in scene.cylinders:
            w.writerow([c.name, c.category, c.material, "cylinder",
                        c.cx, c.cy, c.base_z, c.radius, c.axis, c.height,
                        c.cutlist_part, c.lumber, c.note])


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------

def sanity_checks(scene: Scene) -> list[str]:
    warnings_: list[str] = []
    # Detect framing collisions: any two studs/rails overlap in 3D?
    frame_boxes = [b for b in scene.boxes if b.category == "frame"]
    for i, a in enumerate(frame_boxes):
        for b in frame_boxes[i + 1:]:
            if (a.x < b.x + b.w and a.x + a.w > b.x and
                a.y < b.y + b.d and a.y + a.d > b.y and
                a.z < b.z + b.h and a.z + a.h > b.z):
                warnings_.append(f"Frame collision: {a.name} <-> {b.name}")
    return warnings_


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    scene = build_scene()
    dae = os.path.join(OUT_DIR, "l_bench.dae")
    obj = os.path.join(OUT_DIR, "l_bench.obj")
    mtl = os.path.join(OUT_DIR, "l_bench.mtl")
    svg = os.path.join(OUT_DIR, "l_bench.svg")
    cut = os.path.join(OUT_DIR, "l_bench_cutlist.csv")
    objs_csv = os.path.join(OUT_DIR, "l_bench_objects.csv")
    write_dae(scene, dae)
    write_obj_mtl(scene, obj, mtl)
    write_svg(scene, svg)
    write_cutlist(scene, cut)
    write_objects_csv(scene, objs_csv)
    warnings_ = sanity_checks(scene)
    print(f"Wrote {dae}")
    print(f"Wrote {obj}")
    print(f"Wrote {mtl}")
    print(f"Wrote {svg}")
    print(f"Wrote {cut}")
    print(f"Wrote {objs_csv}")
    print(f"Boxes: {len(scene.boxes)}  Cylinders: {len(scene.cylinders)}")
    if warnings_:
        print(f"WARNINGS ({len(warnings_)}):")
        for w in warnings_[:20]:
            print(f"  - {w}")
        if len(warnings_) > 20:
            print(f"  ... and {len(warnings_) - 20} more")
    else:
        print("No frame collisions.")


if __name__ == "__main__":
    main()
