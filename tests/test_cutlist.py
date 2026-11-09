"""Sheet and bar nesting and the cut-list summary (furniture.cutlist, no Qt needed)."""
import random
from collections import Counter

import pytest

from furniture import cutlist, i18n
from furniture.i18n import T

W, H, KERF = 2730, 1830, 4          # a 2750 x 1850 sheet minus 10 mm trim on each side


def part(name, l, w, grain=""):
    return dict(name=name, l=l, w=w, grain=grain)


def random_parts(seed, n=40):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        a, b = rnd.randint(40, 1200), rnd.randint(40, 700)
        out.append(part(f"P{i}", max(a, b), min(a, b), rnd.choice(["", "", "length", "width"])))
    return out


def placed(sheets):
    return [q for sh in sheets for q in sh["pos"]]


def assert_valid_layout(sheets, W, H, kerf):
    """Independent of cutlist._check_sheets: inside the sheet, and at least one kerf between parts."""
    for sh in sheets:
        P = sh["pos"]
        for q in P:
            assert q["x"] >= 0 and q["y"] >= 0, q["name"]
            assert q["x"] + q["pw"] <= W and q["y"] + q["ph"] <= H, q["name"]
            assert sorted((q["pw"], q["ph"])) == sorted((q["l"], q["w"])), q["name"]
        for i, a in enumerate(P):
            for b in P[i + 1:]:
                gap_x = max(b["x"] - (a["x"] + a["pw"]), a["x"] - (b["x"] + b["pw"]))
                gap_y = max(b["y"] - (a["y"] + a["ph"]), a["y"] - (b["y"] + b["ph"]))
                assert max(gap_x, gap_y) >= kerf, (a["name"], b["name"])


# ------------------------------------------------------------------ sheets
@pytest.mark.parametrize("seed", range(20))
def test_nest_sheets_random_parts_never_overlap_or_leave_the_sheet(seed):
    parts = random_parts(seed)
    sheets = cutlist._nest_sheets(parts, W, H, KERF)
    assert_valid_layout(sheets, W, H, KERF)
    cutlist._check_sheets(sheets, W, H, KERF)            # the library's own check agrees
    assert Counter(q["name"] for q in placed(sheets)) == Counter(p["name"] for p in parts)


@pytest.mark.parametrize("seed", range(10))
def test_parts_with_grain_are_never_rotated(seed):
    """grain=length: the part length runs along the sheet length (x); grain=width: its width does."""
    sheets = cutlist._nest_sheets(random_parts(seed), W, H, KERF)
    for q in placed(sheets):
        if q["grain"] == "length":
            assert (q["pw"], q["ph"], q["rot"]) == (q["l"], q["w"], False), q["name"]
        elif q["grain"] == "width":
            assert (q["pw"], q["ph"], q["rot"]) == (q["w"], q["l"], True), q["name"]


def test_grain_wins_over_a_better_fit():
    # 1800 x 500 fits the 1000 x 2000 sheet only when rotated
    assert cutlist._nest_sheets([part("Free", 1800, 500)], 1000, 2000, 4)[0]["pos"][0]["rot"] is True
    with pytest.raises(ValueError, match="Grain_Part"):
        cutlist._nest_sheets([part("Grain_Part", 1800, 500, "length")], 1000, 2000, 4)


def test_kerf_is_left_between_neighbours():
    # two 500 x 1000 parts on a 1004 x 1000 sheet: they fit side by side with a 4 mm kerf, not with 5
    sheets = cutlist._nest_sheets([part("A", 1000, 500, "width"), part("B", 1000, 500, "width")], 1004, 1000, 4)
    assert len(sheets) == 1
    assert len(cutlist._nest_sheets([part("A", 1000, 500, "width"), part("B", 1000, 500, "width")], 1004, 1000, 5)) == 2


def test_part_exactly_the_sheet_size_fits():
    sheets = cutlist._nest_sheets([part("Full", W, H, "length")], W, H, KERF)
    assert placed(sheets)[0]["x"] == 0 and placed(sheets)[0]["y"] == 0


def test_part_too_big_for_the_sheet_raises():
    with pytest.raises(ValueError, match=r"Huge \(3000x500\) does not fit the 2730x1830 sheet"):
        cutlist._nest_sheets([part("Huge", 3000, 500)], W, H, KERF)


def test_more_parts_than_one_sheet_opens_new_sheets():
    parts = [part(f"Side{i}", 1800, 600, "length") for i in range(9)]   # 3 per sheet (3 x 600 + kerf > 1830)
    sheets = cutlist._nest_sheets(parts, W, H, KERF)
    assert len(sheets) >= 3
    assert_valid_layout(sheets, W, H, KERF)


# ------------------------------------------------------------------ _check_sheets catches bad layouts
def pos(name, x, y, pw, ph):
    return dict(name=name, x=x, y=y, pw=pw, ph=ph)


@pytest.mark.parametrize("layout", [
    [pos("A", 0, 0, 100, 100), pos("B", 50, 50, 100, 100)],          # overlap
    [pos("A", 0, 0, 100, 100), pos("B", 102, 0, 100, 100)],          # touching within the kerf
    [pos("A", 950, 0, 100, 100)],                                    # past the right edge
    [pos("A", 0, -1, 100, 100)],                                     # below the sheet
])
def test_check_sheets_rejects_bad_layouts(layout):
    with pytest.raises(AssertionError):
        cutlist._check_sheets([dict(pos=layout)], 1000, 1000, 4)


def test_check_sheets_accepts_a_kerf_wide_gap():
    cutlist._check_sheets([dict(pos=[pos("A", 0, 0, 100, 100), pos("B", 104, 0, 100, 100)])], 1000, 1000, 4)


# ------------------------------------------------------------------ bars
@pytest.mark.parametrize("seed", range(20))
def test_nest_bars_respects_length_and_kerf(seed):
    rnd = random.Random(seed)
    L, kerf = 6000, 3
    parts = [dict(name=f"R{i}", l=rnd.randint(100, 3000)) for i in range(rnd.randint(1, 30))]
    bars = cutlist._nest_bars(parts, L, kerf)
    for b in bars:
        assert sum(q["l"] for q in b) + kerf * (len(b) - 1) <= L
    assert Counter(q["name"] for b in bars for q in b) == Counter(p["name"] for p in parts)


def test_nest_bars_counts_the_kerf():
    parts = [dict(name="A", l=3000), dict(name="B", l=3000)]
    assert len(cutlist._nest_bars(parts, 6000, 0)) == 1
    assert len(cutlist._nest_bars(parts, 6000, 3)) == 2
    assert len(cutlist._nest_bars(parts, 6003, 3)) == 1


def test_part_exactly_the_bar_length_fits():
    assert cutlist._nest_bars([dict(name="Full", l=6000)], 6000, 3) == [[dict(name="Full", l=6000)]]


def test_part_longer_than_the_bar_raises():
    with pytest.raises(ValueError, match=r"Rail \(6001 mm\) is longer than the 6000 mm bar"):
        cutlist._nest_bars([dict(name="Short", l=500), dict(name="Rail", l=6001)], 6000, 3)


# ------------------------------------------------------------------ summary page
def sheet_plan(**kw):
    sh = dict(name="MDF", thk=15, SL=2750, SW=1850, pos=[1, 2], use=60.0)
    return dict(sheets=[sh], bars=[], solid=[], warnings=[], **kw)


def bar_plan(warnings=()):
    gb = dict(name="Steel", section="SQ 50x2", bars=[[1, 2], [3]], use=70.0)
    return dict(sheets=[], bars=[gb], solid=[], warnings=list(warnings))


def notes(plan_):
    return [it[1] for it in cutlist._summary_items(plan_) if it[0] == "note"]


@pytest.mark.parametrize("lang", ["en", "pt-BR"])
def test_guillotine_note_only_when_the_plan_has_sheets(lang):
    i18n.set_language(lang)
    assert T("note_guillotine") in notes(sheet_plan())
    assert T("note_guillotine") not in notes(bar_plan(["Steel: bar to be confirmed"]))
    assert notes(bar_plan(["Steel: bar to be confirmed"])) == [T("notes"), "- Steel: bar to be confirmed"]


def test_no_notes_heading_without_notes():
    assert notes(bar_plan()) == []


def test_summary_continues_on_more_pages():
    many = dict(sheets=[], bars=[dict(name="Steel", section=f"SQ {20 + i}x2", bars=[[1]], use=50.0) for i in range(40)],
                solid=[], warnings=[])
    chunks = cutlist._summary_chunks(many)
    assert len(chunks) > 1
    assert sum(len(c) for c in chunks) == len(cutlist._summary_items(many))
