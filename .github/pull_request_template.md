## What and why

## Checklist
- [ ] Unit tests pass (`uv run --no-project --with pytest python -m pytest`); new pure logic has a test
- [ ] Self-test run inside FreeCAD: `self-test: N passed, 0 failed` (OS: ...)
- [ ] Renders/videos checked, if `scripts/render.py` or `scripts/animate_assembly.py` changed
- [ ] `CLAUDE.md`, skills and README updated if behaviour or commands changed
- [ ] CHANGELOG.md entry (say if it breaks existing `build.py`, catalogs or `.assembly.json`)
- [ ] New catalog values have a `source`; unconfirmed ones `"verify": true`
- [ ] Example images/PDFs regenerated only if intended
