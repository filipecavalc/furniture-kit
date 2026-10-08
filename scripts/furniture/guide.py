"""Assembly guide PDF (A4 landscape): each page has a title, images on the left and text on the right,
or a full-width table, plus optional detail drawings.

page = dict(
    title="Step 2 - Lower rails",
    images=[(png_path, "caption"), ...],          # 0 to 2 images, stacked in the left column
    blocks=[("Parts", ["A7 Rail 1090x70 (x2)", ...]), ("Fixing", [...]), ("How to", [...])],
    table=(header, rows, relative_widths),       # optional; full width below the text
    drawings=[function(painter, QRectF, font)],  # optional; detail drawings in the left column
    font=px, left_col=0.52,                      # optional layout overrides
)
Text lines starting with "- " become bullets; lines like "1. " stay numbered as written.
"""
import os
from .i18n import font, fit_font


def pdf(path, doc_title, pages):
    from PySide import QtGui, QtCore

    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = QtGui.QPdfWriter(path); w.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    w.setPageOrientation(QtGui.QPageLayout.Landscape); w.setResolution(200); w.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    p = QtGui.QPainter(w); W, H = w.width(), w.height(); m = W * 0.03
    WRAP = QtCore.Qt.TextWordWrap | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

    def text(x, y, width, txt, px, bold=False, color="#222"):
        f = font(px, bold); p.setFont(f); p.setPen(QtGui.QColor(color))
        r = QtGui.QFontMetrics(f).boundingRect(QtCore.QRect(0, 0, int(width), 10000), int(WRAP), txt)
        p.drawText(QtCore.QRectF(x, y, width, r.height() + 2), WRAP, txt)
        return y + r.height()

    def blocks(x, y, width, bl, px):
        for sub, lines in bl:
            y = text(x, y, width, sub, px * 1.15, True, "#1d4f8a") + px * 0.35
            for ln in lines:
                if ln.startswith("- "):
                    p.setFont(font(px)); p.setPen(QtGui.QColor("#222"))
                    p.drawText(QtCore.QRectF(x, y, px, px * 1.5), QtCore.Qt.AlignLeft, "•")
                    y = text(x + px * 1.1, y, width - px * 1.1, ln[2:], px) + px * 0.25
                else:
                    y = text(x, y, width, ln, px) + px * 0.25
            y += px * 0.6
        return y

    def table(x, y, width, tb, px):
        header, rows, rel = tb
        tot = sum(rel); lh = px * 1.7
        CELL = QtCore.Qt.TextWordWrap | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        for li, row in enumerate([header] + rows):
            f = font(px, li == 0); fm = QtGui.QFontMetrics(f)
            widths = [width * wd / tot for wd in rel]
            h = max([lh] + [fm.boundingRect(QtCore.QRect(0, 0, int(cw - 8), 10000), int(CELL), str(t)).height() + px * 0.7
                            for t, cw in zip(row, widths)])        # the row grows when text wraps
            if li % 2 == 1:
                p.fillRect(QtCore.QRectF(x, y, width, h), QtGui.QColor("#f2f2f2"))
            cx = x
            for t, cw in zip(row, widths):
                p.setFont(f); p.setPen(QtGui.QColor("#222"))
                p.drawText(QtCore.QRectF(cx + 4, y, cw - 8, h), CELL, str(t))
                cx += cw
            y += h
        return y

    for k, pg in enumerate(pages):
        if k:
            w.newPage()
        p.fillRect(0, 0, W, H, QtGui.QColor("white"))
        p.setPen(QtGui.QColor("#222")); p.setFont(fit_font(pg["title"], (W - 2 * m) * 0.75, H * 0.032, True))
        p.drawText(QtCore.QRectF(m, m * 0.6, W - 2 * m, H * 0.06), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, pg["title"])
        p.setFont(font(H * 0.017)); p.setPen(QtGui.QColor("#666"))
        p.drawText(QtCore.QRectF(m, m * 0.6, W - 2 * m, H * 0.06), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                   f"{doc_title}  -  {k + 1}/{len(pages)}")
        top = m * 0.6 + H * 0.075; bot = H - m * 0.8
        imgs, drw = pg.get("images", []), pg.get("drawings", [])
        px = pg.get("font", H * 0.0175)
        if imgs or drw:
            cl = W * pg.get("left_col", 0.52); xr = m + cl + m * 0.8; wr = W - m - xr
            n = len(imgs) + len(drw); hc = (bot - top) / max(n, 1)
            y = top
            for img_path, cap in imgs:
                from .images import crop
                im = crop(img_path, 20)
                if not im.isNull():
                    sc = min(cl / im.width(), (hc - px * 1.8) / im.height())
                    iw, ih = im.width() * sc, im.height() * sc
                    p.drawImage(QtCore.QRectF(m + (cl - iw) / 2, y, iw, ih), im)
                    text(m, y + ih + px * 0.2, cl, cap, px * 0.85, False, "#555")
                y += hc
            for d in drw:
                d(p, QtCore.QRectF(m, y, cl, hc - px), font)
                y += hc
            yb = blocks(xr, top, wr, pg.get("blocks", []), px)
            if pg.get("table"):
                table(xr, yb, wr, pg["table"], px * 0.85)
        else:
            yb = blocks(m, top, W - 2 * m, pg.get("blocks", []), px)
            if pg.get("table"):
                table(m, yb, W - 2 * m, pg["table"], px)
    p.end()
    return dict(file=path, pages=len(pages))
