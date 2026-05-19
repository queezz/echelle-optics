from ._version import __version__
from .color import wavelength_to_rgb
from .detector import Detector
from .grating import (
    central_wavelength_nm,
    free_spectral_range_nm,
    groove_spacing_nm,
    linear_dispersion_nm_per_px,
    littrow_constant_nm,
    physical_order_from_wavelength,
)
from .spectrometer import EchelleGrating, EchelleSpectrometer, lhd_cmos_echelle
from .synthetic import render_echelle_lines

__all__ = [
    "__version__",
    # grating
    "groove_spacing_nm",
    "littrow_constant_nm",
    "central_wavelength_nm",
    "physical_order_from_wavelength",
    "linear_dispersion_nm_per_px",
    "free_spectral_range_nm",
    # detector
    "Detector",
    # spectrometer
    "EchelleGrating",
    "EchelleSpectrometer",
    "lhd_cmos_echelle",
    # color
    "wavelength_to_rgb",
    # synthetic
    "render_echelle_lines",
]
