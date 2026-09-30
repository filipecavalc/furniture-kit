# Photo-style render of a model exported by the 'furniture' library (FreeCAD -> .glb + .materials.json).
# Runs in Blender in the background (no need to open Blender):
#   blender -b --factory-startup --python scripts/render.py -- <model.glb> <output_folder> <prefix>
#           [--samples 256] [--shots 3q_right,front,3q_left] [--no-wall] [--save-blend] [--resolution 1600x1200]
# Shots: 3q_right, 3q_left, front, high_right, high_left, side, detail_right, detail_left
# GPU: tries OptiX, CUDA, HIP, Metal and oneAPI; falls back to the CPU.
import bpy, sys, os, json, math, argparse
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out"); ap.add_argument("prefix")
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--shots", default="3q_right,front,3q_left")
ap.add_argument("--no-wall", action="store_true")
ap.add_argument("--save-blend", action="store_true")
ap.add_argument("--resolution", default="1600x1200")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

map_file = os.path.splitext(A.glb)[0] + ".materials.json"
MAP = json.load(open(map_file, encoding="utf-8")) if os.path.exists(map_file) else {}
DEFAULT = {"mode": "solid", "color": [0.78, 0.78, 0.76], "roughness": 0.5}
os.makedirs(A.out, exist_ok=True)

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=A.glb)
parts = [o for o in bpy.data.objects if o.type == "MESH"]


def world_bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


# ---------------------------------------------------------------- materials
_cache = {}

def mat_solid(name, r):
    m = bpy.data.materials.new(name); m.use_nodes = True
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
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = r.get("roughness", 0.45)
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    sc = [26.0, 26.0, 26.0]; sc[axis] = 0.9                     # stretched along the grain
    mp.inputs["Scale"].default_value = sc
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2
    nz.inputs["Detail"].default_value = 6.0; nz.inputs["Distortion"].default_value = 0.7
    nf = N.new("ShaderNodeTexNoise"); nf.inputs["Scale"].default_value = 60.0; nf.inputs["Detail"].default_value = 4.0
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.38; cr.color_ramp.elements[0].color = (*r["dark"], 1)
    cr.color_ramp.elements[1].position = 0.62; cr.color_ramp.elements[1].color = (*r["light"], 1)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 0.15
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.05
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], nz.inputs["Vector"]); L.new(mp.outputs["Vector"], nf.inputs["Vector"])
    L.new(nz.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], mix.inputs["A"]); L.new(nf.outputs["Color"], mix.inputs["B"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"]); L.new(nf.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

def material_for(o):
    info = MAP.get(o.name) or MAP.get(o.name.rsplit(".", 1)[0]) or {}
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
    if key not in _cache:
        _cache[key] = mat_glass(key, r) if r["mode"] == "glass" else mat_solid(key, r)
    return _cache[key]

for o in parts:
    o.data.materials.clear(); o.data.materials.append(material_for(o))
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0008; bv.segments = 2; bv.limit_method = "ANGLE"

# ---------------------------------------------------------------- scene
bmin, bmax = world_bbox(parts); center = (bmin + bmax) / 2; S = max(bmax - bmin)
bpy.ops.mesh.primitive_plane_add(size=max(12, S * 10), location=(center.x, center.y, bmin.z))
bpy.context.object.name = "Floor"; bpy.context.object.data.materials.append(mat_solid("Floor", {"color": [0.30, 0.27, 0.24], "roughness": 0.6}))
if not A.no_wall:
    bpy.ops.mesh.primitive_plane_add(size=max(12, S * 10), location=(center.x, bmax.y + 0.01, bmin.z + max(6, S * 5)), rotation=(math.radians(90), 0, 0))
    bpy.context.object.name = "Wall"
    bpy.context.object.data.materials.append(mat_solid("Wall", {"color": [0.52, 0.50, 0.47], "roughness": 0.9}))

w = bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes = True
hdri = bpy.utils.system_resource("DATAFILES", path=os.path.join("studiolights", "world", "interior.exr"))
if hdri and os.path.exists(hdri):
    env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri)
    w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

focus = bpy.data.objects.new("Focus", None); bpy.context.collection.objects.link(focus); focus.location = center

def light(name, rel, energy, size):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy * (S / 0.9) ** 2; d.size = size * S / 0.9
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = center + Vector(rel) * S
    c = o.constraints.new("TRACK_TO"); c.target = focus; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
light("Key_Light", (-2.0, -2.4, 2.2), 220, 1.2)
light("Fill_Light", (2.6, -1.3, 0.9), 50, 2.5)

cam_d = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", cam_d)
bpy.context.collection.objects.link(cam); bpy.context.scene.camera = cam
tt = cam.constraints.new("TRACK_TO"); tt.target = focus; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"

# ---------------------------------------------------------------- render
sc = bpy.context.scene; sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
    try:
        prefs.compute_device_type = kind; prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices: d.use = d.type == kind
            sc.cycles.device = "GPU"; print("DEVICE", kind); break
    except Exception: pass
else:
    print("DEVICE CPU")
sc.cycles.samples = A.samples; sc.cycles.use_denoising = True
rx, ry = (int(v) for v in A.resolution.lower().split("x"))
sc.render.resolution_x, sc.render.resolution_y = rx, ry
sc.view_settings.view_transform = "AgX"
try: sc.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass

SHOTS = {  # azimuth (0 = front, + = right), elevation, zoom (1 = whole piece), focus height (fraction)
    "3q_right": (35, 18, 1.0, 0.5), "3q_left": (-35, 18, 1.0, 0.5), "front": (0, 6, 1.0, 0.5),
    "high_right": (30, 38, 1.0, 0.45), "high_left": (-30, 38, 1.0, 0.45), "side": (90, 8, 1.0, 0.5),
    "detail_right": (28, 35, 0.6, 0.65), "detail_left": (-28, 35, 0.6, 0.65),
}
lens = 50; fov_v = 2 * math.atan((36 * ry / rx) / 2 / lens)
R = (bmax - bmin).length / 2
for name in [t.strip() for t in A.shots.split(",") if t.strip()]:
    az, el, zoom, hf = SHOTS[name]
    target = Vector((center.x, center.y if zoom >= 1 else bmin.y + (bmax.y - bmin.y) * 0.3, bmin.z + (bmax.z - bmin.z) * hf))
    dist = R * zoom / math.sin(fov_v / 2) * 1.05
    a, e = math.radians(az), math.radians(el)
    direction = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    focus.location = target; cam.location = target + direction * dist; cam_d.lens = lens
    sc.render.filepath = os.path.join(A.out, f"{A.prefix}_{name}.png")
    bpy.ops.render.render(write_still=True); print("RENDER", sc.render.filepath)

if A.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A.out, f"{A.prefix}_scene.blend"))
