# L-Bench Build Guide

Step-by-step instructions for cutting and assembling the L-bench frame +
top + skin. **Does not cover the planer lift mechanism** - leave that
cavity open and skip to the saw cleats. The planer lift goes in later
(see `planer_lift_bom.md` when you're ready).

The cut list (`l_bench_cutlist.csv`) is your source of truth for what
to buy and cut. The placement file (`l_bench_objects.csv`) has the exact
X/Y/Z for every part. This doc is the human-readable build order.

> **Coordinate convention**: looking down at the bench from above with
> the back wall at the top of the page, X runs left-to-right along the
> back wall (0..144 in for the top leg) and Y runs front-to-back into
> the room (0..36 in is the top leg, 36..120 in is the short leg
> extending out from the LHS corner). Z is height (0 = floor, 37 = top).

---

## Tools you need

| Category | Tools |
| --- | --- |
| Cutting | Circular saw + straight edge (or track saw), miter saw, jigsaw for cavity cutouts |
| Layout | 25 ft tape, combination square, 4 ft level, chalk line, pencil, framing square |
| Driving | Cordless impact + drill (separate is better than swap-chuck), Forstner bit set, countersink |
| Holding | 4-6 bar clamps (24 in min), spring clamps, 2-3 quick clamps |
| Safety | Safety glasses, ear protection, N95s |
| Helpful | Sliding T-bevel for the miter recess, kreg jig if you want pocket holes |

---

## Materials checklist

Reference `l_bench_cutlist.csv`. Quick summary:

- **22 SPF 2x4 studs** (28.5 in vertical) - get 26 boards to allow for cuts and rejects
- **2 SPF 2x12s** OR 2 SPF 2x4x12 ft for the 144 in rails
- **6 sheets 3/4 in plywood** (birch or sande - your call)
- **8 cross stretchers** at 29 in for the top leg, **8 more** at 29 in for the short leg
- **4 stud pairs** at 4 positions for the short leg (8 studs)
- **2 husky cleats / blocking pieces** for the miter recess (36 in and 23 in)
- Construction adhesive (Loctite PL Premium), wood glue (Titebond II), screws (#9 x 2.5 in, #8 x 1.25 in), lag bolts (1/4 x 3.5 for wall anchoring)

See `BUILD.md` and `SHOPPING_LIST.md` for the consolidated buy-list.

---

## Cut day (1-2 sessions)

Do **all the cutting** before you start assembly. It is faster, cleaner,
and lets you batch waste.

### Step 1: Cross-cut the 2x4 stock

1. Cull bad boards first - reject visible twist, crown >1/4 in, or
   knots larger than 1 in diameter at edges.
2. From the straight boards, cross-cut in this order (longest first
   to leave usable offcuts):
   - **4 x 144 in rails** (top leg front + back, top + bottom). Use
     the 12 ft boards. If you must splice, splice at a stud only.
   - **4 x 84 in rails** (short leg sides, top + bottom). Cross-cut
     from 8-footers - 12 in offcut per board.
   - **22 x 28.5 in studs** (frame verticals). Each 8 ft board yields
     three 28.5 in studs + 10.5 in offcut.
   - **16 x 29 in cross stretchers** (8 top leg + 8 short leg). Use
     the 28.5 in offcuts trimmed slightly... wait, no - these are
     longer. Cut new 29 in pieces from straight 8-footers.
   - **4 saw sled cleats**: 2 x 32 in, 2 x 25 in.
   - **2 miter recess blocking (front + back)**: 36 in.
   - **2 miter recess blocking (sides)**: 23 in.
3. Stamp each piece with its name (sharpie on the end grain) as you
   cut it. You will not remember "is this the 84 or the 86 in?" in 3 days.

### Step 2: Rip and crosscut plywood

Lay out the cuts using `l_bench_partsheets.svg` printed on letter
paper. Each unique cut shape has a card. Mark each sheet before
cutting.

Order (largest panels first):

1. **Doubled top panels** (1.5 in finished = two 3/4 plies glued):
   - TopLeg_Top_Left: 50 x 36 - cut 2 plies
   - TopLeg_Top_MidRight: 36 x 22 - cut 2 plies
   - TopLeg_Top_FarRight: 36 x 12 - cut 2 plies
   - LeftLeg_Top_AbovePlaner: 36 x 6 - cut 2 plies
   - LeftLeg_Top_BetweenCavities: 36 x 12 - cut 2 plies
   - LeftLeg_Top_End: 36 x 4 - cut 2 plies
   - Plus 4 router-area sub-panels (around insert plate)
   - Plus the saw cavity strips (2 x 32 x 2) and planer cavity strips
     (2 x 30 x 3)
   - Plus the miter recess lips (36 x 2 back, 36 x 4 front)
2. **Single 3/4 in panels** (one ply each):
   - 2 x End panels (36 x 33)
   - 2 x Toe kicks (144 x 4) - front + back of top leg
   - 2 x Toe kick end caps (36 x 4) - right end + short leg front end
   - 2 x Toe kicks (84 x 4) - short leg sides
   - 1 x Router cabinet floor (32 x 24)
   - 1 x Router cabinet back (31.5 x 24)
   - 2 x Router cabinet sides (32 x 31.5)
   - 1 x Miter recess bottom (36 x 30)
   - 1 x Planer sled (28 x 28) - **set aside, used during lift install**
   - 1 x Saw sled (30 x 30)

3. Label every piece in sharpie as it comes off the saw.

---

## Assembly

### Step 3: Top leg back wall frame (assemble on the floor)

Frame the back face of the top leg as a single wall-style assembly.

**Layout**: lay the bottom rail (144 in) on its face on the floor, flush
to the chalk-line edge of your work area. Mark the centerline of each
stud on the rail with a pencil square.

Stud X-positions (left edge of each 3.5 in stud):

| # | X position | Purpose |
| --- | --- | --- |
| 0 | 0 in | Left end |
| 1 | 24 in | Mid-span left bay |
| 2 | 46.5 in | Left of miter recess |
| 3 | 86 in | Right of miter recess |
| 4 | 104.5 in | Left of router cutout |
| 5 | 132 in | Right of router cutout |
| 6 | 140.5 in | Right end |

Lay the top rail on top, parallel. Drop the 7 studs vertically between
them at the marked positions. Glue + 2 screws per joint (toenailed
through the rail into the stud end, or face-screwed if you pre-drilled
the rail).

**Critical**: confirm the assembly is square - measure both diagonals,
they should match within 1/8 in. Adjust before screws go all the way in.

### Step 4: Top leg front wall frame

Identical procedure to the back. Same 7 stud positions, same dimensions.
The front face has the miter recess and router cutouts, but the FRAMING
itself doesn't change - it's the top panels that have the cutouts.

### Step 5: Top leg cross stretchers

Stand the two wall frames (front + back) parallel, 36 in apart.
Position them on a flat floor with the bottom rails touching the floor.
You will need a helper or 2 right-angle clamps to hold them upright.

Cut + install cross stretchers between front and back faces at each
stud position (top + bottom):
- 7 top stretchers (29 in each) at top rail height
- 7 bottom stretchers (29 in each) at bottom rail height

Wait - the cutlist says 8 stretchers for the top leg. Re-check:
14 cross stretchers total = 7 top + 7 bottom = matches the 7 stud
positions. (The cutlist line saying "8" is per-pair; verify against
`l_bench_objects.csv`.)

Each stretcher is glued + screwed to the inside face of front and
back rails at the same X position as a stud pair. They tie the two
wall frames into one rigid box.

### Step 6: Miter recess blocking

Inside the top leg frame, between stud 2 (X=46.5) and stud 3 (X=86),
build the miter saw recess pocket:

- **Front + back blocking**: 2 x 36 in pieces, sitting at the recess
  drop height (z = 33 in approx, depending on miter saw deck spec).
  These run along Y at X = 50..86, forming the front + back edges of
  the 36 x 30 recess opening.
- **Side blocking**: 2 x 23 in pieces (cut to 23 to allow for the
  side stud nailers), running along X between the front + back blocking.

Result: a 36 x 30 in pocket recessed 4 in below the bench top, with
all four sides supported. The miter saw bolts to the recess floor
later.

### Step 7: Router cabinet inside the top leg

Between studs 4 (X=104.5) and 5 (X=132), build a 24 in wide cabinet:

1. Drop the router cabinet floor (32 x 24 plywood) in at the bottom-rail
   level. Screw it to the bottom rail and bottom stretchers.
2. Stand the 2 cabinet side panels (32 x 31.5) vertically along the
   inside faces of stud 4 and stud 5. Glue + screw.
3. Drop the back panel (31.5 x 24) against the back wall studs at
   X = 108..132. Glue + screw to studs and side panels.
4. The cabinet front is left **open** - that's how you reach the
   router.

### Step 8: Short leg frame

The short leg (36 W x 84 D x 37 H) is a separate stick-frame box
butted to the top leg's left end and the wall.

Stud Y-positions (left edge of each 3.5 in stud, on both LEFT and
RIGHT sides):

| # | Y position | Purpose |
| --- | --- | --- |
| 0 | 38.5 in | Left of planer |
| 1 | 72 in | Right of planer |
| 2 | 80.5 in | Left of saw |
| 3 | 116 in | Right of saw |

Build the short leg as TWO side walls (left side at X=0 and right side
at X=34.5, each one is 84 in long x 37 in tall with 4 studs + top rail
+ bottom rail). Then connect them with 8 cross stretchers at the
same Y positions (4 top + 4 bottom).

The corner of the L (top leg's left end + short leg's top end) shares
framing - **DO NOT double up the corner stud**. The top leg's front
stud at X=0 IS the corner support; the short leg's left side at X=0
butts against it.

### Step 9: Join top leg + short leg + anchor to wall

This is the moment of truth.

1. Stand the top leg frame against the back wall, level it (shim under
   bottom rail as needed - garage floors are never flat), and lag-bolt
   the back face to the wall studs through the back rails at 16 in OC.
2. Walk the short leg frame into position against the LHS wall, mating
   its top end to the top leg's left end. Square the inside L corner -
   measure diagonals from corner to far ends.
3. Lag-bolt the short leg's left side (X=0) to the LHS wall studs at
   16 in OC.
4. Screw the two frames together at the corner: 4-6 screws through
   the short leg's right side stud into the top leg's left end stud.
   Pre-drill to avoid splitting.

**Do not put the top on yet** - you want unobstructed access to the
inside for the cavity work and wiring.

### Step 10: Toe kicks

While you can still reach the bottom rails:

- TopLeg_ToeKick_Back (144 x 4): screw + glue to the back face of the
  bottom rail of the top leg back wall.
- TopLeg_ToeKick_Front (144 x 4): recess 3 in from the front face of
  the top leg, screw to the bottom rail. This is the front kick board.
- TopLeg_ToeKick_RightEnd (36 x 4): the visible right end of the top
  leg, capping the toe kick area.
- LeftLeg_ToeKick_Left (84 x 4): along the LHS wall side of the short
  leg.
- LeftLeg_ToeKick_Right (84 x 4): along the room-facing side of the
  short leg, recessed 3 in.
- LeftLeg_ToeKick_FrontEnd (36 x 4): the front end of the short leg.

### Step 11: Top panels (1.5 in doubled 3/4 ply)

For each doubled panel, **glue + clamp + screw** the two plies together
BEFORE installing on the frame. Apply construction adhesive (Loctite
PL Premium) in a serpentine on the lower ply, drop the upper ply, drive
#8 x 1.25 in screws through the upper into the lower at 6 in OC.

Order of installation (work from the corner outward):

1. **TopLeg_Top_Left** (50 x 36 doubled): goes at X=0..50, covers the
   left bay including the planer-side end of the top leg. Glue + screw
   down to top rails and stretchers.
2. **Miter recess assembly**: install the 36 x 30 recess bottom
   plywood inside the blocking pocket. Then install the front + back
   lips (36 x 2 back at Y=0..2, 36 x 4 front at Y=32..36) so the
   recess opening is bounded by the lips on the front + back.
3. **TopLeg_Top_MidRight** (36 x 22): covers X=86..108 between miter
   and router.
4. **Router area sub-panels**: 4 small panels around the insert plate
   opening at X=108..132. The insert plate itself (Rockler / MLCS)
   drops INTO the cutout - the panels are the surface around the plate.
5. **TopLeg_Top_FarRight** (36 x 12): covers X=132..144.

6. **LeftLeg_Top_AbovePlaner** (36 x 6): covers Y=36..42 of the short
   leg (between top leg corner and planer cavity).
7. **Planer cavity strips** (2 x 30 x 3): the side strips of the planer
   cavity at Y=42..72.
8. **LeftLeg_Top_BetweenCavities** (36 x 12): Y=72..84.
9. **Saw cavity strips** (2 x 32 x 2): Y=84..116.
10. **LeftLeg_Top_End** (36 x 4): Y=116..120.

After this step, the top is complete except for the planer cavity
(left fully open for the lift mechanism later) and the saw cavity
(installed in step 12 next).

### Step 12: Saw sled cleats + sled

The DeWalt DWE7491 drops into the 32 x 32 saw cavity at X=2..34,
Y=84..116. The saw sits on a sled, the sled sits on cleats.

1. Install the 4 sled cleats inside the cavity, around the perimeter
   at the cavity bottom rails (or higher - depends on where you want
   the deck height to land):
   - 2 x 32 in cleats along the back + front (Y=84 and Y=114 sides)
   - 2 x 25 in cleats along the left + right (X=2 and X=32 sides)
   The cleats sit at z = (BENCH_H - SAW_DECK_DROP) - 0.75 ≈ 23.25 in,
   so the 3/4 in sled sits on them at z = 24, and the saw body (13 in
   tall) puts the deck at 37 in.
2. The 30 x 30 saw sled drops onto the cleats. Bolt the saw to the
   sled with the saw's mounting holes. Center carefully - blade
   alignment matters more than centering.
3. Drop the sled (with saw attached) into the cavity. Confirm deck
   is flush with the surrounding bench top. Shim cleats if needed.

### Step 13: End panels + skin

Install the two end panels (36 x 33 plywood each):

- **TopLeg_EndPanel_Right** at X=144 (the right end of the top leg,
  facing the existing 3x8 bench). Glue + screw to the end stud + rails.
- **LeftLeg_EndPanel_Front** at Y=120 (the front end of the short leg).

If you want a clean visible side, add a thin (1/4 in) plywood or MDF
skin over the front face of the top leg and the room-facing face of
the short leg. Optional - the framing is exposed-OK if you don't.

### Step 14: Finish

Sand top to 120 grit. Vacuum. Apply BLO or Arm-R-Seal per the
manufacturer's directions. Let cure 24-48 hrs before putting tools
down.

---

## What's left open after this build

The **planer cavity** (X=3..33, Y=42..72) is intentionally left as a
hole in the bench top. No floor, no internal structure. When you build
the planer lift, you'll add:

- The lift mechanism + drill motor (per `planer_lift_bom.md`)
- The 28 x 28 planer sled (already cut, set aside)
- A cover panel for when the planer is stored

Until then, you can drop a temporary cover (a scrap of 3/4 ply cut to
30 x 30) over the planer hole to keep stuff from falling in.

---

## Sanity-check checklist before you move on

- [ ] Bench top is level corner-to-corner within 1/8 in over 12 ft.
- [ ] No wobble - push hard on the front edge of the top leg, it
      shouldn't move more than 1/8 in. If it does, re-tighten wall lags
      or add a diagonal brace inside one of the bays.
- [ ] Miter recess is 36 x 30 x 4 in deep with the front + back lips
      installed. Drop the miter saw in - should sit on the recess floor
      with the deck flush at 37 in (shim if needed).
- [ ] Router insert plate sits flush with the surrounding top.
- [ ] Saw sled drops in cleanly and deck is flush at 37 in.
- [ ] Planer cavity is OPEN - no obstructions inside. Bottom of frame
      is clear for the future lift mechanism.
- [ ] Toe kicks are 3 in recessed from the front faces.
- [ ] All cavities have framed studs at their boundaries - no
      cantilevered top sections.

---

## Common mistakes (don't make them)

1. **Don't install the top before anchoring the frame to the walls.**
   You won't be able to reach the lags afterward.
2. **Don't fasten the two doubled top layers together with screws
   only.** The construction adhesive is doing 80% of the work; without
   it the top will creak forever as it racks under load.
3. **Don't skip the squaring step at each frame.** Diagonals must
   match. A 1/8 in out-of-square at the bottom becomes 1/2 in by the
   time you get to the top.
4. **Don't forget to recess the toe kicks 3 in.** Flush toe kicks
   look like a kicked-shin waiting to happen.
5. **Don't permanently glue the saw or router insert plates in.**
   You'll want to remove them for service.
6. **Don't fasten through any cavity bottom that has a tool dropping
   into it.** Cleats around the perimeter only - leave the cavity
   floor open for chip drop / dust.
