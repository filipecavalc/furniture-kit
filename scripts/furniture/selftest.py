"""Self-test of the kit inside FreeCAD: builds the examples and every deliverable in a scratch folder.

Run inside FreeCAD (MCP execute_code), with KIT = the repository root:
    import sys; sys.path.insert(0, KIT + "/scripts")
    import furniture; furniture.reload(); from furniture import selftest
    print(selftest.run())                      # writes projects/_selftest/selftest.md and .json

Copies examples/* to projects/_selftest/<Name> (the examples themselves are never touched), runs
build() and deliverables() for each, plus the lumber plan, the assembly guide and a pt-BR cut list.
Everything runs in English except the pt-BR step, whatever config/local.json says.
Each step is timed; an error is recorded with its traceback and the next step still runs.
"""
import os, sys, json, time, shutil, platform, traceback
from . import ROOT, PROJECTS

OUT = os.path.join(PROJECTS, "_selftest")


def _env():
    import FreeCAD as App
    from PySide import QtGui, QtCore
    from .i18n import font
    from . import __version__
    info = dict(kit_version=__version__, os=platform.platform(), machine=platform.machine(), python=sys.version.split()[0],
                freecad=".".join(App.Version()[:3]), freecad_build=App.Version()[3] if len(App.Version()) > 3 else "",
                qt=QtCore.qVersion(), user_dir=App.getUserAppDataDir(), resource_dir=App.getResourceDir(), kit=ROOT)
    try:
        info["pdf_font"] = QtGui.QFontInfo(font(20)).family()
    except Exception as e:
        info["pdf_font"] = f"error: {e}"
    return info


def _step(results, name, fn):
    t0 = time.time()
    try:
        detail = fn()
        results.append(dict(step=name, ok=True, seconds=round(time.time() - t0, 1), detail=detail))
    except Exception:
        results.append(dict(step=name, ok=False, seconds=round(time.time() - t0, 1), error=traceback.format_exc()))


def _load(build_py):
    ns = {"__file__": build_py, "__name__": "selftest_build"}
    with open(build_py, encoding="utf-8") as f:
        exec(compile(f.read(), build_py, "exec"), ns)
    return ns


def _files(folder):
    out = []
    for dp, _, fs in os.walk(folder):
        for f in fs:
            p = os.path.join(dp, f)
            out.append((os.path.relpath(p, OUT).replace("\\", "/"), os.path.getsize(p)))
    return sorted(out)


def run(examples=("Drawer_Cabinet", "Industrial_Table")):
    import FreeCAD as App
    from . import project, lumber, guide, cutlist, i18n
    if os.path.isdir(OUT):
        for name in examples:
            shutil.rmtree(os.path.join(OUT, name), ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    results, env = [], _env()
    ns = {}
    i18n.set_language("en")          # same results on every machine, whatever config/local.json says
    try:
        _run_steps(examples, results, ns, project, lumber, guide, cutlist, i18n)
    finally:
        i18n.set_language(None)
    for name in examples:
        if name in App.listDocuments():
            App.closeDocument(name)
    return _report(results, env)


def _run_steps(examples, results, ns, project, lumber, guide, cutlist, i18n):
    for name in examples:
        src = os.path.join(ROOT, "examples", name)
        dst = os.path.join(OUT, name)
        _step(results, f"{name}: copy", lambda: shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            "*.FCStd", "*.FCBak", "*.glb", "*.json", "images", "drawings", "cutlist", "render")) and "ok")
        build_py = os.path.join(dst, "model", "build.py")
        _step(results, f"{name}: load build.py", lambda: ns.__setitem__(name, _load(build_py)) or "ok")
        if name in ns:
            _step(results, f"{name}: build()", lambda: ns[name]["build"]())
            _step(results, f"{name}: deliverables()", lambda: json.loads(json.dumps(ns[name]["deliverables"](), default=str)))
    if "Industrial_Table" in ns:
        folder = os.path.join(OUT, "Industrial_Table")
        pj = lambda: project.open_project("Industrial_Table", folder=folder)
        stock = [dict(name="Board 40 x 300", thk=35, width=280, length=3000, verify=True)]
        _step(results, "lumber plan", lambda: lumber.generate(pj(), os.path.join(folder, "cutlist"), stock))
        img = os.path.join(folder, "images", "A0_exploded_view.png")
        _step(results, "assembly guide", lambda: guide.pdf(os.path.join(folder, "Industrial_Table_Guide.pdf"), "Industrial table", [
            dict(title="Step 1 - Frame", images=[(img, "Exploded view")],
                 blocks=[("Parts", ["- 4 legs SQ 50x2", "- 4 rails RECT 30x50x1.5"]), ("How to", ["1. Weld the rails.", "2. Check the diagonals."])]),
            dict(title="Parts list", table=(("Part", "Qty", "Size"), [("Leg", 4, "725"), ("Rail", 4, "1380 / 580")], (3, 1, 2)))]))

        def pt_br():
            i18n.set_language("pt-BR")
            try:
                return cutlist.generate(pj(), os.path.join(folder, "cutlist_pt-BR"))
            finally:
                i18n.set_language("en")
        _step(results, "cut list in pt-BR", pt_br)


def _report(results, env):
    ok = sum(r["ok"] for r in results)
    report = dict(env=env, passed=ok, failed=len(results) - ok, steps=results, files=_files(OUT))
    with open(os.path.join(OUT, "selftest.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)
    md = ["# furniture-kit self-test", "", "## Environment", ""] + [f"- {k}: {v}" for k, v in env.items()]
    md += ["", f"## Steps ({ok} passed, {len(results) - ok} failed)", "", "| Step | Result | Seconds |", "|---|---|---|"]
    md += [f"| {r['step']} | {'OK' if r['ok'] else 'FAIL'} | {r['seconds']} |" for r in results]
    for r in results:
        if not r["ok"]:
            md += ["", f"### {r['step']}", "", "```", r["error"].rstrip(), "```"]
    md += ["", "## Files", ""] + [f"- {p} ({s} bytes)" for p, s in report["files"]]
    with open(os.path.join(OUT, "selftest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return f"self-test: {ok} passed, {len(results) - ok} failed - report: {os.path.join(OUT, 'selftest.md')}"
