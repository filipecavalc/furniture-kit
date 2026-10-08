"""Parametric parts with material metadata.

Axes (mm): X = width (left -> right), Y = depth (front plane at y=0, positive towards the back;
anything in front of the front plane, such as drawer fronts and handles, has negative y),
Z = height (floor at z=0).

Every part gets properties in the "Furniture" group:
    Furn_Material  key in the material catalog (catalog/<region>.json)
    Furn_Type      panel | solid | profile | glass | hardware
    Furn_Grain     "" | length | width   (grain direction relative to the part)
    Furn_Section   (profiles) e.g. "RECT 40x20x1.2", "SQ 30x1.5", "ROUND 25.4x1.2", "BAR 38x6"
    Furn_Length    (profiles) length, bound to an expression
    Furn_Desc      (hardware) description for the shopping list
    Furn_Note      free note (edge banding, machining, finish)
"""
import re
import FreeCAD as App
from . import catalog

PROPS = ("Furn_Material", "Furn_Type", "Furn_Grain", "Furn_Section", "Furn_Desc", "Furn_Note")
AXES = (".Placement.Base.x", ".Placement.Base.y", ".Placement.Base.z")
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


class Project:
    def __init__(self, name, new=True, catalog_name=None, folder=None):
        """folder: project folder (default projects/<name>); outputs go to its subfolders."""
        import os
        from . import PROJECTS
        self.name = check_name(name, "project name")
        self.folder = folder or os.path.join(PROJECTS, name)
        if new:
            if name in App.listDocuments():
                App.closeDocument(name)
            self.doc = App.newDocument(name)
        else:
            self.doc = App.getDocument(name)
        self.cat = catalog(catalog_name)
        self.aliases = []
        sp = self.doc.getObject("Params")
        if sp is not None:
            self.aliases = [a for a in (sp.getAlias(c) for c in sp.getUsedCells()) if a]

    # ---------------- parameters
    def params(self, rows):
        """rows: list of (alias, value, description). Creates/updates the 'Params' spreadsheet."""
        sp = self.doc.getObject("Params")
        if sp is None:
            sp = self.doc.addObject("Spreadsheet::Sheet", "Params"); sp.Label = "Parameters"
            sp.set("A1", "Parameter"); sp.set("B1", "Value"); sp.set("C1", "Description")
        row = 2 + len(self.aliases)
        for alias, value, desc in rows:
            if alias in self.aliases:
                sp.set(alias, str(value)); continue
            if alias in RESERVED:
                raise ValueError(f"alias '{alias}' clashes with a FreeCAD constant or unit; use a descriptive name")
            sp.set(f"A{row}", alias); sp.set(f"B{row}", str(value)); sp.set(f"C{row}", desc)
            sp.setAlias(f"B{row}", alias); self.aliases.append(alias); row += 1
        self.doc.recompute()
        return sp

    def set(self, alias, value):
        self.doc.getObject("Params").set(alias, str(value)); self.doc.recompute()

    def val(self, alias):
        return float(self.doc.getObject("Params").get(alias))

    def expr(self, s):
        """Turns an expression using parameter names into a FreeCAD expression (Params.name)."""
        if isinstance(s, (int, float)):
            return str(s)
        names = sorted(self.aliases, key=len, reverse=True)
        if not names:
            return s
        return re.sub(r"(?<![\w.])(" + "|".join(map(re.escape, names)) + r")\b",
                      lambda m: "Params." + m.group(1), s)

    # ---------------- organisation
    def group(self, name, parent=None):
        check_name(name, "group name")
        g = self.doc.getObject(name)
        if g is not None and g.TypeId != "App::DocumentObjectGroup":
            raise ValueError(f"'{name}' is already a part; a group needs a different name (e.g. '{name}_Group')")
        g = g or self.doc.addObject("App::DocumentObjectGroup", name)
        g.Label = name
        if parent is not None:
            self._group(parent).addObject(g)
        return g

    def _group(self, g):
        return self.group(g) if isinstance(g, str) else g

    def _meta(self, o, material, kind, grain="", section="", desc="", note=""):
        if material not in self.cat["materials"]:
            raise KeyError(f"material '{material}' is not in the catalog")
        if grain not in GRAINS:
            raise ValueError(f"grain '{grain}' must be one of {GRAINS}")
        for pr in PROPS:
            if pr not in o.PropertiesList:
                o.addProperty("App::PropertyString", pr, "Furniture")
        o.Furn_Material = material; o.Furn_Type = kind; o.Furn_Grain = grain
        o.Furn_Section = section; o.Furn_Desc = desc; o.Furn_Note = note
        color = self.cat["materials"][material].get("color")
        if color and o.ViewObject:
            o.ViewObject.ShapeColor = tuple(color)
            if kind == "glass":
                o.ViewObject.Transparency = 60

    def _validate(self, name, group, material, grain=""):
        """Checks everything before any object is created, so an error leaves no half-made part behind."""
        self._unique(name)
        if isinstance(group, str):
            check_name(group, "group name")
            g = self.doc.getObject(group)
            if g is not None and g.TypeId != "App::DocumentObjectGroup":
                raise ValueError(f"'{group}' is already a part; a group needs a different name (e.g. '{group}_Group')")
        if material not in self.cat["materials"]:
            raise KeyError(f"material '{material}' is not in the catalog")
        if grain not in GRAINS:
            raise ValueError(f"grain '{grain}' must be one of {GRAINS}")

    def _unique(self, name):
        check_name(name, "part name")
        if self.doc.getObject(name) is not None:
            raise ValueError(f"name '{name}' is already used by a part or group; every part needs its own name")

    def _box(self, name, dims, pos):
        self._unique(name)
        b = self.doc.addObject("Part::Box", name); b.Label = name
        for prop, ex in zip(("Length", "Width", "Height"), dims):
            b.setExpression(prop, self.expr(ex))
        for prop, ex in zip(AXES, pos):
            b.setExpression(prop, self.expr(ex))
        return b

    # ---------------- part types
    def panel(self, name, group, dims, pos, material, grain=None, note=""):
        """Sheet-goods part (MDF, particleboard, plywood...). dims = (dx, dy, dz); the smallest is the
        thickness. grain: None = material default ('length' if the material has grain)."""
        has_grain = self.cat["materials"].get(material, {}).get("grain", False)
        g = grain if grain is not None else ("length" if has_grain else "")
        self._validate(name, group, material, g)
        b = self._box(name, dims, pos)
        self._meta(b, material, "panel", grain=g, note=note)
        self._group(group).addObject(b); return b

    def solid(self, name, group, dims, pos, material, grain="length", note=""):
        """Solid-wood part (final, surfaced dimensions)."""
        self._validate(name, group, material, grain)
        b = self._box(name, dims, pos)
        self._meta(b, material, "solid", grain=grain, note=note)
        self._group(group).addObject(b); return b

    def glass(self, name, group, dims, pos, material="glass_clear", note=""):
        self._validate(name, group, material)
        b = self._box(name, dims, pos)
        self._meta(b, material, "glass", note=note)
        self._group(group).addObject(b); return b

    def hardware(self, name, group, dims, pos, desc, material="hardware_metal"):
        """Simplified (box) stand-in for a bought-in hardware item."""
        self._validate(name, group, material)
        b = self._box(name, dims, pos)
        self._meta(b, material, "hardware", desc=desc)
        self._group(group).addObject(b); return b

    def profile(self, name, group, section, length, pos, axis="x", material="steel_black", note=""):
        """Metal profile / tube.
        section: 'RECT axbxwall' | 'SQ axwall' | 'ROUND diameterxwall' | 'ROUND diameter' (solid rod) |
                 'BAR axb' (solid flat bar). Stored in Furn_Section in a canonical form (larger side first).
        length: number or expression with parameters.
        pos: minimum corner of the bounding box (numbers or expressions).
        axis: direction of the length ('x', 'y' or 'z').
        RECT: 'a' goes on the 1st cross axis (x->y, y->x, z->x) and 'b' on the 2nd (x->z, y->z, z->y)."""
        kind, a, b, t, canon = parse_section(section)
        self._validate(name, group, material)
        if axis not in ("x", "y", "z"):
            raise ValueError(f"axis '{axis}' must be 'x', 'y' or 'z'")
        L = f"({length})"
        dims = lambda s1, s2: {"x": (L, s1, s2), "y": (s1, L, s2), "z": (s1, s2, L)}[axis]
        shift = lambda d: {"x": ("0", d, d), "y": (d, "0", d), "z": (d, d, "0")}[axis]

        if kind == "ROUND":
            outer = self._cylinder(name + "_out" if t else name, a / 2, L, pos, axis, a / 2)
            inner = self._cylinder(name + "_in", a / 2 - t, L, pos, axis, a / 2) if t else None
        else:
            outer = self._box(name + "_out" if t else name, dims(str(a), str(b)), pos)
            inner = None
            if t:
                ipos = [f"({pp}) + {dd}" for pp, dd in zip(pos, shift(str(t)))]
                inner = self._box(name + "_in", dims(str(a - 2 * t), str(b - 2 * t)), ipos)
        if inner is not None:
            self._unique(name)
            obj = self.doc.addObject("Part::Cut", name); obj.Label = name
            obj.Base = outer; obj.Tool = inner
            outer.ViewObject.Visibility = False; inner.ViewObject.Visibility = False
        else:
            obj = outer
        self._meta(obj, material, "profile", section=canon, note=note)
        if "Furn_Length" not in obj.PropertiesList:
            obj.addProperty("App::PropertyFloat", "Furn_Length", "Furniture")
        obj.setExpression("Furn_Length", self.expr(length))
        self._group(group).addObject(obj)
        return obj

    def _cylinder(self, name, r, length, pos, axis, center):
        """Cylinder along 'axis'; 'center' = distance from the minimum corner to the axis."""
        self._unique(name)
        c = self.doc.addObject("Part::Cylinder", name); c.Label = name
        c.Radius = r; c.setExpression("Height", self.expr(length))
        c.Placement.Rotation = {"z": App.Rotation(),
                                "x": App.Rotation(App.Vector(0, 1, 0), 90),
                                "y": App.Rotation(App.Vector(1, 0, 0), -90)}[axis]
        d = {"z": (center, center, 0), "x": (0, center, center), "y": (center, 0, center)}[axis]
        for prop, pp, dd in zip(AXES, pos, d):
            c.setExpression(prop, self.expr(f"({pp}) + {dd}"))
        return c

    # ---------------- utilities
    def parts(self, kinds=None, visible=False):
        out = []
        for o in self.doc.Objects:
            if "Furn_Type" in o.PropertiesList and (kinds is None or o.Furn_Type in kinds):
                if visible and not o.ViewObject.Visibility:
                    continue
                out.append(o)
        return out

    def recompute(self):
        self.doc.recompute()

    def dir(self, sub=None):
        """Project folder or one of its subfolders (created if missing)."""
        import os
        p = os.path.join(self.folder, sub) if sub else self.folder
        os.makedirs(p, exist_ok=True)
        return p

    def save(self, subdir="model"):
        import os
        path = os.path.join(self.dir(subdir), self.name + ".FCStd")
        self.doc.saveAs(path)
        return path


def open_project(name, folder=None):
    """A project already open in FreeCAD."""
    return Project(name, new=False, folder=folder)
