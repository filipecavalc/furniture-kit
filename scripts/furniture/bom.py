"""Bill of materials from the parts' Furn_* properties.

Categories: panel (area), solid (volume + suggested rough size), profile (linear metres),
glass (area) and hardware (count).
"""
import os, csv
from collections import OrderedDict
from .i18n import T, material_name

KINDS = ("panel", "solid", "profile", "glass", "hardware")


def _dims(o):
    if o.TypeId == "Part::Box":
        return sorted([o.Length.Value, o.Width.Value, o.Height.Value])
    bb = o.Shape.BoundBox
    return sorted([bb.XLength, bb.YLength, bb.ZLength])


def raw(proj):
    """Raw list of parts, one entry per object."""
    mats = proj.cat["materials"]
    out = {k: [] for k in KINDS}
    for o in proj.parts():
        k = o.Furn_Type; m = o.Furn_Material
        item = dict(part=o.Label, material=m, material_name=material_name(mats[m]), note=o.Furn_Note)
        if k in ("panel", "solid", "glass"):
            t, w, l = _dims(o)
            item.update(thk=round(t, 1), length=round(l), width=round(w), grain=o.Furn_Grain)
        elif k == "profile":
            item.update(section=o.Furn_Section, length=round(o.Furn_Length))
        elif k == "hardware":
            item.update(desc=o.Furn_Desc or o.Label)
        out[k].append(item)
    return out


def grouped(proj):
    """Groups identical parts (same material, size and grain)."""
    d = raw(proj)
    g = {}
    for k, items in d.items():
        acc = OrderedDict()
        for it in items:
            if k in ("panel", "solid", "glass"):
                key = (it["material"], it["thk"], it["length"], it["width"], it["grain"])
            elif k == "profile":
                key = (it["material"], it["section"], it["length"])
            else:
                key = (it["material"], it["desc"])
            if key not in acc:
                acc[key] = dict(it, qty=0, parts=[])
            acc[key]["qty"] += 1; acc[key]["parts"].append(it["part"])
        g[k] = list(acc.values())
    return g


def totals(proj):
    g = grouped(proj); allow = proj.cat["defaults"]["solid_allowance_mm"]
    area = OrderedDict()
    for it in g["panel"] + g["glass"]:
        key = f"{it['material_name']} {it['thk']:g} mm"
        area[key] = area.get(key, 0) + it["length"] * it["width"] * it["qty"] / 1e6
    vol = OrderedDict()
    for it in g["solid"]:
        rl, rw, rt = it["length"] + allow["length"], it["width"] + allow["width"], it["thk"] + allow["thickness"]
        vol[it["material_name"]] = vol.get(it["material_name"], 0) + rl * rw * rt * it["qty"] / 1e9
    lin = OrderedDict()
    for it in g["profile"]:
        key = f"{it['material_name']} {it['section']}"
        lin[key] = lin.get(key, 0) + it["length"] * it["qty"] / 1000
    hw = OrderedDict((it["desc"], it["qty"]) for it in g["hardware"])
    return dict(area_m2=area, rough_volume_m3=vol, linear_m=lin, hardware=hw)


def rows(proj):
    """Single table: Category, Material, Thk/Section, Part, Length, Width, Qty, Total, Notes."""
    g = grouped(proj); allow = proj.cat["defaults"]["solid_allowance_mm"]
    grain = lambda it: (f"{T('grain')}: {T('grain_' + it['grain'])}" if it["grain"] else "")
    note = lambda it, pre="": " ".join(s for s in (pre, it["note"]) if s)
    L = [T("bom_header")]
    for it in sorted(g["panel"], key=lambda i: (i["material_name"], i["thk"], -i["length"])):
        L.append((T("cat_panel"), it["material_name"], f"{it['thk']:g} mm", ", ".join(it["parts"]), it["length"], it["width"], it["qty"],
                  f"{it['length']*it['width']*it['qty']/1e6:.3f} m2", note(it, grain(it))))
    for it in sorted(g["solid"], key=lambda i: (i["material_name"], -i["length"])):
        rough = T("rough_suggested", l=it["length"] + allow["length"], w=it["width"] + allow["width"],
                  t=f"{it['thk'] + allow['thickness']:g}")
        L.append((T("cat_solid"), it["material_name"], f"{it['thk']:g} mm", ", ".join(it["parts"]), it["length"], it["width"], it["qty"],
                  f"{it['length']*it['width']*it['thk']*it['qty']/1e9:.4f} m3", note(it, rough)))
    for it in sorted(g["profile"], key=lambda i: (i["material_name"], i["section"], -i["length"])):
        L.append((T("cat_profile"), it["material_name"], it["section"], ", ".join(it["parts"]), it["length"], "", it["qty"],
                  f"{it['length']*it['qty']/1000:.2f} m", it["note"]))
    for it in g["glass"]:
        L.append((T("cat_glass"), it["material_name"], f"{it['thk']:g} mm", ", ".join(it["parts"]), it["length"], it["width"], it["qty"],
                  f"{it['length']*it['width']*it['qty']/1e6:.3f} m2", it["note"]))
    for it in g["hardware"]:
        L.append((T("cat_hardware"), it["material_name"], "", it["desc"], "", "", it["qty"], "", ""))
    return L


def generate(proj, folder, sheet_name="Bill_of_Materials"):
    """Writes CSV (';' separator) and Markdown to the folder, and a spreadsheet in the document."""
    L = rows(proj)
    os.makedirs(folder, exist_ok=True)
    f_csv = os.path.join(folder, f"{proj.name}_Bill_of_Materials.csv")
    with open(f_csv, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f, delimiter=";").writerows(L)
    tot = totals(proj)
    md = [f"# {T('bom_title', name=proj.name.replace('_', ' '))}", "", "| " + " | ".join(L[0]) + " |", "|" + "---|" * len(L[0])]
    md += ["| " + " | ".join(str(c) for c in r) + " |" for r in L[1:]]
    md += ["", f"## {T('totals')}", ""]
    for k, v in tot["area_m2"].items(): md.append(f"- {k}: {v:.2f} m2")
    for k, v in tot["rough_volume_m3"].items(): md.append(f"- {k}: {v:.4f} m3 {T('rough_volume')}")
    for k, v in tot["linear_m"].items(): md.append(f"- {k}: {v:.2f} m")
    for k, v in tot["hardware"].items(): md.append(f"- {k}: {v} {T('units')}")
    f_md = os.path.join(folder, f"{proj.name}_Bill_of_Materials.md")
    with open(f_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    sh = proj.doc.getObject(sheet_name)
    if sh is None:
        sh = proj.doc.addObject("Spreadsheet::Sheet", sheet_name); sh.Label = sheet_name.replace("_", " ")
    else:
        sh.clearAll()
    cols = "ABCDEFGHI"
    for r, row in enumerate(L, start=1):
        for c, v in zip(cols, row):
            sh.set(f"{c}{r}", "'" + str(v) if v != "" else "")
    proj.doc.recompute()
    return dict(csv=f_csv, md=f_md, sheet=sh.Name, rows=len(L) - 1, totals=tot)
