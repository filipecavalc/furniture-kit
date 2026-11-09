"""Unit tests for the parts of the library that do not need FreeCAD (plain Python + pytest)."""
import os
import sys

import pytest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


@pytest.fixture(autouse=True)
def english():
    """Messages in English whatever config/local.json says."""
    from furniture import i18n
    i18n.set_language("en")
    yield
    i18n.set_language(None)
