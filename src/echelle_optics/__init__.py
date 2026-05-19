from ._version import __version__
from .color import wavelength_to_rgb
from .detector import Detector
from .geometry import (
    DetectorGeometry,
    GeometryMode,
    OrderTrace,
    fit_order_traces,
    load_lhd_cmos_geometry,
    load_lhd_cmos_pattern,
)
from .grating import (
    central_wavelength_nm,
    free_spectral_range_nm,
    groove_spacing_nm,
    linear_dispersion_nm_per_px,
    littrow_constant_nm,
    physical_order_from_wavelength,
)
from .spectrometer import EchelleGrating, EchelleSpectrometer, lhd_cmos_echelle
from .synthetic import render_echelle_lines, render_white_light

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
    # geometry
    "GeometryMode",
    "OrderTrace",
    "DetectorGeometry",
    "load_lhd_cmos_pattern",
    "fit_order_traces",
    "load_lhd_cmos_geometry",
    # spectrometer
    "EchelleGrating",
    "EchelleSpectrometer",
    "lhd_cmos_echelle",
    # color
    "wavelength_to_rgb",
    # synthetic
    "render_echelle_lines",
    "render_white_light",
]
