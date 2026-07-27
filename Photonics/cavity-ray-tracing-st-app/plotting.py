"""
plotting.py — Plotly figure builders for the optical cavity ray tracing app.

Public API
----------
    build_static_figure(cavity, ray_path, ray_color, arc_angle)  -> go.Figure
    build_animated_figure(cavity, all_points, seg_ids, pt_idx_in_seg,
                          npps, ray_color, arc_angle, fps)          -> go.Figure
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from cavity_ray_tracing import RAY_COLOR_DICT, CavityParameters, CavityRayTracing

# Maximum number of Plotly frames in the animated figure.
MAX_FRAMES = 600
ARC_SAMPLES = 300


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sample_arc(
    center_x: float,
    center_y: float,
    radius: float,
    theta1_deg: float,
    theta2_deg: float,
    n: int = ARC_SAMPLES,
) -> tuple[list, list]:
    """
    Sample a circular arc and return (xs, ys) coordinate lists.

    Parameters
    ----------
    center_x, center_y : float   Arc centre coordinates.
    radius             : float   Radius of the circle.
    theta1_deg         : float   Start angle in degrees.
    theta2_deg         : float   End angle in degrees.
    n                  : int     Number of sample points.

    Returns
    -------
    (xs, ys) : tuple of list
    """
    thetas = np.linspace(math.radians(theta1_deg), math.radians(theta2_deg), n)
    xs = (center_x + radius * np.cos(thetas)).tolist()
    ys = (center_y + radius * np.sin(thetas)).tolist()
    return xs, ys


def _build_base_traces(
    cavity: CavityRayTracing, ray_color: str, arc_angle: float
) -> list[go.BaseTraceType]:
    """
    Build the static backdrop traces: left mirror, right mirror, optical axis.
    """
    theta1_L, theta2_L, theta1_R, theta2_R = cavity._get_mirror_arc_angles(arc_angle)

    # Left mirror arc
    lx, ly = _sample_arc(
        cavity.left_mirror_center_x,
        0.0,
        abs(cavity.R1),
        theta1_L,
        theta2_L,
    )
    # Right mirror arc
    rx, ry = _sample_arc(
        cavity.right_mirror_center_x,
        0.0,
        abs(cavity.R2),
        theta1_R,
        theta2_R,
    )

    mirror_style = dict(
        color="rgb(160,160,170)",
        width=14,
        shape="spline",
        smoothing=1.0,
    )

    left_mirror_trace = go.Scatter(
        x=lx,
        y=ly,
        mode="lines",
        line=mirror_style,
        name="Mirror 1",
        hoverinfo="skip",
        showlegend=False,
    )
    right_mirror_trace = go.Scatter(
        x=rx,
        y=ry,
        mode="lines",
        line=mirror_style,
        name="Mirror 2",
        hoverinfo="skip",
        showlegend=False,
    )

    # Optical axis
    axis_trace = go.Scatter(
        x=[-cavity.L / 2, cavity.L / 2],
        y=[0, 0],
        mode="lines",
        line=dict(color="rgba(180,180,180,0.35)", width=1, dash="dash"),
        name="Optical axis",
        hoverinfo="skip",
        showlegend=False,
    )

    return [left_mirror_trace, right_mirror_trace, axis_trace]


def _calculate_plot_limits(
    cavity: CavityRayTracing, arc_angle: float, max_ray_y: float
) -> tuple[float, float, float, float]:
    """Calculate mathematically robust plot limits ensuring both mirrors and rays fit within the locked aspect ratio."""
    req_x = cavity.L + 2 * (cavity.L * 0.06)

    m1_h = min(abs(cavity.R1), cavity.L * 5) * math.sin(math.radians(arc_angle))
    m2_h = min(abs(cavity.R2), cavity.L * 5) * math.sin(math.radians(arc_angle))

    req_y_extent = max(m1_h, m2_h, max_ray_y) * 1.10
    req_y = req_y_extent * 2.0

    fig_w, fig_h = 700.0, 500.0
    aspect = fig_h / fig_w

    if req_y > req_x * aspect:
        final_y_extent = req_y_extent
        final_x_margin = ((req_y / aspect) - cavity.L) / 2.0
    else:
        final_x_margin = cavity.L * 0.08
        final_y_extent = ((cavity.L + 2 * final_x_margin) * aspect) / 2.0

    return final_x_margin, final_y_extent, fig_w, fig_h


def _figure_layout(
    cavity: CavityRayTracing,
    ray_color: str,
    title: str,
    arc_angle: float,
    max_ray_y: float,
) -> go.Layout:
    """Shared dark Plotly layout with correct axis ranges and tinted background."""
    ax_face = RAY_COLOR_DICT[ray_color]["ax_face"]

    x_margin, y_extent, fig_w, fig_h = _calculate_plot_limits(
        cavity, arc_angle, max_ray_y
    )

    return go.Layout(
        title=dict(
            text=title,
            font=dict(family="Inter, sans-serif", size=16, color="#e0e8ff"),
            x=0.5,
            xanchor="center",
        ),
        autosize=False,
        width=fig_w,
        height=fig_h,
        plot_bgcolor=ax_face,
        paper_bgcolor="#08090d",
        font=dict(family="Inter, sans-serif", color="#c4cfe8"),
        xaxis=dict(
            range=[-cavity.L / 2 - x_margin, cavity.L / 2 + x_margin],
            visible=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=[-y_extent, y_extent],
            visible=False,
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True,
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=False,
        hovermode=False,
    )


def _cavity_title(cavity: CavityRayTracing, prefix: str) -> str:
    """Build a tidy figure title string from cavity properties."""
    if cavity.is_confocal:
        suffix = "Confocal"
    elif cavity.is_symmetric:
        suffix = f"Symmetric {cavity.mirror_description}"
    else:
        suffix = f"Asymmetric {cavity.mirror_description}"
    return f"{prefix} — {suffix} Cavity"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_static_figure(
    cavity: CavityRayTracing,
    ray_path: list[tuple],
    ray_color: str = "red",
    arc_angle: float = 25.0,
) -> go.Figure:
    """
    Build a static Plotly figure showing the full ray path through the cavity.

    Parameters
    ----------
    cavity    : CavityRayTracing   Configured cavity object.
    ray_path  : list of (x, y)    Full ray path from trace_single_ray().
    ray_color : str               One of 'red', 'blue', 'green', 'orange', 'purple'.
    arc_angle : float             Mirror arc half-angle in degrees (0 < arc_angle < 90).

    Returns
    -------
    go.Figure
        Static figure with mirror arcs, optical axis, and full ray path.
        No annotation boxes — parameters displayed via metric cards in app.py.
    """
    base_traces = _build_base_traces(cavity, ray_color, arc_angle)

    # Ray path trace
    path_x = [p[0] for p in ray_path]
    path_y = [p[1] for p in ray_path]
    ray_trace = go.Scatter(
        x=path_x,
        y=path_y,
        mode="lines+markers",
        line=dict(color=RAY_COLOR_DICT[ray_color]["plotly_rgb"], width=2),
        marker=dict(size=3, color=RAY_COLOR_DICT[ray_color]["plotly_rgb"]),
        name="Ray path",
        hoverinfo="skip",
        showlegend=False,
    )

    traces = [ray_trace] + base_traces

    max_ray_y = max((abs(y) for x, y in ray_path), default=0.0)

    layout = _figure_layout(
        cavity,
        ray_color,
        _cavity_title(cavity, "Single Ray Tracing"),
        arc_angle,
        max_ray_y,
    )

    return go.Figure(data=traces, layout=layout)


def build_animated_figure(
    cavity: CavityRayTracing,
    all_points: list[tuple],
    seg_ids: list[int],
    pt_idx_in_seg: list[int],
    npps: int,
    ray_color: str = "red",
    arc_angle: float = 25.0,
    fps: int = 30,
) -> go.Figure:
    """
    Build a Plotly figure with frame-by-frame animation of ray propagation.

    Parameters
    ----------
    cavity         : CavityRayTracing   Configured cavity object.
    all_points     : list of (x, y)     Interpolated ray points from _interpolate_segments().
    seg_ids        : list of int        Segment ID per point (for round-trip counter labels).
    pt_idx_in_seg  : list of int        Point index within each segment.
    npps           : int                Points per segment used in interpolation.
    ray_color      : str                Ray colour key.
    arc_angle      : float              Mirror arc half-angle in degrees.
    fps            : int                Playback frame rate.

    Returns
    -------
    go.Figure
        Animated figure with Plotly updatemenus (Play/Pause) and a scrub slider.
        Frame count is capped at MAX_FRAMES via uniform downsampling.
    """
    n_total = len(all_points)

    if n_total > MAX_FRAMES:
        stride = math.ceil(n_total / MAX_FRAMES)
        frame_indices = list(range(0, n_total, stride))
        if frame_indices[-1] != n_total - 1:
            frame_indices.append(n_total - 1)
    else:
        frame_indices = list(range(n_total))

    base_traces = _build_base_traces(cavity, ray_color, arc_angle)
    total_rt = (seg_ids[-1] // 2 + 1) if seg_ids else 0

    rgb = RAY_COLOR_DICT[ray_color]["plotly_rgb"]

    ray_trail = go.Scatter(
        x=[],
        y=[],
        mode="lines",
        line=dict(color=rgb, width=2),
        name="Ray trail",
        hoverinfo="skip",
        showlegend=False,
    )
    arrowhead = go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            symbol="triangle-up",
            size=14,
            color=rgb,
            standoff=0,
        ),
        name="Arrowhead",
        hoverinfo="skip",
        showlegend=False,
    )

    all_traces = [ray_trail, arrowhead] + base_traces

    trail_idx = 0
    arrow_idx = 1

    frames = []
    slider_steps = []

    for fi, pt_idx in enumerate(frame_indices):
        trail_x = [p[0] for p in all_points[: pt_idx + 1]]
        trail_y = [p[1] for p in all_points[: pt_idx + 1]]

        s_idx = seg_ids[pt_idx]
        completed = s_idx // 2
        if (s_idx % 2 == 1) and (pt_idx_in_seg[pt_idx] == npps - 1):
            completed += 1
        label = f"RT {completed}/{total_rt}"

        if pt_idx > 0:
            x_cur, y_cur = all_points[pt_idx]
            x_prv, y_prv = all_points[pt_idx - 1]
            arr_x = [x_cur]
            arr_y = [y_cur]
            math_angle = math.degrees(math.atan2(y_cur - y_prv, x_cur - x_prv))
            angle = 90 - math_angle
        else:
            arr_x = [None]
            arr_y = [None]
            angle = 0.0

        frame_data = [
            go.Scatter(x=trail_x, y=trail_y),
            go.Scatter(
                x=arr_x,
                y=arr_y,
                marker=dict(
                    symbol="triangle-up",
                    size=14,
                    color=rgb,
                    angle=angle,
                    standoff=0,
                ),
            ),
        ]

        frames.append(
            go.Frame(
                data=frame_data,
                name=str(fi),
                traces=[trail_idx, arrow_idx],
            )
        )

        slider_steps.append(
            dict(
                args=[
                    [str(fi)],
                    dict(
                        frame=dict(duration=int(1000 / fps), redraw=False),
                        mode="immediate",
                        transition=dict(duration=0),
                    ),
                ],
                label=label,
                method="animate",
            )
        )

    frame_duration = int(1000 / fps)

    max_ray_y = max((abs(p[1]) for p in all_points), default=0.0)

    layout = _figure_layout(
        cavity,
        ray_color,
        _cavity_title(cavity, "Ray Tracing Animation"),
        arc_angle,
        max_ray_y,
    )
    layout.update(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.10,
                xanchor="right",
                y=-0.06,
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=frame_duration, redraw=False),
                                fromcurrent=True,
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
                font=dict(color="#e0e8ff"),
                bgcolor="#1a1e2e",
                bordercolor="#3a4060",
            )
        ],
        sliders=[
            dict(
                active=0,
                steps=slider_steps,
                x=0.13,
                y=-0.04,
                len=0.85,
                xanchor="left",
                yanchor="top",
                currentvalue=dict(
                    prefix="Frame: ",
                    visible=True,
                    font=dict(color="#8090b8", size=11),
                    xanchor="center",
                ),
                transition=dict(duration=0),
                pad=dict(t=10),
                bgcolor="#12141c",
                bordercolor="#2a2e40",
                tickcolor="#3a4060",
                font=dict(color="#6070a0", size=9),
            )
        ],
        margin=dict(l=10, r=10, t=50, b=80),
        height=600,
    )

    fig = go.Figure(data=all_traces, layout=layout, frames=frames)
    return fig


def build_stability_diagram(cp: CavityParameters) -> go.Figure:
    """
    Build a static Plotly figure showing the stability diagram (g1-g2 plane).
    """
    x_q1 = [0, 0, 1 / 3] + list(np.linspace(1 / 3, 3, 300)) + [3, 0]
    y_q1 = [0, 3, 3] + list(1 / np.linspace(1 / 3, 3, 300)) + [0, 0]

    x_q3 = [0, 0, -1 / 3] + list(np.linspace(-1 / 3, -3, 300)) + [-3, 0]
    y_q3 = [0, -3, -3] + list(1 / np.linspace(-1 / 3, -3, 300)) + [0, 0]

    stable_fill = dict(
        type="scatter",
        mode="lines",
        line=dict(width=0),
        fill="toself",
        fillcolor="#0B3036",
        hoverinfo="skip",
        showlegend=False,
    )

    trace_q1 = go.Scatter(x=x_q1, y=y_q1, **stable_fill)
    trace_q3 = go.Scatter(x=x_q3, y=y_q3, **stable_fill)

    hyp_x1 = np.linspace(1 / 3, 3, 300)
    hyp_y1 = 1 / hyp_x1
    hyp_x2 = np.linspace(-3, -1 / 3, 300)
    hyp_y2 = 1 / hyp_x2

    line_style = dict(color="white", width=1.5, dash="dash")
    trace_hyp1 = go.Scatter(
        x=hyp_x1,
        y=hyp_y1,
        mode="lines",
        line=line_style,
        showlegend=False,
        hoverinfo="skip",
    )
    trace_hyp2 = go.Scatter(
        x=hyp_x2,
        y=hyp_y2,
        mode="lines",
        line=line_style,
        showlegend=False,
        hoverinfo="skip",
    )

    trace_xaxis = go.Scatter(
        x=[-3, 3],
        y=[0, 0],
        mode="lines",
        line=dict(color="white", width=1.5),
        showlegend=False,
        hoverinfo="skip",
    )
    trace_yaxis = go.Scatter(
        x=[0, 0],
        y=[-3, 3],
        mode="lines",
        line=dict(color="white", width=1.5),
        showlegend=False,
        hoverinfo="skip",
    )

    legend_label = f"Current Cavity<br>(g₁={cp.g1:.2f}, g₂={cp.g2:.2f}, g₁g₂={cp.stability_product:.2f})"
    trace_point = go.Scatter(
        x=[cp.g1],
        y=[cp.g2],
        mode="markers",
        marker=dict(size=12, color="#00FF00", line=dict(color="white", width=2)),
        name=legend_label,
    )

    annotations = [
        dict(
            x=0.5,
            y=0.7,
            text="STABLE",
            font=dict(color="#00FFCC", size=14, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=-0.5,
            y=-0.7,
            text="STABLE",
            font=dict(color="#00FFCC", size=14, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=-1.5,
            y=2.2,
            text="UNSTABLE",
            font=dict(color="#FF6666", size=14, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=1.5,
            y=-2.2,
            text="UNSTABLE",
            font=dict(color="#FF6666", size=14, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=2.5,
            y=2.5,
            text="UNSTABLE<br>(g₁g₂ > 1)",
            font=dict(color="#FF6666", size=12, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=-2.5,
            y=-2.5,
            text="UNSTABLE<br>(g₁g₂ > 1)",
            font=dict(color="#FF6666", size=12, weight="bold"),
            showarrow=False,
        ),
        dict(
            x=1.1,
            y=1.1,
            text="Planar",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
        ),
        dict(
            x=0.1,
            y=0.1,
            text="Confocal",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
        ),
        dict(
            x=1.1,
            y=0.1,
            text="Hemispherical",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
        ),
        dict(
            x=-0.9,
            y=-1.1,
            text="Concentric",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            xanchor="left",
            yanchor="top",
        ),
        dict(
            x=-2.5,
            y=0.15,
            text="g₁g₂ = 0 (marginal)",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            xanchor="left",
        ),
        dict(
            x=2.2,
            y=0.8,
            text="g₁g₂ = 1 (marginal)",
            font=dict(color="#CCCCCC", size=10),
            showarrow=False,
            textangle=15,
        ),
    ]

    ref_x = [1, 0, 1, -1]
    ref_y = [1, 0, 0, -1]
    trace_refs = go.Scatter(
        x=ref_x,
        y=ref_y,
        mode="markers",
        marker=dict(symbol="cross", size=8, color="white"),
        showlegend=False,
        hoverinfo="skip",
    )

    layout = go.Layout(
        title=dict(
            text="Stability Diagram (g₁ - g₂ Plane)",
            font=dict(color="white", size=18, family="Inter, sans-serif"),
            x=0.5,
            xanchor="center",
        ),
        plot_bgcolor="#040816",
        paper_bgcolor="#040816",
        xaxis=dict(
            title="g₁ = 1 + L/R₁",
            range=[-3, 3],
            color="white",
            gridcolor="#1A1F35",
            zeroline=False,
            constrain="domain",
            showline=True,
            linewidth=1,
            linecolor="grey",
            mirror=True,
        ),
        yaxis=dict(
            title="g₂ = 1 + L/R₂",
            range=[-3, 3],
            color="white",
            gridcolor="#1A1F35",
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            constrain="domain",
            showline=True,
            linewidth=1,
            linecolor="grey",
            mirror=True,
        ),
        annotations=annotations,
        legend=dict(
            x=0.03,
            y=1,
            font=dict(color="white", size=10),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        autosize=False,
        width=600,
        height=600,
    )

    fig = go.Figure(
        data=[
            trace_q1,
            trace_q3,
            trace_hyp1,
            trace_hyp2,
            trace_xaxis,
            trace_yaxis,
            trace_refs,
            trace_point,
        ],
        layout=layout,
    )
    return fig
