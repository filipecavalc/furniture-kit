"""Export for rendering in Blender.

glb()       -> <file>.glb + <file>.materials.json (material, type, grain and render settings per part)
assembly()  -> <file>.assembly.json, the script read by scripts/animate_assembly.py
"""
import os, json
from . import check
from .images import parts_of


def glb(proj, path):
    import ImportGui
    parts = proj.parts(visible=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ImportGui.export(parts, path)
    mats = proj.cat["materials"]
    mapping = {o.Label: dict(material=o.Furn_Material, type=o.Furn_Type, grain=o.Furn_Grain,
                             render=mats[o.Furn_Material].get("render", {})) for o in parts}
    with open(os.path.splitext(path)[0] + ".materials.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=1)
    return path


def assembly(proj, glb_path, steps, title, final=""):
    """Writes <glb>.assembly.json for scripts/animate_assembly.py from simple steps.

    steps: list of dict(
        title="Step 1 - Carcass", caption="Sides, bottom and kick board",
        parts=[groups or part labels],         # parts that enter in this step
        entry=(0, 0, 400),                     # mm offset each part slides in from
        az=35, el=22, zoom=1.0,                # camera (azimuth, elevation; zoom 1 = whole piece)
        interval=0.4, dur=1.0)                 # seconds between parts / duration of each move
    For grouped moves (lids, drawers), hardware that screws in, or custom camera targets, edit the
    JSON by hand; the full schema is documented at the top of scripts/animate_assembly.py.
    """
    bb = check.envelope(proj)
    kinds = {o.Label: o.Furn_Type for o in proj.parts()}
    shots, items = [], []
    for i, st in enumerate(steps, 1):
        sid = f"s{i}"
        shots.append(dict(id=sid, title=st["title"], caption=st.get("caption", ""), target="items",
                          az=st.get("az", 35), el=st.get("el", 22), zoom=st.get("zoom", 1.0),
                          interval=st.get("interval", 0.4), dur=st.get("dur", 1.0)))
        for lab in parts_of(proj, st["parts"], strict=True):
            items.append(dict(label=lab, shot=sid, type=kinds.get(lab, "panel"), entry=list(st.get("entry", (0, 0, 300)))))
    data = dict(title=title, final=final, bbox=[[bb.XMin, bb.YMin, bb.ZMin], [bb.XMax, bb.YMax, bb.ZMax]],
                shots=shots, items=items, groups={})
    path = os.path.splitext(glb_path)[0] + ".assembly.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return path
