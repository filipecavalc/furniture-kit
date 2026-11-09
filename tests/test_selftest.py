"""The self-test's model check fails on collisions or invalid parts (FreeCAD replaced by fakes)."""
import types

import pytest

from furniture import selftest


def fakes(collisions=(), invalid=()):
    pj = types.SimpleNamespace(parts=lambda: ["A", "B", "C"])
    project = types.SimpleNamespace(open_project=lambda name, folder=None: pj)
    check = types.SimpleNamespace(collisions=lambda p: list(collisions), invalid=lambda p: list(invalid))
    return project, check


def test_model_check_passes_on_a_clean_model():
    assert selftest._model_check(*fakes(), "Table", "folder") == "3 parts, no collisions, no invalid parts"


def test_model_check_fails_on_collisions():
    with pytest.raises(AssertionError, match=r"collisions=\[\('Leg', 'Rail', 12.5\)\]"):
        selftest._model_check(*fakes(collisions=[("Leg", "Rail", 12.5)]), "Table", "folder")


def test_model_check_fails_on_invalid_parts():
    with pytest.raises(AssertionError, match=r"invalid=\['Top'\]"):
        selftest._model_check(*fakes(invalid=["Top"]), "Table", "folder")


def test_failed_check_is_recorded_as_a_failed_step():
    results = []
    selftest._step(results, "Table: check", lambda: selftest._model_check(*fakes(invalid=["Top"]), "Table", "f"))
    assert results[0]["ok"] is False and "invalid=['Top']" in results[0]["error"]
