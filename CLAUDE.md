# furniture-kit

A workspace for designing furniture of any kind from a conversation: sheet goods (MDF, particleboard,
plywood, OSB), solid wood, metal (industrial), glass and combinations. The process goes from briefing
to render: parametric 3D model, checks, bill of materials, cut list, technical drawings, assembly
images, assembly animation and photo-style render.

Talk to the user in their language (see `CLAUDE.local.md`; ask if it is missing). Files in this
repository (code, comments, docs) stay in English. Generated documents follow `config/local.json`
(`"language": "en"` or `"pt-BR"`; see `scripts/furniture/i18n.py` to add one).

## Tools

- **FreeCAD** (tested 1.1.3) driven through the `freecad` MCP server (`.mcp.json`, runs with `uvx`),
  which talks to the **FreeCAD MCP addon** on port 9875. Modelling uses the kit's own library
  `scripts/furniture` (runs inside FreeCAD's Python; no system Python needed).
- **Blender** (tested 5.1.2) from the command line for renders and animations (Blender never needs
  to be opened). Optional: everything else works without it.
- Optional FreeCAD addons for manual work: Woodworking and FrameForge.

## Session start (every session)

1. Run the environment check (read-only):
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File setup/check.ps1`
   - macOS / Linux: `bash setup/check.sh`
2. `RESULT: MISSING ...`, or `TODO` for settings/profile → use the **kit-setup** skill before any
   design work. Tell the user plainly what is missing, what you can do and what they must do.
   Never install or download anything without asking first.
3. `READY` but the RPC server is not listening → start FreeCAD with the path the check printed and
   wait for port 9875, then call `mcp__freecad__get_rpc_status`:
   - Windows: `explorer.exe "<path to FreeCAD.exe>"` (mandatory in the desktop app: launched
     directly, FreeCAD runs inside the app's MSIX sandbox and does not see its real settings).
   - macOS: `open -a FreeCAD` · Linux: start the printed command in the background.
   If it still does not listen, ask the user: FreeCAD > **MCP Addon** workbench > **Start RPC Server**.
   If the `mcp__freecad__*` tools do not exist in the session, see "MCP server not connected" in
   the kit-setup skill.
4. Existing project: read `projects/<Name>/project.md` (briefing, decisions, open items) first.

## Layout

```
CLAUDE.md                this file            CLAUDE.local.md     user profile (gitignored)
config/local.json        language, catalog (gitignored; example in config/example.json)
catalog/<region>.json    materials, sheet/bar sizes, construction defaults (br.json = Brazil)
scripts/furniture/       library (runs inside FreeCAD)
scripts/render.py        render in Blender       scripts/animate_assembly.py   assembly video
setup/check.ps1 / .sh    environment check    templates/project/  new project skeleton
examples/                Drawer_Cabinet (panels, drawers, detailed drawings, animation)
                         Industrial_Table (steel profiles + solid wood, automatic dimensions)
projects/<Name>/         user projects (gitignored)
  project.md             briefing, decisions, open items, deliverables
  model/build.py         parametric model + deliverables
  model/*.FCStd *.glb    saved model and exports      references/ images/ drawings/ cutlist/ render/
```

Start every new `build.py` from one of the examples.

## Workflow for a new project

The user usually works in three phases and explains everything in plain language. Do not skip
phases: only model when they ask you to design.

0. **References (no modelling):** receive photos/screenshots/links, or research the web on request
   (styles, usual sizes, materials, makers). Summarise what each reference offers (proportions,
   joints, finish). Create the project already in this phase (skill **new-project**) and write it
   down in `project.md` > References; images the user provides go in `references/`. Download files
   from the web only with the user's permission.
1. **Idea and briefing:** translate the idea into furniture type, sizes, materials and finishes,
   hardware, and who builds it. Ask about what is open; when information is missing, propose market
   standards and record them as decisions. Confirm the summary before modelling.
2. Create/fill the project (skill **new-project**).
3. Write `projects/<Name>/model/build.py` with `build()` and `deliverables()`, using the library.
4. Run it in FreeCAD with `mcp__freecad__execute_code` (absolute path):
   `__file__ = r"<kit>/projects/<Name>/model/build.py"; exec(open(__file__, encoding="utf-8").read())`
   then `build()`. Check the screenshot and the report (collisions, invalid parts, envelope).
5. Iterate with the user by changing parameters (`pj.set("alias", value)`) or `build.py`.
6. `deliverables()` writes the bill of materials, cut list, images, drawings and `.glb` exports.
7. Render and assembly animation: skill **render**.
8. **Review visually** (read the PNGs and PDFs) before delivering. Record deliverables and open
   items in `project.md`.

## Library `furniture` (summary)

```python
from furniture import project, check, bom, cutlist, lumber, guide, images, drawing, export, selftest
pj = project.Project("Name", folder=HERE)          # new document (project.open_project(...) for an open one)
pj.params([("width", 800, "Overall width"), ...])  # 'Params' spreadsheet; use the aliases in expressions
pj.panel(name, group, (dx, dy, dz), (x, y, z), "mdf_white", grain=None, note="")
pj.solid(name, group, dims, pos, "pine", grain="length")
pj.profile(name, group, "RECT 30x50x1.5", length, pos, axis="x", material="steel_black")
        # sections: "RECT axbxwall", "SQ axwall", "ROUND diameterxwall", "BAR axb"
pj.glass(name, group, dims, pos, "glass_clear")
pj.hardware(name, group, dims, pos, "description for purchase", material="hardware_metal")
pj.set("alias", v) / pj.val("alias") / pj.parts() / pj.dir("images") / pj.save()
check.report(pj) / collisions(pj) / envelope(pj)
bom.generate(pj, folder)                           # CSV + MD + spreadsheet in the document
cutlist.generate(pj, folder)                       # sheets (guillotine, grain) + bars (linear) as PDF
lumber.generate(pj, folder, stock, extra_width={"tongue and groove": 8})
        # solid wood: which boards/battens to buy and how to rip and crosscut them
guide.pdf(file, title, pages)                      # assembly guide: images + parts + fixing + steps
images.standard_views / assembly (steps with options {"el":, "hide": [...]}) / exploded / contact_sheet / cam / save / crop
drawing.page / view / dim / envelope_dims / text / label / table / export_pdf
export.glb(pj, file)                               # .glb + .materials.json for the render
export.assembly(pj, glb, steps, title, final)      # .assembly.json for the animation
selftest.run()                                     # builds the examples in projects/_selftest (see TESTING.md)
```

Dims and positions accept numbers or expressions with the aliases (e.g. `"width - 2*thk"`).
After changing the library run `furniture.reload()` (every `build.py` already does it).

## Conventions

- Units in mm. Axes: X = width (left→right), Y = depth (front plane at y=0, positive towards the
  back; fronts and handles have negative y), Z = height (floor at z=0).
- Every part is created through the library methods so it carries material and type (`Furn_*`).
  A part without them is left out of the bill of materials, cut list and render.
- Material always by key from the active catalog. New material: add it there with its source.
  Without supplier confirmation mark `"verify": true`; the cut list warns about it.
- Grain: `length` = along the longer side of the part; `width` = along the shorter side. Parts with
  grain are never rotated in the cut list.
- Parameter aliases must not be FreeCAD constants or unit symbols (`e`, `pi`, `mm`, `m`, `in`, `h`,
  `t`, `H`, `W`...; full list in `RESERVED`, `scripts/furniture/project.py`, which rejects them).
  Prefer descriptive names (`thk`, `width`, `height`).
- Part names without accents or spaces, unique in the project, and different from group names
  (part `Back` cannot live in a group called `Back`; use `Back_Panel`). Drawing texts and captions may
  use accents.
- Everything a user reads comes out in the documents language (`config/local.json`): part names
  (they appear in the bill of materials and cut lists: `Lateral_Esq` for pt-BR, `Side_Left` for en),
  `note=` texts, drawing titles and notes, assembly captions and guide pages written in `build.py`.
  The examples are in English; translate those texts when you start from them.

## Quality rules

- Never invent supplier data (sheet sizes, bar lengths, hardware, prices). Research and cite the
  source, or mark it "to be confirmed".
- Always run the collision check after building or changing the model.
- Never deliver a file without opening and checking it (read the PNG/PDF).
- Joinery, drilling and edge banding depend on who builds it: ask, or leave an explicit open item;
  never assume silently.
- Shopping lists use the trade names and units of the user's region (profile). Screws with the full
  commercial specification needed to buy them; pocket-hole joints use pocket-hole screws.

## Technical pitfalls

- If an `execute_code` call fails, everything defined in it is lost: run `build.py` again.
- TechDraw: views compute edges in the background (`drawing.wait()` before dimensioning); set text
  X/Y only after `addView`; the page must be opened before exporting the PDF (otherwise no frame);
  vertex coordinates come in real mm, centred on the view.
- The active FreeCAD window may be a drawing: `images.use(pj)` picks the right 3D view.
- Blender: use absolute paths for outputs (relative ones may land elsewhere).
- Windows + Claude desktop app (MSIX; observed, not in the Claude Code docs): files written by Claude
  under `%APPDATA%` go to a private copy that FreeCAD does not see. Prepare files inside the kit folder
  and ask the user to move them.
- If reading a PDF with a page range fails, read the whole file.

## Known limitations

- Solid-wood joinery (mortise and tenon, dovetail), mitred profiles and drilling (32 mm system, cam
  locks) are not in the library yet: model them in `build.py` with Part, or use the Woodworking /
  FrameForge addons manually.
- Edge banding is not calculated automatically (use `note=` on the parts).
- Render wood is procedural (approximate colour and grain), not the manufacturer's texture.
- Drawing layouts are per project: if sizes change a lot, adjust positions and scale in `build.py`.
- Tested on Windows 11 and macOS on Apple Silicon (see TESTING.md). macOS on Intel and Linux should
  work but are untested: tell the user, and suggest `/kit-test` if they want to help.
