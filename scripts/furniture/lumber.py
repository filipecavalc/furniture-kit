"""Solid-wood cut plan from commercial stock (boards, battens, beams).

Each part goes to the narrowest stock of the same thickness that fits its width:
- width ~equal to the stock: crosscut only (linear nesting, like a bar);
- narrower: ripped on the table saw. Parts with the same rip width form strips as long as the
  board (linear nesting), and the strips are packed across the board width. This is a simple
  workshop plan (rip first, crosscut after), not an optimal 2D nesting.

Usage:
    stock = [dict(name="Board 25 x 300", thk=20, width=280, length=3000, verify=True), ...]
    lumber.generate(pj, folder, stock, extra_width={"tongue and groove": 8})
extra_width: text contained in Furn_Note -> mm added to the rip width (e.g. the tongue).
extra_length: same, added to the final length (e.g. tenon, groove).
Stock sizes are local (ask the user or research the lumber yard); mark unconfirmed ones verify=True.
"""
import os, re
from collections import OrderedDict
from . import bom
from .i18n import T, font

COLORS = ("#cfe3f7", "#d8efd3", "#fbe3c4", "#e6d9f2", "#f9d5d5", "#d4efef", "#f3eec7", "#e2e2e2")


def _root(name):
    """M1_Rail_Front_3 -> Rail_Front"""
    n = re.sub(r"^M\d+_", "", name)
    return re.sub(r"_\d+$", "", n)


def _ffd(items, cap, kerf, size=lambda i: i):
    """First-fit decreasing: list of bins, each a list of items."""
    bins = []
    for it in sorted(items, key=size, reverse=True):
        for b in bins:
            if b["used"] + kerf + size(it) <= cap:
                b["items"].append(it); b["used"] += kerf + size(it); break
        else:
            bins.append(dict(items=[it], used=size(it)))
    return bins


def plan(proj, stock, extra_width=None, kerf=3, trim=10, extra_length=None):
    extra_width = extra_width or {}; extra_length = extra_length or {}
    groups = bom.grouped(proj)["solid"]
    legend, parts = [], []
    for k, g in enumerate(sorted(groups, key=lambda g: (-g["thk"], -g["length"], -g["width"]))):
        code = f"{chr(65 + k // 9)}{k % 9 + 1}"
        ew = sum(v for txt, v in extra_width.items() if txt in (g["note"] or ""))
        el = sum(v for txt, v in extra_length.items() if txt in (g["note"] or ""))
        roots = list(OrderedDict.fromkeys(_root(p) for p in g["parts"]))
        mods = sorted({m.group(0)[:-1] for m in (re.match(r"^M\d+_", p) for p in g["parts"]) if m})
        lg = dict(code=code, name=", ".join(roots), mods=", ".join(mods), qty=g["qty"], thk=g["thk"], width=g["width"],
                  parts=g["parts"], length=g["length"] + el, rip=g["width"] + ew, cut=g["length"] + el + trim, note=g["note"])
        legend.append(lg)
        parts += [lg] * g["qty"]
    out = dict(stock=[], legend=legend, no_stock=[], kerf=kerf, trim=trim)
    by_stock = OrderedDict((i, []) for i in range(len(stock)))
    for pc in parts:
        cand = [i for i, s in enumerate(stock) if abs(s["thk"] - pc["thk"]) < 0.6 and s["width"] + 0.6 >= pc["rip"]
                and s["length"] >= pc["cut"]]
        if not cand:
            out["no_stock"].append(pc); continue
        by_stock[min(cand, key=lambda i: stock[i]["width"])].append(pc)
    for i, pcs in by_stock.items():
        if not pcs:
            continue
        s = stock[i]
        full = [pc for pc in pcs if pc["rip"] >= s["width"] - 5]
        ripped = [pc for pc in pcs if pc["rip"] < s["width"] - 5]
        boards = []
        for b in _ffd(full, s["length"], kerf, lambda p: p["cut"]):           # full width
            boards.append([dict(width=s["width"], parts=b["items"], full=True)])
        strips = []
        for w in sorted({pc["rip"] for pc in ripped}, reverse=True):
            for b in _ffd([pc for pc in ripped if pc["rip"] == w], s["length"], kerf, lambda p: p["cut"]):
                strips.append(dict(width=w, parts=b["items"], full=False))
        for b in _ffd(strips, s["width"], kerf, lambda t: t["width"]):
            boards.append(b["items"])
        used = sum(pc["width"] * pc["length"] for pc in pcs)
        out["stock"].append(dict(s, boards=boards, use=100 * used / (len(boards) * s["width"] * s["length"])))
    return out


def pdf(plan_, path, title):
    from PySide import QtGui, QtCore
    colors = [QtGui.QColor(c) for c in COLORS]
    color_of = {lg["code"]: colors[k % len(colors)] for k, lg in enumerate(plan_["legend"])}

    def page(p, W, H, sub, body):
        p.fillRect(0, 0, W, H, QtGui.QColor("white")); m = W * 0.035
        p.setPen(QtGui.QColor("#222")); p.setFont(font(H * 0.034, True))
        p.drawText(QtCore.QRectF(m, m * 0.5, W - 2 * m, H * 0.06), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, sub)
        p.setFont(font(H * 0.02))
        p.drawText(QtCore.QRectF(m, m * 0.5, W - 2 * m, H * 0.06), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, title)
        body(p, QtCore.QRectF(m, m * 0.5 + H * 0.075, W - 2 * m, H - m * 1.3 - H * 0.075))

    def table(p, widths, rows, R, y, lh, fs):
        for li, row in enumerate(rows):
            f = font(fs, li == 0); p.setFont(f); fm = QtGui.QFontMetrics(f)
            if li % 2 == 1:
                p.fillRect(QtCore.QRectF(R.left(), y, R.width(), lh), QtGui.QColor("#f4f4f4"))
            x = R.left()
            for wd, t in zip(widths, row):
                if isinstance(t, QtGui.QColor):
                    p.fillRect(QtCore.QRectF(x + 2, y + lh * 0.2, lh * 0.6, lh * 0.6), t)
                else:
                    p.setPen(QtGui.QColor("#222"))
                    p.drawText(QtCore.QRectF(x + 3, y, R.width() * wd - 6, lh), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                               fm.elidedText(str(t), QtCore.Qt.ElideRight, int(R.width() * wd - 6)))
                x += R.width() * wd
            y += lh
        return y

    def body_summary(start, end, buy):
        def _b(p, R):
            y = R.top(); lh = R.height() * 0.042; fs = R.height() * 0.024
            if buy:
                rows = [T("lumber_buy")]
                for s in plan_["stock"]:
                    rows.append((s["name"] + (" *" if s.get("verify") else ""), f"{s['thk']:g} x {s['width']:g} x {s['length']:g} mm",
                                 len(s["boards"]), f"{s['use']:.0f}%"))
                y = table(p, (0.34, 0.3, 0.1, 0.26), rows, R, y, lh, fs) + lh * 0.4
            rows = [T("lumber_parts")]
            for lg in plan_["legend"][start:end]:
                rows.append((color_of[lg["code"]], lg["code"], lg["name"], lg["mods"], lg["qty"],
                             f"{lg['length']} x {lg['width']} x {lg['thk']:g}", f"W {lg['rip']} / L {lg['cut']}", lg["note"]))
            y = table(p, (0.025, 0.04, 0.17, 0.09, 0.04, 0.12, 0.11, 0.405), rows, R, y, lh * 0.82, fs * 0.8)
            p.setFont(font(fs * 0.85)); p.setPen(QtGui.QColor("#333"))
            for t in (T("lumber_note1", k=plan_["kerf"], s=plan_["trim"]), T("lumber_note2")):
                p.drawText(QtCore.QRectF(R.left(), y + lh * 0.2, R.width(), lh), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, t); y += lh * 0.8
        return _b

    def body_boards(s, start, end):
        def _b(p, R):
            bds = s["boards"][start:end]; n = max(len(bds), 1)
            lh = min(R.height() / n, R.height() * 0.33)
            sc = min(R.width() * 0.9 / s["length"], lh * 0.72 / s["width"])
            for k, bd in enumerate(bds):
                y0 = R.top() + k * lh; x0 = R.left() + R.width() * 0.09
                p.setPen(QtGui.QColor("#222")); p.setFont(font(lh * 0.1, True))
                p.drawText(QtCore.QRectF(R.left(), y0, R.width() * 0.09, lh * 0.3), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                           f"{start + k + 1}/{len(s['boards'])}")
                p.setPen(QtGui.QPen(QtGui.QColor("#555"), 1.2)); p.setBrush(QtGui.QColor("#eee"))
                p.drawRect(QtCore.QRectF(x0, y0 + lh * 0.05, s["length"] * sc, s["width"] * sc))
                yy = 0
                for strip in bd:
                    x = 0
                    for pc in strip["parts"]:
                        r = QtCore.QRectF(x0 + x * sc, y0 + lh * 0.05 + yy * sc, pc["cut"] * sc, strip["width"] * sc)
                        p.setPen(QtGui.QPen(QtGui.QColor("#333"), 1)); p.setBrush(color_of[pc["code"]]); p.drawRect(r)
                        p.setPen(QtGui.QColor("#111")); p.setFont(font(min(r.height() * 0.5, r.width() * 0.22, lh * 0.09)))
                        p.drawText(r, QtCore.Qt.AlignCenter, pc["code"])
                        x += pc["cut"] + plan_["kerf"]
                    yy += strip["width"] + plan_["kerf"]
                widths = " + ".join(str(t["width"]) for t in bd)
                p.setPen(QtGui.QColor("#444")); p.setFont(font(lh * 0.075))
                if bd[0].get("full"):
                    txt = T("lumber_full", v=f"{s['length'] - sum(pc['cut'] + plan_['kerf'] for pc in bd[0]['parts']):.0f}")
                else:
                    txt = T("lumber_strips", w=widths, v=f"{s['width'] - sum(t['width'] for t in bd) - plan_['kerf'] * (len(bd) - 1):.0f}")
                p.drawText(QtCore.QRectF(x0, y0 + lh * 0.07 + s["width"] * sc, s["length"] * sc, lh * 0.15),
                           QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, txt)
        return _b

    n1, n2 = 16, 24          # legend rows on the first page and on the following ones
    pages = [(T("lumber_title"), body_summary(0, n1, True))]
    for start in range(n1, len(plan_["legend"]), n2):
        pages.append((T("lumber_cont"), body_summary(start, start + n2, False)))
    for s in plan_["stock"]:
        per = 3 if s["width"] > 100 else 6
        for start in range(0, len(s["boards"]), per):
            pages.append((T("lumber_plan", name=s["name"], t=f"{s['thk']:g}", w=f"{s['width']:g}", l=f"{s['length']:g}"),
                          body_boards(s, start, start + per)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = QtGui.QPdfWriter(path); w.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    w.setPageOrientation(QtGui.QPageLayout.Landscape); w.setResolution(200); w.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    p = QtGui.QPainter(w); W, H = w.width(), w.height()
    for k, (t, b) in enumerate(pages):
        if k: w.newPage()
        page(p, W, H, t, b)
    p.end()
    return dict(file=path, pages=len(pages))


def generate(proj, folder, stock, extra_width=None, kerf=3, trim=10, extra_length=None):
    pl = plan(proj, stock, extra_width, kerf, trim, extra_length)
    path = os.path.join(folder, f"{proj.name}_Lumber_Cut_Plan.pdf")
    info = pdf(pl, path, proj.name.replace("_", " "))
    info["buy"] = [f"{s['name']} {s['thk']:g}x{s['width']:g}x{s['length']:g}: {len(s['boards'])} pcs ({s['use']:.0f}%)" for s in pl["stock"]]
    info["no_stock"] = sorted({pc["code"] + " " + pc["name"] for pc in pl["no_stock"]})
    return info
