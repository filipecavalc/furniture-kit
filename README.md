# furniture-kit

Design furniture by describing it in plain language. This kit turns a conversation into a parametric
3D model in FreeCAD and, from it, the documents you need to build: bill of materials, cut lists,
technical drawings with dimensions, assembly images, an assembly video and photo-style renders.

It covers sheet goods (MDF, particleboard, plywood, OSB), solid wood, metal profiles (industrial
style), glass and combinations of them.

| Render | Assembly steps |
|---|---|
| ![Drawer cabinet render](examples/Drawer_Cabinet/render/Drawer_Cabinet_3q_right.png) | ![Assembly steps](examples/Drawer_Cabinet/images/SHEET_assembly.png) |
| ![Industrial table render](examples/Industrial_Table/render/Industrial_Table_3q_right.png) | [Drawing (PDF)](examples/Drawer_Cabinet/drawings/Drawer_Cabinet_Sheet1_Assembly.pdf) · [Cut list (PDF)](examples/Drawer_Cabinet/cutlist/Drawer_Cabinet_Cut_List.pdf) · [Bill of materials](examples/Drawer_Cabinet/cutlist/Drawer_Cabinet_Bill_of_Materials.md) |

## How it works

You talk to [Claude Code](https://code.claude.com/docs/en/overview) (desktop app or terminal) with
this folder open. The instructions in `CLAUDE.md` and `.claude/skills/` tell it how to work: gather
references, turn your idea into a briefing, write the parametric model with the kit's library
(`scripts/furniture`), run it in **FreeCAD** through the FreeCAD MCP server, check it for collisions,
and generate the documents. **Blender** renders the images and the assembly video from the command
line.

## Getting started

You do not need to install Python, Git or anything else beforehand. On the first run the assistant
checks your computer and walks you through what is missing.

| Step | You do | The assistant does |
|---|---|---|
| 1. Claude Code | Install the [desktop app](https://claude.com/download) or the [CLI](https://code.claude.com/docs/en/setup) and sign in (needs a plan that includes Claude Code) | - |
| 2. Get the kit | **Code > Download ZIP** on this page and extract it (e.g. to Documents), or `git clone` it | - |
| 3. Open it | Open the folder in Claude Code, accept the **trust** prompt and approve the `freecad` server | Reads `CLAUDE.md` and runs the read-only environment check |
| 4. Programs | Install FreeCAD, uv and (optionally) Blender from the official links it gives you, or let it do it | Tells you exactly what is missing; installs only if you say yes |
| 5. FreeCAD addon | Copy one folder into FreeCAD's addon folder when asked (it opens both folders for you on Windows) and click **Start RPC Server** once | Downloads the addon with your permission and checks it is in the right place |
| 6. Profile | Answer a few questions: language, country, who builds, which tools you have | Saves `config/local.json` and `CLAUDE.local.md` (both stay on your computer) |
| 7. Test | - | Builds an example, shows it, and a quick render if Blender is installed |

Administrator prompts (Windows "Yes/No", macOS password) can only be answered by you.

After that, just describe what you want: "a shoe cabinet 90 cm wide for the hallway, white MDF,
two doors". Send photos or links as references if you have them.

### What the folder trust allows

Accepting the trust prompt enables `.mcp.json` (starts the FreeCAD MCP server with `uvx`) and the
permissions in `.claude/settings.json`: the assistant may run code inside FreeCAD and the environment
check without asking each time. Everything else (installing, downloading, writing outside the
project) still asks you first.

## What you get per project

- `project.md`: references, briefing, decisions, open items, deliverables
- `model/build.py`: parametric model (change a parameter, everything updates)
- `cutlist/`: bill of materials (CSV/Markdown), sheet cut list with grain direction, bar cut list,
  solid-wood buying and ripping plan
- `drawings/`: technical drawings (PDF) with dimensions
- `images/`: standard views, exploded view, step-by-step assembly images, assembly guide (PDF)
- `render/`: photo-style renders and the assembly video (MP4)

## Languages and regions

- Conversation: any language; the assistant replies in yours.
- Generated documents: English or Brazilian Portuguese (`config/local.json`). Adding a language is a
  single dictionary in `scripts/furniture/i18n.py`.
- Materials: `catalog/<region>.json`. Only Brazil (`br.json`) exists today; the setup can help you
  create your region's catalog, marking every size not confirmed with a supplier. See
  [catalog/README.md](catalog/README.md). Contributions welcome.

## Status

- Tested on Windows 11 with FreeCAD 1.1.3, Blender 5.1.2 and uv 0.11.
- macOS and Linux: the library, render scripts and checks are written to be cross-platform, but have
  not been tested on real machines yet. You can help: see [TESTING.md](TESTING.md) (run `/kit-test`).
- Newer FreeCAD/Blender versions will probably work; the check tells you when yours differs from
  the tested one.

## Limitations

- Solid-wood joinery (mortise and tenon, dovetail), mitred profiles and drilling patterns (32 mm
  system, cam locks) are not automated yet; they can be modelled per project.
- Edge banding is recorded as notes, not calculated.
- Render wood is procedural (approximate colour and grain), not the manufacturer's texture.
- Supplier data (sheet sizes, prices) is never guessed: unconfirmed values are flagged.

## Repository layout

```
CLAUDE.md                  instructions for the assistant
.claude/skills/            kit-setup, new-project, render, kit-test
.mcp.json                  FreeCAD MCP server
setup/check.ps1, check.sh  read-only environment check
scripts/furniture/         modelling library (runs inside FreeCAD)
scripts/render.py          photo-style render (Blender)
scripts/animate_assembly.py  assembly video (Blender)
catalog/                   material catalogs per region
templates/project/         skeleton for new projects
examples/                  Drawer_Cabinet, Industrial_Table
projects/                  your projects (not versioned)
```

## Credits

- [FreeCAD](https://www.freecad.org/) and [Blender](https://www.blender.org/)
- [freecad-mcp](https://github.com/neka-nat/freecad-mcp) (FreeCAD MCP server and addon)
- [uv](https://docs.astral.sh/uv/)
- Optional FreeCAD addons: [Woodworking](https://github.com/dprojects/Woodworking), [FrameForge](https://github.com/lukh/frameforge)

## License

[MIT](LICENSE)
