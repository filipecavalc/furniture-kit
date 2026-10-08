# Contributing

Thanks for helping. Everything in the repository is in English (code, comments, docs).

## Test reports (no coding needed)

Open the folder in Claude Code and type `/kit-test`. It sets up the kit, runs the checks, designs a
small bookshelf and writes `projects/_selftest/REPORT.md` plus a zip. Open a "Platform test report"
issue, paste the report and attach the zip. macOS on Intel and Linux reports are especially welcome.

## Regional material catalogs

1. Copy `catalog/br.json` to `catalog/<country code>.json` and follow [catalog/README.md](catalog/README.md).
2. Every size you have not confirmed with a supplier gets `"verify": true`, and every material a
   `"source"` (shop, maker's catalogue or link). Don't guess.
3. Open a pull request saying where you are and which suppliers you checked.

## Document languages

Add a block to `STRINGS` in `scripts/furniture/i18n.py` (copy `"en"`, keep every key) and
`name_<lang>` entries in the catalogs you use.

## Code

- The library in `scripts/furniture/` runs inside FreeCAD's Python (no pip packages). The Blender
  scripts in `scripts/` run with `blender -b --factory-startup`. Both must keep working on Windows,
  macOS and Linux.
- Before opening a PR, run the self-test inside FreeCAD (see [TESTING.md](TESTING.md)) and include its
  summary line. If you changed rendering, attach a render made with `--samples 32`.
- The examples are also regression fixtures. Don't commit regenerated example images or PDFs unless
  the change is meant to alter them.
- Changes to the library API, the catalog format or `.assembly.json` go in [CHANGELOG.md](CHANGELOG.md);
  they are breaking when existing `build.py` files stop working.
- Keep `CLAUDE.md` and the skills in `.claude/skills/` in sync with the code: they are the
  instructions Claude Code follows.

## Versioning

[Semantic Versioning](https://semver.org/): MAJOR when existing `build.py` files, catalogs or
`.assembly.json` files need changes; MINOR for new features, catalogs or languages; PATCH for fixes.
The version is `__version__` in `scripts/furniture/__init__.py`.
