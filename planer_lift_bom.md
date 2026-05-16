# Planer Vertical Lift - Hardware Bill of Materials

This is the buildable hardware spec for the planer vertical lift cavity
in the L-bench's short leg. The primary recommended mechanism is a
**Harbor Freight scissor stabilizer driven by an old drill through a
socket adapter** - cheap, strong, easy to motorize, simple geometry.

## Quick answer on PLA brackets

**Don't use them.** PLA creeps under sustained load and becomes brittle
in shear. A 92 lb planer + cyclical loading will cause failure in
months. Use steel brackets only. The mechanism below avoids the
custom-bracket problem entirely by using off-the-shelf stamped steel.

## Primary mechanism: Scissor stabilizer + drill motor

### Parts (Harbor Freight + Home Depot)

| Item | Source / SKU | Qty | Approx |
| --- | --- | --- | --- |
| HAUL-MASTER 2.5 Ton Trailer/RV Scissor Stabilizer | HF #96406 | 1 | $38 |
| Old corded or cordless drill (your shelf find) | already owned | 1 | $0 |
| 1/4" hex to 3/4" socket adapter (your jack input is most likely 3/4" or 13/16") | HD or Amazon | 1 | $5 |
| Magnetic reed switch or limit switch (for top-of-travel cutoff) | Amazon (any) | 2 | $10 ea |
| 12V relay rated for drill amperage (or auto-stop drill circuit) | Amazon | 1 | $8 |
| 1/2" x 6" steel hitch pin (for positive lock at working height) | HD #660429 | 1 | $4 |
| 1/2" pipe coupling (pin receiver) | HD #392104 | 2 | $3 ea |
| 2 in x 2 in x 1/8 in steel angle (for jack mount brackets) | HD or local steel | 1 ft | $5 |
| Lag bolts 5/16 x 2 in (mount jack base to plywood platform) | HD bulk | 8 | $4 |
| Wood screws #10 x 1.5 in (drill bracket + general assembly) | HD bulk | 1 box | $7 |

**Approximate total: $90-110**, plus the drill which you have.

### Design

The scissor jack rises straight up - parallelogram linkage keeps the
top plate parallel to the base. The screw input shaft rotates in place;
its position does not change as the jack extends. This means:

- **The drill does NOT need to float.** Mount it rigidly to a bracket
  bolted to the jack's BASE plate. The drill stays put while the jack
  raises the sled.
- Drill chuck holds a 1/4" hex socket adapter. Socket adapter holds a
  3/4" or 13/16" socket. Socket engages the jack's hex input shaft.

### Geometry

- Cavity: PLANER_X0..+W, PLANER_Y0..+D, full bench height (37 in).
- The jack base sits on a 3/4 in plywood platform inside the cavity at
  z = 4 in (above the toe-kick height).
- HF #96406 advertised max height is in the 17-23 in range (check the
  unit in store; both versions have been sold under this SKU).
- With base on platform at z=4 and jack at min height ~4.5 in, sled
  bottom starts at z ~ 8.5 in. Planer top ends at z ~ 26 in - just
  below bench surface. Cover with the planer-storage insert panel and
  the bench reads flush.
- Cranked to max, sled bottom reaches z ~ 22-27 in. Planer base sits on
  sled at ~ z=23-28. Bed (4 in above planer base) reaches z=27-32. To
  bring bed to z=37, you may need spacers between jack top and sled
  (1-9 in depending on which version of the jack you got). Measure when
  the jack is in hand.

### Safety - mandatory

1. **End-stop switches** at top and bottom of travel. Magnetic reed
   switches with magnets on the moving sled, switches mounted on the
   cavity wall. Wire them in series with the drill's power lead through
   a relay so the drill loses power at either end of travel. Otherwise:
   drill keeps spinning, jack input shaft snaps or strips socket.
2. **Drill clutch as backup.** Set the clutch torque just above the
   needed lifting torque. Clutch slips if you hit an obstruction. Both
   protections, belt-and-suspenders.
3. **Hitch pin lock at working height, non-negotiable.** Once the sled
   is at the top, slide the pin through the receiver in the cavity
   wall, through the sled. Now the sled cannot drop even if the jack
   fails. Test by pushing down on the unpowered planer - sled should
   not move.

### Drill mounting bracket

Bolted to the steel angle that anchors the jack to the cavity floor:
- Drill body cradled in a half-pipe of 1.5 in PVC or sheet-metal, with
  two hose clamps. The drill's pistol-grip rests in a cradle cut from
  a 2x4 scrap, screwed to the steel angle.
- Trigger held DOWN by a zip tie or velcro strap; the actual on/off
  is done by the relay + limit switches.
- Direction switch on the drill body remains accessible. You flip it
  by hand to reverse direction (raise vs lower).
- Alternative: foot pedal switch in series with the drill power so you
  hands-free start/stop while guiding the planer in.

## Alternative 1: Trailer tongue jack + drill motor

Same approach as the scissor stabilizer, different jack type. Tongue
jacks (e.g., Bulldog 500-1000 lb capacity) have an exposed shaft input
on top. Mount jack inverted (head down, shaft up out of the cavity), or
sideways with a 90-degree adapter. More complex to integrate than the
scissor stabilizer; same drill-motor concept. Skip unless you have a
strong reason.

## Alternative 2: Gas struts

The original spec called for 4 gas struts mounted at angle. Here's the
honest assessment if you still want to go this route:

- Sled travel ~14 in. Hardware-store gas struts have 5-8 in stroke. To
  cover 14 in with a 7 in stroke you mount at ~60 degrees from
  vertical, which halves the vertical lift component.
- Realistic spec: 4 struts, 24-30 in extended, 12-14 in stroke,
  25-30 lb force each, 10 mm ball-stud ends. Sources: lift-supports-
  depot.com, Amazon ("gas spring 30 inch 14 inch stroke 25 lb"). Home
  Depot does NOT stock this combination.
- Brand names worth searching: Suspa, Bansbach, Apexstone, StrongArm,
  BOXI. Buy a 4-pack plus 8 ball studs and 8 stamped-steel L-brackets.
- Mount geometry: ~30 degrees from vertical, lower mount at cavity
  floor corner, upper mount at sled-bottom opposite corner.

**Why this is worse than the scissor stabilizer:**
- Sourcing fussier (no HD/HF option).
- Struts weaken over years; need replacement.
- No positive position holding - drift over time as gas pressure drops.
- Counterbalance only; you still lift by hand.
- Mounting brackets need careful steel selection.

If you want the BOM anyway:

| Item | HD SKU / Spec | Qty | Approx |
| --- | --- | --- | --- |
| 4-pack gas struts 28 in / 14 stroke / 25 lb / 10 mm ball end | Amazon | 1 | $40-60 |
| 8 stamped steel L-brackets, Simpson A23 | HD #100375103 | 8 | $1.50 ea |
| Heavy-duty 24 in vertical drawer slides, 220 lb | Accuride 7434 (Woodcraft/Amazon) | 4 | $35-50 ea |
| #10 x 1.5 in zinc wood screws | HD #100143031 | 1 box | $7 |

Plus the pin lock parts from the main BOM. **Total $250-350**, vs $90
for the scissor stabilizer path.

## Safety summary (all designs)

- **Mechanical pin lock at working height. Always.** The lift mechanism
  is for raising and lowering only. The pin holds during use.
- Re-tighten all bolted joints after the first 10 cycles (initial
  settling).
- Test with the planer mounted but powered off, pushing down firmly on
  the planer. Nothing should move.
- Replace gas struts at the first sign of weakening. Buy spares.
- Inspect drill brush condition annually if going the motorized route;
  cordless drills are fine for occasional use but expect ~1 year of
  service for daily use.
