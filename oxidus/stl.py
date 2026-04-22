from __future__ import annotations

from typing import Iterable, Tuple


Vec3 = Tuple[float, float, float]
Triangle = Tuple[Vec3, Vec3, Vec3]


def _normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return nx, ny, nz


def _to_ascii_stl(name: str, triangles: Iterable[Triangle]) -> bytes:
    lines = [f"solid {name}"]
    for tri in triangles:
        n = _normal(*tri)
        lines.append(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        lines.append("    outer loop")
        for x, y, z in tri:
            lines.append(f"      vertex {x:.6f} {y:.6f} {z:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines).encode("ascii")


def make_box_stl(name: str, x_mm: float, y_mm: float, z_mm: float) -> bytes:
    """Generate a simple rectangular prism STL in millimeters."""

    p0 = (0.0, 0.0, 0.0)
    p1 = (x_mm, 0.0, 0.0)
    p2 = (x_mm, y_mm, 0.0)
    p3 = (0.0, y_mm, 0.0)
    p4 = (0.0, 0.0, z_mm)
    p5 = (x_mm, 0.0, z_mm)
    p6 = (x_mm, y_mm, z_mm)
    p7 = (0.0, y_mm, z_mm)

    triangles = [
        (p0, p1, p2),
        (p0, p2, p3),
        (p4, p6, p5),
        (p4, p7, p6),
        (p0, p4, p5),
        (p0, p5, p1),
        (p1, p5, p6),
        (p1, p6, p2),
        (p2, p6, p7),
        (p2, p7, p3),
        (p3, p7, p4),
        (p3, p4, p0),
    ]
    return _to_ascii_stl(name=name, triangles=triangles)
