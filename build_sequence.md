# Woodshop Build Sequence

The order to actually build the shop modeled in `woodshop_layout.dae`.
Do not skip phases - electrical comes before bench, dust comes before
finished tool integration, validation comes last. Skipping order means
ripping out work later.

## Phase 1 - Cleanout and measurement

Goal: confirm the model matches reality before you commit to it.

- Clear the future L-bench footprint (back wall + left wall, top-left
  zone of the bay).
- Confirm exact room dimensions to within 1/4 in. Garages are rarely
  square.
- Mark and measure:
  - window locations on the back wall (the dust collector mounts
    between them - if they're not where you think, the collector position
    moves)
  - garage door track / spring hardware clearance (curtain track must
    not foul)
  - existing outlet and subpanel locations
  - ceiling height at center and at corners
  - any beams, soffits, or HVAC obstructions
- Confirm tool deck heights:
  - existing bench top: 37 in (assumed)
  - DeWalt jobsite table-saw deck height (with stand or off stand)
  - DeWalt 10 in miter saw deck height
  - DeWalt planer bed height
  - desired router-table surface height
- If any of these differ from the model, edit `generate_woodshop.py` and
  regenerate before continuing.

## Phase 2 - Electrical rough-in

Do this **before** you build the bench. You cannot easily fish wire
through framed-in cavities later.

Target circuits:
- Dedicated dust-collector circuit (Circuit A in the model). 20A or 240V
  per electrician.
- Dedicated planer circuit (Circuit C). 20A preferred.
- Saw / miter / router circuit (Circuit B). 20A.
- Air-filter / fan / lights / chargers circuit (Circuit D). 15-20A.
- Ceiling outlet for the air filter at approximately x=58, y=88, z=94.
- High wall outlet for the dust collector at approximately x=58, y=0, z=72.

Layout principles:
- Enough outlets that no extension cord crosses a walkway.
- Outlets at z = 44 in along walls so they sit above bench but below
  shelving.
- GFCI / AFCI per local code - electrician's call.

> Reminder: the colors and circuit assignments in the CAD are layout
> intent. The electrician sizes breakers, wire, and protection.

## Phase 3 - Dust collection mounting

Do this before bench framing so you can run pipe along walls without
working around cabinetry.

- Mount Harbor Freight 1800 CFM collector high on the back wall between
  windows. Use cleats / brackets rated for the load and for vibration.
- Run 4 in hard trunk along the back wall at z ~ 82 in.
- Branch trunk down the left wall to the planer drop.
- Drop pipes at:
  - miter saw (top bench, left of center)
  - router table (top bench, right of center)
  - planer (left leg, mid-run)
  - table saw (mid-bay, ceiling drop)
- Install blast gates at z ~ 56 in - reachable without a stool.
- Use wyes, not sharp tees.
- Keep flex hose to the last few feet between gate and tool.
- Decide PVC vs metal duct now, not after install. Talk to the
  electrician about static / bonding / code.

## Phase 4 - Stationary L-bench frame

- Build 37 in tall fixed bench frames per the L geometry:
  - Top leg: 120 W x 36 D
  - Left leg: 36 W x 108 L
- Anchor frames to wall studs.
- Integrate the two Husky chests as structural / storage modules:
  - Tall Husky (40 x 18 x 36) under the back bench. 1 in shim on top.
  - Short Husky (40 x 18 x 20) on a 16 in plinth under the left leg.
- Leave the planned cavities open:
  - Planer vertical lift cavity (30 x 30, full bench height) on left leg.
  - Miter-saw recess on top leg (32 x 28 in opening).
  - Router-table opening on top leg (24 x 32 in).
  - Dust drops where pipe lands.
- Surface: 1.5 in plywood top (or doubled MDF / hardboard sandwich).

## Phase 5 - Tool integration

- **Table saw**: build the 36 x 36 x 3 in fixed platform so the saw deck
  sits flush with the 37 in bench / outfeed. Shim if needed.
- **Miter saw**: recess so the deck is flush at 37 in. Build long-stock
  support wings at the same height extending left and right along the
  bench.
- **Router table**: flush-mount the insert plate in the top bench.
  Confirm fence clearance and dust port routing under the bench.
- **Planer lift**: build with a mechanical lift mechanism (scissor lift,
  drawer-slide rails, or screw jack), vertical guides on both sides, and
  **hard mechanical stops at the work height**. Do not rely on the
  jack / actuator alone to hold the planer at 37 in.

## Phase 6 - Air filtration and lighting

- Relocate the DWXAF101 air filter from the garage door opener area to
  the ceiling above the work zone (x=60, y=90, z=84). Aim airflow across
  the work zone, not directly opposing the dust collector intake.
- Install the three 48 in LED shop lights at z = 94:
  - over the miter / router zone
  - over the planer left-leg zone
  - over the table-saw outfeed zone

## Phase 7 - Curtain containment

- Install a 20 ft sliding ceiling track at z = 94, at the y-position
  chosen to close off the active work area from the rest of the garage
  (model uses y = 170, leaving the curtain to seal the 10 ft x 14 ft
  inner zone).
- Hang dark canvas or industrial dust curtain.
- Verify track does not foul:
  - garage door hardware
  - dust pipes
  - light fixtures
  - the ceiling outlet for the air filter

## Phase 8 - Validation

Run each test before declaring the shop done.

- Power up each tool individually on its assigned circuit. Confirm no
  trips at startup.
- Run dust collection at each blast gate, one at a time. Confirm
  draw at the tool inlet (a tissue at the port works for a smoke test).
- Table saw: rip an 8 ft board to confirm outfeed clearance and
  deck-flush behavior.
- Planer: feed a 6 ft board through and confirm infeed + outfeed
  clearance and lift stability under load.
- Miter saw: cut a long board at full extension to confirm long-stock
  support and rear-hood capture.
- Simultaneous load test, **with the electrician present or per their
  written plan**: dust collector + air filter + two box fans + lights +
  saw running. No nuisance trips, no warm panels.

## Important design warnings

- Miter-saw dust capture is poor by default. Build a rear hood / shroud
  or accept floor cleanup.
- Jobsite table-saw dust capture is imperfect. Plan for an overarm
  capture later if needed.
- PVC dust trunk requires a static-bonding plan and code review. Don't
  default to PVC silently.
- Don't block window access, dust-collector maintenance, filter
  cleaning, or any blast gate.
- Keep all power cords off the floor and out of feed paths.
- Maintain 36 in walking clearance everywhere you can - injuries
  happen in pinched aisles.
- The planer lift must lock mechanically at the work height. The jack /
  actuator is a lift, not a hold.
