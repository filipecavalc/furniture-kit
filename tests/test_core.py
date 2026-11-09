"""Names, parameter aliases, grain values and profile sections (furniture.core)."""
import sys
import types

import pytest

from furniture import core


# ------------------------------------------------------------------ names
@pytest.mark.parametrize("name", ["Side_Left", "Lateral_Esq", "_tmp", "A1", "Shelf_2", "x"])
def test_check_name_accepts_valid_names(name):
    assert core.check_name(name) == name


@pytest.mark.parametrize("name, suggestion", [
    ("Side Left", "Side_Left"),          # space
    ("Lateral-Esq", "Lateral_Esq"),      # hyphen
    ("1Shelf", "Shelf"),                 # leading digit
    ("Prateleira Média", "Prateleira_M_dia"),   # accent
    ("9", "Name"),                       # nothing usable left
    ("", "x"),
    (None, "x"),
])
def test_check_name_rejects_invalid_names_with_a_suggestion(name, suggestion):
    with pytest.raises(ValueError) as e:
        core.check_name(name, "part name")
    msg = str(e.value)
    assert msg.startswith(f"part name '{name}'")
    assert "use only letters, digits and '_'" in msg
    assert f"(e.g. '{suggestion}')" in msg


def test_check_name_suggestion_is_itself_valid():
    for bad in ("Side Left", "1Shelf", "Lateral-Esq", "Prateleira Média", "9", "-1a"):
        with pytest.raises(ValueError) as e:
            core.check_name(bad)
        suggestion = str(e.value).rsplit("(e.g. '", 1)[1].rstrip("')")
        assert core.check_name(suggestion) == suggestion


# ------------------------------------------------------------------ aliases
@pytest.mark.parametrize("alias", ["e", "pi", "mm", "m", "in", "h", "t", "H", "W", "deg", "kg"])
def test_reserved_aliases_are_rejected(alias):
    with pytest.raises(ValueError, match="clashes with a FreeCAD constant or unit"):
        core.check_alias(alias)


@pytest.mark.parametrize("alias", ["width", "height", "thk", "depth", "n_shelves", "w", "top_len"])
def test_descriptive_aliases_are_accepted(alias):
    assert core.check_alias(alias) == alias


def test_every_reserved_name_is_rejected():
    for alias in core.RESERVED:
        with pytest.raises(ValueError):
            core.check_alias(alias)


def test_reserved_list_covers_the_names_documented_in_claude_md():
    assert {"e", "pi", "mm", "m", "in", "h", "t", "H", "W"} <= core.RESERVED


# ------------------------------------------------------------------ grain
@pytest.mark.parametrize("grain", ["", "length", "width"])
def test_check_grain_accepts_known_values(grain):
    assert core.check_grain(grain) == grain


@pytest.mark.parametrize("grain", ["Length", "along", None, "x"])
def test_check_grain_rejects_other_values(grain):
    with pytest.raises(ValueError, match="must be one of"):
        core.check_grain(grain)


# ------------------------------------------------------------------ sections
@pytest.mark.parametrize("section, expected", [
    ("RECT 30x50x1.5", ("RECT", 30, 50, 1.5, "RECT 50x30x1.5")),
    ("RECT 50x30x1.5", ("RECT", 50, 30, 1.5, "RECT 50x30x1.5")),   # same tube, same stock item
    ("rect 30x50x1,5", ("RECT", 30, 50, 1.5, "RECT 50x30x1.5")),   # lower case, decimal comma
    ("SQ 50x2", ("SQ", 50, 50, 2, "SQ 50x2")),
    ("sq 20X1,2", ("SQ", 20, 20, 1.2, "SQ 20x1.2")),
    ("ROUND 25.4x1.2", ("ROUND", 25.4, 25.4, 1.2, "ROUND 25.4x1.2")),
    ("ROUND 12", ("ROUND", 12, 12, None, "ROUND 12")),             # solid round bar
    ("BAR 6x38", ("BAR", 6, 38, None, "BAR 38x6")),
    ("BAR 38x6", ("BAR", 38, 6, None, "BAR 38x6")),
])
def test_parse_section(section, expected):
    assert core.parse_section(section) == expected


@pytest.mark.parametrize("section", [
    "", "RECT", "RECT30x50x1.5", "RECT 30x50", "RECT 30x50x1.5x2", "SQ 30", "BAR 38",
    "ROUND 10x1x1", "HEX 10x1", "SQ axb", "RECT 30 x 50 x 1.5",
])
def test_parse_section_rejects_malformed_specs(section):
    with pytest.raises(ValueError, match="invalid section"):
        core.parse_section(section)


@pytest.mark.parametrize("section", ["SQ 30x15", "SQ 30x20", "RECT 30x50x15", "ROUND 10x5", "SQ 30x0", "RECT 30x50x-1"])
def test_parse_section_rejects_a_wall_too_thick_or_not_positive(section):
    with pytest.raises(ValueError, match="wall is too thick"):
        core.parse_section(section)


# ------------------------------------------------------------------ backwards compatibility
def test_project_module_reexports_the_core_rules(monkeypatch):
    """build.py files call project.check_name / project.parse_section / project.RESERVED."""
    monkeypatch.setitem(sys.modules, "FreeCAD", types.ModuleType("FreeCAD"))   # project.py imports it at load
    monkeypatch.delitem(sys.modules, "furniture.project", raising=False)
    from furniture import project
    for attr in ("RESERVED", "GRAINS", "check_name", "check_alias", "check_grain", "parse_section"):
        assert getattr(project, attr) is getattr(core, attr), attr
    sys.modules.pop("furniture.project", None)
