"""Industrial dining table - black steel tube frame + solid-wood top made of glued boards.

Reference for projects with metal profiles and solid wood (bar cut list, automatic dimensions).

Run inside FreeCAD (MCP execute_code), with the absolute path of this file:
    __file__ = r"<kit>/examples/Industrial_Table/model/build.py"; exec(open(__file__, encoding="utf-8").read())
    build(); deliverables()
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

NAME = "Industrial_Table"
LEG = 50            # 50x50x2 square tube (legs)
FW, FH = 30, 50     # frame: 30 (width) x 50 (height) x 1.5 rectangular tube


def build():
    pj = project.Project(NAME, folder=HERE)
    pj.params([
        ("top_len", 1600, "Top length"), ("top_w", 800, "Top width"), ("height", 760, "Overall height"),
        ("top_thk", 35, "Solid top thickness"), ("n_boards", 4, "Number of boards in the top"),
        ("inset", 60, "Frame inset from the top edge"),
    ])
    # top made of boards glued along the length
    for i in range(int(pj.val("n_boards"))):   # changing n_boards requires running build() again
        pj.solid(f"Top_Board_{i + 1}", "Top", ("top_len", "top_w / n_boards", "top_thk"),
                 (0, f"{i} * top_w / n_boards", "height - top_thk"), "freijo", note="glue the boards; matte varnish finish")
    leg_h = "height - top_thk"
    z_frame = f"height - top_thk - {FH}"
    for name, x, y in (("Leg_FL", "inset", "inset"), ("Leg_FR", f"top_len - inset - {LEG}", "inset"),
                       ("Leg_BL", "inset", f"top_w - inset - {LEG}"), ("Leg_BR", f"top_len - inset - {LEG}", f"top_w - inset - {LEG}")):
        pj.profile(name, "Frame", f"SQ {LEG}x2", leg_h, (x, y, 0), axis="z", material="steel_black")
    L_long = f"top_len - 2*inset - {2 * LEG}"; L_short = f"top_w - 2*inset - {2 * LEG}"
    pj.profile("Rail_Front", "Frame", f"RECT {FW}x{FH}x1.5", L_long, (f"inset + {LEG}", "inset", z_frame), axis="x")
    pj.profile("Rail_Back", "Frame", f"RECT {FW}x{FH}x1.5", L_long, (f"inset + {LEG}", f"top_w - inset - {FW}", z_frame), axis="x")
    pj.profile("Rail_Left", "Frame", f"RECT {FW}x{FH}x1.5", L_short, ("inset", f"inset + {LEG}", z_frame), axis="y")
    pj.profile("Rail_Right", "Frame", f"RECT {FW}x{FH}x1.5", L_short, (f"top_len - inset - {FW}", f"inset + {LEG}", z_frame), axis="y")
    for name, x, y in (("Foot_FL", "inset", "inset"), ("Foot_FR", f"top_len - inset - {LEG}", "inset"),
                       ("Foot_BL", "inset", f"top_w - inset - {LEG}"), ("Foot_BR", f"top_len - inset - {LEG}", f"top_w - inset - {LEG}")):
        pj.hardware(name, "Hardware", (LEG, LEG, 2), (x, y, -2), "Levelling foot / end cap for 50x50 tube", material="hardware_black")
    pj.recompute()
    images.use(pj); images.cam(35, 22)
    return check.report(pj)


def deliverables():
    pj = project.open_project(NAME, folder=HERE)
    out = {"check": check.report(pj)}
    out["bom"] = bom.generate(pj, pj.dir("cutlist"))["csv"]
    out["cutlist"] = cutlist.generate(pj, pj.dir("cutlist"))
    pi = pj.dir("images")
    vs = images.standard_views(pj, pi)
    exp = images.exploded(pj, {"Top": (0, 0, 450), "Rail_Front": (0, -250, 120), "Rail_Back": (0, 250, 120),
                               "Rail_Left": (-300, 0, 120), "Rail_Right": (300, 0, 120), "Hardware": (0, 0, -120)},
                          os.path.join(pi, "A0_exploded_view.png"))
    caps = ["Front / right", "Front / left", "Front", "Side", "Back", "Top", "Exploded view"]
    images.contact_sheet(list(zip(vs + [exp], caps)), 4, (560, 480), os.path.join(pi, "SHEET_views.png"), "Industrial table - Views")
    # generic drawing: 3 views with overall dimensions + perspective
    everything = pj.parts(visible=True)
    pg = drawing.page(pj, "Sheet_Assembly", "Sheet 1 - Assembly",
                      {"title": "Industrial table - Assembly", "document_type": "Assembly drawing", "drawing_number": "IT-01",
                       "part_material": "Black steel + freijo", "scale": "1 : 20", "sheet_number": "1 / 1"})
    vF = drawing.view(pg, "V_Front", everything, (0, -1, 0), 110, 205, 0.05)
    vL = drawing.view(pg, "V_Side", everything, (-1, 0, 0), 235, 205, 0.05, xdir=(0, -1, 0))
    vT = drawing.view(pg, "V_Top", everything, (0, 0, 1), 110, 95, 0.05)
    vP = drawing.view(pg, "V_Perspective", everything, (1, -1, 1), 330, 205, 0.045)
    pj.recompute(); drawing.wait(25)
    for vv, txt in ((vF, "FRONT VIEW"), (vL, "LEFT SIDE VIEW"), (vT, "TOP VIEW")):
        drawing.envelope_dims(pg, vv)
        x0, x1, y0, y1 = drawing.extremes(vv); drawing.label(pg, vv, txt, y0 * vv.Scale - 12)
    drawing.label(pg, vP, "PERSPECTIVE", -38)
    drawing.text(pg, ["NOTES", "1. Dimensions in millimetres.", "2. Frame: steel tube 50x50x2 (legs) and 30x50x1.5 (frame),",
                      "   welded, matte black powder coat.", "3. Top: 4 freijo boards glued, 35 mm, matte varnish.",
                      "4. Top fixed with screws through the frame (to be defined).", "5. Levelling feet on the 4 legs."], 250, 100, 3.5, 160)
    out["drawings"] = [drawing.export_pdf(pg, os.path.join(pj.dir("drawings"), f"{NAME}_Sheet1_Assembly.pdf"))]
    export.glb(pj, os.path.join(pj.dir("model"), f"{NAME}.glb"))
    out["model"] = pj.save()
    return out
