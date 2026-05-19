"""Core reflective echelle grating formulas and parameter container.

All wavelengths in nanometres, angles in degrees, lengths in mm or µm as noted.
Sign convention: grating equation  m λ = d (sin α + sin β).
Quasi-Littrow: α ≈ β ≈ blaze_angle.
"""

import math
from dataclasses import dataclass

__all__ = [
    "EchelleGrating",
    "groove_spacing_nm",
    "littrow_constant_nm",
    "central_wavelength_nm",
    "physical_order_from_wavelength",
    "linear_dispersion_nm_per_px",
    "free_spectral_range_nm",
]


@dataclass
class EchelleGrating:
    """Reflective echelle grating parameters.

    Parameters
    ----------
    grooves_per_mm:
        Ruling density in grooves per mm.
    blaze_deg:
        Blaze angle in degrees.
    """

    grooves_per_mm: float
    blaze_deg: float


def groove_spacing_nm(grooves_per_mm: float) -> float:
    """Return grating groove spacing in nm."""
    return 1.0e6 / grooves_per_mm


def littrow_constant_nm(grooves_per_mm: float, blaze_deg: float) -> float:
    """Return Littrow constant K = 2 d sin(blaze) in nm.

    K = m * λ_center  for any order m in quasi-Littrow geometry.
    """
    d_nm = groove_spacing_nm(grooves_per_mm)
    return 2.0 * d_nm * math.sin(math.radians(blaze_deg))


def central_wavelength_nm(
    order: float, grooves_per_mm: float, blaze_deg: float
) -> float:
    """Return blaze-peak wavelength for *order* in nm."""
    return littrow_constant_nm(grooves_per_mm, blaze_deg) / order


def physical_order_from_wavelength(
    lambda_nm: float, grooves_per_mm: float, blaze_deg: float
) -> float:
    """Return the (fractional) physical order for a given wavelength in nm."""
    return littrow_constant_nm(grooves_per_mm, blaze_deg) / lambda_nm


def linear_dispersion_nm_per_px(
    order: float,
    grooves_per_mm: float,
    beta_deg: float,
    focal_length_mm: float,
    pixel_size_um: float,
) -> float:
    """Return linear dispersion dλ/dpx in nm/px.

    Derived from the grating equation differentiating w.r.t. position on detector::

        dλ/dpx = d cos(β) · pixel_size / (m · f)

    with d in nm, pixel_size in mm, f in mm.  The factor 1e-3 converts
    pixel_size from µm to mm so that the result is in nm/px.
    """
    d_nm = groove_spacing_nm(grooves_per_mm)
    pixel_size_mm = pixel_size_um * 1.0e-3
    return d_nm * math.cos(math.radians(beta_deg)) * pixel_size_mm / (order * focal_length_mm)


def free_spectral_range_nm(lambda_nm: float, order: float) -> float:
    """Return free spectral range FSR ≈ λ / m in nm."""
    return lambda_nm / order
