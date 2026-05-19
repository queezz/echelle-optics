"""Tests for the empirical detector geometry module."""

import numpy as np
import pytest

from echelle_optics import (
    DetectorGeometry,
    GeometryMode,
    OrderTrace,
    load_lhd_cmos_geometry,
    load_lhd_cmos_pattern,
    fit_order_traces,
    lhd_cmos_echelle,
    render_white_light,
    render_echelle_lines,
    central_wavelength_nm,
)


# ---------------------------------------------------------------------------
# Pattern file loading
# ---------------------------------------------------------------------------


class TestPatternLoading:
    def test_load_returns_correct_shapes(self):
        x, traces = load_lhd_cmos_pattern()
        assert x.shape == (2560,)
        assert traces.shape == (2560, 29)

    def test_x_pixels_are_sequential(self):
        x, _ = load_lhd_cmos_pattern()
        np.testing.assert_array_equal(x, np.arange(2560, dtype=np.float64))

    def test_y_values_are_positive(self):
        _, traces = load_lhd_cmos_pattern()
        assert traces.min() > 0

    def test_y_values_within_detector_bounds(self):
        """Values should be near detector height (2160); a few pixels
        overshoot is acceptable due to integer rounding in the original
        pattern generation."""
        _, traces = load_lhd_cmos_pattern()
        assert traces.max() <= 2165

    def test_orders_are_monotonically_increasing_in_y(self):
        """Higher-numbered orders (later columns) should have lower y (or
        be interleaved).  For CMOS LHD, column 0 is order 30 (lowest y)
        and column 28 is order 58 (highest y)."""
        _, traces = load_lhd_cmos_pattern()
        # Check at detector center
        center_y = traces[1280, :]
        assert np.all(np.diff(center_y) > 0), "Order centers should increase with column"


# ---------------------------------------------------------------------------
# Trace fitting
# ---------------------------------------------------------------------------


class TestTraceFitting:
    @pytest.fixture
    def geometry(self):
        return load_lhd_cmos_geometry()

    def test_fitted_geometry_has_29_traces(self, geometry):
        assert geometry.n_orders == 29
        assert len(geometry.traces) == 29

    def test_order_range(self, geometry):
        assert geometry.order_min == 30
        assert geometry.order_max == 58

    def test_trace_order_numbers(self, geometry):
        orders = geometry.order_numbers()
        assert orders == list(range(30, 59))

    def test_quadratic_fit_residuals_small(self, geometry):
        """Quadratic fit should give sub-pixel residuals for most points."""
        for trace in geometry.traces:
            rms = np.sqrt(np.mean(trace.residuals**2))
            assert rms < 1.0, (
                f"Order {trace.order}: RMS residual {rms:.3f} px exceeds 1.0 px"
            )

    def test_polynomial_degree(self, geometry):
        for trace in geometry.traces:
            assert trace.poly_degree == 2
            assert len(trace.coefficients) == 3  # c0, c1, c2

    def test_cubic_fit_reduces_residuals(self):
        geom_quad = load_lhd_cmos_geometry(poly_degree=2)
        geom_cubic = load_lhd_cmos_geometry(poly_degree=3)
        for t2, t3 in zip(geom_quad.traces, geom_cubic.traces):
            rms2 = np.sqrt(np.mean(t2.residuals**2))
            rms3 = np.sqrt(np.mean(t3.residuals**2))
            assert rms3 <= rms2 + 1e-6

    def test_y_at_matches_raw_at_center(self, geometry):
        """Fitted trace should be close to raw data at detector center."""
        for trace in geometry.traces:
            x_mid = 1280.0
            y_fitted = trace.y_at(x_mid)
            y_raw_mid = trace.y_raw[1280]
            assert abs(y_fitted - y_raw_mid) < 2.0

    def test_trace_for_order_lookup(self, geometry):
        trace = geometry.trace_for_order(44)
        assert trace.order == 44

    def test_trace_for_order_invalid_raises(self, geometry):
        with pytest.raises(ValueError):
            geometry.trace_for_order(20)
        with pytest.raises(ValueError):
            geometry.trace_for_order(70)


# ---------------------------------------------------------------------------
# Curved rendering
# ---------------------------------------------------------------------------


class TestCurvedRendering:
    def test_white_light_curved_orders_not_constant_y(self):
        """With measured geometry, rendered order centers should vary with x."""
        spec = lhd_cmos_echelle()
        orders = [40, 44, 50]
        h, w = 512, 512
        img = render_white_light(
            spec, orders, shape=(h, w),
            geometry=GeometryMode.MEASURED_LHD_CMOS, color=False,
        )
        # Find the row with max signal for each column
        peak_rows = np.argmax(img, axis=0)
        # For curved geometry, peak row should vary across columns
        assert peak_rows.max() - peak_rows.min() > 0

    def test_ideal_mode_gives_constant_y(self):
        """With ideal geometry, order centers should be constant across x."""
        spec = lhd_cmos_echelle()
        img = render_white_light(
            spec, orders=[44], shape=(128, 256),
            x_center=128.0, y_center=64.0, reference_order=44,
            geometry=GeometryMode.IDEAL_STRAIGHT, color=False,
        )
        peak_rows = np.argmax(img, axis=0)
        # Should be constant (all same row)
        nonzero_cols = img.max(axis=0) > 0.01
        peak_at_signal = peak_rows[nonzero_cols]
        assert peak_at_signal.max() - peak_at_signal.min() <= 1

    def test_none_geometry_is_same_as_ideal(self):
        """geometry=None should behave identically to IDEAL_STRAIGHT."""
        spec = lhd_cmos_echelle()
        kw = dict(
            orders=[44], shape=(128, 256),
            x_center=128.0, y_center=64.0, reference_order=44,
            color=False,
        )
        img_none = render_white_light(spec, geometry=None, **kw)
        img_ideal = render_white_light(spec, geometry=GeometryMode.IDEAL_STRAIGHT, **kw)
        np.testing.assert_array_equal(img_none, img_ideal)

    def test_render_lines_with_measured_geometry(self):
        """render_echelle_lines should work with measured geometry."""
        spec = lhd_cmos_echelle()
        m = 44
        lam_c = central_wavelength_nm(m, spec.grating.grooves_per_mm, spec.grating.blaze_deg)
        lines = [(lam_c, 100.0)]
        img = render_echelle_lines(
            lines, spec, orders=[m], shape=(2160, 2560),
            geometry=GeometryMode.MEASURED_LHD_CMOS,
        )
        assert img.max() > 1.0
        assert img.shape == (2160, 2560)

    def test_geometry_mode_enum_values(self):
        assert GeometryMode.IDEAL_STRAIGHT.value == "ideal_straight"
        assert GeometryMode.MEASURED_LHD_CMOS.value == "measured_lhd_cmos"
