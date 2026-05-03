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

- Origin `(0, 0, 0)` = back-left corner of the shop footprint, floor level.
- **X** = shop width, 0 -> 120 in, left to right
- **Y** = shop length, 0 -> 240 in, back wall to garage door
- **Z** = height, 0 -> 96 in
- Up axis: `Z_UP`
- Units: inches (`<unit name="inch" meter="0.0254"/>`)

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
- `L_Bench_Top_Leg`: 120 x 36 x 37 along the back wall.
- `L_Bench_Left_Leg`: 36 x 108 x 37 along the left wall.
- The plan brief asked for ~12 ft x 10 ft. The bay is only 10 ft wide, so
  the top leg is 10 ft and the long leg is 9 ft. Going past 108 in
  collides with the table-saw outfeed zone and steals the right-side
  walking aisle - if you want a longer left leg, you have to give up the
  table-saw position or the aisle.

### Existing 3' x 8' workbench
- 36 x 96 x 37 along the right wall, y = 60..156. Drill press lives on it.
- Darker tan material so it reads as "existing, keep" vs "new, build."

### Husky chests
- Tall (40 x 18 x 36) under the back bench, with a 1 in shim to meet 37 in.
- Short (40 x 18 x 20) on a 16 in plinth along the left leg, also 37 in top.

### Tools
| Tool | Position note |
| --- | --- |
| Miter saw (DeWalt 10") | Recessed in top bench, deck flush at 37 in. Recess depth 4 in. |
| Router table | Flush in top bench, x = 72..96. Insert plate as a thin top layer. |
| Planer (DeWalt) | Vertical lift cavity in left leg, 30 x 30 opening. Stored at z = 20, raises to 37. Both states are in the model: solid block lowered, ghost outline raised. |
| Table saw (DeWalt jobsite) | On a 36 x 36 x 3 in fixed platform, deck reaches 37 in. Outfeed faces the back bench. |
| Drill press | On the existing 3 x 8 bench. |
| Laser cutter | 4 x 4 rolling table near the front, away from the L bench. |

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
- Track at y = 170 across the full 10 ft width, z = 94.
- Two states: closed (translucent panel hanging from track to floor) and
  open (folded stack at the right end).

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
- Table saw infeed and outfeed: 96 x 36 each.
- Planer infeed and outfeed: 72 x 30 each.
- Miter saw long-stock support: 96 in either side along the top bench.
- Right-side walking aisle: 36 in clear path full length.

These are real geometry with low alpha so they show up in SketchUp but
don't get in the way.

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
