# Step-by-step assembly animation (Blender in the background).
# Input: .glb exported from FreeCAD + .materials.json + .assembly.json (next to the .glb).
#   blender -b --factory-startup --python scripts/animate_assembly.py -- <model.glb> <out.mp4>
#           [--fps 24] [--resolution 1280x720] [--engine eevee|cycles] [--samples 64]
#           [--frame N[,M] (renders only those frames as PNG, to check before the video)]
#           [--until N (cuts the video at frame N)] [--save-blend]
# Use absolute paths: with relative paths Blender may write somewhere else.
#
# .assembly.json (furniture.export.assembly() writes a simple one; edit by hand for more):
# {
#   "title": "Opening title",  "final": "Closing caption",
#   "bbox": [[xmin, ymin, zmin], [xmax, ymax, zmax]],           # model envelope in mm (FreeCAD)
#   "shots": [{
#       "id": "s1", "title": "Step 1", "caption": "text at the bottom of the frame",
#       "target": "all" | "items" | [[x0,y0,z0], [x1,y1,z1]],   # what the camera frames (mm)
#       "az": 35, "el": 22, "zoom": 1.0,                         # zoom only applies to "all"
#       "interval": 0.4, "dur": 1.0,                             # s between parts / s per move
#       "interval_screw": 0.3, "dur_screw": 0.8,                 # same, for screwed hardware
#       "move":  [action, ...],                                  # group moves at the start of the shot
#       "after": [action, ...]                                   # group moves after the parts
#   }],
#   "items": [{
#       "label": "Side_Left", "shot": "s1", "type": "panel",    # type from Furn_Type
#       "entry": [0, 0, 300],                                    # mm offset the part slides in from
#       "together": false,                                       # true = starts with the previous item
#       "group": "",                                             # moves along with this group afterwards
#       "origin": [x, y, z], "axis": [0, 0, -1], "turns": 4      # hardware only: screws in along the axis
#   }],
#   "groups": {"Lid": {"pivot": [x, y, z], "parent": "", "base": [0, 0, 0], "axis": [1, 0, 0]}},
#   "extra": {"open": {"group": "Lid", "degrees": -100}}        # optional: opens and closes at the end
# }
# action = {"group": "Lid", "path": [[dx,dy,dz], ...], "angles": [deg, ...], "rotate": deg, "delay": s, "dur": s}
#   path: offsets in mm relative to the final position; angles: rotation along the path; rotate: final angle.
import bpy, sys, os, json, math, argparse
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out")
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--resolution", default="1280x720")
ap.add_argument("--engine", default="eevee")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--frame", default="")
ap.add_argument("--until", type=int, default=0)
ap.add_argument("--save-blend", action="store_true")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])


def use_nodes(idblock):
    """Node trees are always on in newer Blender; 'use_nodes' is deprecated (removed in 6.0)."""
    try:
        idblock.use_nodes = True
    except AttributeError:
        pass

base_file = os.path.splitext(A.glb)[0]
MAP = json.load(open(base_file + ".materials.json", encoding="utf-8"))
SEQ = json.load(open(base_file + ".assembly.json", encoding="utf-8"))
DEFAULT = {"mode": "solid", "color": [0.55, 0.56, 0.58], "roughness": 0.3, "metal": 1.0}
FPS = A.fps

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=A.glb)
OBJ = {}
for o in bpy.data.objects:
    if o.type == "MESH":
        OBJ[o.name.rsplit(".", 1)[0] if o.name.rsplit(".", 1)[-1].isdigit() else o.name] = o
parts = list(OBJ.values())
for o in parts:                                   # detach from the glTF hierarchy keeping the position
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
bpy.context.view_layer.update()


def world_bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


# mm -> Blender units, checked against the model envelope
bmin, bmax = world_bbox(parts)
jb = [Vector(v) for v in SEQ["bbox"]]
K = (bmax.x - bmin.x) / (jb[1].x - jb[0].x)
offset = bmin - jb[0] * K                      # should be ~0 (no offset between FreeCAD and glTF)
print("SCALE", K, "OFFSET", offset)
mm = lambda v: Vector(v) * K + offset


# ---------------------------------------------------------------- materials (same logic as render.py)
_cache = {}

def mat_solid(name, r):
    m = bpy.data.materials.new(name); use_nodes(m)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*r["color"], 1); b.inputs["Roughness"].default_value = r.get("roughness", 0.5)
    b.inputs["Metallic"].default_value = r.get("metal", 0.0)
    return m

def mat_glass(name, r):
    m = mat_solid(name, r); b = m.node_tree.nodes["Principled BSDF"]
    for k in ("Transmission Weight", "Transmission"):
        if k in b.inputs: b.inputs[k].default_value = 1.0; break
    b.inputs["IOR"].default_value = 1.5
    return m

def mat_wood(name, r, axis):
    m = bpy.data.materials.new(name); use_nodes(m)
    N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = r.get("roughness", 0.45)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    sc = [26.0, 26.0, 26.0]; sc[axis] = 0.9
    mp.inputs["Scale"].default_value = sc
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2
    nz.inputs["Detail"].default_value = 6.0; nz.inputs["Distortion"].default_value = 0.7
    nf = N.new("ShaderNodeTexNoise"); nf.inputs["Scale"].default_value = 60.0; nf.inputs["Detail"].default_value = 4.0
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.38; cr.color_ramp.elements[0].color = (*r["dark"], 1)
    cr.color_ramp.elements[1].position = 0.62; cr.color_ramp.elements[1].color = (*r["light"], 1)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 0.15
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], nz.inputs["Vector"]); L.new(mp.outputs["Vector"], nf.inputs["Vector"])
    L.new(nz.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], mix.inputs["A"]); L.new(nf.outputs["Color"], mix.inputs["B"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m

def material_for(name, o):
    info = MAP.get(name, {})
    key = info.get("material", "_default")
    r = info.get("render") or DEFAULT
    if r["mode"] == "wood":
        bb = [Vector(c) for c in o.bound_box]           # in the part's own frame: the texture uses 'Object' coordinates
        ext = [max(p[i] for p in bb) - min(p[i] for p in bb) for i in range(3)]
        order = sorted(range(3), key=lambda i: -ext[i])
        axis = order[1] if info.get("grain") == "width" else order[0]
        k = (key, axis)
        if k not in _cache: _cache[k] = mat_wood(f"{key}_{'XYZ'[axis]}", r, axis)
        return _cache[k]
    if key not in _cache: _cache[key] = mat_glass(key, r) if r["mode"] == "glass" else mat_solid(key, r)
    return _cache[key]

for name, o in OBJ.items():
    o.data = o.data.copy()
    o.data.materials.clear(); o.data.materials.append(material_for(name, o))
    if MAP.get(name, {}).get("type") == "solid":
        bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0008; bv.segments = 2; bv.limit_method = "ANGLE"
    o.data.shade_flat() if hasattr(o.data, "shade_flat") else None

# ---------------------------------------------------------------- scene
center = (bmin + bmax) / 2; S = max(bmax - bmin)
bpy.ops.mesh.primitive_plane_add(size=S * 80, location=(center.x, center.y, bmin.z - 0.0005))
floor = bpy.context.object; floor.name = "Floor"; floor.data.materials.append(mat_solid("Floor", {"color": [0.22, 0.21, 0.19], "roughness": 0.7}))
w = bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world = w; use_nodes(w)
hdri = bpy.utils.system_resource("DATAFILES", path=os.path.join("studiolights", "world", "interior.exr"))
if hdri and os.path.exists(hdri):
    env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri)
    w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

light_focus = bpy.data.objects.new("LightFocus", None); bpy.context.collection.objects.link(light_focus); light_focus.location = center
def light(name, rel, energy, size):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy * (S / 0.9) ** 2; d.size = size * S / 0.9
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = center + Vector(rel) * S
    c = o.constraints.new("TRACK_TO"); c.target = light_focus; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
light("Key_Light", (-1.6, -2.2, 2.4), 150, 1.4)
light("Fill_Light", (2.4, -1.0, 1.2), 40, 2.5)
light("Back_Light", (0.5, 2.5, 1.8), 40, 2.0)

cam_d = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", cam_d)
bpy.context.collection.objects.link(cam); sc = bpy.context.scene; sc.camera = cam
cam_d.lens = 35; cam_d.clip_start = 0.01
target = bpy.data.objects.new("Target", None); bpy.context.collection.objects.link(target)
tt = cam.constraints.new("TRACK_TO"); tt.target = target; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
rx, ry = (int(v) for v in A.resolution.lower().split("x"))
fov_v = 2 * math.atan((36 * ry / rx) / 2 / cam_d.lens)


def frame_on(lo, hi, az, el, zoom=1.0):
    c = (lo + hi) / 2; R = max((hi - lo).length / 2, 0.08) * zoom
    dist = R / math.sin(fov_v / 2) * 1.12
    c = c - Vector((0, 0, R * 0.14))                  # lower the target: the caption band covers the bottom of the frame
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    return c, c + d * dist


def key_cam(f, target_pos, cam_pos):
    target.location = target_pos; target.keyframe_insert("location", frame=f)
    cam.location = cam_pos; cam.keyframe_insert("location", frame=f)


# ---------------------------------------------------------------- captions (dark band at the bottom, attached to the camera)
def mat_emission(name, color, strength=1.0):
    m = bpy.data.materials.new(name); use_nodes(m); N = m.node_tree.nodes
    for n in list(N): N.remove(n)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1); em.inputs["Strength"].default_value = strength
    out = N.new("ShaderNodeOutputMaterial"); m.node_tree.links.new(em.outputs[0], out.inputs[0])
    return m
M_TXT = mat_emission("Text", (1, 1, 1), 1.0); M_TIT = mat_emission("Title", (1.0, 0.78, 0.35), 1.0)
M_BAND = mat_emission("Band", (0.02, 0.02, 0.025), 1.0)
DZ = 0.05                                                     # captions 5 cm from the camera (in front of everything)
LW = 36 / cam_d.lens * DZ; LH = LW * ry / rx                  # visible width/height at that distance
bpy.ops.mesh.primitive_plane_add(size=1)
band = bpy.context.object; band.name = "Band"; band.data.materials.append(M_BAND)
band.parent = cam; band.location = (0, -LH / 2 + LH * 0.065, -DZ * 1.001); band.scale = (LW * 1.02, LH * 0.13, 1)
band.visible_shadow = False


def text(body, size, pos, mat, width):
    cu = bpy.data.curves.new("txt", "FONT"); cu.body = body; cu.size = size
    cu.text_boxes[0].width = width; cu.align_x = "LEFT"
    o = bpy.data.objects.new("Caption", cu); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat); o.parent = cam; o.location = pos; o.visible_shadow = False
    return o


def show_between(o, f0, f1):
    for f, v in ((0, True), (f0, False), (f1, True)):
        o.hide_render = v; o.hide_viewport = v
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)


# ---------------------------------------------------------------- hardware pivots (origin at the contact point)
def pivot(o, origin_mm, axis):
    p = mm(origin_mm); M = o.matrix_world.copy()
    pl = M.inverted() @ p
    o.data.transform(Matrix.Translation(-pl)); o.matrix_world = M @ Matrix.Translation(pl)
    a = Vector(axis).normalized()
    rot = a.to_track_quat("Z", "Y").to_matrix().to_4x4()
    e_pos = bpy.data.objects.new(o.name + "_pos", None); bpy.context.collection.objects.link(e_pos)
    e_pos.matrix_world = Matrix.Translation(p) @ rot
    e_rot = bpy.data.objects.new(o.name + "_rot", None); bpy.context.collection.objects.link(e_rot)
    e_rot.parent = e_pos; e_rot.matrix_parent_inverse = Matrix(); e_rot.location = (0, 0, 0)
    mw = o.matrix_world.copy(); o.parent = e_rot; o.matrix_parent_inverse = Matrix()
    bpy.context.view_layer.update()
    o.matrix_world = mw                              # local = inverse(parent) x world
    return e_pos, e_rot


# ---------------------------------------------------------------- groups (sub-assemblies that move together)
GRP, GCUR, GACTIONS = {}, {}, []
for gn, gd in SEQ.get("groups", {}).items():
    e = bpy.data.objects.new("Group_" + gn, None); bpy.context.collection.objects.link(e)
    e.location = mm(gd["pivot"]) if gd.get("pivot") else Vector((0, 0, 0))
    e.rotation_mode = "AXIS_ANGLE"
    GRP[gn] = e
bpy.context.view_layer.update()
for gn, gd in SEQ.get("groups", {}).items():
    if gd.get("parent"):
        e = GRP[gn]
        e.parent = GRP[gd["parent"]]; e.matrix_parent_inverse = GRP[gd["parent"]].matrix_world.inverted()
bpy.context.view_layer.update()
REST = {gn: e.location.copy() for gn, e in GRP.items()}
for gn, gd in SEQ.get("groups", {}).items():
    GCUR[gn] = dict(off=Vector(gd.get("base", (0, 0, 0))), ang=0.0)


def attach(o, gn):
    """Attaches the object to the group without changing its rest position (inverse of the group's rest pose)."""
    if gn in GRP:
        e = GRP[gn]; mw = o.matrix_world.copy()
        o.parent = e; o.matrix_parent_inverse = e.matrix_world.inverted()
        o.matrix_world = mw


def group_action(gd, a, b):
    GACTIONS.append((gd, a, b))


def apply_actions():
    """Writes the group keys: path (mm offsets relative to the final position) and rotation (degrees)."""
    for gn, e in GRP.items():
        c = GCUR[gn]; axis = SEQ["groups"][gn].get("axis", (1, 0, 0))
        e.location = REST[gn] + c["off"] * K; e.keyframe_insert("location", frame=0)
        e.rotation_axis_angle = (0, *axis); e.keyframe_insert("rotation_axis_angle", frame=0)
    for gd, a, b in sorted(GACTIONS, key=lambda x: x[1]):
        gn = gd["group"]; e = GRP[gn]; c = GCUR[gn]; axis = SEQ["groups"][gn].get("axis", (1, 0, 0))
        e.location = REST[gn] + c["off"] * K; e.keyframe_insert("location", frame=a)
        e.rotation_axis_angle = (math.radians(c["ang"]), *axis); e.keyframe_insert("rotation_axis_angle", frame=a)
        path = gd.get("path")
        if path:
            n = len(path)
            angs = gd.get("angles")
            for k, pt in enumerate(path, 1):
                fk = a + int(round((b - a) * k / n))
                e.location = REST[gn] + Vector(pt) * K; e.keyframe_insert("location", frame=fk)
                if angs:                                   # rotation following the path (point by point)
                    e.rotation_axis_angle = (math.radians(angs[k - 1]), *axis)
                    e.keyframe_insert("rotation_axis_angle", frame=fk)
            c["off"] = Vector(path[-1])
            if angs:
                c["ang"] = angs[-1]
        if "rotate" in gd and not gd.get("angles"):
            e.rotation_axis_angle = (math.radians(gd["rotate"]), *axis); e.keyframe_insert("rotation_axis_angle", frame=b)
            c["ang"] = gd["rotate"]


# ---------------------------------------------------------------- timeline
sec = lambda s: int(round(s * FPS))
items_by_shot = {}
for it in SEQ["items"]:
    items_by_shot.setdefault(it["shot"], []).append(it)
all_lo, all_hi = bmin, bmax
f = 1
# opening: title over the finished piece
tit = text(SEQ.get("title", "Assembly"), LH * 0.07, (-LW * 0.45, LH * 0.12, -DZ), M_TIT, LW * 0.9)
c0, p0 = frame_on(all_lo, all_hi, 35, 22)
key_cam(f, c0, p0)
f_start = f + sec(3.0)
show_between(tit, f, f_start)
f = f_start
last = (c0, p0)
for shot in SEQ["shots"]:
    its = items_by_shot.get(shot["id"], [])
    tg = shot.get("target", "items")
    if tg == "all":
        lo, hi = all_lo, all_hi
    elif isinstance(tg, list):
        lo, hi = mm(tg[0]), mm(tg[1])
    else:
        found = [OBJ[i["label"]] for i in its if i["label"] in OBJ]
        lo, hi = world_bbox(found) if found else (all_lo, all_hi)
    c, p = frame_on(lo, hi, shot.get("az", 35), shot.get("el", 22), shot.get("zoom", 1.0) if tg == "all" else 1.0)
    key_cam(f, *last)
    f_move = f + sec(1.2)
    key_cam(f_move, c, p); last = (c, p)
    t_it = f_move - sec(0.2)
    for m in shot.get("move", []):
        a_ = f_move - sec(0.2) + sec(m.get("delay", 0)); b_ = a_ + sec(m["dur"])
        group_action(m, a_, b_); t_it = max(t_it, b_ + sec(0.2))
    end = t_it
    t_next = t_it; a = t_it
    for it in its:
        o = OBJ.get(it["label"])
        if o is None:
            print("NO OBJECT", it["label"]); continue
        screw = it.get("type") == "hardware" and "axis" in it
        interval = shot.get("interval_screw", shot.get("interval", 0.4)) if screw else shot.get("interval", 0.4)
        dur = shot.get("dur_screw", shot.get("dur", 1.0)) if screw else shot.get("dur", 1.0)
        if not it.get("together"):
            a = t_next
            t_next = a + sec(interval)
        b = a + sec(dur)
        end = max(end, b)
        ent = Vector(it.get("entry", (0, 0, 300))) * K
        if screw:
            e_pos, e_rot = pivot(o, it["origin"], it["axis"])
            final = e_pos.location.copy()
            e_pos.location = final + ent; e_pos.keyframe_insert("location", frame=a)
            e_pos.location = final; e_pos.keyframe_insert("location", frame=b)
            if it.get("turns"):
                e_rot.rotation_euler = (0, 0, -2 * math.pi * it["turns"]); e_rot.keyframe_insert("rotation_euler", frame=a)
                e_rot.rotation_euler = (0, 0, 0); e_rot.keyframe_insert("rotation_euler", frame=b)
            attach(e_pos, it.get("group", ""))
        else:
            final = o.location.copy()
            o.location = final + ent; o.keyframe_insert("location", frame=a)
            o.location = final; o.keyframe_insert("location", frame=b)
            attach(o, it.get("group", ""))
        show_between(o, a, 10 ** 7)
    for m in shot.get("after", []):
        a_ = end + sec(m.get("delay", 0)); b_ = a_ + sec(m["dur"])
        group_action(m, a_, b_); end = b_
    f_end = max(end, f_move) + sec(1.0 if its else 2.5)
    print("SHOT", shot["id"], f, f_end, shot.get("title", ""), "|", shot.get("caption", "")[:50])
    cap = text(f"{shot.get('title', '')}\n{shot.get('caption', '')}", LH * 0.028, (-LW * 0.49, -LH / 2 + LH * 0.1, -DZ), M_TXT, LW * 0.97)
    show_between(cap, f, f_end)
    f = f_end

# ending: optionally opens and closes a group, then orbits the finished piece
f_total = f + sec(16)
op = SEQ.get("extra", {}).get("open")
if op:
    group_action(dict(group=op["group"], rotate=op["degrees"]), f + sec(1.5), f + sec(3.5))
    group_action(dict(group=op["group"], rotate=0), f + sec(5.5), f + sec(7.5))
apply_actions()
cf, pf = frame_on(all_lo, all_hi, 25, 32)
key_cam(f, *last); key_cam(f + sec(1.2), cf, pf); key_cam(f + sec(8), cf, pf)
for k in range(1, 9):                                     # then orbits the piece
    ck, pk_ = frame_on(all_lo, all_hi, 25 + k * 45, 22)
    key_cam(f + sec(8 + k * 0.95), ck, pk_)
cap = text(SEQ.get("final", ""), LH * 0.028, (-LW * 0.49, -LH / 2 + LH * 0.1, -DZ), M_TXT, LW * 0.97)
show_between(cap, f, f_total)

sc.frame_start = 1; sc.frame_end = A.until or f_total
sc.render.fps = FPS
print("FRAMES", sc.frame_end, "SECONDS", sc.frame_end / FPS)

# ---------------------------------------------------------------- render
sc.render.resolution_x, sc.render.resolution_y = rx, ry
try: sc.view_settings.view_transform = "AgX"          # Blender 4.0+; older versions keep Filmic
except Exception: pass
sc.view_settings.exposure = -0.2
if A.engine == "cycles":
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(dv.type == kind for dv in prefs.devices):
                for dv in prefs.devices: dv.use = dv.type == kind
                sc.cycles.device = "GPU"; break
        except Exception: pass
    sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
else:
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = eng; break
        except Exception: pass
    try: sc.eevee.taa_render_samples = A.samples
    except Exception: pass
print("ENGINE", sc.render.engine, "DEVICE", getattr(sc.cycles, "device", "") if sc.render.engine == "CYCLES" else "GPU (EEVEE)",
      "SAMPLES", A.samples)
if A.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(A.out)[0] + ".blend")
for fr in [int(q) for q in A.frame.split(",") if q.strip()]:
    sc.frame_set(fr)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.splitext(A.out)[0] + f"_f{fr}.png"
    bpy.ops.render.render(write_still=True); print("FRAME", sc.render.filepath)
if not A.frame:
    ims = sc.render.image_settings
    try: ims.media_type = "VIDEO"
    except Exception: pass
    ims.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = A.out
    bpy.ops.render.render(animation=True); print("VIDEO", A.out)
