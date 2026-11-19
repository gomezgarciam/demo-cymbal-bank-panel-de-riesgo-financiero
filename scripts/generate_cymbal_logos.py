#!/usr/bin/env python3
"""Generate official Cymbal Bank vector logos (SVG) and high-res PNG visual boards."""

import math
import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(REPO_ROOT, "assets", "logos")
BOARDS_DIR = os.path.join(REPO_ROOT, "assets", "brand-boards")
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(BOARDS_DIR, exist_ok=True)

# Official Cymbal Bank Palette
PRIMARY = "#1A73E8"
SECONDARY = "#0F9D58"
RISK_HIGH = "#D93025"
RISK_MED = "#F9AB00"
BG_LIGHT = "#F8F9FA"
BG_DARK = "#12161F"
WHITE = "#FFFFFF"
MUTED_LIGHT = "#5F6368"
MUTED_DARK = "#9AA0A6"
BORDER_LIGHT = "#DADCE0"
BORDER_DARK = "#2A3142"


def annular_sector_path(cx, cy, r_outer, r_inner, start_deg, end_deg):
    """Build an SVG path for a crisp annular sector (clockwise from start_deg to end_deg)."""
    a1 = math.radians(start_deg)
    a2 = math.radians(end_deg)
    sweep = (end_deg - start_deg) % 360
    large_arc = 1 if sweep > 180 else 0

    ox1, oy1 = cx + r_outer * math.cos(a1), cy + r_outer * math.sin(a1)
    ox2, oy2 = cx + r_outer * math.cos(a2), cy + r_outer * math.sin(a2)
    ix2, iy2 = cx + r_inner * math.cos(a2), cy + r_inner * math.sin(a2)
    ix1, iy1 = cx + r_inner * math.cos(a1), cy + r_inner * math.sin(a1)

    return (
        f"M {ox1:.3f} {oy1:.3f} "
        f"A {r_outer:.3f} {r_outer:.3f} 0 {large_arc} 1 {ox2:.3f} {oy2:.3f} "
        f"L {ix2:.3f} {iy2:.3f} "
        f"A {r_inner:.3f} {r_inner:.3f} 0 {large_arc} 0 {ix1:.3f} {iy1:.3f} Z"
    )


def cymbal_emblem_group(
    cx=50,
    cy=50,
    scale=1.0,
    primary_color=PRIMARY,
    secondary_color=SECONDARY,
    core_color=BG_DARK,
):
    """
    Official Cymbal Bank Isotipo (100x100 canonical unit space centered at cx, cy):
    - Outer ring (R_out=44, R_in=29): symmetric geometric 'C' opening at +/-38 deg.
      * Institutional primary arc (38 deg -> 256 deg, 218 deg sweep) in Primario (#1A73E8)
      * Ascending growth/stability arc (266 deg -> 322 deg, 56 deg sweep) in Secundario (#0F9D58)
      * Clean 10 deg precision structural miter gap between arcs
    - Central Cymbal bell / vault core (r=11.5) centered at (cx, cy)
    """
    r_out = 44.0 * scale
    r_in = 29.0 * scale
    r_core = 11.5 * scale

    arc_primary = annular_sector_path(cx, cy, r_out, r_in, 38, 256)
    arc_secondary = annular_sector_path(cx, cy, r_out, r_in, 266, 322)

    return f"""  <g class="cymbal-emblem">
    <path d="{arc_primary}" fill="{primary_color}" />
    <path d="{arc_secondary}" fill="{secondary_color}" />
    <circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r_core:.3f}" fill="{core_color}" />
  </g>"""


def horizontal_lockup_group(
    x=0,
    y=0,
    scale=1.0,
    primary_color=PRIMARY,
    secondary_color=SECONDARY,
    core_color=BG_DARK,
    text_primary=BG_DARK,
    text_secondary=BG_DARK,
    show_tagline=False,
    tagline_color=MUTED_LIGHT,
):
    """
    Canonical horizontal lockup (height = 100 * scale, ink width from x=6 to x=414 -> 408u).
    Emblem centered at (50, 50); clear gap = 22u; wordmark starts at x=116.
    """
    emblem = cymbal_emblem_group(
        cx=50,
        cy=50,
        scale=1.0,
        primary_color=primary_color,
        secondary_color=secondary_color,
        core_color=core_color,
    )
    baseline_y = 65 if not show_tagline else 56
    tagline_svg = ""
    if show_tagline:
        tagline_svg = (
            f'    <text x="118" y="81" font-family="Roboto" font-weight="500" '
            f'font-size="11.5" letter-spacing="1.6" fill="{tagline_color}">'
            f"BANCA CORPORATIVA Y GESTIÓN DE RIESGOS</text>\n"
        )

    return f"""  <g transform="translate({x:.2f}, {y:.2f}) scale({scale:.4f})">
{emblem}
    <text x="116" y="{baseline_y}" font-family="Roboto" font-weight="700" font-size="52" letter-spacing="-0.8" fill="{text_primary}">Cymbal</text>
    <text x="301" y="{baseline_y}" font-family="Roboto" font-weight="300" font-size="52" letter-spacing="-0.4" fill="{text_secondary}">Bank</text>
{tagline_svg}  </g>"""


def save_svg_and_png(svg_content, svg_path, png_path, width_px):
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    subprocess.run(
        ["rsvg-convert", "-w", str(width_px), "-o", png_path, svg_path],
        check=True,
    )


# ---------------------------------------------------------------------------
# 1. PRODUCTION LOGO ASSETS (SVG + high-res PNG for Drive upload)
# ---------------------------------------------------------------------------
def build_production_assets():
    # Ink spans x=6..414 (width 408), y=6..94 (height 88). With translate(28, 22) in 476x144 -> centered symmetrically!
    svg_light = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 476 144" width="476" height="144">
  <title>Cymbal Bank — Logotipo Principal (Fondo Claro)</title>
{horizontal_lockup_group(x=28, y=22, scale=1.0, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}
</svg>
"""
    save_svg_and_png(
        svg_light,
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-principal-claro.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-principal-claro.png"),
        1904,
    )

    svg_dark = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 476 144" width="476" height="144">
  <title>Cymbal Bank — Logotipo Modo Oscuro</title>
  <rect width="476" height="144" rx="14" fill="{BG_DARK}" />
{horizontal_lockup_group(x=28, y=22, scale=1.0, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_LIGHT, text_primary=BG_LIGHT, text_secondary=BG_LIGHT)}
</svg>
"""
    save_svg_and_png(
        svg_dark,
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-modo-oscuro.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-modo-oscuro.png"),
        1904,
    )

    svg_mono_dark = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 476 144" width="476" height="144">
  <title>Cymbal Bank — Logotipo Monocromo Oscuro</title>
{horizontal_lockup_group(x=28, y=22, scale=1.0, primary_color=BG_DARK, secondary_color=BG_DARK, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}
</svg>
"""
    save_svg_and_png(
        svg_mono_dark,
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-monocromo-oscuro.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-monocromo-oscuro.png"),
        1904,
    )

    svg_mono_light = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 476 144" width="476" height="144">
  <title>Cymbal Bank — Logotipo Monocromo Claro sobre Primario</title>
  <rect width="476" height="144" rx="14" fill="{PRIMARY}" />
{horizontal_lockup_group(x=28, y=22, scale=1.0, primary_color=WHITE, secondary_color=WHITE, core_color=WHITE, text_primary=WHITE, text_secondary=WHITE)}
</svg>
"""
    save_svg_and_png(
        svg_mono_light,
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-monocromo-claro.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-logo-monocromo-claro.png"),
        1904,
    )

    svg_iso_light = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <title>Cymbal Bank — Isotipo Oficial</title>
{cymbal_emblem_group(cx=64, cy=64, scale=1.18, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK)}
</svg>
"""
    save_svg_and_png(
        svg_iso_light,
        os.path.join(ASSETS_DIR, "cymbal-bank-isotipo.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-isotipo.png"),
        1024,
    )

    svg_iso_dark = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <title>Cymbal Bank — Icono de Aplicación (Modo Oscuro)</title>
  <rect width="128" height="128" rx="28" fill="{BG_DARK}" />
{cymbal_emblem_group(cx=64, cy=64, scale=0.92, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_LIGHT)}
</svg>
"""
    save_svg_and_png(
        svg_iso_dark,
        os.path.join(ASSETS_DIR, "cymbal-bank-icono-app-oscuro.svg"),
        os.path.join(ASSETS_DIR, "cymbal-bank-icono-app-oscuro.png"),
        1024,
    )


# ---------------------------------------------------------------------------
# 2. VISUAL SPECIFICATION BOARDS (for embedding inside Guia de Logos Doc)
# ---------------------------------------------------------------------------
def build_board_1_primary_versions():
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 430" width="1200" height="430">
  <rect width="1200" height="430" fill="{WHITE}" />

  <!-- Left Card: Light Surface (#F8F9FA) -->
  <rect x="0" y="0" width="584" height="370" rx="14" fill="{BG_LIGHT}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <rect x="24" y="22" width="184" height="26" rx="13" fill="#E8F0FE" />
  <text x="116" y="39" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11.5" fill="{PRIMARY}">VERSIÓN PRINCIPAL · CLARO</text>
  <text x="560" y="39" text-anchor="end" font-family="Roboto" font-weight="500" font-size="11.5" fill="{MUTED_LIGHT}">Fondo #F8F9FA</text>

{horizontal_lockup_group(x=74, y=128, scale=1.02, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK, show_tagline=True, tagline_color=MUTED_LIGHT)}

  <line x1="24" y1="316" x2="560" y2="316" stroke="{BORDER_LIGHT}" stroke-width="1" />
  <circle cx="34" cy="343" r="6" fill="{PRIMARY}" />
  <text x="48" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_DARK}">#1A73E8</text>
  <circle cx="128" cy="343" r="6" fill="{SECONDARY}" />
  <text x="142" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_DARK}">#0F9D58</text>
  <circle cx="222" cy="343" r="6" fill="{BG_DARK}" />
  <text x="236" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_DARK}">#12161F</text>
  <text x="560" y="347" text-anchor="end" font-family="Roboto" font-weight="400" font-size="11" fill="{MUTED_LIGHT}">Inter / Roboto · Contraste 17.4:1</text>

  <!-- Right Card: Dark Surface (#12161F) -->
  <rect x="616" y="0" width="584" height="370" rx="14" fill="{BG_DARK}" stroke="{BORDER_DARK}" stroke-width="1.5" />
  <rect x="640" y="22" width="184" height="26" rx="13" fill="#1E293B" />
  <text x="732" y="39" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11.5" fill="#8AB4F8">VERSIÓN MODO OSCURO</text>
  <text x="1176" y="39" text-anchor="end" font-family="Roboto" font-weight="500" font-size="11.5" fill="{MUTED_DARK}">Fondo #12161F</text>

{horizontal_lockup_group(x=690, y=128, scale=1.02, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_LIGHT, text_primary=BG_LIGHT, text_secondary=BG_LIGHT, show_tagline=True, tagline_color=MUTED_DARK)}

  <line x1="640" y1="316" x2="1176" y2="316" stroke="{BORDER_DARK}" stroke-width="1" />
  <circle cx="650" cy="343" r="6" fill="{PRIMARY}" />
  <text x="664" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_LIGHT}">#1A73E8</text>
  <circle cx="744" cy="343" r="6" fill="{SECONDARY}" />
  <text x="758" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_LIGHT}">#0F9D58</text>
  <circle cx="838" cy="343" r="6" fill="{BG_LIGHT}" />
  <text x="852" y="347" font-family="Roboto" font-weight="500" font-size="11.5" fill="{BG_LIGHT}">#F8F9FA</text>
  <text x="1176" y="347" text-anchor="end" font-family="Roboto" font-weight="400" font-size="11" fill="{MUTED_DARK}">Tableros de riesgo y portadas ejecutivas</text>

  <!-- Footer caption -->
  <text x="0" y="408" font-family="Roboto" font-weight="500" font-size="12.5" fill="{MUTED_LIGHT}">Figura 1. Logotipo horizontal oficial de Cymbal Bank en superficies claras (#F8F9FA) y oscuras (#12161F), reservando #D93025 y #F9AB00 exclusivamente para alertas de riesgo.</text>
</svg>
"""
    save_svg_and_png(
        svg,
        os.path.join(BOARDS_DIR, "board_1_primary_versions.svg"),
        os.path.join(BOARDS_DIR, "board_1_primary_versions.png"),
        2000,
    )


def build_board_2_construction_and_clearspace():
    cx, cy, sc = 225, 196, 2.5
    r_out, r_in, r_core = 44 * sc, 29 * sc, 11.5 * sc

    grid_lines = []
    for gx in range(55, 405, 28):
        grid_lines.append(f'  <line x1="{gx}" y1="48" x2="{gx}" y2="344" stroke="#E2E8F0" stroke-width="0.8" />')
    for gy in range(56, 344, 28):
        grid_lines.append(f'  <line x1="45" y1="{gy}" x2="405" y2="{gy}" stroke="#E2E8F0" stroke-width="0.8" />')

    def ray(deg, length=138):
        rad = math.radians(deg)
        return cx + length * math.cos(rad), cy + length * math.sin(rad)

    x38, y38 = ray(38)
    x322, y322 = ray(322)
    x256, y256 = ray(256)
    x266, y266 = ray(266)

    # Exact bounding box of horizontal lockup: x in [6, 414] (w=408), y in [6, 94] (h=88)
    # Center inside right panel (x=492..1200 -> center at x=846):
    lsc = 1.0
    logo_w = 408.0 * lsc
    logo_h = 88.0 * lsc
    pad_x = 44.0 * lsc  # 1x = outer radius of emblem
    logo_x0 = 846.0 - logo_w / 2.0
    logo_y0 = 148.0
    lx = logo_x0 - 6.0 * lsc
    ly = logo_y0 - 6.0 * lsc

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 440" width="1200" height="440">
  <rect width="1200" height="440" fill="{WHITE}" />

  <!-- LEFT PANEL: Geometric Construction -->
  <rect x="0" y="0" width="460" height="384" rx="14" fill="{BG_LIGHT}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <text x="22" y="32" font-family="Roboto" font-weight="700" font-size="13" fill="{BG_DARK}">A. RETÍCULA GEOMÉTRICA DEL ISOTIPO</text>
{"".join(grid_lines)}

  <circle cx="{cx}" cy="{cy}" r="{r_out:.1f}" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="4 3" />
  <circle cx="{cx}" cy="{cy}" r="{r_in:.1f}" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="4 3" />
  <circle cx="{cx}" cy="{cy}" r="{r_core:.1f}" fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3 2" />

  <line x1="65" y1="{cy}" x2="385" y2="{cy}" stroke="#94A3B8" stroke-width="1" stroke-dasharray="5 4" />
  <line x1="{cx}" y1="54" x2="{cx}" y2="340" stroke="#94A3B8" stroke-width="1" stroke-dasharray="5 4" />
  <line x1="{cx}" y1="{cy}" x2="{x38:.1f}" y2="{y38:.1f}" stroke="{PRIMARY}" stroke-width="1" stroke-dasharray="3 3" opacity="0.7" />
  <line x1="{cx}" y1="{cy}" x2="{x322:.1f}" y2="{y322:.1f}" stroke="{SECONDARY}" stroke-width="1" stroke-dasharray="3 3" opacity="0.7" />
  <line x1="{cx}" y1="{cy}" x2="{x256:.1f}" y2="{y256:.1f}" stroke="{BG_DARK}" stroke-width="1" stroke-dasharray="3 3" opacity="0.55" />
  <line x1="{cx}" y1="{cy}" x2="{x266:.1f}" y2="{y266:.1f}" stroke="{BG_DARK}" stroke-width="1" stroke-dasharray="3 3" opacity="0.55" />

{cymbal_emblem_group(cx=cx, cy=cy, scale=sc, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK)}

  <text x="352" y="191" font-family="Roboto" font-weight="700" font-size="11.5" fill="{PRIMARY}">76°</text>
  <text x="348" y="206" font-family="Roboto" font-weight="400" font-size="10" fill="{MUTED_LIGHT}">apertura</text>
  <text x="138" y="64" font-family="Roboto" font-weight="700" font-size="11" fill="{SECONDARY}">10° corte</text>
  <text x="22" y="366" font-family="Roboto" font-weight="500" font-size="11" fill="{MUTED_LIGHT}">R_ext = 2x  ·  R_int = 1.32x  ·  Núcleo = 0.52x  ·  Grosor anillo = 0.68x</text>

  <!-- RIGHT PANEL: Clearspace Blueprint -->
  <rect x="492" y="0" width="708" height="384" rx="14" fill="{BG_LIGHT}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <text x="516" y="32" font-family="Roboto" font-weight="700" font-size="13" fill="{BG_DARK}">B. ZONA DE SEGURIDAD OBLIGATORIA (MÍNIMO = 1x EN TODOS LOS LADOS)</text>

  <rect x="{logo_x0 - pad_x:.1f}" y="{logo_y0 - pad_x:.1f}" width="{logo_w + 2*pad_x:.1f}" height="{logo_h + 2*pad_x:.1f}" fill="#E8F0FE" fill-opacity="0.55" stroke="{PRIMARY}" stroke-width="1.5" stroke-dasharray="6 4" rx="6" />
  <rect x="{logo_x0:.1f}" y="{logo_y0:.1f}" width="{logo_w:.1f}" height="{logo_h:.1f}" fill="{WHITE}" stroke="#94A3B8" stroke-width="1" />

  <rect x="{logo_x0 - pad_x:.1f}" y="{logo_y0 - pad_x:.1f}" width="{pad_x}" height="{pad_x}" fill="{PRIMARY}" fill-opacity="0.18" stroke="{PRIMARY}" stroke-width="1" />
  <text x="{logo_x0 - pad_x/2:.1f}" y="{logo_y0 - pad_x/2 + 4:.1f}" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="12" fill="{PRIMARY}">1x</text>

  <rect x="{logo_x0 + logo_w:.1f}" y="{logo_y0 - pad_x:.1f}" width="{pad_x}" height="{pad_x}" fill="{PRIMARY}" fill-opacity="0.18" stroke="{PRIMARY}" stroke-width="1" />
  <text x="{logo_x0 + logo_w + pad_x/2:.1f}" y="{logo_y0 - pad_x/2 + 4:.1f}" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="12" fill="{PRIMARY}">1x</text>

  <rect x="{logo_x0 - pad_x:.1f}" y="{logo_y0 + logo_h:.1f}" width="{pad_x}" height="{pad_x}" fill="{PRIMARY}" fill-opacity="0.18" stroke="{PRIMARY}" stroke-width="1" />
  <text x="{logo_x0 - pad_x/2:.1f}" y="{logo_y0 + logo_h + pad_x/2 + 4:.1f}" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="12" fill="{PRIMARY}">1x</text>

  <rect x="{logo_x0 + logo_w:.1f}" y="{logo_y0 + logo_h:.1f}" width="{pad_x}" height="{pad_x}" fill="{PRIMARY}" fill-opacity="0.18" stroke="{PRIMARY}" stroke-width="1" />
  <text x="{logo_x0 + logo_w + pad_x/2:.1f}" y="{logo_y0 + logo_h + pad_x/2 + 4:.1f}" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="12" fill="{PRIMARY}">1x</text>

{horizontal_lockup_group(x=lx, y=ly, scale=lsc, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}

  <line x1="{logo_x0:.1f}" y1="{logo_y0 + logo_h + pad_x + 28:.1f}" x2="{logo_x0 + logo_w:.1f}" y2="{logo_y0 + logo_h + pad_x + 28:.1f}" stroke="{BG_DARK}" stroke-width="1.2" />
  <line x1="{logo_x0:.1f}" y1="{logo_y0 + logo_h + pad_x + 22:.1f}" x2="{logo_x0:.1f}" y2="{logo_y0 + logo_h + pad_x + 34:.1f}" stroke="{BG_DARK}" stroke-width="1.2" />
  <line x1="{logo_x0 + logo_w:.1f}" y1="{logo_y0 + logo_h + pad_x + 22:.1f}" x2="{logo_x0 + logo_w:.1f}" y2="{logo_y0 + logo_h + pad_x + 34:.1f}" stroke="{BG_DARK}" stroke-width="1.2" />
  <text x="{logo_x0 + logo_w/2:.1f}" y="{logo_y0 + logo_h + pad_x + 48:.1f}" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11.5" fill="{BG_DARK}">Ancho mínimo digital: 120 px  ·  Impreso: 32 mm  (1x = radio externo del isotipo)</text>

  <text x="516" y="366" font-family="Roboto" font-weight="400" font-size="11" fill="{MUTED_LIGHT}">Ningún texto, borde, botón o elemento gráfico puede invadir el perímetro punteado de seguridad.</text>

  <text x="0" y="420" font-family="Roboto" font-weight="500" font-size="12.5" fill="{MUTED_LIGHT}">Figura 2. Construcción modular concéntrica basada en la geometría de Cymbal (Google Cloud) y perímetro de resguardo 1x para preservar la legibilidad ejecutiva.</text>
</svg>
"""
    save_svg_and_png(
        svg,
        os.path.join(BOARDS_DIR, "board_2_construction_clearspace.svg"),
        os.path.join(BOARDS_DIR, "board_2_construction_clearspace.png"),
        2000,
    )


def build_board_3_approved_variants():
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 370" width="1200" height="370">
  <rect width="1200" height="370" fill="{WHITE}" />

  <!-- Card 1: Standalone Isotipo -->
  <rect x="0" y="0" width="282" height="316" rx="14" fill="{BG_LIGHT}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <text x="18" y="30" font-family="Roboto" font-weight="700" font-size="12" fill="{PRIMARY}">01 · ISOTIPO (CLARO)</text>
{cymbal_emblem_group(cx=141, cy=148, scale=1.55, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK)}
  <line x1="18" y1="252" x2="264" y2="252" stroke="{BORDER_LIGHT}" stroke-width="1" />
  <text x="18" y="274" font-family="Roboto" font-weight="700" font-size="11.5" fill="{BG_DARK}">Favicon, avatar y barra lateral</text>
  <text x="18" y="294" font-family="Roboto" font-weight="400" font-size="10.5" fill="{MUTED_LIGHT}">Tamaño mínimo: 24 × 24 px</text>

  <!-- Card 2: App Icon Dark Tile -->
  <rect x="306" y="0" width="282" height="316" rx="14" fill="{BG_LIGHT}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <text x="324" y="30" font-family="Roboto" font-weight="700" font-size="12" fill="{BG_DARK}">02 · ICONO APP (OSCURO)</text>
  <rect x="381" y="82" width="132" height="132" rx="28" fill="{BG_DARK}" />
{cymbal_emblem_group(cx=447, cy=148, scale=1.02, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_LIGHT)}
  <line x1="324" y1="252" x2="570" y2="252" stroke="{BORDER_LIGHT}" stroke-width="1" />
  <text x="324" y="274" font-family="Roboto" font-weight="700" font-size="11.5" fill="{BG_DARK}">Apps móviles y Workspace</text>
  <text x="324" y="294" font-family="Roboto" font-weight="400" font-size="10.5" fill="{MUTED_LIGHT}">Contenedor #12161F · radio 22%</text>

  <!-- Card 3: Monochrome Dark (#12161F) -->
  <rect x="612" y="0" width="282" height="316" rx="14" fill="{WHITE}" stroke="{BORDER_LIGHT}" stroke-width="1.5" />
  <text x="630" y="30" font-family="Roboto" font-weight="700" font-size="12" fill="{BG_DARK}">03 · MONOCROMO OSCURO</text>
{horizontal_lockup_group(x=634, y=120, scale=0.56, primary_color=BG_DARK, secondary_color=BG_DARK, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}
  <line x1="630" y1="252" x2="876" y2="252" stroke="{BORDER_LIGHT}" stroke-width="1" />
  <text x="630" y="274" font-family="Roboto" font-weight="700" font-size="11.5" fill="{BG_DARK}">Contratos, PDF legal e impresión</text>
  <text x="630" y="294" font-family="Roboto" font-weight="400" font-size="10.5" fill="{MUTED_LIGHT}">Tinta única #12161F</text>

  <!-- Card 4: Monochrome Light (#FFFFFF over #1A73E8) -->
  <rect x="918" y="0" width="282" height="316" rx="14" fill="{PRIMARY}" />
  <text x="936" y="30" font-family="Roboto" font-weight="700" font-size="12" fill="{WHITE}">04 · NEGATIVO SOBRE PRIMARIO</text>
{horizontal_lockup_group(x=940, y=120, scale=0.56, primary_color=WHITE, secondary_color=WHITE, core_color=WHITE, text_primary=WHITE, text_secondary=WHITE)}
  <line x1="936" y1="252" x2="1182" y2="252" stroke="#669DF6" stroke-width="1" />
  <text x="936" y="274" font-family="Roboto" font-weight="700" font-size="11.5" fill="{WHITE}">Portadas, banners y encabezados</text>
  <text x="936" y="294" font-family="Roboto" font-weight="400" font-size="10.5" fill="#E8F0FE">Blanco #FFFFFF sobre #1A73E8</text>

  <text x="0" y="352" font-family="Roboto" font-weight="500" font-size="12.5" fill="{MUTED_LIGHT}">Figura 3. Variaciones oficiales aprobadas para aplicaciones digitales, documentación legal y presentaciones ejecutivas de Cymbal Bank.</text>
</svg>
"""
    save_svg_and_png(
        svg,
        os.path.join(BOARDS_DIR, "board_3_approved_variants.svg"),
        os.path.join(BOARDS_DIR, "board_3_approved_variants.png"),
        2000,
    )


def build_board_4_misuse_rules():
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 350" width="1200" height="350">
  <rect width="1200" height="350" fill="{WHITE}" />

  <!-- Don't 1: Stretching / Distortion (cleanly contained inside Card 1!) -->
  <rect x="0" y="0" width="282" height="296" rx="14" fill="#FFF8F8" stroke="#F6C8C4" stroke-width="1.5" />
  <rect x="16" y="16" width="144" height="24" rx="12" fill="{RISK_HIGH}" />
  <text x="88" y="32" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11" fill="{WHITE}">✗  NO DISTORSIONAR</text>
  <g transform="translate(34, 96) scale(0.50, 0.94)">
{horizontal_lockup_group(x=0, y=0, scale=1.0, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}
  </g>
  <line x1="20" y1="220" x2="262" y2="220" stroke="#F6C8C4" stroke-width="1" />
  <text x="18" y="244" font-family="Roboto" font-weight="700" font-size="11.5" fill="{RISK_HIGH}">Alteración de escala</text>
  <text x="18" y="264" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">Prohibido estirar o comprimir</text>
  <text x="18" y="280" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">el isotipo o la tipografía.</text>

  <!-- Don't 2: Using Risk Alert Colors (#D93025 / #F9AB00) in Logo -->
  <rect x="306" y="0" width="282" height="296" rx="14" fill="#FFF8F8" stroke="#F6C8C4" stroke-width="1.5" />
  <rect x="322" y="16" width="194" height="24" rx="12" fill="{RISK_HIGH}" />
  <text x="419" y="32" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11" fill="{WHITE}">✗  NO USAR COLORES DE RIESGO</text>
{horizontal_lockup_group(x=328, y=114, scale=0.56, primary_color=RISK_HIGH, secondary_color=RISK_MED, core_color=RISK_HIGH, text_primary=RISK_HIGH, text_secondary=RISK_MED)}
  <line x1="326" y1="220" x2="568" y2="220" stroke="#F6C8C4" stroke-width="1" />
  <text x="324" y="244" font-family="Roboto" font-weight="700" font-size="11.5" fill="{RISK_HIGH}">Recoloreo semántico inválido</text>
  <text x="324" y="264" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">#D93025 y #F9AB00 se reservan</text>
  <text x="324" y="280" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">solo para alertas de riesgo.</text>

  <!-- Don't 3: Low Contrast Background -->
  <rect x="612" y="0" width="282" height="296" rx="14" fill="#FFF8F8" stroke="#F6C8C4" stroke-width="1.5" />
  <rect x="628" y="16" width="178" height="24" rx="12" fill="{RISK_HIGH}" />
  <text x="717" y="32" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11" fill="{WHITE}">✗  SIN CONTRASTE WCAG AA</text>
  <rect x="628" y="84" width="250" height="114" rx="10" fill="#1F4E8C" />
{horizontal_lockup_group(x=642, y=114, scale=0.53, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK, text_primary=BG_DARK, text_secondary=BG_DARK)}
  <line x1="632" y1="220" x2="874" y2="220" stroke="#F6C8C4" stroke-width="1" />
  <text x="630" y="244" font-family="Roboto" font-weight="700" font-size="11.5" fill="{RISK_HIGH}">Fondos no autorizados</text>
  <text x="630" y="264" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">No aplicar versión oscura sobre</text>
  <text x="630" y="280" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">fondos azules o saturados.</text>

  <!-- Don't 4: Rotation / Unapproved Font -->
  <rect x="918" y="0" width="282" height="296" rx="14" fill="#FFF8F8" stroke="#F6C8C4" stroke-width="1.5" />
  <rect x="934" y="16" width="214" height="24" rx="12" fill="{RISK_HIGH}" />
  <text x="1041" y="32" text-anchor="middle" font-family="Roboto" font-weight="700" font-size="11" fill="{WHITE}">✗  NO ROTAR NI CAMBIAR FUENTE</text>
  <g transform="translate(1058, 146) rotate(-14) translate(-114, -24)">
{cymbal_emblem_group(cx=28, cy=28, scale=0.52, primary_color=PRIMARY, secondary_color=SECONDARY, core_color=BG_DARK)}
    <text x="62" y="38" font-family="Liberation Serif" font-style="italic" font-weight="700" font-size="26" fill="{BG_DARK}">Cymbal Bank</text>
  </g>
  <line x1="938" y1="220" x2="1180" y2="220" stroke="#F6C8C4" stroke-width="1" />
  <text x="936" y="244" font-family="Roboto" font-weight="700" font-size="11.5" fill="{RISK_HIGH}">Rotación y fuente ajena</text>
  <text x="936" y="264" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">Mantener horizonte recto y usar</text>
  <text x="936" y="280" font-family="Roboto" font-weight="400" font-size="10.5" fill="{BG_DARK}">únicamente Inter o Roboto.</text>

  <text x="0" y="332" font-family="Roboto" font-weight="500" font-size="12.5" fill="{MUTED_LIGHT}">Figura 4. Restricciones de uso prohibidas en interfaces, presentaciones ejecutivas y comunicaciones corporativas de Cymbal Bank.</text>
</svg>
"""
    save_svg_and_png(
        svg,
        os.path.join(BOARDS_DIR, "board_4_misuse_rules.svg"),
        os.path.join(BOARDS_DIR, "board_4_misuse_rules.png"),
        2000,
    )


if __name__ == "__main__":
    build_production_assets()
    build_board_1_primary_versions()
    build_board_2_construction_and_clearspace()
    build_board_3_approved_variants()
    build_board_4_misuse_rules()
    print("All v2 assets and boards rendered successfully!")
