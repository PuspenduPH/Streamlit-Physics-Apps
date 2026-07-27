"""
app.py — Streamlit entry point for Optical Cavity Ray Tracing.

Page flow (ST_DESIGN.md §10)
-----------------------------
    Hero → Theory (collapsible) → [Sidebar: theme / controls / presets / color]
    → Metric cards → Static figure + PNG export
    → Animation + MP4 export → Footer

Usage
-----
    streamlit run app.py
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import streamlit as st

from cavity_ray_tracing import CavityRayTracing
from export_utils import export_gif, export_png
from plotting import build_animated_figure, build_stability_diagram, build_static_figure
from presets import CAVITY_PRESETS, get_presets_by_category, is_confocal

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
THEMES_DIR = _HERE / "themes"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Optical Cavity Ray Tracing",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Google Fonts import (injected once)
# ---------------------------------------------------------------------------
st.markdown(
    """<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Theme loading
# ---------------------------------------------------------------------------


@st.cache_data
def load_themes() -> dict[str, dict]:
    """Load all theme JSON files from the themes/ directory."""
    themes = {}
    for p in sorted(THEMES_DIR.glob("theme_*.json")):
        with p.open() as f:
            data = json.load(f)
        themes[data["name"]] = data
    return themes


def inject_theme(theme: dict) -> None:
    """
    Inject a single <style> block derived from the theme JSON.

    Only static CSS — no @keyframes or animated gradient (ST_DESIGN.md §5).
    """
    c = theme["color"]
    g = theme["gradient"]

    bg_primary = c["background"]["primary"]
    bg_secondary = c["background"]["secondary"]
    bg_tertiary = c["background"]["tertiary"]
    bg_elevated = c["background"]["elevated"]
    txt_primary = c["text"]["primary"]
    txt_secondary = c["text"]["secondary"]
    txt_muted = c["text"]["muted"]
    border = c["border"]["default"]
    border_strong = c["border"]["strong"]
    acc1 = c["accent"]["primary"]
    acc2 = c["accent"]["secondary"]
    acc3 = c["accent"]["tertiary"]
    acc4 = c["accent"]["quaternary"]
    sem_success = c["semantic"]["success"]
    sem_error = c["semantic"]["error"]
    sem_info = c["semantic"]["info"]
    bg_gradient = g["background"]
    accent_bar = g["accent_bar"]

    css = f"""
    <style>
    /* ---------- CSS variables ---------- */
    :root {{
        --bg:          {bg_primary};
        --bg2:         {bg_secondary};
        --bg3:         {bg_tertiary};
        --elevated:    {bg_elevated};
        --txt:         {txt_primary};
        --txt2:        {txt_secondary};
        --muted:       {txt_muted};
        --border:      {border};
        --border2:     {border_strong};
        --accent-1:    {acc1};
        --accent-2:    {acc2};
        --accent-3:    {acc3};
        --accent-4:    {acc4};
        --success:     {sem_success};
        --error:       {sem_error};
        --info:        {sem_info};
    }}

    /* ---------- App container ---------- */
    .stApp, [data-testid="stAppViewContainer"] {{
        background: {bg_gradient} !important;
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        color: {txt_primary};
    }}

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {{
        background: {bg_secondary} !important;
        border-right: 1px solid {border} !important;
    }}
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {{
        color: {txt_primary} !important;
    }}

    /* ---------- Headers ---------- */
    h1, h2, h3, h4, h5, h6 {{ color: {txt_primary}; font-weight: 700; }}

    /* ---------- Buttons ---------- */
    .stButton > button {{
        background: {bg_elevated} !important;
        color: {txt_primary} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        padding: 5px 12px;
        transition: border-color 0.18s, background 0.18s;
    }}
    .stButton > button:hover {{
        border-color: {acc2} !important;
        background: {bg_tertiary} !important;
    }}
    /* Primary run button */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {acc1}22, {acc2}33) !important;
        border-color: {acc2} !important;
        color: {txt_primary} !important;
        font-weight: 600;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, {acc1}44, {acc2}55) !important;
    }}

    /* ---------- Active preset button ---------- */
    .stButton:has(+ .preset-active-marker) > button,
    .preset-active > button {{
        border-color: {acc2} !important;
        background: {acc2}22 !important;
        color: {acc2} !important;
        font-weight: 600;
    }}

    /* ---------- Expanders ---------- */
    .streamlit-expanderHeader {{
        background: {bg_tertiary} !important;
        color: {txt_primary} !important;
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid {border};
    }}
    .streamlit-expanderContent {{
        background: {bg_secondary} !important;
        border: 1px solid {border};
        border-top: none;
        border-radius: 0 0 8px 8px;
    }}

    /* ---------- Number / slider inputs ---------- */
    .stNumberInput input, .stTextInput input, .stSelectbox select {{
        background: {bg_elevated} !important;
        color: {txt_primary} !important;
        border: 1px solid {border} !important;
        border-radius: 6px !important;
    }}
    .stSlider [data-baseweb="slider"] div[role="slider"] {{
        background: {acc2} !important;
    }}
    .stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] {{
        background: {border} !important;
    }}

    /* ---------- Radio ---------- */
    .stRadio [data-testid="stMarkdownContainer"] {{ color: {txt_primary}; }}

    /* ---------- Metric ---------- */
    [data-testid="stMetric"] {{
        background: {bg_elevated};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 12px 16px;
    }}
    [data-testid="stMetricLabel"] {{ color: {txt_muted} !important; font-size: 0.78rem; }}
    [data-testid="stMetricValue"] {{ color: {txt_primary} !important; font-size: 1.1rem; font-weight: 700; }}

    /* ---------- Download button ---------- */
    [data-testid="stDownloadButton"] > button {{
        border-color: {acc3} !important;
        color: {acc3} !important;
    }}
    [data-testid="stDownloadButton"] > button:hover {{
        background: {acc3}22 !important;
    }}

    /* ---------- Columns border ---------- */
    [data-testid="stColumn"] .stVerticalBlock {{
        border-radius: 10px;
    }}

    /* ---------- Hero section ---------- */
    .hero {{
        text-align: center;
        padding: 2.2rem 1rem 1.4rem;
    }}
    .hero h1 {{
        font-size: clamp(2.5rem, 6vw, 4.5rem);
        font-weight: 800;
        background: {accent_bar};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.35rem;
        letter-spacing: -0.5px;
    }}
    .hero p {{
        color: {txt_muted};
        font-size: 1rem;
        max-width: 560px;
        margin: 0 auto;
    }}

    /* ---------- Accent bar under hero ---------- */
    .accent-bar {{
        height: 3px;
        background: {accent_bar};
        border-radius: 2px;
        margin: 0 auto 1.6rem;
        width: 100%;
    }}

    /* ---------- Metric card boxes ---------- */
    .param-box {{
        background: {bg_elevated};
        border: 1px solid {border_strong};
        border-radius: 12px;
        padding: 16px 18px 14px;
        height: 100%;
        font-family: 'Space Mono', ui-monospace, monospace;
        font-size: 0.82rem;
    }}
    .param-box-title {{
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid {border};
    }}

    .param-box.card-1 {{ background: linear-gradient(145deg, {bg_elevated} 30%, {acc1}15 130%); border-color: {acc1}33; }}
    .param-box.card-1 .param-box-title {{ color: {acc1}; border-bottom-color: {acc1}44; }}

    .param-box.card-2 {{ background: linear-gradient(145deg, {bg_elevated} 30%, {acc2}15 130%); border-color: {acc2}33; }}
    .param-box.card-2 .param-box-title {{ color: {acc2}; border-bottom-color: {acc2}44; }}

    .param-box.card-3 {{ background: linear-gradient(145deg, {bg_elevated} 30%, {acc3}15 130%); border-color: {acc3}33; }}
    .param-box.card-3 .param-box-title {{ color: {acc3}; border-bottom-color: {acc3}44; }}
    .param-row {{
        display: flex;
        justify-content: space-between;
        padding: 3px 0;
        color: {txt_secondary};
    }}
    .param-label {{ color: {txt_muted}; }}
    .param-value {{ color: {txt_primary}; font-weight: 600; }}
    .stable-badge {{
        display: inline-block;
        background: {sem_success}22;
        color: {sem_success};
        border: 1px solid {sem_success}55;
        border-radius: 6px;
        padding: 1px 8px;
        font-size: 0.78rem;
        font-weight: 700;
    }}
    .unstable-badge {{
        display: inline-block;
        background: {sem_error}22;
        color: {sem_error};
        border: 1px solid {sem_error}55;
        border-radius: 6px;
        padding: 1px 8px;
        font-size: 0.78rem;
        font-weight: 700;
    }}
    .color-dot {{
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        vertical-align: middle;
    }}

    /* ---------- Empty state ---------- */
    .empty-state {{
        text-align: center;
        padding: 4rem 2rem;
        color: {txt_muted};
    }}
    .empty-state .icon {{ font-size: 3.5rem; margin-bottom: 0.8rem; }}
    .empty-state p {{ font-size: 1rem; max-width: 420px; margin: 0 auto; }}

    /* ---------- Theory section ---------- */
    .theory-callout {{
        background: {bg_tertiary};
        border: 1px solid {border};
        border-left: 3px solid {acc2};
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        font-size: 0.9rem;
        color: {txt_secondary};
    }}
    .theory-callout strong {{ color: {acc2}; }}

    /* ---------- Preset badge ---------- */
    .confocal-badge {{
        display: inline-block;
        background: {acc3}25;
        color: {acc3};
        border: 1px solid {acc3}50;
        border-radius: 5px;
        padding: 0px 6px;
        font-size: 0.68rem;
        font-weight: 700;
        margin-left: 4px;
        vertical-align: middle;
    }}
    .category-header {{
        color: {txt_muted};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 10px 0 4px;
    }}

    /* ---------- Section separator ---------- */
    .section-sep {{
        border: none;
        border-top: 1px solid {border};
        margin: 1.6rem 0 1rem;
    }}



    /* ---------- Footer ---------- */
    .footer {{
        text-align: center;
        color: {txt_muted};
        font-size: 0.78rem;
        padding: 2rem 1rem 1rem;
        border-top: 1px solid {border};
        margin-top: 2rem;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Preset button helpers
# ---------------------------------------------------------------------------

_COLOR_HEX = {
    "red": "#ff3c3c",
    "blue": "#3c78ff",
    "green": "#32dc50",
    "orange": "#ff961e",
    "purple": "#b450ff",
}

_COLOR_NAMES = list(_COLOR_HEX.keys())


def _apply_preset(key: str) -> None:
    """
    on_click callback: copy all preset values into session state,
    or reset to defaults if the preset is already active.
    """
    if _is_active_preset(key):
        st.session_state["R1"] = -80.0
        st.session_state["R2"] = -80.0
        st.session_state["L"] = 70.0
        st.session_state["y0"] = 15.0
        st.session_state["theta0"] = 0.0
        st.session_state["N"] = 25
        st.session_state["arc_angle"] = 25.0
        st.session_state["ray_color"] = "red"
        st.session_state["active_preset"] = None
    else:
        p = CAVITY_PRESETS[key]
        st.session_state["R1"] = float(p["R1"])
        st.session_state["R2"] = float(p["R2"])
        st.session_state["L"] = float(p["L"])
        st.session_state["y0"] = float(p["y0_initial"])
        st.session_state["theta0"] = float(p["theta0_initial_deg"])
        st.session_state["N"] = int(p["N_round_trips"])
        st.session_state["arc_angle"] = float(p["arc_angle"])
        st.session_state["ray_color"] = p["ray_color"]
        st.session_state["active_preset"] = key

    st.session_state.pop("run_result_cavity", None)
    st.session_state.pop("gif_bytes", None)


def _is_active_preset(key: str) -> bool:
    """True if the current control values exactly match this preset's values."""
    p = CAVITY_PRESETS[key]
    return (
        abs(st.session_state.get("R1", 0) - p["R1"]) < 1e-9
        and abs(st.session_state.get("R2", 0) - p["R2"]) < 1e-9
        and abs(st.session_state.get("L", 0) - p["L"]) < 1e-9
        and abs(st.session_state.get("y0", 0) - p["y0_initial"]) < 1e-9
        and abs(st.session_state.get("theta0", 0) - p["theta0_initial_deg"]) < 1e-9
        and st.session_state.get("N", 0) == p["N_round_trips"]
        and st.session_state.get("ray_color", "") == p["ray_color"]
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def sidebar_controls(themes: dict) -> dict:
    """
    Render the sidebar and return a dict of current parameter values.

    Handles:
    - Theme selector
    - Common settings (fps, points_per_segment)
    - Cavity parameters (R1, R2, L, y0, theta0, N, arc_angle)
    - Preset buttons grouped by computed category
    - Ray color picker
    """
    with st.sidebar:
        st.markdown("## 🔬 Cavity Controls")
        st.markdown(
            "<hr style='border:1px solid var(--border); margin:0.5rem 0 1rem'>",
            unsafe_allow_html=True,
        )

        # ---- Theme selector ------------------------------------------------
        theme_name = st.selectbox(
            "🎨 Theme",
            options=list(themes.keys()),
            key="theme_name",
            help="Switch the app colour palette",
        )

        st.markdown(
            "<hr style='border:1px solid var(--border); margin:0.8rem 0'>",
            unsafe_allow_html=True,
        )

        # ---- Common settings -----------------------------------------------
        with st.expander("⚙️ Common Settings", expanded=True):
            fps = st.slider(
                "FPS (animation)",
                min_value=5,
                max_value=60,
                value=30,
                step=1,
                key="fps",
                help="Frame rate for animation playback and MP4 export",
            )
            pts_per_seg = st.slider(
                "Points per segment",
                min_value=2,
                max_value=20,
                value=5,
                step=1,
                key="pts_per_seg",
                help="Interpolation density; higher = smoother animation, more frames",
            )

        # ---- Cavity parameters --------------------------------------------
        with st.expander("📐 Cavity Parameters", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                R1 = st.number_input(
                    "R₁ (cm)",
                    value=st.session_state.get("R1", -80.0),
                    step=5.0,
                    format="%.1f",
                    key="R1",
                    help="Mirror 1 radius — negative = concave, positive = convex",
                )
                R2 = st.number_input(
                    "R₂ (cm)",
                    value=st.session_state.get("R2", -80.0),
                    step=5.0,
                    format="%.1f",
                    key="R2",
                    help="Mirror 2 radius — negative = concave, positive = convex",
                )
                L = st.number_input(
                    "L (cm)",
                    value=st.session_state.get("L", 70.0),
                    min_value=1.0,
                    step=5.0,
                    format="%.1f",
                    key="L",
                    help="Cavity length (distance between mirror vertices)",
                )
            with col_b:
                y0 = st.number_input(
                    "y₀ (cm)",
                    value=st.session_state.get("y0", 15.0),
                    step=0.5,
                    format="%.2f",
                    key="y0",
                    help="Initial ray height from optical axis",
                )
                theta0 = st.slider(
                    "θ₀ (°)",
                    min_value=-45.0,
                    max_value=45.0,
                    value=float(st.session_state.get("theta0", 0.0)),
                    step=0.5,
                    key="theta0",
                    help="Initial ray angle in degrees",
                )
                N = st.slider(
                    "Round trips",
                    min_value=1,
                    max_value=100,
                    value=int(st.session_state.get("N", 25)),
                    key="N",
                    help="Number of cavity round trips to simulate",
                )
                arc_angle = st.slider(
                    "Arc angle (°)",
                    min_value=5.0,
                    max_value=60.0,
                    value=float(st.session_state.get("arc_angle", 25.0)),
                    step=1.0,
                    key="arc_angle",
                    help="Visual half-angle of the mirror arcs",
                )

        # ---- Preset buttons ------------------------------------------------
        with st.expander("🎯 Cavity Presets", expanded=True):
            grouped = get_presets_by_category()
            category_labels = {
                "CONCAVE-CONCAVE": "Concave – Concave",
                "CONCAVE-CONVEX": "Concave – Convex",
                "CONVEX-CONCAVE": "Convex – Concave",
                "CONVEX-CONVEX": "Convex – Convex",
            }
            for cat, keys in grouped.items():
                if not keys:
                    continue
                st.markdown(
                    f"<div class='category-header'>{category_labels.get(cat, cat)}</div>",
                    unsafe_allow_html=True,
                )
                for i in range(0, len(keys), 2):
                    row_keys = keys[i : i + 2]
                    btn_cols = st.columns(len(row_keys))
                    for col, key in zip(btn_cols, row_keys):
                        preset = CAVITY_PRESETS[key]
                        label = preset["label"]
                        if is_confocal(preset):
                            label_html = (
                                f"{label} <span class='confocal-badge'>confocal</span>"
                            )
                        else:
                            label_html = label
                        active = _is_active_preset(key)
                        with col:
                            btn_label = preset["label"]
                            btn_type = "primary" if active else "secondary"
                            st.button(
                                btn_label,
                                key=f"preset_{key}",
                                help=f"{key}  R1={preset['R1']}  R2={preset['R2']}  L={preset['L']}",
                                use_container_width=True,
                                on_click=_apply_preset,
                                args=(key,),
                                type=btn_type,
                            )

        # ---- Ray color picker ---------------------------------------------
        st.markdown("#### Ray Colour")
        ray_color = st.radio(
            "Ray colour",
            options=_COLOR_NAMES,
            index=_COLOR_NAMES.index(st.session_state.get("ray_color", "red")),
            horizontal=True,
            key="ray_color",
            label_visibility="collapsed",
            format_func=lambda c: f"{'●'} {c.capitalize()}",
        )

    return {
        "theme_name": theme_name,
        "fps": fps,
        "pts_per_seg": pts_per_seg,
        "R1": R1,
        "R2": R2,
        "L": L,
        "y0": y0,
        "theta0": theta0,
        "N": N,
        "arc_angle": arc_angle,
        "ray_color": ray_color,
    }


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Optical Cavity Ray Tracing</h1>
            <p>Explore stable and unstable resonators through the ABCD matrix formalism —
            visualise single-ray trajectories and animated round trips in concave,
            convex, and mixed-mirror cavities.</p>
        </div>
        <div class="accent-bar"></div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Theory section
# ---------------------------------------------------------------------------


def theory_cavity() -> None:
    with st.expander(
        "📖 THEORY · ABCD matrices, g-parameters, stability", expanded=True
    ):
        st.markdown(
            """
            An **optical cavity** confines light between two mirrors with radii of curvature
            $R_1$ and $R_2$ separated by a length $L$.  The **ABCD (ray transfer) matrix**
            method propagates a ray state vector $\\begin{pmatrix} y \\\\ \\theta \\end{pmatrix}$
            — height $y$ from the optical axis and paraxial angle $\\theta$ — through each
            optical element.  A round trip is stable if and only if
            $0 \\le g_1 g_2 \\le 1$, where the **g-parameters** quantify each mirror's
            focusing power relative to the cavity length.
            """,
            unsafe_allow_html=False,
        )

        col1, col2 = st.columns(2, gap="large", border=True)  # type: ignore

        with col1:
            st.markdown(
                "<div class='theory-callout'><strong>ABCD Matrices</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown("**Free-space propagation** over length $L$:")
            st.latex(r"M_{\text{prop}} = \begin{pmatrix} 1 & L \\ 0 & 1 \end{pmatrix}")
            st.markdown(
                "**Mirror reflection** at radius $R_i$ ($R < 0$ concave, $R > 0$ convex):"
            )
            st.latex(
                r"M_{\text{refl},i} = \begin{pmatrix} 1 & 0 \\ 2/R_i & 1 \end{pmatrix}"
            )
            st.markdown("**Mirror–surface intersection** at height $y$:")
            st.latex(r"x = x_c \pm \operatorname{sign}(R)\,\sqrt{R^2 - y^2}")
            st.markdown(
                "_where $x_c = \\mp L/2 - R$ is the mirror centre._",
                unsafe_allow_html=False,
            )

        with col2:
            st.markdown(
                "<div class='theory-callout'><strong>g-Parameters &amp; Stability</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown("**g-parameters** for each mirror:")
            st.latex(r"g_i = 1 + \frac{L}{R_i}, \qquad i = 1, 2")
            st.markdown("**Stability condition** (beam remains bounded):")
            st.latex(r"0 \;\le\; g_1\,g_2 \;\le\; 1")
            st.markdown("**Confocal** boundary condition:")
            st.latex(
                r"L = |R_1| = |R_2| \quad \Longrightarrow \quad g_1 g_2 = \tfrac{1}{4}"
            )
            st.markdown(
                "_Confocal is a special point **within** the concave-concave family, "
                "not a separate category.  At the confocal point every paraxial ray "
                "passes through the common focal plane between the mirrors after each "
                "half-trip._",
            )


# ---------------------------------------------------------------------------
# Metric cards
# ---------------------------------------------------------------------------


def _param_row(label: str, value: str) -> str:
    return (
        f"<div class='param-row'>"
        f"<span class='param-label'>{label}</span>"
        f"<span class='param-value'>{value}</span>"
        f"</div>"
    )


def _stability_badge(is_stable: bool) -> str:
    if is_stable:
        return "<span class='stable-badge'>● STABLE</span>"
    return "<span class='unstable-badge'>● UNSTABLE</span>"


def _color_dot(color: str) -> str:
    hex_col = _COLOR_HEX.get(color, "#aaaaaa")
    return (
        f"<span class='color-dot' style='background:{hex_col}'></span>"
        f"{color.capitalize()}"
    )


def render_metric_cards(cp, params: dict) -> None:
    """
    Render the three metric-card boxes (ST_DESIGN.md §8.2).

    cp     : CavityParameters from get_cavity_parameters()
    params : sidebar parameter dict (for theta0, y0, N, ray_color)
    """
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        rows = (
            _param_row("R₁ (cm)", f"{cp.R1:.1f}")
            + _param_row("Mirror 1", cp.mirror1_type)
            + _param_row("R₂ (cm)", f"{cp.R2:.1f}")
            + _param_row("Mirror 2", cp.mirror2_type)
            + _param_row("L (cm)", f"{cp.L:.1f}")
            + _param_row("Config", cp.cavity_config)
        )
        st.markdown(
            f"<div class='param-box card-1'>"
            f"<div class='param-box-title'>Mirror Geometry</div>"
            f"{rows}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col2:
        stability_html = _stability_badge(cp.is_stable)
        rows = (
            _param_row("g₁", f"{cp.g1:.4f}")
            + _param_row("g₂", f"{cp.g2:.4f}")
            + _param_row("g₁ · g₂", f"{cp.stability_product:.4f}")
            + f"<div class='param-row'><span class='param-label'>Stability</span>"
            f"<span class='param-value'>{stability_html}</span></div>"
        )
        if cp.is_confocal:
            rows += _param_row("Special", "⭐ Confocal boundary")
        elif cp.is_symmetric:
            rows += _param_row("Symmetry", "Symmetric")
        st.markdown(
            f"<div class='param-box card-2'>"
            f"<div class='param-box-title'>g-Parameters &amp; Stability</div>"
            f"{rows}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col3:
        color_html = _color_dot(params["ray_color"])
        rows = (
            _param_row("θ₀ (°)", f"{params['theta0']:.1f}")
            + _param_row("y₀ (cm)", f"{params['y0']:.2f}")
            + _param_row("Round trips", str(params["N"]))
            + f"<div class='param-row'><span class='param-label'>Ray colour</span>"
            f"<span class='param-value'>{color_html}</span></div>"
        )
        st.markdown(
            f"<div class='param-box card-3'>"
            f"<div class='param-box-title'>Ray &amp; Trip Info</div>"
            f"{rows}"
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Simulation section
# ---------------------------------------------------------------------------


def _auto_filename(cp, params: dict, suffix: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if cp.is_confocal:
        prefix = "confocal"
    elif cp.is_symmetric:
        prefix = "symmetric"
    else:
        prefix = "asymmetric"
    return (
        f"{prefix}_cavity_R1_{int(cp.R1)}_R2_{int(cp.R2)}_L_{int(cp.L)}"
        f"_theta_{params['theta0']:.0f}_rc_{params['ray_color']}_{ts}.{suffix}"
    )


def simulation_section(params: dict) -> None:
    """
    Main simulation area (ST_DESIGN.md §8):
      Run button → metric cards → static figure + PNG → animation + MP4
    """
    run_clicked = st.button(
        "▶  Run Simulation", type="primary", use_container_width=False
    )

    if run_clicked:
        st.session_state.pop("gif_bytes", None)
        R1 = params["R1"]
        R2 = params["R2"]
        L = params["L"]

        try:
            with st.spinner("⚙️ Tracing rays through the cavity…"):
                cavity = CavityRayTracing(R1=R1, R2=R2, L=L)
                ray_segments, _ = cavity.trace_ray(
                    y0_initial=params["y0"],
                    theta0_initial_deg=params["theta0"],
                    N_round_trips=params["N"],
                )
                all_points, seg_ids, pt_idx_in_seg, npps = cavity._interpolate_segments(
                    ray_segments, params["pts_per_seg"]
                )
                ray_path = []
                for i, seg in enumerate(ray_segments):
                    if i == 0:
                        ray_path.extend(seg)
                    else:
                        ray_path.extend(seg[1:])

                static_fig = build_static_figure(
                    cavity,
                    ray_path,
                    ray_color=params["ray_color"],
                    arc_angle=params["arc_angle"],
                )
                anim_fig = build_animated_figure(
                    cavity,
                    all_points,
                    seg_ids,
                    pt_idx_in_seg,
                    npps,
                    ray_color=params["ray_color"],
                    arc_angle=params["arc_angle"],
                    fps=params["fps"],
                )
                cp = cavity.get_cavity_parameters()
                stability_fig = build_stability_diagram(cp)

            st.session_state["run_result_cavity"] = {
                "static_fig": static_fig,
                "anim_fig": anim_fig,
                "stability_fig": stability_fig,
                "cp": cp,
                "params": params.copy(),
            }

        except (ValueError, TypeError) as exc:
            st.error(f"❌ Simulation error: {exc}")
            return

    # ---- Render cached result --------------------------------------------
    result = st.session_state.get("run_result_cavity")

    if result is None:
        st.markdown(
            """
            <div class='empty-state'>
                <div class='icon'>🔬</div>
                <p>Adjust the cavity controls in the sidebar,
                then click <strong>▶ Run Simulation</strong>
                to reveal the ray path.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cp = result["cp"]
    static_fig = result["static_fig"]
    anim_fig = result["anim_fig"]
    stability_fig = result.get("stability_fig")
    if stability_fig is None:
        stability_fig = build_stability_diagram(cp)
        result["stability_fig"] = stability_fig
    res_params = result["params"]

    # ---- Metric cards ------------------------------------------------------
    st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)
    render_metric_cards(cp, res_params)
    st.markdown("<div style='margin-bottom: 1.2rem'></div>", unsafe_allow_html=True)

    # ---- Static figure -----------------------------------------------------
    st.markdown("### 🖼️ Static Ray Diagram")
    st.plotly_chart(
        static_fig, use_container_width=False, config={"displaylogo": False}
    )

    png_col, _ = st.columns([1, 3])
    with png_col:
        try:
            png_bytes = export_png(static_fig)
            st.download_button(
                label="⬇️ Download PNG",
                data=png_bytes,
                file_name=_auto_filename(cp, res_params, "png"),
                mime="image/png",
                help="Exports the static ray diagram at 3× resolution (Kaleido)",
            )
        except Exception as exc:
            st.warning(f"PNG export unavailable: {exc}")

    st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)

    # ---- Animated figure ---------------------------------------------------
    st.markdown("### 🎬 Ray Tracing Animation")
    st.caption(
        "Use the **▶ Play** button or drag the scrub bar. "
        "The animation shows the ray growing segment by segment in real time."
    )
    st.plotly_chart(anim_fig, use_container_width=False, config={"displaylogo": False})

    # ---- GIF Export panel --------------------------------------------------
    with st.expander("💾 Export Animation as GIF", expanded=False):
        st.markdown(
            "_Renders each Plotly frame through Kaleido (headless Chromium) then "
            "muxes into an animated GIF.  This is CPU-intensive — allow ~1–3 min for large "
            f"frame counts.  Current frame count: **{len(anim_fig.frames)}**._"
        )
        export_fps = st.slider(
            "Export FPS",
            5,
            60,
            int(res_params["fps"]),
            key="export_fps",
        )
        export_name = st.text_input(
            "File name",
            value=_auto_filename(cp, res_params, "gif"),
            key="export_name",
        )
        do_export = st.button("🎬 Render & Export GIF", key="btn_export_gif")

        if do_export:
            st.session_state.pop("gif_bytes", None)
            progress_bar = st.progress(0, text="Rendering frames…")
            status_text = st.empty()

            def _progress(current: int, total: int) -> None:
                frac = current / total
                progress_bar.progress(frac, text=f"Rendering frame {current}/{total}…")
                status_text.markdown(f"_{current} / {total} frames done_")

            try:
                gif_bytes = export_gif(anim_fig, fps=export_fps, progress_cb=_progress)
                progress_bar.progress(1.0, text="✅ Done!")
                status_text.empty()
                st.session_state["gif_bytes"] = gif_bytes
                st.session_state["gif_name"] = export_name
            except Exception as exc:
                st.error(f"GIF export failed: {exc}")

        if "gif_bytes" in st.session_state and st.session_state["gif_bytes"]:
            st.download_button(
                label="⬇️ Download GIF",
                data=st.session_state["gif_bytes"],
                file_name=st.session_state.get("gif_name", "animation.gif"),
                mime="image/gif",
            )

    # ---- Stability Diagram -------------------------------------------------
    st.markdown("### 📊 Stability Diagram")
    st.plotly_chart(
        stability_fig, use_container_width=False, config={"displaylogo": False}
    )

    png_col_stab, _ = st.columns([1, 3])
    with png_col_stab:
        try:
            png_bytes_stab = export_png(stability_fig)
            st.download_button(
                label="⬇️ Download PNG",
                data=png_bytes_stab,
                file_name=_auto_filename(cp, res_params, "png").replace(
                    ".png", "_stability.png"
                ),
                mime="image/png",
                help="Exports the stability diagram at 3× resolution (Kaleido)",
            )
        except Exception as exc:
            st.warning(f"PNG export unavailable: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    themes = load_themes()

    # Sidebar (also sets session state)
    params = sidebar_controls(themes)

    # Apply theme CSS
    selected_theme = themes.get(params["theme_name"], list(themes.values())[0])
    inject_theme(selected_theme)

    # Hero
    render_hero()

    # Theory
    theory_cavity()

    # Simulation
    simulation_section(params)

    # Footer
    st.markdown(
        "<div class='footer'>"
        "Built with <strong>Streamlit</strong> · <strong>Plotly</strong> · "
        "<strong>NumPy</strong> · <strong>Kaleido</strong> · <strong>imageio</strong>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
