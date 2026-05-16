# Planer Vertical Lift - Hardware Bill of Materials

This is the buildable hardware spec for the planer vertical lift cavity
in the L-bench's left leg. Read before buying. There's an honest
discussion of why gas struts + drawer slides is a fussy mechanism for
this geometry, and a simpler alternative if you want to skip that whole
problem.

## Are 3D-printed brackets OK?

**No.** You're right to be skeptical.

- PLA at any practical bracket thickness will creep (slowly deform under
  sustained load) and become brittle over months. A 92 lb planer + 4 gas
  struts pulling on PLA brackets will fail in months, possibly at the
  worst moment.
- PETG is better but still not appropriate for a part that experiences
  shear + tension cycles every time you raise/lower the planer.
- Even Onyx or CF-nylon (which we assume you don't have a printer for)
  would be marginal for the strut mounts.

**Steel brackets only.** Either store-bought stamped-steel angle brackets
or simple shop-made plates from flat bar. Both are cheap.

## Reality check on the gas-strut mechanism

The plan model spec is "4 gas struts for near-neutral buoyancy, one
beside each drawer slide." That works in principle, but the geometry is
fussy:

- Sled vertical travel: ~14 in (planer top must drop below 37 in bench
  surface when stored, planer bed must rise to 37 in when working).
- Typical hardware-store gas struts have a stroke of 5-8 in. That's a
  lot less than 14.
- To use a short-stroke strut for a 14 in travel, you mount it at a
  steep angle (closer to horizontal than vertical). At a 60-degree
  angle from vertical, a 7 in stroke covers 14 in of vertical travel,
  but the vertical component of the strut's force is half of its rated
  force. So you need ~2x as much rated strut force.

**Strut spec that actually fits 14 in travel:**

- 4 struts, ~24 in extended / ~12 in compressed (12 in stroke)
- ~40-50 lb force each
- 10 mm ball-stud ends (standard automotive / hood-lift size)
- Mounted at ~30 degrees from vertical
- Total vertical lift force: 4 x 45 x cos(30) = ~156 lb (vs ~102 lb
  for planer + sled; gives ~50 lb of net upward bias for easy lifting,
  pin holds the bench down when stored)

Sources: Amazon "lift support struts" or lift-supports-depot.com. Home
Depot does **not** stock these in any useful length / force / end type
combination. Buy a 4-pack with included ball studs.

## Honest alternative: a trailer tongue jack

If the gas-strut sourcing + geometry feels fragile, here's a cheaper,
simpler, stronger option that uses one part:

- **Harbor Freight 1000 lb trailer tongue jack** (~$30). It's a hand
  crank that turns a screw to raise/lower a 1000 lb load. Designed for
  trailers; perfectly suited for lifting a 100 lb planer 14 in.
- Mount it inverted (crank handle accessible at the front of the
  cavity, screw lifting the sled).
- Drawer slides become unnecessary - the jack's screw provides positive
  vertical positioning at any height.
- No struts, no springs, no balance issues. Crank up to use, crank down
  to stow.

I'd genuinely recommend this over the gas-strut approach. It's $30,
it's overkill for the load, and there's no geometry to get wrong.

The downside: you crank by hand for the full 14 in of travel (which is
30-60 seconds). Gas struts give you near-instant lift. Your call.

## Home Depot BOM if you stick with gas struts

For mounting the struts (assumes you buy struts + ball studs together
from Amazon):

| Item | HD SKU / Spec | Qty | Approx |
| --- | --- | --- | --- |
| Simpson Strong-Tie A23 angle bracket (2 in x 1.5 in) | 100375103 | 8 | $1.50 ea |
| Heavy-duty 24 in vertical drawer slides (220 lb rated) | (not at HD - order Accuride 7434 or KV 8400 from Amazon / Woodcraft) | 4 | $35-50 ea |
| #10 x 1.5 in zinc wood screws (100 ct) | 100143031 | 1 box | $7 |
| 1/4 in x 1.5 in carriage bolts | 304097 | 16 | $0.30 ea |
| 1/4 in flat washers (100 ct) | 100052381 | 1 box | $4 |
| 1/4 in nylon-insert lock nuts (100 ct) | 100132555 | 1 box | $5 |

**Bracket layout per strut (one of 4):**
- Lower bracket: A23 angle mounted to cavity wall near floor.
  Ball stud threads through the bracket's perpendicular face.
- Upper bracket: A23 angle mounted to underside of sled.
  Ball stud threads through the bracket's perpendicular face.
- Each ball stud secured with washer + lock nut on the back side of the
  bracket.

**Bracket location on the bench (model coordinates, inches):**
- Lower-left-back: x=2.5, y=42.5, z=4 (toe-kick top)
- Lower-left-front: x=2.5, y=71.5, z=4
- Lower-right-back: x=33.5, y=42.5, z=4
- Lower-right-front: x=33.5, y=71.5, z=4
- Upper mounts on sled, 1.5 in inset from each corner, mirror-image.

## Home Depot BOM if you go with the trailer jack

| Item | HD SKU / Spec | Qty | Approx |
| --- | --- | --- | --- |
| Trailer tongue jack 1000 lb (or Harbor Freight equiv) | (HF item 38644) | 1 | $30 |
| 2 in x 2 in x 1/8 in steel angle (3 ft length) | (HD or local steel) | 1 | $15 |
| 1/4-20 x 1 in machine bolts (10-pack) | 803395 | 1 | $4 |
| 1/4-20 nuts + washers | 100132555 / 100052381 | as above | - |
| Linear bearings or 24 in drawer slides | (optional - jack provides vertical position; slides help with side-to-side stability) | 0-4 | optional |

**Mounting:** the jack screws to a 2x2 steel angle anchored to the
cavity floor. The lifting head bolts up through the sled. Sled is
constrained against tilting by 2 vertical guide bars (3/4 in steel rod
or 2 light-duty drawer slides at front and back).

## Pin lock (both designs)

Regardless of lift mechanism, you want a **positive mechanical lock**
at the working height. The bench top should NOT depend on the lift
mechanism alone to hold position - a sled that drops while you're
feeding a board through is a serious injury risk.

| Item | HD SKU / Spec | Qty | Approx |
| --- | --- | --- | --- |
| 1/2 in x 6 in steel hitch pin | 660429 | 1 | $4 |
| 1/2 in steel pipe coupling (the receiver) | 392104 | 2 | $3 ea |
| #14 x 1.5 in self-tap screws (to mount coupling) | various | 4 | - |

Mount one coupling on the cavity wall, drill a matching hole through
the sled. When sled is raised, slide the pin through the coupling and
through the sled hole. Now the sled cannot drop even if the lift
mechanism fails.

## Safety summary

- Pin lock is non-negotiable. Even with brand-new gas struts or a
  trailer jack, a mechanical pin is your last line of defense.
- Test the lock with the planer mounted but powered off, by pushing
  down on the planer firmly. The sled should not move.
- Re-tighten ball-stud nuts after the first 10 cycles (initial settling).
- If gas struts: replace at the first sign of weakening (struts lose
  force over years). Cheap. Buy 8 so you have a spare set.
