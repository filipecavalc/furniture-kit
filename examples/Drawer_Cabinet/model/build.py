"""Drawer cabinet (2 drawers, sheet goods) - parametric model and deliverables.

Reference for panel furniture: drawers, slides, fronts, detailed drawings with dimensions.

Run inside FreeCAD (MCP execute_code), with the absolute path of this file:
    __file__ = r"<kit>/examples/Drawer_Cabinet/model/build.py"; exec(open(__file__, encoding="utf-8").read())
    build()          # creates the model and returns the check report
    deliverables()   # bill of materials, cut list, images, drawings, export for rendering
"""
import os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # project folder
ROOT = HERE
while not os.path.isdir(os.path.join(ROOT, "scripts", "furniture")):
    if os.path.dirname(ROOT) == ROOT:
        raise RuntimeError("furniture-kit root not found above " + HERE)
    ROOT = os.path.dirname(ROOT)
if os.path.join(ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
import furniture; furniture.reload()
from furniture import project, check, bom, cutlist, images, drawing, export

NAME = "Drawer_Cabinet"
HF = "((height - edge_gap - plinth - front_gap) / 2)"                          # height of each front
ZD = {1: "(plinth + thk + 15)", 2: f"(plinth + {HF} + front_gap + 15)"}          # bottom of each drawer box
ZF = {1: "plinth", 2: f"(plinth + {HF} + front_gap)"}                             # bottom of each front
X0 = "(thk + slide_gap)"; WD = "(width - 2*thk - 2*slide_gap)"


def build():
    pj = project.Project(NAME, folder=HERE)
    pj.params([
        ("width", 800, "Overall width"), ("depth", 550, "Carcass depth (with back)"),
        ("height", 875, "Carcass height (floor to top, without worktop)"),
        ("thk", 18, "MDF thickness, carcass and fronts"), ("back_thk", 6, "Back panel thickness"),
        ("drawer_thk", 15, "MDF thickness, drawer boxes"), ("plinth", 100, "Plinth height"),
        ("setback", 50, "Plinth setback"), ("top_thk", 25, "Worktop thickness"),
        ("overhang", 20, "Worktop front overhang"), ("edge_gap", 2, "Gap between fronts and edges"),
        ("front_gap", 3, "Gap between fronts"), ("slide_gap", 13, "Side clearance per slide"),
        ("slide_len", 500, "Slide / drawer length"), ("drawer_h", 300, "Drawer box height"),
        ("rail_w", 100, "Width of the top rails"),
        ("open1", 0, "Drawer 1 opening (bottom)"), ("open2", 0, "Drawer 2 opening (top)"),
    ])
    C = "Carcass"
    pj.panel("Side_Left", C, ("thk", "depth - back_thk", "height"), (0, 0, 0), "mdf_white")
    pj.panel("Side_Right", C, ("thk", "depth - back_thk", "height"), ("width - thk", 0, 0), "mdf_white")
    pj.panel("Bottom", C, ("width - 2*thk", "depth - back_thk", "thk"), ("thk", 0, "plinth"), "mdf_white")
    pj.panel("Rail_Front", C, ("width - 2*thk", "rail_w", "thk"), ("thk", 0, "height - thk"), "mdf_white")
    pj.panel("Rail_Back", C, ("width - 2*thk", "rail_w", "thk"), ("thk", "depth - back_thk - rail_w", "height - thk"), "mdf_white")
    pj.panel("Plinth", C, ("width - 2*thk", "thk", "plinth"), ("thk", "setback", 0), "mdf_white")
    pj.panel("Back", C, ("width", "back_thk", "height - plinth"), (0, "depth - back_thk", "plinth"), "mdf_white")
    pj.panel("Worktop", "Top", ("width", "depth + thk + overhang", "top_thk"), (0, "-(thk + overhang)", "height"), "mdf_woodgrain_dark")
    for n in (1, 2):
        op = f"open{n}"
        pj.panel(f"Drawer_Front_{n}", "Fronts", ("width - 2*edge_gap", "thk", HF), ("edge_gap", f"-thk - {op}", ZF[n]), "mdf_woodgrain")
        g = f"Drawer_{n}"; zb = ZD[n]
        pj.panel(f"D{n}_Bottom", g, (WD, "slide_len", "back_thk"), (X0, f"-{op}", zb), "mdf_white")
        pj.panel(f"D{n}_Side_Left", g, ("drawer_thk", "slide_len", "drawer_h - back_thk"), (X0, f"-{op}", f"{zb} + back_thk"), "mdf_white")
        pj.panel(f"D{n}_Side_Right", g, ("drawer_thk", "slide_len", "drawer_h - back_thk"),
                 (f"{X0} + {WD} - drawer_thk", f"-{op}", f"{zb} + back_thk"), "mdf_white")
        pj.panel(f"D{n}_Inner_Front", g, (f"{WD} - 2*drawer_thk", "drawer_thk", "drawer_h - back_thk"),
                 (f"{X0} + drawer_thk", f"-{op}", f"{zb} + back_thk"), "mdf_white")
        pj.panel(f"D{n}_Back", g, (f"{WD} - 2*drawer_thk", "drawer_thk", "drawer_h - back_thk"),
                 (f"{X0} + drawer_thk", f"slide_len - drawer_thk - {op}", f"{zb} + back_thk"), "mdf_white")
        for side, x in (("Left", "thk"), ("Right", "width - thk - slide_gap")):
            pj.hardware(f"Slide_D{n}_{side}", "Hardware", ("slide_gap", "slide_len", 45), (x, 0, f"{zb} + (drawer_h - 45)/2"),
                        "Full-extension ball-bearing slide 500 mm (one side)")
        pj.hardware(f"Handle_D{n}", "Hardware", (160, 25, 12), ("width/2 - 80", f"-thk - 25 - {op}", f"{ZF[n]} + {HF} - 50"),
                    "Handle 160 mm (128 mm hole spacing)")
    pj.recompute()
    images.use(pj); images.cam(35, 22)
    return check.report(pj)


# ----------------------------------------------------------------------------- deliverables
def _sheet_assembly(pj, folder):
    v = pj.val; W, D, H, tt = v("width"), v("depth"), v("height"), v("top_thk")
    t, eg, fg, pl, ov = v("thk"), v("edge_gap"), v("front_gap"), v("plinth"), v("overhang")
    hf = (H - eg - pl - fg) / 2
    everything = pj.parts(visible=True)
    bb = check.envelope(pj); cx, cy, cz = bb.Center.x, bb.Center.y, bb.Center.z
    inner = [o for o in everything if not (o.Label.startswith(("Drawer_Front", "Handle")) or o.Label == "Worktop")]
    pg = drawing.page(pj, "Sheet_Assembly", "Sheet 1 - Assembly",
                      {"title": "Drawer cabinet - Assembly", "document_type": "Assembly drawing", "drawing_number": "DC-01",
                       "part_material": "See bill of materials", "scale": "1 : 10", "sheet_number": "1 / 2"})
    vF = drawing.view(pg, "V_Front", everything, (0, -1, 0), 85, 200, 0.1)
    vL = drawing.view(pg, "V_Side", everything, (-1, 0, 0), 197, 200, 0.1, xdir=(0, -1, 0))
    vT = drawing.view(pg, "V_Top", everything, (0, 0, 1), 85, 88, 0.1)
    vI = drawing.view(pg, "V_Inside", inner, (0, -1, 0), 322, 200, 0.1)
    vP = drawing.view(pg, "V_Perspective", everything, (1, -1, 1), 180, 88, 0.06)
    pj.recompute(); drawing.wait(25)
    X = lambda x: round(x - cx, 2); Z = lambda z: round(z - cz, 2); Yl = lambda y: round(-(y - cy), 2); Yt = lambda y: round(y - cy, 2)
    # front
    drawing.dim(pg, vF, (X(0), Z(H + tt)), (X(W), Z(H + tt)), "DistanceX", 0, 58)
    drawing.dim(pg, vF, (X(0), Z(0)), (X(0), Z(H + tt)), "DistanceY", -52, 0)
    drawing.dim(pg, vF, (X(W), Z(H)), (X(W), Z(H + tt)), "DistanceY", 64, 45)
    drawing.dim(pg, vF, (X(W - eg), Z(pl)), (X(W - eg), Z(pl + hf)), "DistanceY", 52, -16)
    drawing.dim(pg, vF, (X(W - eg), Z(pl + hf + fg)), (X(W - eg), Z(pl + 2 * hf + fg)), "DistanceY", 52, 23)
    drawing.dim(pg, vF, (X(W), Z(0)), (X(W - eg), Z(pl)), "DistanceY", 52, -40)
    # side
    drawing.dim(pg, vL, (Yl(D), Z(H + tt)), (Yl(-(t + ov)), Z(H + tt)), "DistanceX", 0, 58)
    drawing.dim(pg, vL, (Yl(D), Z(H)), (Yl(0), Z(0)), "DistanceX", 0, -56)
    drawing.dim(pg, vL, (Yl(D - v("back_thk")), Z(0)), (Yl(D), Z(H)), "DistanceY", -40, 0)
    # top
    drawing.dim(pg, vT, (X(0), Yt(D)), (X(W), Yt(D)), "DistanceX", 0, 42)
    drawing.dim(pg, vT, (X(0), Yt(-(t + ov))), (X(0), Yt(D)), "DistanceY", -52, 0)
    # inside (own centre: x 0..W, z 0..H)
    icx, icz = W / 2, H / 2
    Xi = lambda x: round(x - icx, 2); Zi = lambda z: round(z - icz, 2)
    x0 = t + v("slide_gap"); x1 = W - t - v("slide_gap"); dh = v("drawer_h")
    zb1 = pl + t + 15; zb2 = pl + hf + fg + 15
    drawing.dim(pg, vI, (Xi(t), Zi(pl + t)), (Xi(W - t), Zi(pl + t)), "DistanceX", 0, 50)
    drawing.dim(pg, vI, (Xi(x0), Zi(zb1)), (Xi(x1), Zi(zb1)), "DistanceX", 0, -52)
    drawing.dim(pg, vI, (Xi(x0), Zi(zb1)), (Xi(x0), Zi(zb1 + dh)), "DistanceY", -52, -15)
    drawing.dim(pg, vI, (Xi(x0), Zi(zb2)), (Xi(x0), Zi(zb2 + dh)), "DistanceY", -52, 22)
    for vv, txt, dy in ((vF, "FRONT VIEW", -58), (vL, "LEFT SIDE VIEW", -66), (vT, "TOP VIEW", -40),
                        (vI, "FRONT VIEW WITHOUT FRONTS AND WORKTOP", -64), (vP, "PERSPECTIVE", -42)):
        drawing.label(pg, vv, txt, dy)
    drawing.text(pg, ["NOTES", "1. Dimensions in millimetres.", "2. Carcass: white MDF 18 mm. Fronts: woodgrain MDF 18 mm.",
                      "3. Worktop: MDF 25 mm, 20 mm front overhang.", "4. Drawer boxes: MDF 15 mm. Bottoms: MDF 6 mm.",
                      "5. Full-extension slides 500 mm, 13 mm clearance per side.", "6. Handles 160 mm (128 mm hole spacing).",
                      "7. Gap between fronts 3 mm; at the edges 2 mm.", "8. Plinth 100 mm high, set back 50 mm."], 318, 98, 3.5, 150)
    return drawing.export_pdf(pg, os.path.join(folder, f"{NAME}_Sheet1_Assembly.pdf"))


def _sheet_parts(pj, folder):
    v = pj.val; t, sg, dt, dh, sl, bt = v("thk"), v("slide_gap"), v("drawer_thk"), v("drawer_h"), v("slide_len"), v("back_thk")
    wd = v("width") - 2 * t - 2 * sg
    drw = images.parts_of(pj, ["Drawer_1"]); drw = [pj.doc.getObjectsByLabel(l)[0] for l in drw]
    # compact parts table for the sheet
    sh = pj.doc.getObject("Sheet_Table") or pj.doc.addObject("Spreadsheet::Sheet", "Sheet_Table")
    sh.clearAll()
    for c, txt in zip("ABCDEF", ("Material", "Thk.", "Part", "Length", "Width", "Qty")): sh.set(f"{c}1", txt)
    r = 2
    clean = lambda s: (s.replace("_Left", "").replace("_Right", "").replace("_1", "").replace("_2", "")
                        .replace("D1_", "Drawer ").replace("D2_", "Drawer ").replace("_", " "))
    for it in sorted(bom.grouped(pj)["panel"], key=lambda i: (i["material_name"], i["thk"], -i["length"])):
        name = ", ".join(sorted(set(clean(s) for s in it["parts"])))
        for c, txt in zip("ABCDEF", (it["material_name"], f"{it['thk']:g}", name, it["length"], it["width"], it["qty"])):
            sh.set(f"{c}{r}", "'" + str(txt))
        r += 1
    for col, w in zip("ABCDEF", (190, 45, 260, 70, 60, 40)): sh.setColumnWidth(col, w)
    pj.recompute()
    pg = drawing.page(pj, "Sheet_Parts", "Sheet 2 - Drawer and parts",
                      {"title": "Drawer cabinet - Drawer and parts", "document_type": "Detail and parts list", "drawing_number": "DC-02",
                       "part_material": "See bill of materials", "scale": "1 : 5", "sheet_number": "2 / 2"})
    gF = drawing.view(pg, "D_Front", drw, (0, -1, 0), 125, 225, 0.2)
    gT = drawing.view(pg, "D_Top", drw, (0, 0, 1), 125, 100, 0.2)
    pj.recompute(); drawing.wait(20)
    drawing.dim(pg, gF, (-wd / 2, dh / 2), (wd / 2, dh / 2), "DistanceX", 0, 48)
    drawing.dim(pg, gF, (-wd / 2 + dt, dh / 2), (wd / 2 - dt, dh / 2), "DistanceX", 0, 38)
    drawing.dim(pg, gF, (-wd / 2, -dh / 2), (-wd / 2, dh / 2), "DistanceY", -84, 0)
    drawing.dim(pg, gT, (-wd / 2, sl / 2), (wd / 2, sl / 2), "DistanceX", 0, 56)
    drawing.dim(pg, gT, (-wd / 2, -sl / 2), (-wd / 2, sl / 2), "DistanceY", -84, 0)
    drawing.text(pg, "DRAWER - FRONT VIEW (2 pcs) - SCALE 1:5", 125, 186)
    drawing.text(pg, "DRAWER - TOP VIEW - SCALE 1:5", 125, 40)
    drawing.text(pg, "PARTS LIST", 318, 276, 5.0)
    drawing.table(pg, sh, 318, 205, end=f"F{r - 1}")
    drawing.text(pg, ["HARDWARE", "- 4 full-extension slides 500 mm (2 pairs)", "- 2 handles 160 mm (128 mm hole spacing)",
                      "- Carcass joinery: to be defined by the maker", "  (cam lock, dowel or screw)", "",
                      "DRAWER", f"- Sides, inner front and back: MDF {dt:g} mm", f"- MDF {bt:g} mm bottom under the sides",
                      f"- Overall height {dh:g} mm ({dh - bt:g} + bottom {bt:g})"], 318, 110, 3.5)
    return drawing.export_pdf(pg, os.path.join(folder, f"{NAME}_Sheet2_Parts.pdf"))


def deliverables():
    pj = project.open_project(NAME, folder=HERE)
    out = {"check": check.report(pj)}
    out["bom"] = bom.generate(pj, pj.dir("cutlist"))["csv"]
    out["cutlist"] = cutlist.generate(pj, pj.dir("cutlist"))
    # review images
    pi = pj.dir("images")
    vs = images.standard_views(pj, pi)
    pj.set("open2", 400); images.cam(-35, 25); a1 = images.save(os.path.join(pi, "07_top_drawer_open.png"))
    pj.set("open1", 450); pj.set("open2", 250); images.cam(30, 30); a2 = images.save(os.path.join(pi, "08_both_drawers_open.png"))
    images.cam(-25, 55); a3 = images.save(os.path.join(pi, "09_drawers_open_from_above.png"))
    pj.set("open1", 0); pj.set("open2", 0)
    caps = ["Front / right", "Front / left", "Front", "Side", "Back", "Top",
            "Top drawer open", "Both drawers open", "Drawers open - from above"]
    images.contact_sheet(list(zip(vs + [a1, a2, a3], caps)), 3, (620, 520), os.path.join(pi, "SHEET_views.png"), "Drawer cabinet - Views")
    exp = images.exploded(pj, {"Side_Left": (-330, 0, 0), "Side_Right": (330, 0, 0), "Bottom": (0, 0, -40), "Plinth": (0, -300, -60),
                               "Rail_Front": (0, 0, 200), "Rail_Back": (0, 0, 200), "Back": (0, 420, 0), "Worktop": (0, 0, 650),
                               "Fronts": (0, -900, 0), "Handle_D1": (0, -980, 0), "Handle_D2": (0, -980, 0),
                               "Drawer_1": (0, -520, 0), "Drawer_2": (0, -520, 0),
                               "Slide_D1_Left": (-170, 0, 0), "Slide_D2_Left": (-170, 0, 0),
                               "Slide_D1_Right": (170, 0, 0), "Slide_D2_Right": (170, 0, 0)},
                         os.path.join(pi, "A0_exploded_view.png"))
    steps = [("sides_bottom_plinth", ["Side_Left", "Side_Right", "Bottom", "Plinth"], 35, "Sides, bottom and plinth"),
             ("rails", ["Rail_Front", "Rail_Back"], 35, "Top rails"),
             ("back", ["Back"], 215, "Back panel (seen from behind)"),
             ("slides", [f"Slide_D{n}_{s}" for n in (1, 2) for s in ("Left", "Right")], 30, "Slides"),
             ("drawer_boxes", ["Drawer_1", "Drawer_2"], 30, "Drawer boxes"),
             ("fronts_and_handles", ["Fronts", "Handle_D1", "Handle_D2"], 35, "Fronts and handles"),
             ("worktop", ["Worktop"], 35, "Worktop - done")]
    asm = images.assembly(pj, steps, pi)
    images.contact_sheet([(exp, "Exploded view")] + asm, 4, (560, 520), os.path.join(pi, "SHEET_assembly.png"), "Drawer cabinet - Assembly")
    # drawings
    pd = pj.dir("drawings")
    out["drawings"] = [_sheet_assembly(pj, pd), _sheet_parts(pj, pd)]
    # export for rendering (closed and open) + assembly animation script
    pm = pj.dir("model")
    closed = export.glb(pj, os.path.join(pm, f"{NAME}_closed.glb"))
    export.assembly(pj, closed, [
        dict(title="Step 1 - Carcass", caption="Sides, bottom and plinth", parts=["Side_Left", "Side_Right", "Bottom", "Plinth"], entry=(0, 0, 400)),
        dict(title="Step 2 - Rails and back", caption="Top rails and back panel", parts=["Rail_Front", "Rail_Back", "Back"], entry=(0, 0, 400), az=-35),
        dict(title="Step 3 - Slides", caption="Slides on the sides", parts=["Slide_D1_Left", "Slide_D1_Right", "Slide_D2_Left", "Slide_D2_Right"], entry=(0, -500, 0)),
        dict(title="Step 4 - Drawers", caption="Drawer boxes, fronts and handles", parts=["Drawer_1", "Drawer_2", "Fronts", "Handle_D1", "Handle_D2"], entry=(0, -700, 0)),
        dict(title="Step 5 - Worktop", caption="Worktop screwed from inside", parts=["Worktop"], entry=(0, 0, 400)),
    ], "Drawer cabinet\nStep-by-step assembly", "Done.")
    pj.set("open1", 420); pj.set("open2", 240)
    export.glb(pj, os.path.join(pm, f"{NAME}_open.glb"))
    pj.set("open1", 0); pj.set("open2", 0)
    out["model"] = pj.save()
    return out
