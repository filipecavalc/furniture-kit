"""Geometric checks of the model."""
import FreeCAD as App
from .i18n import T


def _visible(proj, ignore=()):
    return [o for o in proj.parts() if o.ViewObject.Visibility and o.Label not in ignore]


def collisions(proj, tol=0.01, ignore=()):
    """Pairs of parts that overlap (common volume > tol mm3). Touching does not count."""
    objs = _visible(proj, ignore)
    out = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            a, b = objs[i], objs[j]
            if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):
                continue
            v = a.Shape.common(b.Shape).Volume
            if v > tol:
                out.append((a.Label, b.Label, round(v, 1)))
    return out


def invalid(proj):
    return [o.Label for o in proj.parts() if o.Shape.isNull() or not o.Shape.isValid() or o.Shape.Volume <= 0]


def envelope(proj):
    bb = App.BoundBox()
    for o in _visible(proj):
        bb.add(o.Shape.BoundBox)
    return bb


def report(proj):
    bb = envelope(proj)
    col = collisions(proj); inv = invalid(proj)
    empty = not bb.isValid()
    lines = [f"{T('parts')}: {len(proj.parts())}",
             T("envelope", w=0 if empty else bb.XLength, d=0 if empty else bb.YLength, h=0 if empty else bb.ZLength),
             f"{T('invalid')}: {inv or T('none')}",
             f"{T('collisions')}: {col or T('none')}"]
    return "\n".join(lines)
