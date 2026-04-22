from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrinterSpec:
    """User-selected build envelope in millimeters."""

    x_mm: int
    y_mm: int
    z_mm: int

    @property
    def max_axis(self) -> int:
        return max(self.x_mm, self.y_mm, self.z_mm)

    @property
    def volume_liters(self) -> float:
        return (self.x_mm * self.y_mm * self.z_mm) / 1_000_000
