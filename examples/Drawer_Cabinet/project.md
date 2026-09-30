# Drawer cabinet

Example project: panel furniture with two drawers and a worktop.

## Briefing
- Furniture type: base cabinet with 2 drawers and a worktop
- Room / use: not defined (example)
- Size: 800 x 593 x 900 mm (W x D x H, with worktop and fronts)
- Materials and finishes: carcass white MDF 18; fronts woodgrain MDF 18; worktop dark woodgrain MDF 25;
  drawer boxes white MDF 15; backs and drawer bottoms white MDF 6
- Hardware / components: 2 pairs of 500 mm full-extension slides; 2 handles 160 mm (128 mm spacing)
- Who builds it: not defined

## Decisions
- Usual cabinet-making sizes chosen without a client briefing (example).
- Plinth set back 50 mm; 100 mm top rails instead of a full top panel.

## Open items
- Exact woodgrain MDF pattern (maker/colour).
- Carcass joinery (cam locks, dowels or screws) and drilling.
- Edge banding: which edges.

## Deliverables
- `cutlist/`: bill of materials (CSV/MD) and sheet cut list (PDF)
- `drawings/`: assembly drawing and drawer/parts drawing with dimensions
- `images/`: standard views, assembly steps, exploded view, contact sheets
- `render/`: photo-style render
- `model/build.py`: parametric model; `deliverables()` also exports `.glb` and `.assembly.json`
