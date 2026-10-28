# 3D model of ATARIA AT-SM23 (Blender)

`build_mixer2.py` builds the machine procedurally (proportions measured on the owner's photos) and renders a frame with Cycles.
Decals (`logo.png`, `icons.png`, `dial.png`, `display.png`) are cut from the real photos so lettering is always correct.

    python3.11 -m venv bpyenv && bpyenv/bin/pip install bpy==4.2.0
    bpyenv/bin/python build_mixer2.py -- out.png front34 64     # views: front34 | front | side | close_panel

The render is then passed to GPT Image as the first reference with "keep exact geometry, only make materials photoreal".
