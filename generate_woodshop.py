"""
Woodshop CAD layout generator.

Produces:
  - woodshop_layout.svg  (top-down 2D plan, sanity check)
  - woodshop_layout.obj  (Wavefront OBJ geometry)
  - woodshop_layout.mtl  (matching material library)
  - woodshop_layout.dae  (Collada, primary deliverable for SketchUp)
  - woodshop_layout_objects.csv  (flat object list with positions/sizes)

Coordinate system (LANDSCAPE per the user's sketch):
  - Origin (0,0,0) = back-left corner of the shop footprint, floor.
  - X = shop length along the 20 ft back wall  (0..240 in)
  - Y = shop depth from back wall to garage opening  (0..120 in)
  - Z = height  (0..96 in)

The L-shaped bench occupies the back-left:
  - Top leg runs along the back wall (Y=0), filling 12 ft of the 20 ft length.
  - Existing 3 ft x 8 ft bench fills the remaining right portion of the back
    wall, with the drill press on top.
  - Short leg of the L drops down the left side (X=0).
  - Planer vertical lift sits inside the left-leg bench.
  - Table saw on a 36 in x 36 in floor platform lives just past the end of
    the left leg, deck flush at 37 in.
  - Laser cutter rolling table sits in the lower-right open quadrant.

All units are inches. SketchUp imports Collada in meters by default; the
generator writes <unit name="inch" meter="0.0254"/> in the asset header so
SketchUp picks up the correct scale.
"""

from __future__ import annotations

import csv
import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterable

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Material:
    name: str
    rgb: tuple[float, float, float]
    alpha: float = 1.0  # 1 = opaque, <1 = transparent

    @property
    def hex(self) -> str:
        r, g, b = self.rgb
        return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))


MATERIALS: dict[str, Material] = {
    "floor":        Material("floor",        (0.85, 0.83, 0.78)),
    "wall":         Material("wall",         (0.94, 0.94, 0.94), 0.30),
    "bench":        Material("bench",        (0.78, 0.62, 0.40)),       # plywood tan
    "bench_existing": Material("bench_existing", (0.62, 0.45, 0.25)),   # darker tan
    "cabinet":      Material("cabinet",      (0.10, 0.10, 0.12)),       # husky black
    "tool_yellow":  Material("tool_yellow",  (0.95, 0.78, 0.05)),       # dewalt yellow
    "tool_dark":    Material("tool_dark",    (0.18, 0.18, 0.18)),
    "tool_metal":   Material("tool_metal",   (0.55, 0.55, 0.58)),
    "duct":         Material("duct",         (0.75, 0.75, 0.78)),
    "duct_flex":    Material("duct_flex",    (0.45, 0.45, 0.50)),
    "blast_gate":   Material("blast_gate",   (0.85, 0.30, 0.20)),
    "ghost":        Material("ghost",        (0.30, 0.55, 0.95), 0.18), # clearance zones
    "ghost_planer": Material("ghost_planer", (0.30, 0.85, 0.55), 0.18),
    "curtain":      Material("curtain",      (0.12, 0.12, 0.16), 0.35),
    "light":        Material("light",        (1.00, 0.97, 0.85)),
    "air_filter":   Material("air_filter",   (0.92, 0.92, 0.92)),
    "fan":          Material("fan",          (0.25, 0.25, 0.30)),
    "circuit_a":    Material("circuit_a",    (0.90, 0.10, 0.10)),       # red - dust collector
    "circuit_b":    Material("circuit_b",    (0.10, 0.55, 0.95)),       # blue - saws/router
    "circuit_c":    Material("circuit_c",    (0.95, 0.55, 0.05)),       # orange - planer
    "circuit_d":    Material("circuit_d",    (0.20, 0.75, 0.30)),       # green - air/light
    "label":        Material("label",        (0.05, 0.05, 0.05)),
    "platform":     Material("platform",     (0.55, 0.40, 0.25)),
    "plinth":       Material("plinth",       (0.30, 0.25, 0.20)),
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
    w: float  # along X
    d: float  # along Y
    h: float  # along Z
    material: str
    note: str = ""
    category: str = "object"  # used by SVG layer


@dataclass
class Cylinder:
    name: str
    cx: float
    cy: float
    base_z: float
    radius: float
    height: float
    material: str
    axis: str = "z"  # "x", "y", or "z"
    note: str = ""
    category: str = "object"


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
# Layout
# ---------------------------------------------------------------------------

ROOM_W = 240.0   # X = length along 20ft back wall
ROOM_L = 120.0   # Y = depth, back wall (Y=0) to garage opening (Y=120)
ROOM_H = 96.0    # Z


def build_scene() -> Scene:
    s = Scene()

    # ------- Floor and walls --------------------------------------------------
    s.box("Floor", 0, 0, -1, ROOM_W, ROOM_L, 1, "floor", category="room")
    wall_t = 2.0
    # Back wall at Y=0 (the long 20ft wall with the windows + dust collector)
    s.box("Wall_Back",  0, -wall_t, 0, ROOM_W, wall_t, ROOM_H, "wall", category="room")
    # Left short wall at X=0 (10ft - per sketch this is the "GARAGE" side that
    # opens to the rest of the garage; sliding curtain closes it off).
    s.box("Wall_Left",  -wall_t, 0, 0, wall_t, ROOM_L, ROOM_H, "wall", category="room")
    # Right short wall at X=240 (10ft - solid end wall)
    s.box("Wall_Right", ROOM_W, 0, 0, wall_t, ROOM_L, ROOM_H, "wall", category="room")
    # Front long wall at Y=120 (20ft - opposite the back wall)
    s.box("Wall_Front", 0, ROOM_L, 0, ROOM_W, wall_t, ROOM_H, "wall", category="room")

    # ------- L-shaped fixed bench (NEW build) --------------------------------
    BENCH_H = 37.0

    # Top leg: 12 ft along the back wall (left portion). The right 8 ft of
    # the back wall is the existing 3x8 workbench.
    s.box("L_Bench_Top_Leg", 0, 0, 0, 144, 36, BENCH_H, "bench",
          note="L Bench top leg 144Wx36Dx37H along back wall", category="bench")

    # Left leg: 7 ft drop down the left side, 3 ft wide. Starts below the
    # corner of the top leg (Y=36) so the two pieces don't double up.
    s.box("L_Bench_Left_Leg", 0, 36, 0, 36, 84, BENCH_H, "bench",
          note="L Bench left leg 36Wx84Dx37H", category="bench")

    # ------- Existing 3x8 workbench (right portion of back wall) -------------
    s.box("Existing_3x8_Workbench", 144, 0, 0, 96, 36, BENCH_H, "bench_existing",
          note="Existing 3'x8' bench, drill press on top", category="bench")

    # ------- Husky tool chests -----------------------------------------------
    # Per the photo: both chests sit in the right portion of the shop, under
    # the existing bench area. They serve as structural / storage modules.
    # Tall Husky under the existing bench, mid-right.
    s.box("Tall_Husky_40x18x36", 148, 12, 0, 40, 18, 36, "cabinet",
          note="Tall Husky chest 40Wx18Dx36H under existing bench", category="cabinet")
    s.box("Tall_Husky_Shim", 148, 12, 36, 40, 18, 1, "platform", category="cabinet")
    # Short Husky on a 16" plinth, far right.
    s.box("Short_Husky_Plinth", 196, 12, 0, 40, 18, 16, "plinth",
          note="16in plinth so 20H Husky reaches 37in top", category="cabinet")
    s.box("Short_Husky_40x18x20", 196, 12, 16, 40, 18, 20, "cabinet",
          note="Short Husky chest 40Wx18Dx20H on plinth", category="cabinet")
    s.box("Short_Husky_Shim", 196, 12, 36, 40, 18, 1, "platform", category="cabinet")

    # ------- Miter saw station (recessed in top leg, left of center) --------
    # Per sketch: miter is in the left third of the back-wall bench.
    s.box("Miter_Saw_Recess_Surround", 50, 2, BENCH_H - 0.5, 36, 30, 0.5,
          "platform", note="Visual frame for miter recess", category="tool")
    s.box("Miter_Saw_Body", 54, 4, BENCH_H - 4, 30, 24, 12, "tool_yellow",
          note="DeWalt 10in miter saw, deck flush to 37in bench (recessed 4in)",
          category="tool")

    # ------- Router table (flush in top leg, right portion of new bench) ----
    s.box("Router_Table_Cabinet", 108, 4, 0, 24, 32, BENCH_H, "tool_dark",
          note="Router enclosure inside bench", category="tool")
    s.box("Router_Table_Insert", 108, 4, BENCH_H, 24, 32, 0.5, "tool_metal",
          note="Phenolic insert plate flush with bench top", category="tool")

    # ------- Planer vertical lift cavity / mechanism -------------------------
    # Cavity inside the left-leg bench. Planer rises through the bench top
    # to deck-flush 37in for use, drops to 16in stored.
    s.box("Planer_Lift_Cavity", 3, 42, 0, 30, 30, BENCH_H, "ghost",
          note="Planer lift cavity opening (30x30)", category="ghost")
    s.box("Planer_Lowered", 5, 44, 16, 26, 22, 16, "tool_yellow",
          note="DeWalt planer in lowered/stored position", category="tool")
    s.box("Planer_Raised_Ghost", 3, 42, BENCH_H - 0.25, 30, 30, 2,
          "ghost_planer",
          note="Planer raised position - bed flush to 37in (ghost)",
          category="ghost")

    # ------- Table saw on fixed floor platform -------------------------------
    # Sketch puts the saw at the lower end of the left leg, on the floor.
    # Platform extends the bench's left-leg footprint past the bench end.
    # Outfeed direction is toward the L-bench (-Y), with the bench acting as
    # outfeed support beyond the platform. Operator stands at the high-Y end
    # (front of room); short infeed clearance there is the main tradeoff.
    s.box("Table_Saw_Platform", 42, 60, 0, 36, 36, 3, "platform",
          note="Fixed platform raises saw deck to 37in flush with bench",
          category="tool")
    s.box("Table_Saw_Body", 44, 62, 3, 32, 32, 34, "tool_yellow",
          note="DeWalt jobsite table saw, deck @ 37in", category="tool")

    # ------- Drill press on existing bench -----------------------------------
    # Per sketch: drill is on the right portion of the existing bench.
    s.box("Drill_Press_Column", 198, 6, BENCH_H, 18, 18, 36, "tool_metal",
          note="Drill press on existing 3x8 bench", category="tool")

    # ------- Laser cutter rolling table --------------------------------------
    # Per sketch: 4'x4' rolling table in lower-right open quadrant.
    s.box("Laser_Rolling_Table", 180, 60, 0, 48, 48, 34, "tool_dark",
          note="4'x4' rolling table for laser", category="tool")
    s.box("Laser_Enclosure", 186, 66, 34, 36, 30, 20, "tool_metal",
          note="Laser cutter enclosure", category="tool")

    # ------- Dust collector (high, between windows on back wall) ------------
    # Cylinder 24" dia x 48" tall, mounted high on the long back wall,
    # centered along the 20ft length per sketch annotation.
    s.cyl("Dust_Collector_Body", 120, 12, 36, 12, 48, "tool_metal",
          note="Harbor Freight 1800 CFM dust collector mounted high",
          category="dust")

    # ------- 4" main dust trunk ----------------------------------------------
    # Main horizontal trunk along the back wall at z=82, full 20ft length.
    s.cyl("Dust_Main_BackWall", 0, 12, 82, 2.0, ROOM_W, "duct",
          axis="x", note="4in main trunk along 20ft back wall", category="dust")
    # Vertical riser from the collector outlet to the back-wall trunk.
    s.cyl("Dust_Riser_From_Collector", 120, 12, 82, 2.0, 14, "duct",
          axis="z", note="Riser from collector to main trunk", category="dust")
    # Secondary branch running out from the back-wall trunk along Y to feed
    # the planer (mid left leg) and the table saw (lower left leg).
    s.cyl("Dust_Branch_ToFloorTools", 18, 12, 82, 2.0, 84, "duct",
          axis="y", note="Branch out from back wall to floor-tool drops",
          category="dust")

    # Drops + blast gates + flex hoses
    # name, drop_x, drop_y, top_z, drop_height, gate_z, flex_target (x,y,z)
    drops = [
        ("Drop_Miter",    69, 12, 82, 30, 56, (69, 16, 38)),
        ("Drop_Router",  120, 12, 82, 30, 56, (120, 20, 38)),
        ("Drop_Planer",   18, 57, 82, 30, 56, (18, 57, 24)),
        ("Drop_TableSaw", 18, 78, 82, 50, 56, (60, 78, 18)),
    ]
    for name, dx, dy, top_z, height, gate_z, target in drops:
        s.cyl(f"{name}_Pipe", dx, dy, top_z - height, 2.0, height, "duct",
              axis="z", note=f"{name} 4in drop", category="dust")
        s.box(f"{name}_BlastGate", dx - 3, dy - 3, gate_z, 6, 6, 4,
              "blast_gate", note=f"Blast gate for {name}", category="dust")
        tx, ty, tz = target
        flex_dx, flex_dy, flex_dz = tx - dx, ty - dy, tz - gate_z
        flex_len = math.sqrt(flex_dx ** 2 + flex_dy ** 2 + flex_dz ** 2)
        s.box(f"{name}_FlexHose_Approx",
              min(dx, tx) - 1.5, min(dy, ty) - 1.5, min(gate_z, tz) - 1.5,
              abs(flex_dx) + 3, abs(flex_dy) + 3, abs(flex_dz) + 3,
              "duct_flex",
              note=f"Approx flex hose run, length ~{flex_len:.0f}in",
              category="dust")

    # ------- Air filter (DWXAF101) -------------------------------------------
    # Ceiling-mounted, over the open quadrant so airflow circulates across
    # the work zone without directly fighting the dust-collector intake.
    s.box("Air_Filter_DWXAF101", 138, 54, 84, 24, 18, 12, "air_filter",
          note="DeWalt DWXAF101 ceiling-mounted air filter", category="air")

    # ------- Box fans --------------------------------------------------------
    # Near the curtain end (front of bay). Use only with safe outdoor exhaust.
    s.box("Box_Fan_1",  12, 100, 6, 20, 4, 20, "fan",
          note="Box fan near curtain end (left side)", category="air")
    s.box("Box_Fan_2", 208, 100, 6, 20, 4, 20, "fan",
          note="Box fan near curtain end (right side)", category="air")

    # ------- Sliding dust curtain --------------------------------------------
    # Curtain runs the full 20ft shop length along the X axis, parallel to
    # the back wall, sealing off the work zone (Y < curtain) from the
    # garage-opening side (Y > curtain). Track at z=94, full 240in.
    CURTAIN_Y = 108.0
    s.box("Curtain_Track", 0, CURTAIN_Y - 0.5, 94, ROOM_W, 1.0, 2.0, "tool_metal",
          note="20ft sliding ceiling track parallel to back wall",
          category="curtain")
    s.box("Curtain_Closed", 0, CURTAIN_Y - 0.25, 0, ROOM_W, 0.5, 94,
          "curtain", note="Curtain in closed position", category="curtain")
    s.box("Curtain_Open_Stack", ROOM_W - 12, CURTAIN_Y - 2, 0, 12, 4, 94,
          "curtain", note="Curtain folded/open stack", category="curtain")

    # ------- LED shop lights -------------------------------------------------
    # Three 48in LED fixtures, length oriented along the long X axis at z=94.
    lights = [
        # name, center_x, center_y
        ("LED_Shop_Light_1_BackBench",   72,  18),  # over miter + router
        ("LED_Shop_Light_2_LeftLeg",     30,  60),  # over planer + saw zone
        ("LED_Shop_Light_3_OpenZone",   168,  60),  # over laser + open floor
    ]
    for name, lx, ly in lights:
        s.box(name, lx - 24, ly - 2, 94, 48, 4, 2, "light",
              note=name.replace("_", " "), category="light")

    # ------- Electrical outlets ----------------------------------------------
    # Back wall every ~48 in.
    for x in (24, 72, 120, 168, 216):
        circuit = "circuit_b" if x in (72, 168) else "circuit_d"
        s.box(f"Outlet_Back_{x}in", x - 1.5, 0, 44, 3, 1, 5, circuit,
              note=f"Back-wall outlet @ x={x}in", category="electrical")
    # Left wall every ~48 in (skip top corner since the bench is there).
    for y in (60, 108):
        circuit = "circuit_c" if y == 60 else "circuit_b"
        s.box(f"Outlet_Left_{y}in", 0, y - 1.5, 44, 1, 3, 5, circuit,
              note=f"Left-wall outlet @ y={y}in", category="electrical")
    # Right wall outlets - serve the existing bench / drill press / Husky bays.
    for y in (24, 72):
        s.box(f"Outlet_Right_{y}in", ROOM_W - 1, y - 1.5, 44, 1, 3, 5,
              "circuit_b",
              note=f"Right-wall outlet @ y={y}in", category="electrical")
    # Front wall - power for fans, charging, optional laser.
    for x in (60, 180):
        s.box(f"Outlet_Front_{x}in", x - 1.5, ROOM_L - 1, 44, 3, 1, 5,
              "circuit_d", note=f"Front-wall outlet @ x={x}in",
              category="electrical")
    # Ceiling outlet for air filter.
    s.box("Outlet_Ceiling_AirFilter", 138, 50, 94, 4, 4, 2, "circuit_d",
          note="Ceiling outlet for DWXAF101", category="electrical")
    # High back-wall outlet for dust collector (dedicated).
    s.box("Outlet_High_DustCollector", 118, 0, 72, 4, 1, 5, "circuit_a",
          note="High outlet for dust collector (dedicated 20A or 240V)",
          category="electrical")

    # ------- Walking aisle clearance ghost ----------------------------------
    # 36in walking lane across the front of the bay.
    s.box("Walking_Aisle_Front", 36, 84, 0, ROOM_W - 36, 24, 0.25, "ghost",
          note="36in walking clearance across the front", category="ghost")

    # ------- Miter saw long-stock support ghost ------------------------------
    # 96in left + right along the back-wall bench at deck height.
    s.box("Miter_LongStock_Support_Ghost", 0, 0, BENCH_H, ROOM_W, 36, 0.25,
          "ghost", note="Long-stock support along top bench (192in span)",
          category="ghost")

    # ------- Table saw infeed / outfeed clearance ghost ----------------------
    # Outfeed is toward -Y (back bench). Infeed is toward +Y (front).
    s.box("Table_Saw_Outfeed_Ghost", 42, 0, 0, 36, 60, 0.25, "ghost",
          note="Outfeed clearance toward L-bench (60in)", category="ghost")
    s.box("Table_Saw_Infeed_Ghost", 42, 96, 0, 36, 24, 0.25, "ghost",
          note="Infeed clearance toward front (24in - tight, see README)",
          category="ghost")

    # ------- Planer infeed/outfeed ghost zones -------------------------------
    # Planer is in the left-leg bench at y=42..72, feeds along Y.
    s.box("Planer_Infeed_Ghost", 3, 0, 0, 30, 42, 0.25, "ghost_planer",
          note="Planer infeed 42in toward back wall", category="ghost")
    s.box("Planer_Outfeed_Ghost", 3, 72, 0, 30, 48, 0.25, "ghost_planer",
          note="Planer outfeed 48in toward front of bay", category="ghost")

    return s


# ---------------------------------------------------------------------------
# Cylinder tessellation (used by OBJ + DAE)
# ---------------------------------------------------------------------------

def cylinder_mesh(c: Cylinder, segments: int = 20) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Return (vertices, triangles) for a closed cylinder.

    The cylinder is built oriented along its `axis`. Triangles are CCW when
    viewed from outside.
    """
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []

    # Build the cap circles in local space (axis = +Z), then rotate to axis.
    bottom_ring = []
    top_ring = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        bx = c.radius * math.cos(a)
        by = c.radius * math.sin(a)
        bottom_ring.append((bx, by, 0.0))
        top_ring.append((bx, by, c.height))

    def transform(p):
        x, y, z = p
        if c.axis == "z":
            return (c.cx + x, c.cy + y, c.base_z + z)
        elif c.axis == "x":
            # local +Z becomes world +X
            return (c.base_z + z, c.cy + x, c.cx + y)  # arrange so cx,cy still mean perpendicular center
        elif c.axis == "y":
            return (c.cx + x, c.base_z + z, c.cy + y)
        else:
            raise ValueError(c.axis)

    base_idx = len(verts)
    for p in bottom_ring:
        verts.append(transform(p))
    for p in top_ring:
        verts.append(transform(p))
    bot = base_idx
    top = base_idx + segments

    # Side quads -> two tris each
    for i in range(segments):
        j = (i + 1) % segments
        a = bot + i
        b = bot + j
        c2 = top + j
        d = top + i
        tris.append((a, b, c2))
        tris.append((a, c2, d))

    # Cap centers
    bottom_center_idx = len(verts)
    verts.append(transform((0.0, 0.0, 0.0)))
    top_center_idx = len(verts)
    verts.append(transform((0.0, 0.0, c.height)))

    for i in range(segments):
        j = (i + 1) % segments
        # bottom: wind so normal points -Z (outside)
        tris.append((bottom_center_idx, bot + j, bot + i))
        # top: normal points +Z
        tris.append((top_center_idx, top + i, top + j))

    return verts, tris


def box_mesh(b: Box) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    x0, y0, z0 = b.x, b.y, b.z
    x1, y1, z1 = x0 + b.w, y0 + b.d, z0 + b.h
    v = [
        (x0, y0, z0),  # 0
        (x1, y0, z0),  # 1
        (x1, y1, z0),  # 2
        (x0, y1, z0),  # 3
        (x0, y0, z1),  # 4
        (x1, y0, z1),  # 5
        (x1, y1, z1),  # 6
        (x0, y1, z1),  # 7
    ]
    # CCW outward
    f = [
        (0, 3, 2), (0, 2, 1),  # bottom (-Z)
        (4, 5, 6), (4, 6, 7),  # top (+Z)
        (0, 1, 5), (0, 5, 4),  # front (-Y)
        (2, 3, 7), (2, 7, 6),  # back (+Y)
        (1, 2, 6), (1, 6, 5),  # right (+X)
        (3, 0, 4), (3, 4, 7),  # left (-X)
    ]
    return v, f


# ---------------------------------------------------------------------------
# OBJ + MTL writer
# ---------------------------------------------------------------------------

def write_obj_mtl(scene: Scene, obj_path: str, mtl_path: str) -> None:
    with open(mtl_path, "w") as f:
        for m in MATERIALS.values():
            r, g, b = m.rgb
            f.write(f"newmtl {m.name}\n")
            f.write(f"Ka {r:.3f} {g:.3f} {b:.3f}\n")
            f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
            f.write(f"Ks 0.05 0.05 0.05\n")
            f.write(f"Ns 16\n")
            f.write(f"d {m.alpha:.3f}\n")
            f.write(f"illum 2\n\n")

    with open(obj_path, "w") as f:
        f.write(f"mtllib {os.path.basename(mtl_path)}\n")
        vertex_offset = 1  # OBJ is 1-indexed

        def emit(name: str, mat: str, verts, tris):
            nonlocal vertex_offset
            f.write(f"\no {name}\n")
            f.write(f"usemtl {mat}\n")
            for vx, vy, vz in verts:
                f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
            for a, b_, c_ in tris:
                f.write(f"f {a + vertex_offset} {b_ + vertex_offset} {c_ + vertex_offset}\n")
            vertex_offset += len(verts)

        for box in scene.boxes:
            v, t = box_mesh(box)
            emit(box.name, box.material, v, t)
        for cyl in scene.cylinders:
            v, t = cylinder_mesh(cyl)
            emit(cyl.name, cyl.material, v, t)


# ---------------------------------------------------------------------------
# Collada (.dae) writer
# ---------------------------------------------------------------------------

COLLADA_NS = "http://www.collada.org/2005/11/COLLADASchema"


def _el(tag: str, **attrs):
    el = ET.Element(tag)
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def write_dae(scene: Scene, dae_path: str) -> None:
    ET.register_namespace("", COLLADA_NS)
    root = ET.Element(f"{{{COLLADA_NS}}}COLLADA", attrib={"version": "1.4.1"})

    # asset
    asset = ET.SubElement(root, f"{{{COLLADA_NS}}}asset")
    contributor = ET.SubElement(asset, f"{{{COLLADA_NS}}}contributor")
    ET.SubElement(contributor, f"{{{COLLADA_NS}}}author").text = "woodshop_layout_generator"
    ET.SubElement(contributor, f"{{{COLLADA_NS}}}authoring_tool").text = "generate_woodshop.py"
    ET.SubElement(asset, f"{{{COLLADA_NS}}}created").text = "2026-05-03T00:00:00"
    ET.SubElement(asset, f"{{{COLLADA_NS}}}modified").text = "2026-05-03T00:00:00"
    # 1 inch = 0.0254 meter. SketchUp respects this on import.
    unit = ET.SubElement(asset, f"{{{COLLADA_NS}}}unit")
    unit.set("name", "inch")
    unit.set("meter", "0.0254")
    ET.SubElement(asset, f"{{{COLLADA_NS}}}up_axis").text = "Z_UP"

    # library_effects
    lib_effects = ET.SubElement(root, f"{{{COLLADA_NS}}}library_effects")
    for m in MATERIALS.values():
        eff = ET.SubElement(lib_effects, f"{{{COLLADA_NS}}}effect", id=f"{m.name}-effect")
        profile = ET.SubElement(eff, f"{{{COLLADA_NS}}}profile_COMMON")
        technique = ET.SubElement(profile, f"{{{COLLADA_NS}}}technique", sid="common")
        lambert = ET.SubElement(technique, f"{{{COLLADA_NS}}}lambert")
        diffuse = ET.SubElement(lambert, f"{{{COLLADA_NS}}}diffuse")
        color = ET.SubElement(diffuse, f"{{{COLLADA_NS}}}color")
        r, g, b = m.rgb
        color.text = f"{r:.4f} {g:.4f} {b:.4f} {m.alpha:.4f}"
        if m.alpha < 1.0:
            transparency = ET.SubElement(lambert, f"{{{COLLADA_NS}}}transparency")
            t_float = ET.SubElement(transparency, f"{{{COLLADA_NS}}}float")
            t_float.text = f"{m.alpha:.4f}"
            transparent = ET.SubElement(lambert, f"{{{COLLADA_NS}}}transparent",
                                        opaque="A_ONE")
            tcolor = ET.SubElement(transparent, f"{{{COLLADA_NS}}}color")
            tcolor.text = f"1 1 1 {m.alpha:.4f}"

    # library_materials
    lib_materials = ET.SubElement(root, f"{{{COLLADA_NS}}}library_materials")
    for m in MATERIALS.values():
        mat = ET.SubElement(lib_materials, f"{{{COLLADA_NS}}}material",
                            id=f"{m.name}-material", name=m.name)
        ET.SubElement(mat, f"{{{COLLADA_NS}}}instance_effect",
                      url=f"#{m.name}-effect")

    # library_geometries (one per object so we get per-object names in SketchUp)
    lib_geoms = ET.SubElement(root, f"{{{COLLADA_NS}}}library_geometries")

    # Build geometries. We'll record (geometry_id, material_name, name) for nodes.
    geoms: list[tuple[str, str, str]] = []

    def add_geometry(geom_id: str, name: str, material: str, verts, tris):
        geom = ET.SubElement(lib_geoms, f"{{{COLLADA_NS}}}geometry",
                             id=geom_id, name=name)
        mesh = ET.SubElement(geom, f"{{{COLLADA_NS}}}mesh")

        # positions
        pos_id = f"{geom_id}-positions"
        src = ET.SubElement(mesh, f"{{{COLLADA_NS}}}source", id=pos_id)
        flat = []
        for v in verts:
            flat.extend(v)
        fa = ET.SubElement(src, f"{{{COLLADA_NS}}}float_array",
                           id=f"{pos_id}-array",
                           count=str(len(flat)))
        fa.text = " ".join(f"{x:.4f}" for x in flat)
        tcommon = ET.SubElement(src, f"{{{COLLADA_NS}}}technique_common")
        accessor = ET.SubElement(tcommon, f"{{{COLLADA_NS}}}accessor",
                                 source=f"#{pos_id}-array",
                                 count=str(len(verts)),
                                 stride="3")
        for axis in ("X", "Y", "Z"):
            ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", name=axis, type="float")

        # vertices
        verts_el = ET.SubElement(mesh, f"{{{COLLADA_NS}}}vertices",
                                 id=f"{geom_id}-vertices")
        ET.SubElement(verts_el, f"{{{COLLADA_NS}}}input",
                      semantic="POSITION", source=f"#{pos_id}")

        # triangles
        tris_el = ET.SubElement(mesh, f"{{{COLLADA_NS}}}triangles",
                                count=str(len(tris)),
                                material="mat_symbol")
        ET.SubElement(tris_el, f"{{{COLLADA_NS}}}input",
                      semantic="VERTEX", source=f"#{geom_id}-vertices",
                      offset="0")
        p = ET.SubElement(tris_el, f"{{{COLLADA_NS}}}p")
        p.text = " ".join(f"{a} {b} {c}" for (a, b, c) in tris)

        geoms.append((geom_id, material, name))

    def safe(name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name)

    used_ids: set[str] = set()
    def unique_id(base: str) -> str:
        gid = base
        n = 1
        while gid in used_ids:
            n += 1
            gid = f"{base}_{n}"
        used_ids.add(gid)
        return gid

    # Boxes
    for box in scene.boxes:
        v, t = box_mesh(box)
        gid = unique_id(f"geom_{safe(box.name)}")
        add_geometry(gid, box.name, box.material, v, t)
    # Cylinders
    for cyl in scene.cylinders:
        v, t = cylinder_mesh(cyl)
        gid = unique_id(f"geom_{safe(cyl.name)}")
        add_geometry(gid, cyl.name, cyl.material, v, t)

    # library_visual_scenes
    lib_scenes = ET.SubElement(root, f"{{{COLLADA_NS}}}library_visual_scenes")
    vscene = ET.SubElement(lib_scenes, f"{{{COLLADA_NS}}}visual_scene",
                           id="WoodshopScene", name="Woodshop")

    for geom_id, material, name in geoms:
        node = ET.SubElement(vscene, f"{{{COLLADA_NS}}}node",
                             id=f"node_{geom_id}", name=name, type="NODE")
        inst = ET.SubElement(node, f"{{{COLLADA_NS}}}instance_geometry",
                             url=f"#{geom_id}")
        bind_mat = ET.SubElement(inst, f"{{{COLLADA_NS}}}bind_material")
        tcommon = ET.SubElement(bind_mat, f"{{{COLLADA_NS}}}technique_common")
        ET.SubElement(tcommon, f"{{{COLLADA_NS}}}instance_material",
                      symbol="mat_symbol",
                      target=f"#{material}-material")

    # scene
    scene_el = ET.SubElement(root, f"{{{COLLADA_NS}}}scene")
    ET.SubElement(scene_el, f"{{{COLLADA_NS}}}instance_visual_scene",
                  url="#WoodshopScene")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(dae_path, xml_declaration=True, encoding="utf-8")


# ---------------------------------------------------------------------------
# 2D top-down SVG plan
# ---------------------------------------------------------------------------

def write_svg(scene: Scene, svg_path: str) -> None:
    # 1 inch -> 4 svg pixels for legibility
    px_per_in = 4
    margin = 60  # px

    width_px = int(ROOM_W * px_per_in + 2 * margin)
    height_px = int(ROOM_L * px_per_in + 2 * margin + 80)  # extra for legend

    def to_svg_x(in_x: float) -> float:
        return margin + in_x * px_per_in

    def to_svg_y(in_y: float) -> float:
        return margin + in_y * px_per_in

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width_px} {height_px}" '
        f'width="{width_px}" height="{height_px}" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="9">',
        '<style>'
        '.label{font-size:8px;fill:#222;}'
        '.title{font-size:14px;font-weight:bold;fill:#111;}'
        '.note{font-size:9px;fill:#333;}'
        '</style>',
        '<rect x="0" y="0" width="100%" height="100%" fill="#fafafa"/>',
    ]

    # Title block
    parts.append(
        f'<text class="title" x="{margin}" y="{margin - 30}">'
        f'Woodshop Top-Down Plan - 10ft x 20ft bay - Z_UP, units = inches'
        f'</text>'
    )
    parts.append(
        f'<text class="note" x="{margin}" y="{margin - 14}">'
        f'Origin = back-left corner. X = width (left to right). '
        f'Y = length (back wall to garage door, top to bottom). '
        f'1 grid = 12in.'
        f'</text>'
    )

    # Grid (12" major)
    grid = []
    for ix in range(0, int(ROOM_W) + 1, 12):
        x = to_svg_x(ix)
        grid.append(f'<line x1="{x}" y1="{to_svg_y(0)}" x2="{x}" '
                    f'y2="{to_svg_y(ROOM_L)}" stroke="#e2e2e2" stroke-width="0.5"/>')
    for iy in range(0, int(ROOM_L) + 1, 12):
        y = to_svg_y(iy)
        grid.append(f'<line x1="{to_svg_x(0)}" y1="{y}" '
                    f'x2="{to_svg_x(ROOM_W)}" y2="{y}" '
                    f'stroke="#e2e2e2" stroke-width="0.5"/>')
    parts.extend(grid)

    # Room outline
    parts.append(
        f'<rect x="{to_svg_x(0)}" y="{to_svg_y(0)}" '
        f'width="{ROOM_W * px_per_in}" height="{ROOM_L * px_per_in}" '
        f'fill="none" stroke="#222" stroke-width="2"/>'
    )

    # Layer order: ghosts first, then bench, cabinets, tools, dust, electrical
    layer_order = [
        "ghost", "room", "bench", "cabinet", "curtain", "tool",
        "dust", "air", "light", "electrical",
    ]

    def stroke_for(category: str) -> str:
        return {
            "ghost": "none",
            "room": "#222",
            "bench": "#5a4622",
            "cabinet": "#000",
            "curtain": "#222",
            "tool": "#222",
            "dust": "#444",
            "air": "#333",
            "light": "#aa8800",
            "electrical": "#222",
        }.get(category, "#444")

    label_targets: list[tuple[float, float, str]] = []

    # Boxes
    for cat in layer_order:
        for box in scene.boxes:
            if box.category != cat:
                continue
            if cat == "room" and box.name.startswith("Wall"):
                continue  # walls cluttery in top-down; keep outline only
            mat = MATERIALS[box.material]
            x = to_svg_x(box.x)
            y = to_svg_y(box.y)
            w = box.w * px_per_in
            h = box.d * px_per_in
            opacity = mat.alpha
            stroke = stroke_for(cat)
            stroke_w = 0.6
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                f'fill="{mat.hex}" fill-opacity="{opacity:.2f}" '
                f'stroke="{stroke}" stroke-width="{stroke_w}"/>'
            )
            # label at center for tools/bench/cabinets
            if cat in ("bench", "cabinet", "tool", "curtain", "air", "light"):
                cx = x + w / 2
                cy = y + h / 2
                label_targets.append((cx, cy, box.name.replace("_", " ")))

        # Cylinders for the dust layer
        if cat == "dust":
            for cyl in scene.cylinders:
                if cyl.category != cat:
                    continue
                mat = MATERIALS[cyl.material]
                if cyl.axis == "z":
                    cx = to_svg_x(cyl.cx)
                    cy = to_svg_y(cyl.cy)
                    r = cyl.radius * px_per_in
                    parts.append(
                        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                        f'fill="{mat.hex}" fill-opacity="{mat.alpha:.2f}" '
                        f'stroke="#444" stroke-width="0.6"/>'
                    )
                elif cyl.axis == "x":
                    # along X axis -> a horizontal pipe in plan view
                    x = to_svg_x(cyl.base_z if False else cyl.cx)  # cx stored as start X
                    # We stored "Dust_Main_BackWall" with cx=0, height=ROOM_W
                    x_start = to_svg_x(cyl.cx)
                    y_center = to_svg_y(cyl.cy)
                    parts.append(
                        f'<line x1="{x_start:.2f}" y1="{y_center:.2f}" '
                        f'x2="{x_start + cyl.height * px_per_in:.2f}" '
                        f'y2="{y_center:.2f}" stroke="{mat.hex}" stroke-width="3"/>'
                    )
                elif cyl.axis == "y":
                    x_center = to_svg_x(cyl.cx)
                    y_start = to_svg_y(cyl.cy)
                    parts.append(
                        f'<line x1="{x_center:.2f}" y1="{y_start:.2f}" '
                        f'x2="{x_center:.2f}" '
                        f'y2="{y_start + cyl.height * px_per_in:.2f}" '
                        f'stroke="{mat.hex}" stroke-width="3"/>'
                    )

    # Labels last so they sit on top
    for cx, cy, text in label_targets:
        parts.append(
            f'<text class="label" x="{cx:.2f}" y="{cy:.2f}" '
            f'text-anchor="middle" alignment-baseline="middle">'
            f'{text}</text>'
        )

    # Legend
    legend_y = to_svg_y(ROOM_L) + 20
    legend_items = [
        ("L Bench / Existing Bench (37in)", MATERIALS["bench"].hex),
        ("Husky Cabinets", MATERIALS["cabinet"].hex),
        ("DeWalt Tools", MATERIALS["tool_yellow"].hex),
        ("Dust Trunk / Drops (4in)", MATERIALS["duct"].hex),
        ("Blast Gates", MATERIALS["blast_gate"].hex),
        ("Curtain", MATERIALS["curtain"].hex),
        ("Ghost Clearance", MATERIALS["ghost"].hex),
        ("Circuit A - Dust Coll", MATERIALS["circuit_a"].hex),
        ("Circuit B - Saws/Router", MATERIALS["circuit_b"].hex),
        ("Circuit C - Planer", MATERIALS["circuit_c"].hex),
        ("Circuit D - Air/Light", MATERIALS["circuit_d"].hex),
    ]
    for i, (text, color) in enumerate(legend_items):
        col = i % 4
        row = i // 4
        lx = margin + col * 180
        ly = legend_y + row * 18
        parts.append(
            f'<rect x="{lx}" y="{ly - 9}" width="14" height="10" '
            f'fill="{color}" stroke="#222" stroke-width="0.4"/>'
        )
        parts.append(
            f'<text class="label" x="{lx + 18}" y="{ly}">{text}</text>'
        )

    parts.append('</svg>')
    with open(svg_path, "w") as f:
        f.write("\n".join(parts))


# ---------------------------------------------------------------------------
# Object CSV manifest
# ---------------------------------------------------------------------------

def write_csv(scene: Scene, csv_path: str) -> None:
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "category", "material", "shape",
                    "x_in", "y_in", "z_in",
                    "w_in_or_radius", "d_in_or_axis", "h_in", "note"])
        for b in scene.boxes:
            w.writerow([b.name, b.category, b.material, "box",
                        b.x, b.y, b.z, b.w, b.d, b.h, b.note])
        for c in scene.cylinders:
            w.writerow([c.name, c.category, c.material, "cylinder",
                        c.cx, c.cy, c.base_z, c.radius, c.axis, c.height, c.note])


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

def sanity_checks(scene: Scene) -> list[str]:
    """Return list of warnings (collisions / out-of-bounds). Ghost zones and
    walls are exempted from the 'inside the room' check because they
    intentionally extend slightly past the walls.
    """
    warnings_: list[str] = []
    for b in scene.boxes:
        if b.category in ("ghost", "room"):
            continue
        if b.x < -0.01 or b.x + b.w > ROOM_W + 0.01:
            warnings_.append(f"{b.name} extends outside X: {b.x}..{b.x + b.w}")
        if b.y < -0.01 or b.y + b.d > ROOM_L + 0.01:
            warnings_.append(f"{b.name} extends outside Y: {b.y}..{b.y + b.d}")
        if b.z < -0.01 or b.z + b.h > ROOM_H + 0.01:
            warnings_.append(f"{b.name} extends outside Z: {b.z}..{b.z + b.h}")
    return warnings_


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    scene = build_scene()

    obj_path = os.path.join(OUT_DIR, "woodshop_layout.obj")
    mtl_path = os.path.join(OUT_DIR, "woodshop_layout.mtl")
    dae_path = os.path.join(OUT_DIR, "woodshop_layout.dae")
    svg_path = os.path.join(OUT_DIR, "woodshop_layout.svg")
    csv_path = os.path.join(OUT_DIR, "woodshop_layout_objects.csv")

    write_svg(scene, svg_path)
    write_obj_mtl(scene, obj_path, mtl_path)
    write_dae(scene, dae_path)
    write_csv(scene, csv_path)

    warnings_ = sanity_checks(scene)
    summary = {
        "boxes": len(scene.boxes),
        "cylinders": len(scene.cylinders),
        "warnings": warnings_,
    }

    print(f"Wrote {svg_path}")
    print(f"Wrote {obj_path}")
    print(f"Wrote {mtl_path}")
    print(f"Wrote {dae_path}")
    print(f"Wrote {csv_path}")
    print(f"Boxes: {summary['boxes']}, Cylinders: {summary['cylinders']}")
    if warnings_:
        print("WARNINGS:")
        for w in warnings_:
            print(f"  - {w}")
    else:
        print("No bounds warnings.")


if __name__ == "__main__":
    main()
