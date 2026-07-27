"""
export_utils.py — Kaleido PNG export and Kaleido→imageio MP4 export.

Public API
----------
    export_png(fig)                               -> bytes
    export_gif(animated_fig, fps, progress_cb)    -> bytes

"""

from __future__ import annotations

import copy
import io
from typing import Callable, Optional

import imageio
import imageio.v3 as iio
import plotly.graph_objects as go
import plotly.io as pio


def export_png(fig: go.Figure) -> bytes:
    """
    Render a Plotly figure to a PNG byte-string via Kaleido.

    The ``scale=3`` argument is Plotly's analogue of Matplotlib's ``dpi=300``:
    a 3× resolution multiplier that produces a crisp, print-quality image
    regardless of the on-screen render size.

    Parameters
    ----------
    fig : go.Figure
        Any Plotly figure (static or animated — only the ``data``/``layout``
        layers are rendered; frames are ignored).

    Returns
    -------
    bytes
        Raw PNG bytes suitable for ``st.download_button``.
    """
    return fig.to_image(format="png", scale=3)


def export_gif(
    animated_fig: go.Figure,
    fps: int,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> bytes:
    """
    Render every Plotly frame to a PNG via Kaleido, then mux into gif with
    imageio.

    Parameters
    ----------
    animated_fig : go.Figure
        A Plotly figure that has a non-empty ``frames`` list (produced by
        ``plotting.build_animated_figure``).
    fps : int
        Frames per second for the output gif.
    progress_cb : callable or None
        Optional ``progress_cb(current_frame: int, total_frames: int)``
        called after each frame render. Use this to drive ``st.progress`` in
        the Streamlit app without importing Streamlit here.

    Returns
    -------
    bytes
        Raw gif bytes suitable for ``st.download_button``.

    Notes
    -----
    - Each Kaleido render spins up a headless Chromium subprocess; rendering
      many frames is CPU-bound. Show a progress bar in the calling code.
    - The ``scale=2`` argument balances output quality with render time;
      raise to 3 for higher quality at the cost of longer export.
    """
    frames = animated_fig.frames
    if not frames:
        raise ValueError(
            "animated_fig has no frames — call build_animated_figure first"
        )

    total = len(frames)
    images = []

    base_layout = copy.deepcopy(animated_fig.layout)
    base_layout.update(updatemenus=[], sliders=[])

    base_data_json = tuple(trace.to_plotly_json() for trace in animated_fig.data)

    for i, frame in enumerate(frames):
        merged_data = list(copy.deepcopy(base_data_json))

        for j, trace in enumerate(frame.data):
            if trace is not None and j < len(merged_data):
                merged_data[j].update(trace.to_plotly_json())

        frame_fig = go.Figure(data=merged_data, layout=base_layout)
        png_bytes = pio.to_image(frame_fig, format="png", scale=2)
        img_array = iio.imread(io.BytesIO(png_bytes))
        images.append(img_array)

        if progress_cb is not None:
            progress_cb(i + 1, total)

    h, w = images[0].shape[:2]
    if h % 2 != 0:
        images = [img[: h - 1, :, :] for img in images]
    if w % 2 != 0:
        images = [img[:, : w - 1, :] for img in images]

    buf = io.BytesIO()
    buf.name = "animation.gif"
    imageio.mimwrite(
        buf,
        images,
        format="GIF",
        fps=fps,
        loop=0,
    )
    return buf.getvalue()
