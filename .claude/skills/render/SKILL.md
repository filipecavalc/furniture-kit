---
name: render
description: Render photo-style images or a step-by-step assembly video of a project in Blender (command line, Blender stays closed). Use after deliverables() exported the .glb, when the user asks for a render, images for a client, or an assembly animation.
---

# Render and assembly animation

Blender path: from the environment check (`setup/check.ps1` / `setup/check.sh`). Use absolute paths
for every file and folder: with relative ones Blender may write somewhere else.

## Still images

Needs `<model>.glb` + `<model>.materials.json` (written by `export.glb`).

```
"<blender>" -b --factory-startup --python "<kit>/scripts/render.py" -- "<model.glb>" "<project>/render" <prefix> --shots 3q_right,front,3q_left
```

Options: `--samples` (default 256; 32-64 for a quick check or on CPU), `--no-wall` (free-standing
piece), `--save-blend` (keeps the scene), `--resolution 1600x1200`.
Shots: `3q_right`, `3q_left`, `front`, `high_right`, `high_left`, `side`, `detail_right`, `detail_left`.
The log prints `DEVICE OPTIX|CUDA|HIP|METAL|ONEAPI` or `DEVICE CPU`.

## Assembly video (MP4)

Needs `<model>.glb` + `.materials.json` + `.assembly.json`. `export.assembly(pj, glb, steps, title, final)`
writes a simple `.assembly.json` (parts slide in step by step); the full format (sub-assemblies that
move together, lids that open, screws turning in) is documented at the top of
`scripts/animate_assembly.py`. Build the steps from the assembly guide, so the video matches it.

```
"<blender>" -b --factory-startup --python "<kit>/scripts/animate_assembly.py" -- "<model.glb>" "<project>/render/assembly.mp4"
```

Check single frames first with `--frame 200,600` (writes `<out>_f200.png`...), look at them, then
render the video. Options: `--fps`, `--resolution 1920x1080`, `--engine eevee|cycles`, `--samples`,
`--until N`, `--save-blend`. Rules for a good video: parts never float (each enters from a direction
that makes physical sense), groups that are assembled first move together, one caption per step.

## Always

Open the PNGs (and a few frames of the video) and check them before handing them over. Wood in the
render is procedural (approximate colour and grain), not the manufacturer's texture: say so when
presenting to a client.
