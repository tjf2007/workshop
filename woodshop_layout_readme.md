# Woodshop Layout - SketchUp Import Model

Dimensionally accurate planning model for a 10' x 20' garage-bay woodshop.
This is a layout / coordination model, not a rendering. Every block is sized
in real inches so you can verify clearances, dust-pipe runs, electrical
zones, and lift cavities before you cut wood.

## Files

### Shop-level layout (room-scale planning)

| File | Purpose |
| --- | --- |
| `generate_woodshop.py` | Python source. Re-run any time to regenerate every output. |
| `woodshop_layout.dae` | Collada with `unit=inch`, Z-up. Drag into SketchUp. |
| `woodshop_layout.obj` + `.mtl` | Wavefront fallback for tools that don't take Collada. |
| `woodshop_layout.svg` | 2D top-down sanity-check plan with grid + legend. Open in any browser. |
| `woodshop_layout_objects.csv` | Flat list of every object: name, category, material, position, size, note. |
| `build_sequence.md` | Phase-by-phase build order for the real shop. |

### L-bench detailed model (build-from)

| File | Purpose |
| --- | --- |
| `generate_l_bench.py` | Stick-frame L-bench generator. Every 2x4 + panel is a named part. |
| `l_bench.dae` | Collada for SketchUp Pro / Blender / FreeCAD. 110+ named parts. Units in file (inches). |
| `l_bench.obj` + `.mtl` | Wavefront for free tools (Tinkercad, FreeCAD, MeshLab). No units in file - import as inches or scale by 0.0254. |
| `l_bench.svg` | Top-down plan with cavities, framing, hardware, legend. |
| `l_bench_cutlist.csv` | Aggregated cut list. Identical parts grouped with quantity. |
| `l_bench_partsheets.svg` | One card per unique cut, with dimensions + scaled diagram. Print and check off as you cut. |
| `l_bench_objects.csv` | Flat list of every modeled L-bench part. |
| `planer_lift_bom.md` | Honest write-up of the gas-strut mechanism, the simpler trailer-jack alternative, and Home Depot BOM for both. |

**Cut-list note on the bench top:** the cut list shows each top section as
a 1.5 in thick piece. That's the *finished* lamination of two 3/4 in
plywood layers. For purchasing, double the plywood quantity for any row
where thickness = 1.50 (i.e., buy two 3/4 in sheets per top section and
glue + screw together).

**Cut-list note on the planer-lift hardware:** 4 heavy-duty 24 in vertical
drawer slides (220 lb rated each, e.g., Accuride 7957 or Knape & Vogt
8400-series), 4 gas struts (~50 lb force each, mounted at slight angle
for balanced near-neutral lift), 1 1/2 in steel locking pin + receiver
bracket. Sled is 28 x 28 x 3/4 plywood (planer bolts to top of sled).

## Coordinate system

Landscape orientation, matching the user's pencil sketch.

- Origin `(0, 0, 0)` = back-left corner of the shop footprint, floor level.
- **X** = shop length along the 20 ft back wall, 0 -> 240 in, left to right.
- **Y** = shop depth, 0 -> 120 in, back wall (Y=0) to garage opening (Y=120).
- **Z** = height, 0 -> 96 in.
- Up axis: `Z_UP`
- Units: inches (`<unit name="inch" meter="0.0254"/>`)

When you look at the SVG plan with the title at the top, the back wall is
along the top edge, the garage opening is along the bottom edge, the L-bench
fills the upper-left, and the laser cutter lives in the lower-right.

SketchUp respects the `<unit>` tag on import. If something looks 1/40th the
expected size in another tool, that tool likely ignored the unit declaration -
scale by 0.0254 to get meters.

## Importing into SketchUp

1. **File -> Import**, choose `woodshop_layout.dae`.
2. In the Import Options dialog, leave units alone (the file declares them).
3. After import, hit **Zoom Extents**. The model is one group containing
   65 named child nodes. Right-click -> Explode if you want to edit
   individual objects.
4. SketchUp's outliner mirrors the object names, so you can find
   `Table_Saw_Body`, `Planer_Lift_Cavity`, etc. directly.

If your SketchUp version chokes on the Collada (rare), import
`woodshop_layout.obj` instead. The `.mtl` must sit next to it.

## What's modeled

### Room
- 120 x 240 x 96 in shell, walls drawn at 30% opacity so you can see in.
- Front wall left open above 84 in to represent the garage-door opening.

### Fixed L-bench (37 in tall, 36 in deep) - MIRRORED
- `L_Bench_Top_Leg`: 144 x 36 x 37 along the back wall (12 ft, RIGHT portion).
- `L_Bench_Short_Leg`: 36 x 84 x 37 down the RIGHT side (7 ft long, against
  the solid right wall).
- After the mirror, the existing 3 x 8 bench moves to the LEFT portion of
  the back wall (X = 0..96) and the new L occupies X = 96..240 with the
  short leg dropping down the right side at X = 204..240.

### Existing 3' x 8' workbench
- 36 x 96 x 37, sits at the TOP-LEFT of the back wall (X = 0..96, Y = 0..36)
  so it abuts the new top leg of the L. Drill press lives on top.

### Husky chests
- Both sit under the existing 3 x 8 bench (LEFT portion of back wall).
- Tall (40 x 18 x 36) at X = 52..92, Y = 12..30, with a 1 in shim.
- Short (40 x 18 x 20) on a 16 in plinth at X = 4..44, Y = 12..30.

### Tools
| Tool | Position note |
| --- | --- |
| Miter saw (DeWalt 10") | Recessed in top leg, deck flush at 37 in. X = 99..129, Y = 4..28. FAR from new corner (left end of top leg). |
| Router table | Flush in top leg, X = 180..204, Y = 4..36. CLOSE to new corner. |
| Planer (DeWalt) | Vertical lift cavity in short leg, X = 207..237, Y = 84..114. FAR from corner (front of bay). Stored at z = 16, raises to 37. **See tradeoffs below - planer infeed is now short.** |
| Table saw (DeWalt jobsite) | Drop-in cavity in short leg at X = 206..238, Y = 42..74. CLOSE to corner. Outfeed -Y catches the top-leg bench surface (6 in gap, then 36 in supported). |
| Drill press | On top of the existing 3 x 8 bench at X = 24..42, Y = 6..24. |
| Laser cutter | 4 x 4 rolling table at X = 12..60, Y = 60..108 (lower-left open quadrant). |

### Dust collection
- `Dust_Collector_Body`: Harbor Freight 1800 CFM, mounted high on the back wall (z = 36..84).
- `Dust_Main_BackWall`: 4 in trunk along the back wall at z = 82.
- `Dust_Branch_LeftWall`: 4 in branch down the left wall to feed the planer.
- Four blast-gated drops: miter, router, planer, table saw.
- Each drop has a `*_Pipe`, `*_BlastGate` (small red block at z = 56,
  reachable height), and `*_FlexHose_Approx` (last-couple-feet flex,
  approximated as a thin elongated box).

Important dust notes (encoded in the per-object `note` field, also stored
in the CSV):
- Keep 4 in hard pipe as long as possible. Flex only at the tool.
- Use wyes, not sharp tees, when you actually buy fittings.
- Miter-saw capture is weak by default - plan a rear hood.
- Jobsite table saw capture is imperfect - plan for cleanup or an overarm
  capture later.
- Do not run PVC trunk without confirming static / fire / code with your
  electrician. Many hobby shops do, but it is your call to document.

### Air filtration and fans
- `Air_Filter_DWXAF101`: 24 x 18 x 12 ceiling-hung above the work zone (z = 84).
- Two box fans near the curtain end. Note: only use to exhaust outside if
  you have a safe path - blowing fine dust into the rest of the garage is
  a respiratory hazard.

### Curtain
- 20 ft track parallel to the back wall at Y = 108, z = 94, full X length.
  Closes off the work zone (Y < 108) from the garage-opening side.
- Two states: closed (translucent panel hanging from track to floor) and
  open (folded stack at the right end of the track).

### Lighting
- Three 48 in LED shop lights at z = 94, over the miter/router zone, the
  planer left-leg zone, and the table-saw outfeed.

### Electrical zones (coordination only - not engineering)
Color-coded outlet blocks at z = 44 on walls and z = 72/94 on the ceiling:
- **Circuit A (red)** - Dust collector, dedicated. Possibly 240V.
- **Circuit B (blue)** - Table saw / miter saw / router.
- **Circuit C (orange)** - Planer, dedicated 20A preferred.
- **Circuit D (green)** - Air filter, fans, lights, chargers.

> Electrician must size breakers, wire gauge, GFCI/AFCI requirements,
> 120V/240V decisions, and load calculations to local code. The colors
> above are layout intent only.

### Ghost / clearance zones (transparent)
- Table saw outfeed: 36 x 60 toward the L-bench (-Y direction). Infeed
  is only 36 x 24 (front of bay is tight - see tradeoff note below).
- Planer infeed: 30 x 42 toward back wall. Outfeed: 30 x 48 toward front.
- Miter long-stock support: 192 in span across the back-wall bench.
- Front walking lane: 36 in clear across most of the bay width at Y = 84..108.

These are real geometry with low alpha so they show up in SketchUp but
don't get in the way.

### Known layout tradeoffs

- **Table-saw outfeed is now excellent** (close-to-corner placement).
  Workpiece exits the saw at Y = 42, drops 6 in to the top-leg bench
  surface at Y = 36, and continues across the bench for 36 in of supported
  outfeed. Better than the original (which had a 48 in unsupported gap).
- **Planer infeed/outfeed is now constrained.** The planer at Y = 84..114
  has only 6 in of clearance on the +Y side and 84 in on the -Y side. To
  use it effectively, either:
  (a) feed boards from the BACK side (operator reaches across the bench
      to feed, board exits toward operator), or
  (b) accept a maximum board length of ~36 in.
  This is a consequence of swapping the planer and saw positions per
  user direction. If you find this limits you in practice, swap them back
  (set `PLANER_Y0=42` and `SAW_Y0=84` in `generate_l_bench.py`).
- **Two windows, dust collector between.** The dust-collector cylinder
  is centered at X = 120 on the back wall. If your window centers are
  not symmetric around X = 120, edit `Dust_Collector_Body` in
  `generate_woodshop.py` and re-run.
- **Garage door direction not modeled.** The "GARAGE" label on your
  sketch points off the left short wall. The model treats Y = 120
  (front long wall) as the curtained opening, since the curtain is
  20 ft long and must run parallel to a long wall. If your actual
  garage door is on the X = 0 short wall, the curtain orientation
  needs to flip - flag it and I'll regenerate.

## Regenerating

```sh
python3 generate_woodshop.py
```

No third-party packages. Pure stdlib (`xml.etree`, `math`, `csv`).
The script also runs sanity checks and prints any out-of-bounds objects.

## Editing the layout

All geometry is data-driven inside `build_scene()`. To move a tool,
change a single line. To add a new object, call `s.box(...)` or `s.cyl(...)`
with `name`, position, size, material key from `MATERIALS`, an optional
note, and a category (drives the SVG layer + sanity-check exemptions).

Material colors and alphas live in the `MATERIALS` dict at the top of
the script. Add a new material there before referencing it.

## Design assumptions and known approximations

- The L-bench is one solid block per leg. Real cabinetry will have
  toe-kicks, drawer fronts, and panel divisions - those are intentionally
  omitted to keep the model usable for layout coordination.
- Dust pipe is straight cylinders. No fittings are modeled. Wyes and
  elbows will add a few inches at every junction in real life.
- Flex hose runs are shown as elongated boxes between blast gate and tool
  inlet; treat as "this much hose, roughly here," not as a CAD path.
- Cylinders are 20-segment polygons. Plenty for layout, not for renders.
- The model has no doors, windows, or studs. The walls are thin reference
  surfaces, not framing.
