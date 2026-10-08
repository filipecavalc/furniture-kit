# Material catalogs

One file per region (`br.json` = Brazil). The active catalog is set in `config/local.json`
(`"catalog": "br"`). Parts reference materials by key (`mdf_white`, `pine`, `steel_black`...).

## Adding your region

1. Copy `br.json` to `<country code>.json` (e.g. `pt.json`, `us.json`, `de.json`).
2. Keep the keys you need, change names, sheet/bar sizes and thicknesses to what local suppliers sell.
3. For every value you have not confirmed with a supplier, set `"verify": true` and add a `"source"`.
   The cut list prints a warning for these. Never guess supplier data.
4. Set `"catalog": "<code>"` in `config/local.json`.

Pull requests with new regional catalogs are welcome.

## Fields

| Field | Meaning |
|---|---|
| `name` | Local name (used in documents) |
| `name_en`, `name_<lang>` | Name used when the output language matches |
| `type` | `panel`, `solid`, `profile`, `glass` or `hardware` |
| `sheet_mm` | Panel sheet size `[length, width]` |
| `thicknesses` | Thicknesses sold (mm) |
| `grain` | `true` if the panel has a grain/pattern direction |
| `bar_mm` | Stock bar length for profiles |
| `verify` | `true` = not confirmed with a supplier |
| `source` | Where the value came from |
| `color` | RGB 0-1 for the FreeCAD model |
| `render` | Blender material: `mode` `solid` / `wood` / `glass`, `color` or `light`+`dark`, `roughness`, `metal` |

`defaults` holds construction values. The library uses the saw kerfs (`panel_kerf_mm`,
`bar_kerf_mm`), the sheet edge trim (`panel_trim_mm`) and the solid-wood allowance
(`solid_allowance_mm`). Drawer slide clearance and gaps between fronts are reference values for
writing `build.py` parameters. Estimates are flagged with `bar_kerf_verify` / `slide_clearance_verify`
or, inside an object, `"verify": true`.
