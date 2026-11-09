"""Pure rules shared by the library: names, parameter aliases, profile sections.

No FreeCAD or Qt imports here, so the unit tests (tests/) run with plain Python.
project.py re-exports everything, so build.py files keep using project.check_name etc.
"""
import re

# FreeCAD expression constants and unit symbols: an alias with one of these names is read as the
# constant/unit, not as the parameter
RESERVED = {"e", "pi", "mm", "cm", "dm", "m", "km", "um", "nm", "in", "ft", "yd", "mi", "thou", "mil",
            "h", "min", "s", "ms", "g", "kg", "mg", "t", "lb", "oz", "l", "ml", "A", "V", "W", "N", "J",
            "Pa", "kPa", "MPa", "K", "C", "F", "H", "S", "T", "deg", "rad", "Hz", "mol", "cd", "ohm"}
GRAINS = ("", "length", "width")


def check_name(name, what="name"):
    """FreeCAD rewrites names with spaces, accents, '-' or a leading digit, and lookups then fail."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name or ""):
        raise ValueError(f"{what} '{name}': use only letters, digits and '_', starting with a letter "
                         f"(e.g. '{re.sub(r'[^A-Za-z0-9_]', '_', name or 'x').lstrip('0123456789_') or 'Name'}')")
    return name


def check_alias(alias):
    """A parameter alias must not be a FreeCAD constant or unit symbol (see RESERVED)."""
    if alias in RESERVED:
        raise ValueError(f"alias '{alias}' clashes with a FreeCAD constant or unit; use a descriptive name")
    return alias


def check_grain(grain):
    if grain not in GRAINS:
        raise ValueError(f"grain '{grain}' must be one of {GRAINS}")
    return grain


def parse_section(section):
    """'RECT 30x50x1.5' -> ('RECT', a, b, wall, canonical). Accepts lower case and decimal commas.
    canonical is the purchase spec used to group bars: larger side first for RECT."""
    try:
        kind, size = section.split()
        kind = kind.upper()
        n = [float(v) for v in size.lower().replace(",", ".").split("x")]
    except ValueError:
        raise ValueError(f"invalid section '{section}': use 'RECT axbxwall', 'SQ axwall', 'ROUND dxwall', 'ROUND d' or 'BAR axb'")
    if kind == "RECT" and len(n) == 3: a, b, t = n
    elif kind == "SQ" and len(n) == 2: a, b, t = n[0], n[0], n[1]
    elif kind == "BAR" and len(n) == 2: a, b, t = n[0], n[1], None
    elif kind == "ROUND" and len(n) in (1, 2): a, b, t = n[0], n[0], (n[1] if len(n) == 2 else None)
    else: raise ValueError(f"invalid section '{section}': use 'RECT axbxwall', 'SQ axwall', 'ROUND dxwall', 'ROUND d' or 'BAR axb'")
    if t is not None and (t <= 0 or min(a, b) - 2 * t <= 0):
        raise ValueError(f"section '{section}': the wall is too thick for the size")
    g = lambda v: f"{v:g}"
    if kind == "RECT": canon = f"RECT {g(max(a, b))}x{g(min(a, b))}x{g(t)}"
    elif kind == "SQ": canon = f"SQ {g(a)}x{g(t)}"
    elif kind == "BAR": canon = f"BAR {g(max(a, b))}x{g(min(a, b))}"
    else: canon = f"ROUND {g(a)}x{g(t)}" if t else f"ROUND {g(a)}"
    return kind, a, b, t, canon
