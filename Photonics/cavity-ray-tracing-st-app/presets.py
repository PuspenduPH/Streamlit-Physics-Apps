"""
presets.py — Cavity preset configurations and category derivation.

Owns:
    - CAVITY_PRESETS: a flat dict of all preset cavity configurations.
    - classify_preset(): derives the cavity category
      ("CONCAVE-CONCAVE" / "CONVEX-CONCAVE" / "CONCAVE-CONVEX") from a
      preset's *actual* R1/R2 values — never from a hand-picked label.
    - get_presets_by_category(): a convenience grouping used by the
      sidebar preset buttons (see ST_DESIGN.md §6.3), built by calling
      classify_preset() on every preset, so the grouping can never drift
      out of sync with the physics.

Historical note
----------------
The original `presets.txt` nested every preset under hand-written
top-level keys, "concave_concave" and "concave_convex". That was the bug
this module fixes: those keys were *labels*, not computed facts, and they
were wrong in places — e.g. CX03_focused_convex_concave has R1=+50
(convex) and R2=-100 (concave), i.e. CONVEX-CONCAVE, yet it was filed
under the same "concave_convex" bucket as CX01/CX02/CX04, which are
CONCAVE-CONVEX (R1 concave, R2 convex). `classify_preset` fixes this by
always recomputing the category from R1/R2, so it can never be hand-typed
incorrectly again.

Sign convention (matches cavity_ray_tracing.py)
------------------------------------------------
    R < 0  ->  concave mirror
    R > 0  ->  convex mirror
"""

from typing import Dict, List, Literal, TypedDict

MirrorType = Literal["concave", "convex"]
CavityCategory = Literal[
    "CONCAVE-CONCAVE",
    "CONVEX-CONCAVE",
    "CONCAVE-CONVEX",
    "CONVEX-CONVEX",
]


class PresetParams(TypedDict):
    R1: float
    R2: float
    L: float
    y0_initial: float
    theta0_initial_deg: float
    N_round_trips: int
    arc_angle: float
    ray_color: str
    label: str


# ---------------------------------------------------------------------------
# Mirror / category classification — derived from real numbers, never labels
# ---------------------------------------------------------------------------

def mirror_type(R: float) -> MirrorType:
    """Classify a single mirror from its radius of curvature.

    R < 0 -> concave, R > 0 -> convex. This mirrors the sign convention
    used throughout cavity_ray_tracing.py's ABCD matrices (see
    ST_DESIGN.md §4.2, rule 3: "Preserve sign conventions exactly").
    """
    return "concave" if R < 0 else "convex"


def classify_preset(params: Dict) -> CavityCategory:
    """Derive a cavity's category from its real R1/R2 values.

    This is the single source of truth for cavity categorization. It is
    intentionally order-sensitive (R1's type comes first) since a preset
    with R1 convex / R2 concave is optically distinct from one with R1
    concave / R2 convex, even though both mix mirror types.

    Accepts any dict/object exposing "R1" and "R2" (a CAVITY_PRESETS
    entry, live sidebar params, or an app.py CavityParameters instance),
    so the same function classifies presets and free-form user input
    alike.

    Returns
    -------
    "CONCAVE-CONCAVE"
        Both mirrors concave. Includes the confocal boundary case
        (L == |R1| == |R2|) — confocal is a special case *within* this
        category, not a separate one.
    "CONVEX-CONCAVE"
        R1 convex, R2 concave.
    "CONCAVE-CONVEX"
        R1 concave, R2 convex.
    "CONVEX-CONVEX"
        Both mirrors convex. Not physically represented among the shipped
        presets (a convex-convex resonator has no real focusing element
        and is generally unbounded), but returned rather than raised so
        this function stays a pure classifier, not a validator.
    """
    t1 = mirror_type(params["R1"])
    t2 = mirror_type(params["R2"])

    if t1 == "concave" and t2 == "concave":
        return "CONCAVE-CONCAVE"
    if t1 == "convex" and t2 == "concave":
        return "CONVEX-CONCAVE"
    if t1 == "concave" and t2 == "convex":
        return "CONCAVE-CONVEX"
    return "CONVEX-CONVEX"


def is_confocal(params: Dict) -> bool:
    """True at the confocal boundary: L == |R1| == |R2|.

    Confocal is a boundary condition *inside* CONCAVE-CONCAVE, not its own
    top-level category (see ST_DESIGN.md §12 regression note).
    """
    return params["L"] == abs(params["R1"]) == abs(params["R2"])


# ---------------------------------------------------------------------------
# CAVITY_PRESETS — flat dict, ported from presets.txt / the old CAVITY_CASES
# ---------------------------------------------------------------------------

CAVITY_PRESETS: Dict[str, PresetParams] = {
    "CC01_symmetric_confocal_boundary": {
        "R1": -80.0,
        "R2": -80.0,
        "L": 80.0,
        "y0_initial": 15.0,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 10,
        "arc_angle": 30.0,
        "ray_color": "red",
        "label": "Symmetric Confocal Boundary",
    },
    "CC02_symmetric_near_concentric": {
        "R1": -50.0,
        "R2": -50.0,
        "L": 80.0,
        "y0_initial": 12.0,
        "theta0_initial_deg": 1.5,
        "N_round_trips": 40,
        "arc_angle": 40.0,
        "ray_color": "blue",
        "label": "Symmetric Near-Concentric",
    },
    "CC03_asymmetric_near_concentric": {
        "R1": -50.0,
        "R2": -80.0,
        "L": 95.0,
        "y0_initial": -12.0,
        "theta0_initial_deg": 1.0,
        "N_round_trips": 32,
        "arc_angle": 30.0,
        "ray_color": "green",
        "label": "Asymmetric Near-Concentric",
    },
    "CC04_asymmetric_concentric_side": {
        "R1": -85.0,
        "R2": -40.0,
        "L": 90.0,
        "y0_initial": 6.0,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 30,
        "arc_angle": 25.0,
        "ray_color": "purple",
        "label": "Asymmetric Concentric Side",
    },
    "CX01_near_upper_stability_boundary": {
        "R1": -140.0,
        "R2": 70.0,
        "L": 85.0,
        "y0_initial": 5.0,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 30,
        "arc_angle": 20.0,
        "ray_color": "orange",
        "label": "Near Upper Stability Boundary",
    },
    "CX02_focused_concave_convex": {
        "R1": -100.0,
        "R2": 50.0,
        "L": 90.0,
        "y0_initial": 5.5,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 35,
        "arc_angle": 25.0,
        "ray_color": "red",
        "label": "Focused Concave-Convex",
    },
    "CX03_focused_convex_concave": {
        "R1": 50.0,
        "R2": -100.0,
        "L": 95.0,
        "y0_initial": -6.5,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 40,
        "arc_angle": 35.0,
        "ray_color": "blue",
        "label": "Focused Convex-Concave",
    },
    "CX04_low_product_convex_concave": {
        "R1": 60.0,
        "R2": -120.0,
        "L": 115.0,
        "y0_initial": 6.0,
        "theta0_initial_deg": 0.0,
        "N_round_trips": 30,
        "arc_angle": 30.0,
        "ray_color": "green",
        "label": "Low-Product Convex-Concave",
    },
}


# ---------------------------------------------------------------------------
# Sidebar grouping helper — categories computed on demand, never hardcoded
# ---------------------------------------------------------------------------

def get_presets_by_category() -> Dict[CavityCategory, List[str]]:
    """Group CAVITY_PRESETS keys by their *computed* category.

    Used to build the sidebar's preset button rows (ST_DESIGN.md §6.3).
    Grouping is recomputed from classify_preset() on every call, so if a
    preset's R1/R2 are edited it silently moves to the correct category
    row instead of needing a matching manual edit here.
    """
    grouped: Dict[CavityCategory, List[str]] = {
        "CONCAVE-CONCAVE": [],
        "CONVEX-CONCAVE": [],
        "CONCAVE-CONVEX": [],
        "CONVEX-CONVEX": [],
    }
    for name, params in CAVITY_PRESETS.items():
        grouped[classify_preset(params)].append(name)
    return grouped


if __name__ == "__main__":
    # Quick manual sanity check, mirrors ST_DESIGN.md §12's regression note.
    for name, params in CAVITY_PRESETS.items():
        category = classify_preset(params)
        confocal = " (confocal boundary)" if is_confocal(params) else ""
        print(f"{name:45s} R1={params['R1']:>7.1f}  R2={params['R2']:>7.1f}"
              f"  -> {category}{confocal}")
