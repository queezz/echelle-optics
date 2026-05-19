"""Detector geometry dataclass."""

from dataclasses import dataclass

__all__ = ["Detector"]


@dataclass
class Detector:
    """CCD / sCMOS detector geometry.

    Parameters
    ----------
    width_px:
        Number of pixels along the dispersion axis.
    height_px:
        Number of pixels along the cross-dispersion axis.
    pixel_size_um:
        Physical pixel pitch in micrometres.
    """

    width_px: int
    height_px: int
    pixel_size_um: float

    @property
    def width_mm(self) -> float:
        return self.width_px * self.pixel_size_um * 1.0e-3

    @property
    def height_mm(self) -> float:
        return self.height_px * self.pixel_size_um * 1.0e-3
