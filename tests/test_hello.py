"""Basic sanity tests for echelle_optics."""

import math
import numpy as np
import pytest

from echelle_optics import (
    groove_spacing_nm,
    littrow_constant_nm,
    central_wavelength_nm,
    physical_order_from_wavelength,
    linear_dispersion_nm_per_px,
    free_spectral_range_nm,
    Detector,
    EchelleGrating,
    EchelleSpectrometer,
    lhd_cmos_echelle,
    wavelength_to_rgb,
    render_echelle_lines,
)

# ---------------------------------------------------------------------------
# grating formulas
# ---------------------------------------------------------------------------

LHD_GROOVES = 46.1
LHD_BLAZE = 32.0
LHD_F = 304.8
LHD_PX = 6.5


def test_groove_spacing():
    d = groove_spacing_nm(LHD_GROOVES)
    assert abs(d - 1e6 / LHD_GROOVES) < 1.0


def test_littrow_constant():
    K = littrow_constant_nm(LHD_GROOVES, LHD_BLAZE)
    d = groove_spacing_nm(LHD_GROOVES)
    assert abs(K - 2 * d * math.sin(math.radians(LHD_BLAZE))) < 0.1


def test_central_wavelength_roundtrip():
    for m in range(30, 59):
        lam = central_wavelength_nm(m, LHD_GROOVES, LHD_BLAZE)
        m_back = physical_order_from_wavelength(lam, LHD_GROOVES, LHD_BLAZE)
        assert abs(m_back - m) < 1e-9


def test_dispersion_lhd_approx():
    """dλ/dpx ≈ 0.392 / m  nm/px for the LHD CMOS echelle."""
    for m in [30, 40, 50, 58]:
        disp = linear_dispersion_nm_per_px(m, LHD_GROOVES, LHD_BLAZE, LHD_F, LHD_PX)
        expected = 0.392 / m
        assert abs(disp - expected) / expected < 0.01, f"order {m}: {disp:.5f} vs {expected:.5f}"


def test_dispersion_scales_with_pixel_size():
    """Dispersion is proportional to pixel size: 13 µm gives ~2× the 6.5 µm value.

    This is a numerical scaling check only.  The 13 µm case does not correspond
    to the LHD CMOS instrument and is not a supported configuration.
    """
    m = 40
    disp_cmos = linear_dispersion_nm_per_px(m, LHD_GROOVES, LHD_BLAZE, LHD_F, pixel_size_um=6.5)
    disp_ccd = linear_dispersion_nm_per_px(m, LHD_GROOVES, LHD_BLAZE, LHD_F, pixel_size_um=13.0)
    ratio = disp_ccd / disp_cmos
    assert abs(ratio - 2.0) < 1e-9


def test_free_spectral_range():
    lam = 500.0
    m = 40
    fsr = free_spectral_range_nm(lam, m)
    assert abs(fsr - lam / m) < 1e-12


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def test_detector_properties():
    det = Detector(width_px=2560, height_px=2160, pixel_size_um=6.5)
    assert abs(det.width_mm - 2560 * 6.5e-3) < 1e-9
    assert abs(det.height_mm - 2160 * 6.5e-3) < 1e-9


# ---------------------------------------------------------------------------
# EchelleSpectrometer / order_table
# ---------------------------------------------------------------------------

def test_lhd_order_table():
    spec = lhd_cmos_echelle()
    df = spec.order_table(30, 58)
    assert len(df) == 29
    assert list(df.columns) == [
        "order",
        "center_wavelength_nm",
        "free_spectral_range_nm",
        "dispersion_nm_per_px",
        "detector_span_nm",
        "wavelength_min_nm",
        "wavelength_max_nm",
    ]
    # wavelength_min/max bracket center
    assert (df["wavelength_min_nm"] < df["center_wavelength_nm"]).all()
    assert (df["wavelength_max_nm"] > df["center_wavelength_nm"]).all()


def test_beta_defaults_to_blaze():
    spec = lhd_cmos_echelle()
    assert spec.beta_deg == spec.grating.blaze_deg


# ---------------------------------------------------------------------------
# color
# ---------------------------------------------------------------------------

def test_wavelength_to_rgb_range():
    for lam in [400, 500, 550, 600, 700]:
        r, g, b = wavelength_to_rgb(lam)
        assert 0.0 <= r <= 1.0
        assert 0.0 <= g <= 1.0
        assert 0.0 <= b <= 1.0


def test_wavelength_to_rgb_out_of_range():
    assert wavelength_to_rgb(200.0) == (0.0, 0.0, 0.0)
    assert wavelength_to_rgb(1000.0) == (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# synthetic renderer
# ---------------------------------------------------------------------------

def test_render_shape_default():
    spec = lhd_cmos_echelle()
    lines = [(500.0, 1.0), (600.0, 0.5)]
    img = render_echelle_lines(lines, spec, orders=[40, 44])
    assert img.shape == (spec.detector.height_px, spec.detector.width_px)


def test_render_shape_custom():
    spec = lhd_cmos_echelle()
    lines = [(500.0, 1.0)]
    img = render_echelle_lines(lines, spec, orders=[40], shape=(256, 512))
    assert img.shape == (256, 512)


def test_render_color():
    spec = lhd_cmos_echelle()
    lines = [(550.0, 1.0)]
    img = render_echelle_lines(lines, spec, orders=[40], shape=(128, 256), color=True)
    assert img.shape == (128, 256, 3)


def test_render_signal_present():
    """A line placed at the center of the detector should produce nonzero signal."""
    spec = lhd_cmos_echelle()
    m = 40
    lam_c = central_wavelength_nm(m, spec.grating.grooves_per_mm, spec.grating.blaze_deg)
    lines = [(lam_c, 100.0)]
    img = render_echelle_lines(
        lines, spec, orders=[m], shape=(64, 64),
        x_center=32.0, y_center=32.0, reference_order=m,
    )
    assert img.max() > 1.0


def test_render_reproducible_noise():
    spec = lhd_cmos_echelle()
    lines = [(500.0, 1.0)]
    kw = dict(orders=[40], shape=(32, 32), read_noise=5.0, seed=42)
    a = render_echelle_lines(lines, spec, **kw)
    b = render_echelle_lines(lines, spec, **kw)
    np.testing.assert_array_equal(a, b)
