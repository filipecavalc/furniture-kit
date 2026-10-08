"""Review images from FreeCAD: standard views, assembly steps, exploded view and contact sheets.

Angles: azimuth 0 = from the front (camera at -Y looking +Y); positive turns towards the
furniture's right. Elevation in degrees above the horizon.
"""
import os, re
import FreeCAD as App
import FreeCADGui as Gui
from .i18n import font


_V = None   # 3D view in use (set by use(proj))


def use(proj):
    """Activates the project document and keeps its 3D view (the active window may be a drawing)."""
    global _V
    App.setActiveDocument(proj.doc.Name)
    gd = Gui.getDocument(proj.doc.Name)
    vs = gd.mdiViewsOfType("Gui::View3DInventor")
    _V = vs[0] if vs else gd.ActiveView
    return _V


def _view():
    if _V is not None:
        try:
            _V.getCameraNode(); return _V
        except Exception:
            pass
    vs = Gui.ActiveDocument.mdiViewsOfType("Gui::View3DInventor")
    return vs[0] if vs else Gui.ActiveDocument.ActiveView


def cam(azimuth, elevation, persp=True, view=None):
    from pivy import coin
    v = view or _view()
    v.setCameraType("Perspective" if persp else "Orthographic")
    r = App.Rotation(App.Vector(0, 0, 1), azimuth).multiply(App.Rotation(App.Vector(1, 0, 0), 90 - elevation))
    v.getCameraNode().orientation.setValue(coin.SbRotation(*r.Q))
    v.fitAll(); Gui.updateGui()


def save(path, view=None, w=1600, h=1200):
    v = view or _view()
    Gui.updateGui()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    v.saveImage(path, w, h, "White")
    return path


def original_colors(proj):
    mats = proj.cat["materials"]
    return {o.Name: tuple(mats[o.Furn_Material].get("color", (0.8, 0.8, 0.8))) for o in proj.parts()}


def show(proj, visible=None, highlight=(), highlight_color=(0.20, 0.55, 0.95)):
    """visible: list of Labels/Names (None = all). highlight: parts painted blue."""
    use(proj)
    colors = original_colors(proj)
    for o in proj.parts():
        vis = visible is None or o.Label in visible or o.Name in visible
        o.ViewObject.Visibility = vis
        o.ViewObject.ShapeColor = highlight_color if (o.Label in highlight or o.Name in highlight) else colors[o.Name]


def parts_of(proj, names, strict=False):
    """Expands group names into part Labels (recursive). Part names pass through.
    strict: raise if a name matches no part or group (catches typos in steps and offsets)."""
    out, unknown = [], []
    for n in names:
        g = proj.doc.getObject(n) or next((o for o in proj.doc.Objects if o.Label == n), None)
        if g is not None and g.TypeId == "App::DocumentObjectGroup":
            for child in g.Group:
                out += parts_of(proj, [child.Name])
        elif g is not None and "Furn_Type" in g.PropertiesList:
            out.append(g.Label)
        else:
            unknown.append(n)
    if strict and unknown:
        raise ValueError(f"no part or group named {unknown}")
    return out


def standard_views(proj, folder, prefix=""):
    use(proj); show(proj); Gui.Selection.clearSelection()
    shots = [("01_front_right", 35, 22, True), ("02_front_left", -35, 22, True), ("03_front", 0, 0, False),
             ("04_side", 90, 0, False), ("05_back", 215, 22, True), ("06_top", 0, 90, False)]
    out = []
    for name, a, e, persp in shots:
        cam(a, e, persp); out.append(save(os.path.join(folder, prefix + name + ".png")))
    cam(35, 22)
    return out


def assembly(proj, steps, folder, prefix="A"):
    """steps: list of (title, [groups or parts], azimuth[, caption[, options]]). Each step shows everything
    so far and highlights the new parts in blue. 'title' becomes the file name; 'caption' (optional) is
    the contact-sheet text. options: {"el": elevation (25), "hide": [groups or parts hidden in this image
    only, e.g. the front wall to see inside]}."""
    old = re.compile(rf"^{re.escape(prefix)}[1-9]\d*_.*\.png$")       # images of a previous run (keeps A0_ exploded view)
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if old.match(f):
                os.remove(os.path.join(folder, f))
    acc, out = [], []
    for i, step in enumerate(steps, 1):
        title, names, az = step[:3]
        caption = step[3] if len(step) > 3 else title.replace("_", " ").capitalize()
        op = step[4] if len(step) > 4 else {}
        new = parts_of(proj, names, strict=True); acc += new
        hidden = set(parts_of(proj, op.get("hide", []), strict=True))
        show(proj, [l for l in acc if l not in hidden], new); cam(az, op.get("el", 25))
        fname = re.sub(r"[^\w-]", "_", title)                  # titles become file names on every OS
        out.append((save(os.path.join(folder, f"{prefix}{i}_{fname}.png")), f"{i}. {caption}"))
    show(proj); cam(35, 22)
    return out


def exploded(proj, offsets, path, default=(0, 0, 0), azimuth=35, elevation=22):
    """offsets: dict {Label or group: (dx, dy, dz)}. Builds a temporary document with static copies."""
    mapping = {}
    for k, d in offsets.items():
        for lab in parts_of(proj, [k], strict=True):
            mapping[lab] = d
    colors = original_colors(proj)
    tmp = App.newDocument("Exploded_tmp")
    for o in proj.parts(visible=True):
        c = tmp.addObject("Part::Feature", o.Name)
        s = o.Shape.copy(); s.translate(App.Vector(*mapping.get(o.Label, default))); c.Shape = s
        c.ViewObject.ShapeColor = colors[o.Name]
        if o.Furn_Type == "glass": c.ViewObject.Transparency = 60
    tmp.recompute()
    v = Gui.getDocument(tmp.Name).ActiveView
    cam(azimuth, elevation, view=v); save(path, view=v)
    App.closeDocument(tmp.Name); use(proj)
    return path


def crop(path, pad=40):
    """QImage of the PNG without the white margins."""
    import numpy as np
    from PySide import QtGui
    im = QtGui.QImage(path)
    if im.isNull():                      # missing or unreadable file: callers check isNull()
        return im
    im = im.convertToFormat(QtGui.QImage.Format_RGB32)
    w, h = im.width(), im.height()
    arr = np.frombuffer(im.constBits(), dtype=np.uint8, count=im.sizeInBytes()).reshape(h, im.bytesPerLine() // 4, 4)[:, :w, :3]
    ys, xs = np.where((arr < 245).any(axis=2))
    if len(xs) == 0:
        return im
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, w - 1)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, h - 1)
    return im.copy(x0, y0, x1 - x0, y1 - y0)


def contact_sheet(items, cols, cell, path, title):
    """items: list of (png_file, caption). Crops white margins and lays out a captioned grid."""
    from PySide import QtGui, QtCore
    rows = (len(items) + cols - 1) // cols; cw, ch = cell; th, lh = 70, 50
    W, H = cols * cw, th + rows * (ch + lh)
    img = QtGui.QImage(W, H, QtGui.QImage.Format_RGB32); img.fill(QtGui.QColor("white"))
    p = QtGui.QPainter(img); p.setRenderHint(QtGui.QPainter.Antialiasing); p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    p.setFont(font(pt=26, bold=True)); p.setPen(QtGui.QColor("#222"))
    p.drawText(QtCore.QRect(0, 0, W, th), QtCore.Qt.AlignCenter, title)
    p.setFont(font(pt=16))
    for i, (f, cap) in enumerate(items):
        r, c = divmod(i, cols); x, y = c * cw, th + r * (ch + lh)
        im = crop(f).scaled(cw - 40, ch - 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        p.drawImage(x + (cw - im.width()) // 2, y + (ch - im.height()) // 2, im)
        p.setPen(QtGui.QColor("#333")); p.drawText(QtCore.QRect(x, y + ch, cw, lh), QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop, cap)
        p.setPen(QtGui.QColor("#ddd")); p.drawRect(x + 4, y + 4, cw - 8, ch + lh - 8)
    p.end(); img.save(path)
    return path
