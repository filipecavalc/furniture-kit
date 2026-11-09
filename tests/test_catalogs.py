"""Material catalogs (catalog/*.json) and config/example.json: the fields the library and the
Blender scripts read, and the rule that supplier data always says where it came from."""
import glob
import json
import os

import pytest

from furniture import ROOT, i18n
from furniture.bom import KINDS

CATALOGS = sorted(glob.glob(os.path.join(ROOT, "catalog", "*.json")))
SUPPLIER_FIELDS = ("sheet_mm", "thicknesses", "bar_mm")      # sizes bought from a supplier


def load(path):
    with open(path, encoding="utf-8-sig") as f:              # same as furniture.catalog()
        return json.load(f)


def materials():
    return [(os.path.basename(p), key, mat) for p in CATALOGS for key, mat in load(p)["materials"].items()]


def ids(rows):
    return [f"{c}:{k}" for c, k, _ in rows]


def positive(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def rgb(v):
    return isinstance(v, list) and len(v) == 3 and all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in v)


def test_there_is_at_least_one_catalog():
    assert CATALOGS


@pytest.mark.parametrize("path", CATALOGS, ids=os.path.basename)
def test_catalog_defaults_used_by_the_library(path):
    d = load(path)["defaults"]
    for k in ("panel_kerf_mm", "panel_trim_mm", "bar_kerf_mm"):                  # cutlist.plan
        assert isinstance(d[k], (int, float)) and d[k] >= 0, k
    for k in ("length", "width", "thickness"):                                  # bom solid-wood allowance
        assert isinstance(d["solid_allowance_mm"][k], (int, float)) and d["solid_allowance_mm"][k] >= 0, k


@pytest.mark.parametrize("cat, key, mat", materials(), ids=ids(materials()))
def test_material_fields(cat, key, mat):
    assert isinstance(mat.get("name"), str) and mat["name"].strip()
    assert mat.get("type") in KINDS
    if "color" in mat:
        assert rgb(mat["color"])
    if "sheet_mm" in mat:
        assert isinstance(mat["sheet_mm"], list) and len(mat["sheet_mm"]) == 2 and all(map(positive, mat["sheet_mm"]))
    if "thicknesses" in mat:
        assert mat["thicknesses"] and all(map(positive, mat["thicknesses"]))
    if "bar_mm" in mat:
        assert positive(mat["bar_mm"])
    if "grain" in mat:
        assert isinstance(mat["grain"], bool)
    if "verify" in mat:
        assert isinstance(mat["verify"], bool)


@pytest.mark.parametrize("cat, key, mat", materials(), ids=ids(materials()))
def test_supplier_data_has_a_source(cat, key, mat):
    """catalog/README.md: never guess supplier data; unconfirmed values get verify + source."""
    if any(f in mat for f in SUPPLIER_FIELDS) or mat.get("verify"):
        assert isinstance(mat.get("source"), str) and mat["source"].strip(), "add a 'source' (shop, catalogue or link)"


@pytest.mark.parametrize("cat, key, mat", materials(), ids=ids(materials()))
def test_translated_names_match_a_document_language(cat, key, mat):
    """name_<lang> is picked by i18n.material_name; a typo (name_eng) would silently never show."""
    langs = {k.lower() for k in i18n.STRINGS} | {k.lower().split("-")[0] for k in i18n.STRINGS}
    for field in mat:
        if field.startswith("name_"):
            assert field[5:].lower() in langs, f"{field}: no document language '{field[5:]}' in i18n.STRINGS"


@pytest.mark.parametrize("cat, key, mat", materials(), ids=ids(materials()))
def test_render_settings_read_by_blender(cat, key, mat):
    """scripts/render.py and animate_assembly.py: r["mode"], then light/dark (wood) or color."""
    r = mat.get("render")
    if not r:
        return                                    # Blender falls back to a default material
    assert r.get("mode") in ("solid", "wood", "glass")
    if r["mode"] == "wood":
        assert rgb(r.get("light")) and rgb(r.get("dark"))
    else:
        assert rgb(r.get("color"))
    if "roughness" in r:
        assert 0 <= r["roughness"] <= 1
    if "metal" in r:
        assert 0 <= r["metal"] <= 1


def test_example_config_points_to_a_catalog_and_a_language():
    cfg = load(os.path.join(ROOT, "config", "example.json"))
    assert os.path.exists(os.path.join(ROOT, "catalog", cfg["catalog"] + ".json"))
    assert cfg["language"] in i18n.STRINGS
