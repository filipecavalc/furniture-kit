"""Cut list / nesting.

- Sheets: guillotine nesting (edge-to-edge cuts), with saw kerf, edge trim and grain direction.
- Profiles/bars: linear nesting in stock bars (e.g. 6000 mm) with saw kerf.
- Solid wood: not nested here (boards vary); listed in the summary. See lumber.py for board plans.
Writes an A4 landscape PDF with Qt (runs inside FreeCAD).
"""
import os
from . import bom
from .i18n import T, N, pct, font, fit_font, material_name


# ------------------------------------------------------------------ sheets
def _nest_sheets(parts, W, H, kerf):
    """parts: dicts with l, w, grain ('length'|'width'|''), name. Returns a list of sheets."""
    sheets = []
    for p in sorted(parts, key=lambda p: -p["l"] * p["w"]):
        if p["grain"] == "length":  options = [(p["l"], p["w"], False)]
        elif p["grain"] == "width": options = [(p["w"], p["l"], True)]
        else:                       options = [(p["l"], p["w"], False), (p["w"], p["l"], True)]
        best = None
        for si, sh in enumerate(sheets + [dict(free=[(0, 0, W, H)], pos=[])]):
            for fi, (x, y, fw, fh) in enumerate(sh["free"]):
                for w, h, rot in options:
                    if w <= fw and h <= fh:
                        score = (si, min(fw - w, fh - h))
                        if best is None or score < best[0]:
                            best = (score, si, fi, w, h, rot)
        if best is None:
            raise ValueError(T("err_sheet_fit", name=p["name"], l=p["l"], w=p["w"], W=W, H=H))
        _, si, fi, w, h, rot = best
        if si == len(sheets):
            sheets.append(dict(free=[(0, 0, W, H)], pos=[]))
        sh = sheets[si]; x, y, fw, fh = sh["free"].pop(fi)
        sh["pos"].append(dict(p, x=x, y=y, pw=w, ph=h, rot=rot))
        rw, rh = fw - w - kerf, fh - h - kerf
        if rw < rh: new = [(x + w + kerf, y, rw, h), (x, y + h + kerf, fw, rh)]
        else:       new = [(x + w + kerf, y, rw, fh), (x, y + h + kerf, w, rh)]
        sh["free"] += [r for r in new if r[2] > 0 and r[3] > 0]
    return sheets


def _check_sheets(sheets, W, H, kerf):
    for sh in sheets:
        P = sh["pos"]
        for i, a in enumerate(P):
            assert a["x"] >= 0 and a["y"] >= 0 and a["x"] + a["pw"] <= W and a["y"] + a["ph"] <= H, a["name"]
            for b in P[i + 1:]:
                apart = (a["x"] + a["pw"] + kerf <= b["x"] or b["x"] + b["pw"] + kerf <= a["x"] or
                         a["y"] + a["ph"] + kerf <= b["y"] or b["y"] + b["ph"] + kerf <= a["y"])
                assert apart, (a["name"], b["name"])


# ------------------------------------------------------------------ bars
def _nest_bars(parts, L, kerf):
    bars = []
    for p in sorted(parts, key=lambda p: -p["l"]):
        if p["l"] > L:
            raise ValueError(T("err_bar_fit", name=p["name"], l=p["l"], L=L))
        for b in bars:
            used = sum(q["l"] for q in b) + kerf * len(b)
            if used + p["l"] <= L:
                b.append(p); break
        else:
            bars.append([p])
    return bars


# ------------------------------------------------------------------ plan
def plan(proj):
    cat = proj.cat; dfl = cat["defaults"]; mats = cat["materials"]
    d = bom.raw(proj)
    out = dict(sheets=[], bars=[], solid=bom.grouped(proj)["solid"], warnings=[])
    groups = {}
    for it in d["panel"]:
        groups.setdefault((it["material"], it["thk"]), []).append(
            dict(name=it["part"], l=it["length"], w=it["width"], grain=it["grain"]))
    trim, kerf = dfl["panel_trim_mm"], dfl["panel_kerf_mm"]
    for (m, thk), parts in sorted(groups.items()):
        name = material_name(mats[m])
        if not mats[m].get("sheet_mm"):
            out["warnings"].append(T("warn_no_sheet", name=name, mat=m, parts=", ".join(p["name"] for p in parts)))
            continue
        SL, SW = mats[m]["sheet_mm"]
        warn = T("warn_sheet", name=name, l=SL, w=SW)
        if mats[m].get("verify") and warn not in out["warnings"]:      # once per material, not per thickness
            out["warnings"].append(warn)
        W, H = SL - 2 * trim, SW - 2 * trim
        shs = _nest_sheets(parts, W, H, kerf); _check_sheets(shs, W, H, kerf)
        for i, sh in enumerate(shs, 1):
            use = sum(p["l"] * p["w"] for p in sh["pos"]) / (SL * SW) * 100
            out["sheets"].append(dict(material=m, name=name, thk=thk, SL=SL, SW=SW, trim=trim, kerf=kerf,
                                      idx=i, tot=len(shs), pos=sh["pos"], use=use))
    gb = {}
    for it in d["profile"]:
        gb.setdefault((it["material"], it["section"]), []).append(dict(name=it["part"], l=it["length"]))
    kb = dfl["bar_kerf_mm"]
    for (m, section), parts in sorted(gb.items()):
        L = mats[m].get("bar_mm", 6000); name = material_name(mats[m])
        if mats[m].get("verify"):
            out["warnings"].append(T("warn_bar", name=name, section=section, l=L))
        bs = _nest_bars(parts, L, kb)
        out["bars"].append(dict(material=m, name=name, section=section, L=L, kerf=kb, bars=bs,
                                use=sum(p["l"] for b in bs for p in b) / (L * len(bs)) * 100))
    if dfl.get("bar_kerf_verify") and out["bars"]:
        out["warnings"].append(T("warn_bar_kerf", k=kb))
    return out


# ------------------------------------------------------------------ PDF
def pdf(plan_, path, title):
    from PySide import QtGui, QtCore
    colors = [QtGui.QColor(c) for c in ("#cfe3f7", "#d8efd3", "#fbe3c4", "#e6d9f2", "#f9d5d5", "#d4efef", "#f3eec7", "#e2e2e2")]

    def sheet_page(p, W, H, sub, body):
        p.fillRect(0, 0, W, H, QtGui.QColor("white")); m = W * 0.04
        p.setPen(QtGui.QColor("#222")); p.setFont(fit_font(sub, (W - 2 * m) * 0.8, H * 0.035, True))
        p.drawText(QtCore.QRectF(m, m * 0.6, W - 2 * m, H * 0.06), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, sub)
        p.setFont(font(H * 0.02))
        p.drawText(QtCore.QRectF(m, m * 0.6, W - 2 * m, H * 0.06), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, title)
        body(p, QtCore.QRectF(m, m * 0.6 + H * 0.08, W - 2 * m, H - m * 1.6 - H * 0.08))

    def part_text(p, r, txt):
        vert = r.height() > r.width() * 1.6
        small, large = (r.width(), r.height()) if vert else (r.height(), r.width())
        p.setPen(QtGui.QColor("#111")); p.setFont(font(min(small * 0.22, large * 0.075)))
        if vert:
            p.save(); p.translate(r.center()); p.rotate(-90)
            p.drawText(QtCore.QRectF(-r.height() / 2, -r.width() / 2, r.height(), r.width()),
                       QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap, txt); p.restore()
        else:
            p.drawText(r.adjusted(3, 3, -3, -3), QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap, txt)

    def body_sheet(sh):
        def _b(p, R):
            SL, SW, trim = sh["SL"], sh["SW"], sh["trim"]
            sc = min((R.width() * 0.95) / SL, (R.height() * 0.78) / SW)
            ox, oy = R.left() + R.width() * 0.04, R.top()
            sx = lambda v: ox + v * sc; sy = lambda v: oy + (SW - v) * sc
            p.setPen(QtGui.QPen(QtGui.QColor("#555"), 1.5)); p.setBrush(QtGui.QColor("#f4f1ea"))
            p.drawRect(QtCore.QRectF(sx(0), sy(SW), SL * sc, SW * sc))
            p.setPen(QtGui.QPen(QtGui.QColor("#aaa"), 1, QtCore.Qt.DashLine)); p.setBrush(QtCore.Qt.NoBrush)
            p.drawRect(QtCore.QRectF(sx(trim), sy(SW - trim), (SL - 2 * trim) * sc, (SW - 2 * trim) * sc))
            p.setPen(QtGui.QColor("#444")); p.setFont(font(R.height() * 0.03))
            p.drawText(QtCore.QRectF(sx(0), sy(0) + 2, SL * sc, R.height() * 0.05), QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop, f"{SL} mm")
            p.save(); p.translate(sx(0) - R.height() * 0.045, sy(SW / 2)); p.rotate(-90)
            p.drawText(QtCore.QRectF(-SW * sc / 2, 0, SW * sc, R.height() * 0.045), QtCore.Qt.AlignCenter, f"{SW} mm"); p.restore()
            names = sorted(set(q["name"] for q in sh["pos"]))
            for q in sh["pos"]:
                x, y = q["x"] + trim, q["y"] + trim
                r = QtCore.QRectF(sx(x), sy(y + q["ph"]), q["pw"] * sc, q["ph"] * sc)
                p.setPen(QtGui.QPen(QtGui.QColor("#333"), 1.2)); p.setBrush(colors[names.index(q["name"]) % len(colors)]); p.drawRect(r)
                part_text(p, r, f"{q['name']}\n{q['l']} x {q['w']}")
            y0 = sy(0) + R.height() * 0.065
            foot = (f"{sh['name']} {sh['thk']:g} mm  -  {T('sheet_of', i=sh['idx'], n=sh['tot'])}  -  "
                    f"{N(len(sh['pos']), 'part')}  -  {T('yield')} {pct(sh['use'])}")
            p.setPen(QtGui.QColor("#222")); p.setFont(fit_font(foot, R.width(), R.height() * 0.034))
            p.drawText(QtCore.QRectF(R.left(), y0, R.width(), R.height() * 0.05), QtCore.Qt.AlignLeft, foot)
            if any(q["grain"] for q in sh["pos"]):
                p.setFont(font(R.height() * 0.028))
                p.drawText(QtCore.QRectF(R.left(), y0 + R.height() * 0.05, R.width(), R.height() * 0.05), QtCore.Qt.AlignLeft,
                           T("grain_note", l=SL))
        return _b

    def body_bars(gb, start, end):
        def _b(p, R):
            L = gb["L"]; bs = gb["bars"][start:end]
            lh = min(R.height() * 0.8 / max(len(bs), 1), R.height() * 0.11)
            sc = R.width() * 0.9 / L
            for k, bar in enumerate(bs):
                y = R.top() + k * lh
                p.setPen(QtGui.QColor("#222")); p.setFont(font(lh * 0.22))
                p.drawText(QtCore.QRectF(R.left(), y, R.width() * 0.08, lh * 0.7), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                           f"{T('bar')} {start + k + 1}")
                x0 = R.left() + R.width() * 0.08
                p.setPen(QtGui.QPen(QtGui.QColor("#555"), 1.2)); p.setBrush(QtGui.QColor("#eee"))
                p.drawRect(QtCore.QRectF(x0, y + lh * 0.1, L * sc, lh * 0.5))
                x = 0
                for i, q in enumerate(bar):
                    r = QtCore.QRectF(x0 + x * sc, y + lh * 0.1, q["l"] * sc, lh * 0.5)
                    p.setPen(QtGui.QPen(QtGui.QColor("#333"), 1)); p.setBrush(colors[i % len(colors)]); p.drawRect(r)
                    p.setPen(QtGui.QColor("#111")); p.setFont(font(min(lh * 0.16, r.width() * 0.09)))
                    p.drawText(r, QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap, f"{q['name']}\n{q['l']}")
                    x += q["l"] + gb["kerf"]
                left = L - sum(q["l"] for q in bar) - gb["kerf"] * len(bar)
                p.setPen(QtGui.QColor("#666")); p.setFont(font(lh * 0.16))
                p.drawText(QtCore.QRectF(x0, y + lh * 0.62, L * sc, lh * 0.3), QtCore.Qt.AlignRight, T("offcut", v=f"{max(left, 0):.0f}"))
            foot = f"{gb['name']} {gb['section']}  -  {T('bar_len', l=L)}  -  {N(len(gb['bars']), 'bar')}  -  {T('yield')} {pct(gb['use'])}"
            p.setPen(QtGui.QColor("#222")); p.setFont(fit_font(foot, R.width(), R.height() * 0.034))
            p.drawText(QtCore.QRectF(R.left(), R.bottom() - R.height() * 0.08, R.width(), R.height() * 0.06), QtCore.Qt.AlignLeft, foot)
        return _b

    # summary: a list of lines (table rows, gaps, notes), split over as many pages as needed
    items = []
    if plan_["sheets"]:
        items.append(("row", T("sum_sheets"), True))
        seen = {}
        for sh in plan_["sheets"]:
            seen.setdefault((sh["name"], sh["thk"]), []).append(sh)
        for (n, t), shs in seen.items():
            items.append(("row", (f"{n} {t:g} mm ({shs[0]['SL']}x{shs[0]['SW']})", len(shs), sum(len(c["pos"]) for c in shs),
                                  " / ".join(pct(c["use"]) for c in shs)), False))
        items.append(("gap",))
    if plan_["bars"]:
        items.append(("row", T("sum_bars"), True))
        for gb in plan_["bars"]:
            items.append(("row", (f"{gb['name']} {gb['section']}", len(gb["bars"]), sum(len(b) for b in gb["bars"]), pct(gb["use"])), False))
        items.append(("gap",))
    if plan_["solid"]:
        items.append(("row", T("sum_solid"), True))
        for it in plan_["solid"]:
            items.append(("row", (f"{it['material_name']} - {', '.join(it['parts'])}", it["qty"],
                                  f"{it['length']}x{it['width']}x{it['thk']:g}", ""), False))
        items.append(("gap",))
    items += [("note", t) for t in [T("notes"), T("note_guillotine")] + ["- " + a for a in plan_["warnings"]]]
    UNITS = {"row": 1.0, "gap": 0.5, "note": 0.75}     # height of each kind, in summary line heights
    chunks, cur, used = [], [], 0.0
    for it in items:
        if used + UNITS[it[0]] > 16 and cur:           # about 16 line heights fit on a page
            chunks.append(cur); cur, used = [], 0.0
        cur.append(it); used += UNITS[it[0]]
    chunks.append(cur)

    def body_summary(chunk):
        def _b(p, R):
            lh = R.height() * 0.055; y = R.top()
            for it in chunk:
                if it[0] == "row":
                    f = font(R.height() * 0.029, it[2]); p.setFont(f); p.setPen(QtGui.QColor("#222"))
                    fm = QtGui.QFontMetrics(f)
                    for cx, wd, t in zip((0, 0.62, 0.73, 0.84), (0.60, 0.11, 0.11, 0.18), it[1]):
                        txt = fm.elidedText(str(t), QtCore.Qt.ElideRight, int(R.width() * wd))
                        p.drawText(QtCore.QRectF(R.left() + cx * R.width(), y, R.width() * wd, lh), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, txt)
                    y += lh
                elif it[0] == "gap":
                    y += lh * 0.5
                else:
                    p.setFont(fit_font(it[1], R.width(), R.height() * 0.026)); p.setPen(QtGui.QColor("#222"))
                    p.drawText(QtCore.QRectF(R.left(), y, R.width(), lh * 0.8), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, it[1])
                    y += lh * 0.75
        return _b

    pages = [(T("cut_summary") + (f" ({k + 1}/{len(chunks)})" if len(chunks) > 1 else ""), body_summary(c))
             for k, c in enumerate(chunks)]
    for sh in plan_["sheets"]:
        pages.append((f"{T('cut_title')} - {sh['name']} {sh['thk']:g} mm", body_sheet(sh)))
    for gb in plan_["bars"]:
        for start in range(0, len(gb["bars"]), 8):
            pages.append((f"{T('cut_title')} - {gb['name']} {gb['section']}", body_bars(gb, start, start + 8)))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = QtGui.QPdfWriter(path); w.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
    w.setPageOrientation(QtGui.QPageLayout.Landscape); w.setResolution(200); w.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    p = QtGui.QPainter(w); W, H = w.width(), w.height()
    for k, (t, b) in enumerate(pages):
        if k: w.newPage()
        sheet_page(p, W, H, t, b)
    p.end()
    return dict(file=path, pages=len(pages))


def generate(proj, folder):
    pl = plan(proj)
    path = os.path.join(folder, f"{proj.name}_Cut_List.pdf")
    info = pdf(pl, path, proj.name.replace("_", " "))
    info["summary"] = ([f"{c['name']} {c['thk']:g}mm {T('sheet')} {c['idx']}/{c['tot']}: {N(len(c['pos']), 'part')}, {c['use']:.1f}%"
                        for c in pl["sheets"]] +
                       [f"{b['name']} {b['section']}: {N(len(b['bars']), 'bar')}, {b['use']:.1f}%" for b in pl["bars"]])
    info["warnings"] = pl["warnings"]
    return info
