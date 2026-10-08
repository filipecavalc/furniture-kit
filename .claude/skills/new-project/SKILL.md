---
name: new-project
description: Create a new furniture project folder (projects/<Name>) from the template and fill in its project.md. Use when the user starts a new piece of furniture, in the references or briefing phase.
---

# New project

1. Pick a name with the user: letters, digits and underscores, starting with a letter, no accents or
   spaces (`Shoe_Cabinet`, `Garden_Bench`, `Wardrobe_2_Doors`). The folder name becomes the FreeCAD
   document name and the library rejects anything else. If `projects/<Name>/project.md` already
   exists, open it instead.
2. Create `projects/<Name>/` by copying `templates/project/` (it contains `project.md` and
   `model/build.py`), plus the empty folders `references/`, `images/`, `drawings/`, `cutlist/`,
   `render/`. Use your file tools; no script or Python is needed.
3. Fill `project.md`: title, creation date, and whatever is already known (references, briefing).
   Write it in the user's language.
4. Images the user sends go in `references/`, each noted in `project.md` > References with what to
   take from it (proportions, joints, finish).
5. Do not write the model yet: `model/build.py` stays as the template until the user asks to design.
   When they do, start from the closest example (`examples/Drawer_Cabinet` for panels and drawers,
   `examples/Industrial_Table` for metal profiles and solid wood) and keep the template's header,
   which finds the kit root on its own.
