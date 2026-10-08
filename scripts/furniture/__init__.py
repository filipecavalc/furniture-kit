"""Furniture design library (runs inside FreeCAD's Python).

Usage inside FreeCAD (MCP execute_code), with KIT = the repository root:
    import sys; sys.path.insert(0, KIT + "/scripts")
    import furniture; furniture.reload()

Project scripts (projects/<Name>/model/build.py) find the repository root on their own.
"""
import os, json, importlib

__version__ = "1.0.0"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_DIR = os.path.join(ROOT, "catalog")
PROJECTS = os.path.join(ROOT, "projects")
CONFIG_FILE = os.path.join(ROOT, "config", "local.json")

DEFAULT_CONFIG = {"language": "en", "catalog": "br"}


def config():
    """Per-user settings from config/local.json (gitignored), with defaults."""
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8-sig") as f:       # -sig: tolerates a BOM (Windows editors)
            cfg.update(json.load(f))
    return cfg


def catalog(name=None):
    """Material catalog catalog/<name>.json (default: the one set in config/local.json)."""
    name = name or config()["catalog"]
    path = os.path.join(CATALOG_DIR, name + ".json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"catalog '{name}' not found: {path}")
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def reload():
    """Reloads the package and every module (after editing the library or a git pull)."""
    import sys
    importlib.reload(sys.modules[__name__])
    from . import i18n, project, check, bom, cutlist, lumber, guide, images, drawing, export, selftest
    for m in (i18n, project, check, bom, cutlist, lumber, guide, images, drawing, export, selftest):
        importlib.reload(m)
    return "furniture reloaded"
