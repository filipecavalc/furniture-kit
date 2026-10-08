"""Language of generated documents (bill of materials, cut lists, reports, drawings).

The language comes from config/local.json ("language": "en" | "pt-BR"). To add a language,
copy the "en" block below, translate the values and keep the keys.
"""
from . import config

STRINGS = {
    "en": {
        "decimal": ".",
        "date": "%Y-%m-%d",
        "drawing_lang": "EN",
        # check
        "parts": "parts", "envelope": "envelope (mm): W={w:.0f} D={d:.0f} H={h:.0f}",
        "invalid": "invalid", "collisions": "collisions", "none": "none",
        # bom
        "bom_title": "Bill of materials - {name}", "totals": "Totals",
        "bom_header": ("Category", "Material", "Thk./Section", "Part", "Length mm", "Width mm", "Qty", "Total", "Notes"),
        "cat_panel": "Panel", "cat_solid": "Solid wood", "cat_profile": "Profile", "cat_glass": "Glass", "cat_hardware": "Hardware",
        "grain": "grain", "grain_length": "length", "grain_width": "width",
        "rough_suggested": "suggested rough size {l}x{w}x{t}",
        "rough_volume": "(rough, with allowance)", "units": "pcs",
        # cut list
        "cut_title": "Cut list", "cut_summary": "Cut list - Summary",
        "sheet": "sheet", "sheet_of": "sheet {i} of {n}", "yield": "yield",
        "part_one": "{n} part", "part_other": "{n} parts", "bar_one": "{n} bar", "bar_other": "{n} bars",
        "grain_note": "Grain runs along the sheet length ({l} mm). Parts with grain were not rotated.",
        "bar": "Bar", "bar_len": "bar {l} mm", "offcut": "offcut {v} mm",
        "sum_sheets": ("Sheets", "Qty", "Parts", "Yield"), "sum_bars": ("Profiles / bars", "Bars", "Parts", "Yield"),
        "sum_solid": ("Solid wood (final size)", "Qty", "Size", ""),
        "notes": "Notes:",
        "note_guillotine": "- Final part sizes, without edge banding. All sheet cuts run edge to edge (guillotine).",
        "warn_sheet": "{name}: sheet size {l}x{w} to be confirmed with the supplier",
        "warn_bar": "{name} {section}: {l} mm bar to be confirmed with the supplier",
        "warn_bar_kerf": "Saw kerf on bars ({k} mm) is an estimate; confirm with the metal shop",
        "warn_no_sheet": "{name}: no sheet size in the catalog (material '{mat}'), not nested: {parts}",
        "err_sheet_fit": "part {name} ({l}x{w}) does not fit the {W}x{H} sheet respecting the grain",
        "err_bar_fit": "part {name} ({l} mm) is longer than the {L} mm bar",
        # lumber
        "lumber_title": "Lumber - shopping list and parts", "lumber_cont": "Lumber - parts (continued)",
        "lumber_buy": ("Buy", "Size (surfaced)", "Qty", "Yield"),
        "lumber_parts": ("", "Code", "Part", "Modules", "Qty", "Final (L x W x T)", "Rip / crosscut", "Notes"),
        "lumber_note1": "* Stock size to be confirmed at the lumber yard. Saw kerf: {k} mm. Crosscut: +{s} mm per part (final trim square).",
        "lumber_note2": "Rip = width to cut on the table saw (includes tongue when there is tongue and groove).",
        "rip_cut": "W {w} / L {l}",
        "lumber_full": "full width   (offcut {v} mm in length)",
        "lumber_strips": "rip strips of {w} mm   (offcut {v} mm in width)",
        "lumber_plan": "Cut plan - {name} ({t} x {w} x {l})",
        # drawings
        "front_view": "FRONT VIEW", "left_view": "LEFT SIDE VIEW", "top_view": "TOP VIEW", "perspective": "PERSPECTIVE",
        "mm_note": "Dimensions in millimetres.",
    },
    "pt-BR": {
        "decimal": ",",
        "date": "%d/%m/%Y",
        "drawing_lang": "PT",
        "parts": "peças", "envelope": "envelope (mm): L={w:.0f} P={d:.0f} A={h:.0f}",
        "invalid": "inválidas", "collisions": "colisões", "none": "nenhuma",
        "bom_title": "Lista de materiais - {name}", "totals": "Totais",
        "bom_header": ("Categoria", "Material", "Esp./Seção", "Peça", "Comp. mm", "Larg. mm", "Qtd", "Total", "Obs"),
        "cat_panel": "Chapa", "cat_solid": "Maciça", "cat_profile": "Perfil", "cat_glass": "Vidro", "cat_hardware": "Ferragem",
        "grain": "veio", "grain_length": "comprimento", "grain_width": "largura",
        "rough_suggested": "bruto sugerido {l}x{w}x{t}",
        "rough_volume": "(bruto, com sobremetal)", "units": "un.",
        "cut_title": "Plano de corte", "cut_summary": "Plano de corte - Resumo",
        "sheet": "chapa", "sheet_of": "chapa {i} de {n}", "yield": "aproveitamento",
        "part_one": "{n} peça", "part_other": "{n} peças", "bar_one": "{n} barra", "bar_other": "{n} barras",
        "grain_note": "Veio no sentido do comprimento da chapa ({l} mm). Peças com veio não foram giradas.",
        "bar": "Barra", "bar_len": "barra {l} mm", "offcut": "sobra {v} mm",
        "sum_sheets": ("Chapas", "Qtd", "Peças", "Aproveitamento"), "sum_bars": ("Perfis / barras", "Barras", "Peças", "Aproveitamento"),
        "sum_solid": ("Madeira maciça (medida final)", "Qtd", "Medidas", ""),
        "notes": "Observações:",
        "note_guillotine": "- Medidas finais das peças, sem fita de borda. Todos os cortes de chapa são de ponta a ponta (guilhotina).",
        "warn_sheet": "{name}: tamanho de chapa {l}x{w} a confirmar com o fornecedor",
        "warn_bar": "{name} {section}: barra de {l} mm a confirmar com o fornecedor",
        "warn_bar_kerf": "Perda de serra em barras ({k} mm) é estimativa; confirmar com a serralheria",
        "warn_no_sheet": "{name}: sem tamanho de chapa no catálogo (material '{mat}'), fora do plano: {parts}",
        "err_sheet_fit": "peça {name} ({l}x{w}) não cabe na chapa {W}x{H} respeitando o veio",
        "err_bar_fit": "peça {name} ({l} mm) maior que a barra de {L} mm",
        "lumber_title": "Madeira - lista de compra e peças", "lumber_cont": "Madeira - peças (continuação)",
        "lumber_buy": ("Comprar", "Medida (aparelhada)", "Qtd", "Aproveitamento"),
        "lumber_parts": ("", "Cód.", "Peça", "Módulos", "Qtd", "Final (C x L x E)", "Refilar / destopar", "Obs."),
        "lumber_note1": "* Medida de estoque a confirmar na madeireira. Serra: {k} mm. Destopo: +{s} mm por peça (acerto final no esquadro).",
        "lumber_note2": "Refilar = largura a tirar na serra de bancada (inclui língua do macho e fêmea quando houver).",
        "rip_cut": "L {w} / C {l}",
        "lumber_full": "largura inteira   (sobra {v} mm no comprimento)",
        "lumber_strips": "refilar tiras de {w} mm   (sobra {v} mm na largura)",
        "lumber_plan": "Plano de corte - {name} ({t} x {w} x {l})",
        "front_view": "VISTA FRONTAL", "left_view": "VISTA LATERAL ESQUERDA", "top_view": "VISTA SUPERIOR", "perspective": "PERSPECTIVA",
        "mm_note": "Medidas em milímetros.",
    },
}


import sys
_PKG = sys.modules[__package__]      # the override lives on the package so furniture.reload() keeps it


def set_language(code=None):
    """Forces a language for this FreeCAD session (None = back to config/local.json)."""
    _PKG._language_override = code


def lang():
    """Configured language, matched leniently ('pt-br', 'pt' -> 'pt-BR'); English if unknown."""
    code = str(getattr(_PKG, "_language_override", None) or config().get("language", "en"))
    for k in STRINGS:
        if k.lower() == code.lower():
            return k
    for k in STRINGS:
        if k.lower().split("-")[0] == code.lower().split("-")[0]:
            return k
    return "en"


def T(key, **kw):
    """Translated string (or tuple) for the configured language; falls back to English, then to the key."""
    s = STRINGS[lang()].get(key) or STRINGS["en"].get(key, key)
    return s.format(**kw) if kw and isinstance(s, str) else s


def N(n, word):
    """Count with singular/plural: N(1, "part") -> "1 part", N(3, "part") -> "3 parts"."""
    return T(f"{word}_one" if n == 1 else f"{word}_other", n=n)


def num(v, fmt=".1f"):
    """Number with the language's decimal separator."""
    return format(v, fmt).replace(".", STRINGS[lang()]["decimal"])


def pct(v):
    return num(v, ".1f") + "%"


def material_name(mat):
    """Material display name: 'name_<lang>' when present (e.g. name_en), else 'name'."""
    return mat.get("name_" + lang()) or mat.get("name_" + lang().split("-")[0]) or mat["name"]


def font(px=None, bold=False, pt=None):
    """Qt font that exists on Windows, macOS and Linux."""
    from PySide import QtGui
    f = QtGui.QFont()
    f.setFamilies(["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans", "Liberation Sans"])
    if px is not None:
        f.setPixelSize(max(8, int(px)))
    if pt is not None:
        f.setPointSize(int(pt))
    f.setBold(bold)
    return f


def fit_font(text, width, px, bold=False, min_px=8):
    """Largest font up to px whose rendering of text fits in width (fonts differ between systems)."""
    from PySide import QtGui
    f = font(px, bold)
    while px > min_px and QtGui.QFontMetrics(f).horizontalAdvance(text) > width:
        px *= 0.92
        f = font(px, bold)
    return f
