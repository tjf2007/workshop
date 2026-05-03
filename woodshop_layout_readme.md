# Woodshop Layout - SketchUp Import Model

Dimensionally accurate planning model for a 10' x 20' garage-bay woodshop.
This is a layout / coordination model, not a rendering. Every block is sized
in real inches so you can verify clearances, dust-pipe runs, electrical
zones, and lift cavities before you cut wood.

## Files

| File | Purpose |
| --- | --- |
| `generate_woodshop.py` | Python source. Re-run any time to regenerate every output. |
| `woodshop_layout.dae` | **Primary deliverable.** Collada with `unit=inch`, Z-up. Drag into SketchUp. |
| `woodshop_layout.obj` + `.mtl` | Wavefront fallback for tools that don't take Collada. |
| `woodshop_layout.svg` | 2D top-down sanity-check plan with grid + legend. Open in any browser. |
| `woodshop_layout_objects.csv` | Flat list of every object: name, category, material, position, size, note. |
| `build_sequence.md` | Phase-by-phase build order for the real shop. |

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

### Fixed L-bench (37 in tall, 36 in deep)
- `L_Bench_Top_Leg`: 144 x 36 x 37 along the back wall (12 ft long).
- `L_Bench_Left_Leg`: 36 x 84 x 37 down the left side (7 ft long).
- The plan brief asked for ~12 ft x 10 ft. The bay is 20 ft along the back
  wall and 10 ft deep, so 12 ft of new bench fits comfortably along the
  back; the right 8 ft of the back wall is the existing 3 x 8 bench (see
  next item). The left leg is 7 ft - long enough for the planer cavity
  plus the table-saw platform extending past its end.

### Existing 3' x 8' workbench
- 36 x 96 x 37, sits in the top-right of the back wall (X = 144..240,
  Y = 0..36) so it abuts the new top leg. Drill press lives on top.
- Darker tan material so it reads as "existing, keep" vs "new, build."

### Husky chests
- Both sit under the existing 3 x 8 bench (right portion of back wall),
  matching the photo of the current shop. Both reach 37 in via shims.
- Tall (40 x 18 x 36) at X = 148..188, Y = 12..30, with a 1 in shim.
- Short (40 x 18 x 20) on a 16 in plinth at X = 196..236, Y = 12..30.

### Tools
| Tool | Position note |
| --- | --- |
| Miter saw (DeWalt 10") | Recessed in top leg, deck flush at 37 in. X = 54..84, Y = 4..28. Recess depth 4 in. |
| Router table | Flush in top leg, X = 108..132, Y = 4..36. Insert plate as a thin top layer. |
| Planer (DeWalt) | Vertical lift cavity in left leg, 30 x 30 opening at X = 3..33, Y = 42..72. Stored at z = 16, raises to 37. Both states modeled (solid block lowered, ghost outline raised). |
| Table saw (DeWalt jobsite) | On a 36 x 36 x 3 in fixed floor platform at X = 42..78, Y = 60..96. Deck flush at 37 in. Outfeed -Y toward the L-bench. |
| Drill press | On top of the existing 3 x 8 bench at X = 198..216, Y = 6..24. |
| Laser cutter | 4 x 4 rolling table at X = 180..228, Y = 60..108 (lower-right open quadrant). |

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

- **Table-saw infeed is short.** With the saw at the bottom of the left
  leg and outfeed pointed at the bench, the operator stands ~24 in from
  the front wall. Fine for short rips and sheet goods that come in from
  the side; long boards need diagonal feed or you reposition the saw to
  the middle of the bay during the cut.
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
