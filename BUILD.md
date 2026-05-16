# BUILD - Master Build Plan and Bill of Materials

One-stop reference for actually building the woodshop. Pulls together
the auto-generated cutlists, the hardware BOMs, and the consumables
that aren't tracked in any other file.

## How to use this document

1. **Read** `build_sequence.md` first. That tells you the order of
   operations across the whole shop (electrical -> dust -> bench -> tool
   integration -> validation). Don't skip phases.
2. **Buy the materials** listed below. Tabs in this file:
   - Lumber and sheet goods (from `l_bench_cutlist.csv`)
   - Hardware for the bench itself (this file, section "Bench Hardware")
   - Planer lift hardware (`planer_lift_bom.md`)
   - Dust collection (this file, section "Dust Collection BOM")
   - Electrical (your electrician sizes this - see `build_sequence.md`)
   - Consumables (this file)
3. **Print** `l_bench_partsheets.svg` to plan plywood cuts on the
   driveway before any sawdust flies.
4. **Reference during build:** `l_bench_objects.csv` has every part
   with its X, Y, Z position and dimensions for assembly.

## Source files this BUILD aggregates

| File | What's in it |
| --- | --- |
| `build_sequence.md` | Phase-by-phase build order. **Read first.** |
| `l_bench_cutlist.csv` | Every framing and sheet-good piece, with quantity and dimensions, auto-generated from the CAD model. |
| `l_bench_objects.csv` | Every named part with X/Y/Z position - use during assembly. |
| `l_bench_partsheets.svg` | Visual nesting diagram for plywood cuts. |
| `l_bench.svg` | Plan view of the L-bench. |
| `l_bench.dae` / `.obj` | 3D model (open in FreeCAD, Blender, or any DAE viewer). |
| `woodshop_layout_readme.md` | Shop-level context: floor plan, clearances, dust path. |
| `woodshop_layout.svg` | Plan view of the whole shop. |
| `woodshop_layout_objects.csv` | Every shop-level object with position. |
| `planer_lift_bom.md` | Scissor stabilizer + drill mechanism BOM and safety notes. |

---

## Lumber and sheet goods - rolled up from cutlist

Numbers below come from `l_bench_cutlist.csv` with a 30% waste factor
for cross-cuts, defects, and mistakes. **Buy long, cut short.**

### Dimensional lumber

| Item | Quantity | Notes |
| --- | --- | --- |
| 2x4 x 8 ft SPF stud | **26** | Studs, rails, cross stretchers, sled cleats, blocking. Pick straight ones - reject bowed boards at the rack. |
| 2x4 x 12 ft SPF | **2** | The two 144 in front+back top rails on the top leg. (Or splice two 8 ft boards on a stud - cleaner to use one piece.) |

**Cost estimate:** ~$80 at current SPF prices ($3 / 8 ft, $7 / 12 ft).

### Sheet goods

| Item | Quantity | Notes |
| --- | --- | --- |
| 3/4 in birch or sande plywood, 4 x 8 sheet | **6-7** | Bench tops are doubled 3/4 (= 1.5 in). Panels, toe kicks, end caps, sleds, router cabinet. Birch is nicer; sande or AC is half the price. |
| 3/4 in MDF or hardboard, 4 x 8 sheet (optional) | **1** | Alternative for the very top sacrificial layer - cheaper to replace when chewed up. |

**Cost estimate:** ~$420-560 (birch is $60-80/sheet at HD, sande is
$40-50/sheet, MDF is $35/sheet). Sourcing from a lumber yard instead
of HD typically saves 20-30%.

---

## Bench hardware

Not tracked in the cutlist - buy separately.

### Fasteners

| Item | Quantity | HD SKU example | Approx |
| --- | --- | --- | --- |
| #9 x 2.5 in construction screws (frame to frame, top deck to frame) | **1 lb box (~250 ct)** | GRK R4, SPAX, or HD #198975 | $35 |
| #8 x 1.25 in wood screws (toe kicks, end panels) | **1 lb box** | HD bulk | $10 |
| 1/4 x 3.5 in lag screws (frame to wall studs) | **8** | HD #279234 | $5 |
| 1/4 in flat washers | **8** | HD bulk | $1 |
| 3/8 x 4 in lag screws (Husky chest tie-down to bench frame) | **4** | HD #279238 | $4 |
| Construction adhesive (Loctite PL Premium or equivalent) | **2 tubes** | HD #100050168 | $14 |
| Wood glue (Titebond II or III) | **1 quart** | HD #100179104 | $13 |

**Total fasteners + glue: ~$82.**

### Finish (optional but recommended)

| Item | Quantity | Notes | Approx |
| --- | --- | --- | --- |
| BLO (boiled linseed oil) or General Finishes Arm-R-Seal | **1 quart** | For the bench top - protects but is renewable. Skip polyurethane (chips and is hard to refresh). | $20 |
| Mineral spirits | **1 quart** | Thinning + cleanup | $10 |
| Foam brushes / lint-free rags | bulk | | $10 |

**Total finish: ~$40.**

---

## Dust collection BOM

Not modeled in detail in the CAD. Sizes assume the Harbor Freight
1800 CFM collector and 4 in trunk that's already in the shop plan.

| Item | Quantity | Notes | Approx |
| --- | --- | --- | --- |
| 4 in S&D PVC pipe, 10 ft | **3** | Main trunk and branches. ASTM D2729. | $12 ea |
| 4 in 45-degree wye | **4** | One per tool drop - use wyes, not tees | $14 ea |
| 4 in 45-degree elbow | **4** | For direction changes | $9 ea |
| 4 in long-radius 90 elbow | **2** | Only where 45s won't work | $13 ea |
| 4 in blast gate, aluminum | **4** | One per tool: miter, router, planer, table saw | $14 ea |
| 4 in to 2.5 in reducer | **2** | For tool ports that aren't 4 in (miter, router) | $9 ea |
| 4 in flex hose, 6 ft | **2** | Last 2 ft to each tool | $20 ea |
| 4 in hose clamps | **8** | At every flex-to-rigid joint | $3 ea |
| Pipe hangers / strap (10 ct) | **2 packs** | Hangs trunk from ceiling/wall | $10 ea |
| Bare copper grounding wire, 14 ga, 25 ft | **1 spool** | Static bonding - **ask your electrician** before assuming PVC is OK | $20 |
| Pipe sealant + foil tape | each 1 | At every joint, sealed not glued (for future changes) | $12 |

**Dust collection total: ~$280-320.**

> **Read the static-bonding warning in `build_sequence.md`** before
> committing to PVC vs metal. Code authorities and your electrician
> may require metal duct.

---

## Electrical

Sizing and circuit count is your electrician's call. Plan with them
using `build_sequence.md` Phase 2 as the spec. Typical materials:

- 12/2 Romex - several hundred feet
- 4-5 dedicated 20A circuits + breakers
- 1 dedicated 240V circuit (planer, optional)
- 8-10 outlet boxes at z=44 in along walls
- Ceiling outlet for air filter
- Switches for lights

**Budget: $400-800 for materials, $1,500-3,000 for electrician labor**
depending on your area and panel capacity.

---

## Tool integration hardware

| Item | Quantity | Notes | Approx |
| --- | --- | --- | --- |
| Router insert plate, 11.75 x 9.25 in phenolic | **1** | Rockler, Woodpeckers, MLCS. Get matching levelers. | $80 |
| Router plate levelers (set of 4) | **1 set** | Comes with most plates | included |
| Insert ring set for router plate | **1 set** | 4-6 rings for different bit sizes | $30 |
| T-track for fence rails (4 ft) | **2** | Optional but useful for miter saw stops | $20 ea |
| Heavy-duty cabinet feet or 3/4 in HDPE pucks (under frame contact points) | **6** | If concrete floor is uneven | $15 |

**Tool integration: ~$165.**

---

## Planer vertical lift

See `planer_lift_bom.md` for the full BOM and safety notes.

**Summary cost:** ~$90 for the scissor-stabilizer + drill design,
~$280 for the gas-strut alternative.

---

## Master cost rollup

| Category | Low | High |
| --- | --- | --- |
| Lumber (SPF) | $75 | $90 |
| Sheet goods (6-7 sheets ply) | $300 | $560 |
| Fasteners + adhesives | $75 | $90 |
| Finish | $35 | $50 |
| Dust collection | $260 | $320 |
| Planer lift | $90 | $110 |
| Tool integration hardware | $145 | $200 |
| **Subtotal (bench + dust + lift, you build it)** | **$980** | **$1,420** |
| Electrical materials | $400 | $800 |
| Electrician labor | $1,500 | $3,000 |
| **Total including electrical** | **$2,880** | **$5,220** |

Existing tools (DeWalt saws, planer, HF dust collector, Husky chests,
air filter) are assumed to already be on-hand and are not in this total.

---

## Time estimate

Assuming you've built workshop cabinetry before and are working
weekends:

| Phase | Weekend-days |
| --- | --- |
| 1 - Cleanout + measurement | 0.5 |
| 2 - Electrical (with electrician) | 1-2 |
| 3 - Dust collection mounting | 1.5 |
| 4 - L-bench framing | 2 |
| 5 - Tool integration (saws, router, planer lift) | 2-3 |
| 6 - Lighting + air filter | 0.5 |
| 7 - Curtain | 0.5 |
| 8 - Validation + punchlist | 1 |
| **Total** | **9-11 weekend days** |

First-timer or no helper: double it.

---

## Pre-build checklist

Don't start cutting until **all** of these are true:

- [ ] Room dimensions confirmed to within 1/4 in (Phase 1)
- [ ] Tool deck heights physically measured, not assumed
- [ ] Electrician has walked the space and quoted
- [ ] PVC vs metal duct decision made with electrician input
- [ ] All sheet goods + lumber on-site, acclimated 48 hours
- [ ] Existing Husky chests measured (manufacturer specs vary slightly)
- [ ] Router insert plate purchased - cavity size depends on the plate
- [ ] Scissor stabilizer purchased and dry-fit measured (HF #96406 has
      come in two travel-height variants)
- [ ] Cross-check `l_bench.svg` against the wall the bench will sit on
- [ ] Driveway / garage cleared as a layout + cutting station
