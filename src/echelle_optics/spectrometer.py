"""Echelle spectrometer model and order-table generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from .detector import Detector
from .grating import (
    EchelleGrating,
    central_wavelength_nm,
    free_spectral_range_nm,
    linear_dispersion_nm_per_px,
)

__all__ = ["EchelleGrating", "EchelleSpectrometer", "lhd_cmos_echelle"]


@dataclass
class EchelleSpectrometer:
    """Echelle spectrometer optical layout.

    Parameters
    ----------
    grating:
        Echelle grating parameters.
    detector:
        Detector geometry.
    focal_length_mm:
        Camera (and collimator) focal length in mm.
    beta_deg:
        Camera angle β in degrees.  Defaults to blaze angle (quasi-Littrow).
    """

    grating: EchelleGrating
    detector: Detector
    focal_length_mm: float
    beta_deg: Optional[float] = field(default=None)

    def __post_init__(self) -> None:
        if self.beta_deg is None:
            self.beta_deg = self.grating.blaze_deg

    # ------------------------------------------------------------------
    def order_table(self, order_min: int, order_max: int) -> pd.DataFrame:
        """Return a DataFrame with per-order dispersion and wavelength data.

        Parameters
        ----------
        order_min, order_max:
            Inclusive range of diffraction orders to tabulate.

        Returns
        -------
        DataFrame with columns:
            order, center_wavelength_nm, free_spectral_range_nm,
            dispersion_nm_per_px, detector_span_nm,
            wavelength_min_nm, wavelength_max_nm
        """
        rows = []
        for m in range(order_min, order_max + 1):
            lam_c = central_wavelength_nm(m, self.grating.grooves_per_mm, self.grating.blaze_deg)
            fsr = free_spectral_range_nm(lam_c, m)
            disp = linear_dispersion_nm_per_px(
                m,
                self.grating.grooves_per_mm,
                self.beta_deg,  # type: ignore[arg-type]
                self.focal_length_mm,
                self.detector.pixel_size_um,
            )
            span = disp * self.detector.width_px
            rows.append(
                {
                    "order": m,
                    "center_wavelength_nm": lam_c,
                    "free_spectral_range_nm": fsr,
                    "dispersion_nm_per_px": disp,
                    "detector_span_nm": span,
                    "wavelength_min_nm": lam_c - span / 2.0,
                    "wavelength_max_nm": lam_c + span / 2.0,
                }
            )
        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Convenience constructor
# ---------------------------------------------------------------------------

def lhd_cmos_echelle() -> EchelleSpectrometer:
    """Return the primary built-in instrument: the LHD CMOS echelle spectrometer.

    This is the main reference instrument for the package.  Use it as the
    starting point for order-table generation and synthetic detector images.

    Hardware configuration:

    - Grating: Newport echelle, 46.1 gr/mm, blaze angle 32°, quasi-Littrow
    - Camera/collimator: f = 304.8 mm
    - Detector: Andor Zyla 4.2 sCMOS, 2560 × 2160 px, 6.5 µm pixel pitch
    - Useful orders: ~30–58 (wavelength range ~370–720 nm)
    - Dispersion: ≈ 0.392 / m  nm/px
    """
    grating = EchelleGrating(grooves_per_mm=46.1, blaze_deg=32.0)
    detector = Detector(width_px=2560, height_px=2160, pixel_size_um=6.5)
    return EchelleSpectrometer(grating=grating, detector=detector, focal_length_mm=304.8)
