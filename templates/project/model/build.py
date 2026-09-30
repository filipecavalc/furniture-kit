"""<Project name> - parametric model and deliverables.

Run inside FreeCAD (MCP execute_code), with the absolute path of this file:
    __file__ = r"<kit>/projects/<Name>/model/build.py"; exec(open(__file__, encoding="utf-8").read())
    build()          # creates the model and returns the check report
    deliverables()   # bill of materials, cut list, images, drawings, export for rendering
Start from the closest example in examples/ when writing the model.
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

NAME = os.path.basename(HERE)


def build():
    pj = project.Project(NAME, folder=HERE)
    pj.params([
        ("width", 800, "Overall width"),
    ])
    # parts: pj.panel / pj.solid / pj.profile / pj.glass / pj.hardware
    pj.recompute()
    images.use(pj); images.cam(35, 22)
    return check.report(pj)


def deliverables():
    pj = project.open_project(NAME, folder=HERE)
    out = {"check": check.report(pj)}
    out["bom"] = bom.generate(pj, pj.dir("cutlist"))["csv"]
    out["cutlist"] = cutlist.generate(pj, pj.dir("cutlist"))
    out["views"] = images.standard_views(pj, pj.dir("images"))
    export.glb(pj, os.path.join(pj.dir("model"), f"{NAME}.glb"))
    out["model"] = pj.save()
    return out
