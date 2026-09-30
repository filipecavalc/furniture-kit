"""Technical drawings (TechDraw) from scripts.

Lessons learned:
- view edges/vertices are computed in the background: call wait() before adding dimensions;
- set X/Y of annotations only AFTER page.addView;
- the page must be open in the GUI before exporting the PDF (otherwise it comes out without the frame);
- vertex coordinates come in real mm, centred on the view; X/Y of dimensions are paper mm
  relative to the view centre.
Useful directions: front (0,-1,0); top (0,0,1); left side (-1,0,0) with xdir (0,-1,0);
right side (1,0,0) with xdir (0,1,0); perspective (1,-1,1).
"""
import os, time
import FreeCAD as App
import FreeCADGui as Gui
from .i18n import T

TEMPLATES = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "ISO")


def wait(cycles=20):
    for _ in range(cycles):
        Gui.updateGui(); time.sleep(0.2)


def page(proj, name, label, texts, template="A3_Landscape_ISO5457_minimal.svg"):
    doc = proj.doc
    if doc.getObject(name):
        old = doc.getObject(name)
        names = [v.Name for v in old.Views]
        tpl_name = old.Template.Name if old.Template else None
        for n in names:
            if doc.getObject(n): doc.removeObject(n)
        doc.removeObject(name)
        if tpl_name and doc.getObject(tpl_name): doc.removeObject(tpl_name)
    pg = doc.addObject("TechDraw::DrawPage", name); pg.Label = label
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Tpl_" + name); tpl.Template = os.path.join(TEMPLATES, template)
    pg.Template = tpl
    et = dict(tpl.EditableTexts)
    base = {"creator": "", "approval_person": "", "language_code": T("drawing_lang"), "general_tolerances": "+/- 1 mm",
            "date_of_issue": time.strftime(T("date")), "revision_index": "A", "legal_owner_1": ""}
    base.update(texts)
    et.update({k: v for k, v in base.items() if k in et})
    tpl.EditableTexts = et
    return pg


def view(pg, name, sources, direction, x, y, scale, xdir=None):
    doc = pg.Document
    v = doc.addObject("TechDraw::DrawViewPart", name); pg.addView(v)
    v.Source = sources; v.Direction = App.Vector(*direction)
    if xdir: v.XDirection = App.Vector(*xdir)
    v.ScaleType = "Custom"; v.Scale = scale; v.X, v.Y = x, y
    return v


def vertices(v):
    pts, i = [], 0
    while True:
        try: p = v.getVertexByIndex(i).Point
        except Exception: break
        pts.append((i, round(p.x, 2), round(p.y, 2))); i += 1
    return pts


def extremes(v):
    pts = vertices(v)
    xs = [p[1] for p in pts]; ys = [p[2] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def vertex_id(v, x, y, tol=0.6):
    c = [i for i, px, py in vertices(v) if abs(px - x) < tol and abs(py - y) < tol]
    if not c:
        raise ValueError(f"vertex not found in {v.Name}: ({x}, {y})")
    return c[0]


def dim(pg, v, p1, p2, kind, lx, ly):
    """kind: DistanceX | DistanceY | Distance. p1/p2: coordinates (real mm) of view vertices."""
    d = pg.Document.addObject("TechDraw::DrawViewDimension", "Dim"); d.Type = kind
    d.References2D = [(v, f"Vertex{vertex_id(v, *p1)}"), (v, f"Vertex{vertex_id(v, *p2)}")]
    pg.addView(d); d.X, d.Y = lx, ly
    return d


def envelope_dims(pg, v, x_side="top", y_side="left", gap=13):
    """Dimensions the overall width and height of the view from its extreme vertices."""
    pts = vertices(v); x0, x1, y0, y1 = extremes(v); s = v.Scale
    a = next(p for p in pts if abs(p[1] - x0) < 0.01); b = next(p for p in pts if abs(p[1] - x1) < 0.01)
    c = next(p for p in pts if abs(p[2] - y0) < 0.01); d = next(p for p in pts if abs(p[2] - y1) < 0.01)
    ly = (y1 * s + gap) if x_side == "top" else (y0 * s - gap)
    lx = (x0 * s - gap) if y_side == "left" else (x1 * s + gap)
    return (dim(pg, v, a[1:], b[1:], "DistanceX", 0, ly), dim(pg, v, c[1:], d[1:], "DistanceY", lx, 0))


def text(pg, lines, x, y, size=4.0, width=None):
    a = pg.Document.addObject("TechDraw::DrawViewAnnotation", "Text"); pg.addView(a)
    a.Text = lines if isinstance(lines, list) else [lines]; a.TextSize = size
    if width: a.MaxWidth = width
    a.X, a.Y = x, y
    return a


def label(pg, v, txt, dy):
    return text(pg, txt, v.X.Value, v.Y.Value + dy)


def table(pg, sheet, x, y, end="I30", size=10.0):
    t = pg.Document.addObject("TechDraw::DrawViewSpreadsheet", "Table"); pg.addView(t)
    t.Source = sheet; t.CellStart = "A1"; t.CellEnd = end; t.TextSize = size; t.X, t.Y = x, y
    return t


def export_pdf(pg, path):
    import TechDrawGui
    pg.Document.recompute(); wait(10)
    pg.ViewObject.doubleClicked(); wait(10)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    TechDrawGui.exportPageAsPdf(pg, path)
    return path
