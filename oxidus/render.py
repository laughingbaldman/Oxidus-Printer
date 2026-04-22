from __future__ import annotations

from typing import Any

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    go = None

from .models import PrinterSpec


def _cuboid_mesh(origin: tuple[float, float, float], size: tuple[float, float, float]):
    x0, y0, z0 = origin
    dx, dy, dz = size
    verts = [
        (x0, y0, z0),
        (x0 + dx, y0, z0),
        (x0 + dx, y0 + dy, z0),
        (x0, y0 + dy, z0),
        (x0, y0, z0 + dz),
        (x0 + dx, y0, z0 + dz),
        (x0 + dx, y0 + dy, z0 + dz),
        (x0, y0 + dy, z0 + dz),
    ]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 6, 7, 4, 5, 5, 6, 6, 7, 7, 4]
    k = [2, 3, 5, 6, 5, 1, 6, 2, 7, 3, 4, 0]
    return verts, i, j, k


def _add_cuboid(
    fig: Any,
    origin: tuple[float, float, float],
    size: tuple[float, float, float],
    color: str,
    opacity: float,
    name: str,
):
    verts, i, j, k = _cuboid_mesh(origin, size)
    xs, ys, zs = zip(*verts)
    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=i,
            j=j,
            k=k,
            color=color,
            opacity=opacity,
            name=name,
            flatshading=True,
            hovertemplate=f"{name}<extra></extra>",
        )
    )


def build_printer_figure(spec: PrinterSpec) -> Any:
    if go is None:
        return None

    margin = 70
    frame_x = spec.x_mm + margin * 2
    frame_y = spec.y_mm + margin * 2
    frame_z = spec.z_mm + 180

    fig = go.Figure()

    _add_cuboid(
        fig,
        origin=(margin, margin, 20),
        size=(spec.x_mm, spec.y_mm, spec.z_mm),
        color="#08A4BD",
        opacity=0.22,
        name="Build Volume",
    )

    # Four vertical posts
    post_w = 20
    for ox, oy in [
        (0, 0),
        (frame_x - post_w, 0),
        (0, frame_y - post_w),
        (frame_x - post_w, frame_y - post_w),
    ]:
        _add_cuboid(
            fig,
            origin=(ox, oy, 0),
            size=(post_w, post_w, frame_z),
            color="#1F2937",
            opacity=0.65,
            name="Frame",
        )

    # Top ring
    _add_cuboid(fig, (0, 0, frame_z - 20), (frame_x, 20, 20), "#111827", 0.7, "Top Rail")
    _add_cuboid(fig, (0, frame_y - 20, frame_z - 20), (frame_x, 20, 20), "#111827", 0.7, "Top Rail")
    _add_cuboid(fig, (0, 20, frame_z - 20), (20, frame_y - 40, 20), "#111827", 0.7, "Top Rail")
    _add_cuboid(fig, (frame_x - 20, 20, frame_z - 20), (20, frame_y - 40, 20), "#111827", 0.7, "Top Rail")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            xaxis=dict(backgroundcolor="rgba(18,18,18,0.02)"),
            yaxis=dict(backgroundcolor="rgba(18,18,18,0.02)"),
            zaxis=dict(backgroundcolor="rgba(18,18,18,0.02)"),
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.5, z=0.9)),
        ),
        showlegend=False,
    )
    return fig
