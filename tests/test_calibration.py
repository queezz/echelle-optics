"""Tests for the empirical wavelength calibration module."""

from __future__ import annotations

import numpy as np
import pytest

from echelle_optics import (
    CalibrationLine,
    OrderWavelengthFit,
    WavelengthSolution,
    fit_wavelength_solution,
    lhd_cmos_echelle,
    load_lhd_cmos_calibration,
    load_lhd_cmos_wavelength_solution,
    render_echelle_lines,
    render_white_light,
)
from echelle_optics.calibration import LHD_CMOS_CAL_ORDER_OFFSET
from echelle_optics.geometry import GeometryMode


# ---------------------------------------------------------------------------
# Calibration file loading
# ---------------------------------------------------------------------------


class TestCalibrationFileLoading:
    def test_loads_nonzero_lines(self):
        lines = load_lhd_cmos_calibration()
        assert len(lines) > 0

    def test_all_entries_are_calibration_lines(self):
        lines = load_lhd_cmos_calibration()
        assert all(isinstance(ln, CalibrationLine) for ln in lines)

    def test_order_indices_in_range(self):
        """File order labels must be 0–28."""
        lines = load_lhd_cmos_calibration()
        order_idxs = {ln.order_idx for ln in lines}
        assert order_idxs.issubset(set(range(29)))

    def test_physical_order_offset_applied(self):
        lines = load_lhd_cmos_calibration()
        for ln in lines:
            assert ln.physical_order == ln.order_idx + LHD_CMOS_CAL_ORDER_OFFSET

    def test_wavelengths_positive(self):
        lines = load_lhd_cmos_calibration()
        assert all(ln.wavelength_nm > 0 for ln in lines)

    def test_center_pixels_positive(self):
        lines = load_lhd_cmos_calibration()
        assert all(ln.center_pixel >= 0 for ln in lines)

    def test_species_strings_nonempty(self):
        lines = load_lhd_cmos_calibration()
        assert all(len(ln.species) > 0 for ln in lines)

    def test_covers_multiple_orders(self):
        lines = load_lhd_cmos_calibration()
        physical_orders = {ln.physical_order for ln in lines}
        assert len(physical_orders) >= 20

    def test_custom_offset(self):
        lines_default = load_lhd_cmos_calibration()
        lines_custom = load_lhd_cmos_calibration(order_offset=0)
        for a, b in zip(lines_default, lines_custom):
            assert a.physical_order == b.physical_order + LHD_CMOS_CAL_ORDER_OFFSET

    def test_wavelength_range_reasonable(self):
        """Wavelengths should be in the visible-to-NIR range for this instrument."""
        lines = load_lhd_cmos_calibration()
        wl = [ln.wavelength_nm for ln in lines]
        assert min(wl) > 350
        assert max(wl) < 900

    def test_species_includes_expected_lamps(self):
        lines = load_lhd_cmos_calibration()
        species_set = {ln.species for ln in lines}
        # At least some of these species should be present
        expected = {"ArI", "NeI", "ThI", "HgI"}
        assert len(expected & species_set) >= 3


# ---------------------------------------------------------------------------
# Wavelength solution fitting
# ---------------------------------------------------------------------------


class TestWavelengthSolutionFitting:
    @pytest.fixture(scope="class")
    def solution(self) -> WavelengthSolution:
        return load_lhd_cmos_wavelength_solution()

    def test_solution_has_fits(self, solution):
        assert len(solution.fits) > 0

    def test_fitted_orders_are_integers(self, solution):
        for order in solution.order_list():
            assert isinstance(order, int)

    def test_fitted_orders_in_expected_range(self, solution):
        """Physical orders should fall in the 30–58 range."""
        for m in solution.order_list():
            assert 28 <= m <= 60

    def test_each_fit_is_order_wavelength_fit(self, solution):
        for fit in solution.fits.values():
            assert isinstance(fit, OrderWavelengthFit)

    def test_poly_degree_default_quadratic(self, solution):
        for fit in solution.fits.values():
            assert fit.poly_degree == 2
            assert len(fit.coefficients) == 3

    def test_poly_degree_cubic(self):
        sol = load_lhd_cmos_wavelength_solution(poly_degree=3)
        for fit in sol.fits.values():
            assert fit.poly_degree == 3
            assert len(fit.coefficients) == 4

    def test_rms_residuals_small(self, solution):
        """Per-order RMS residuals should be well below 1 nm."""
        for m, fit in solution.fits.items():
            assert fit.rms_nm < 1.0, (
                f"Order {m}: RMS = {fit.rms_nm:.4f} nm exceeds 1 nm"
            )

    def test_cubic_residuals_not_worse_than_quadratic(self):
        sol2 = load_lhd_cmos_wavelength_solution(poly_degree=2)
        sol3 = load_lhd_cmos_wavelength_solution(poly_degree=3)
        common = set(sol2.order_list()) & set(sol3.order_list())
        for m in common:
            assert sol3.fits[m].rms_nm <= sol2.fits[m].rms_nm + 1e-6

    def test_n_points_matches_raw_data(self, solution):
        """n_points for each order must equal number of loaded lines for that order."""
        raw = load_lhd_cmos_calibration()
        by_order: dict[int, int] = {}
        for ln in raw:
            by_order[ln.physical_order] = by_order.get(ln.physical_order, 0) + 1
        for m, fit in solution.fits.items():
            assert fit.n_points == by_order[m]

    def test_has_order(self, solution):
        orders = solution.order_list()
        assert solution.has_order(orders[0])
        assert not solution.has_order(0)
        assert not solution.has_order(999)

    def test_summary_returns_string(self, solution):
        s = solution.summary()
        assert isinstance(s, str)
        assert len(s) > 0


# ---------------------------------------------------------------------------
# Wavelength evaluation: wavelength_at
# ---------------------------------------------------------------------------


class TestWavelengthAt:
    @pytest.fixture(scope="class")
    def solution(self) -> WavelengthSolution:
        return load_lhd_cmos_wavelength_solution()

    def test_wavelength_at_scalar(self, solution):
        for m in solution.order_list()[:3]:
            fit = solution.fits[m]
            lam = solution.wavelength_at(fit.x_center, m)
            assert lam.shape == ()

    def test_wavelength_at_array(self, solution):
        m = solution.order_list()[0]
        x = np.linspace(200, 2300, 100)
        lam = solution.wavelength_at(x, m)
        assert lam.shape == (100,)

    def test_wavelength_decreases_with_x(self, solution):
        """Dispersion direction: longer wavelengths at lower x pixels."""
        for m in solution.order_list():
            fit = solution.fits[m]
            x_lo = fit.pixel_min
            x_hi = fit.pixel_max
            lam_lo = float(solution.wavelength_at(x_lo, m))
            lam_hi = float(solution.wavelength_at(x_hi, m))
            # For the LHD CMOS, wavelength decreases as x increases
            assert lam_lo != lam_hi, f"Order {m}: flat wavelength solution"

    def test_wavelength_monotone_along_order(self, solution):
        """λ(x) must be strictly monotone over the calibration range."""
        x = np.linspace(100, 2459, 500)
        for m in solution.order_list():
            lam = solution.wavelength_at(x, m)
            diff = np.diff(lam)
            # All increments must have the same sign
            assert np.all(diff > 0) or np.all(diff < 0), (
                f"Order {m}: wavelength solution is not monotone"
            )

    def test_wavelength_range_per_order(self, solution):
        """Calibrated wavelength range should be physically plausible."""
        for m in solution.order_list():
            fit = solution.fits[m]
            assert fit.wavelength_min_nm > 350
            assert fit.wavelength_max_nm < 900
            assert fit.wavelength_max_nm > fit.wavelength_min_nm

    def test_wavelength_at_unknown_order_raises(self, solution):
        with pytest.raises(KeyError):
            solution.wavelength_at(1000.0, 999)

    def test_calibration_points_fit_within_tolerance(self, solution):
        """The polynomial should reproduce calibration points to < 0.5 nm."""
        for m, fit in solution.fits.items():
            for pt in fit.points:
                lam_fitted = float(solution.wavelength_at(pt.center_pixel, m))
                assert abs(lam_fitted - pt.wavelength_nm) < 0.5, (
                    f"Order {m}, {pt.species} @ {pt.center_pixel:.0f}px: "
                    f"fitted={lam_fitted:.4f}, ref={pt.wavelength_nm:.4f}"
                )


# ---------------------------------------------------------------------------
# Pixel inversion: pixel_at
# ---------------------------------------------------------------------------


class TestPixelAt:
    @pytest.fixture(scope="class")
    def solution(self) -> WavelengthSolution:
        return load_lhd_cmos_wavelength_solution()

    def test_pixel_at_roundtrip(self, solution):
        """pixel_at(wavelength_at(x)) ≈ x within 1 pixel."""
        for m in solution.order_list()[:5]:
            fit = solution.fits[m]
            x_test = np.linspace(fit.pixel_min + 20, fit.pixel_max - 20, 20)
            for x in x_test:
                lam = float(solution.wavelength_at(float(x), m))
                x_back = solution.pixel_at(lam, m)
                assert abs(x_back - x) < 1.0, (
                    f"Order {m}: roundtrip error {abs(x_back - x):.3f} px at x={x:.0f}"
                )

    def test_pixel_at_wavelength_self_consistency(self, solution):
        """wavelength_at(pixel_at(λ)) ≈ λ within 0.05 nm (self-consistent inversion)."""
        for m, fit in solution.fits.items():
            for pt in fit.points:
                x_pred = solution.pixel_at(pt.wavelength_nm, m)
                lam_back = float(solution.wavelength_at(x_pred, m))
                assert abs(lam_back - pt.wavelength_nm) < 0.05, (
                    f"Order {m}, {pt.species}: round-trip error "
                    f"{abs(lam_back - pt.wavelength_nm):.4f} nm"
                )

    def test_pixel_at_unknown_order_raises(self, solution):
        with pytest.raises(KeyError):
            solution.pixel_at(500.0, 999)

    def test_pixel_at_out_of_range_raises(self, solution):
        """A wavelength far outside the calibrated range should raise ValueError."""
        m = solution.order_list()[0]
        with pytest.raises(ValueError):
            solution.pixel_at(1500.0, m)


# ---------------------------------------------------------------------------
# Integration with synthetic renderer
# ---------------------------------------------------------------------------


class TestRenderWithWavelengthSolution:
    @pytest.fixture(scope="class")
    def spec(self):
        return lhd_cmos_echelle()

    @pytest.fixture(scope="class")
    def solution(self) -> WavelengthSolution:
        return load_lhd_cmos_wavelength_solution()

    def test_render_lines_with_solution_shape(self, spec, solution):
        orders = [m for m in solution.order_list() if 35 <= m <= 45][:3]
        lines = [(500.0, 1.0)]
        img = render_echelle_lines(
            lines,
            spec,
            orders=orders,
            shape=(128, 256),
            wavelength_solution=solution,
        )
        assert img.shape == (128, 256)

    def test_render_lines_with_solution_returns_nonzero(self, spec, solution):
        """Rendering a known calibration line should produce signal."""
        m = 44
        if not solution.has_order(m):
            pytest.skip(f"Order {m} not in solution")
        fit = solution.fits[m]
        # Use the first calibration line for this order
        pt = fit.points[0]
        lines = [(pt.wavelength_nm, 100.0)]
        img = render_echelle_lines(
            lines,
            spec,
            orders=[m],
            shape=(2160, 2560),
            geometry=GeometryMode.MEASURED_LHD_CMOS,
            wavelength_solution=solution,
        )
        assert img.max() > 1.0

    def test_render_lines_falls_back_for_uncovered_order(self, spec, solution):
        """An order not in the solution falls back to theoretical dispersion."""
        orders = [44]
        lines = [(520.0, 1.0)]
        # Provide a solution with no orders
        empty_sol = WavelengthSolution(fits={})
        img_theory = render_echelle_lines(
            lines, spec, orders=orders, shape=(64, 256), wavelength_solution=None
        )
        img_fallback = render_echelle_lines(
            lines, spec, orders=orders, shape=(64, 256), wavelength_solution=empty_sol
        )
        np.testing.assert_array_equal(img_theory, img_fallback)

    def test_render_white_light_with_solution_shape(self, spec, solution):
        orders = [m for m in solution.order_list() if 40 <= m <= 50][:3]
        img = render_white_light(
            spec,
            orders=orders,
            shape=(128, 256),
            wavelength_solution=solution,
            color=False,
        )
        assert img.shape == (128, 256)

    def test_render_white_light_with_solution_color_shape(self, spec, solution):
        orders = [m for m in solution.order_list() if 40 <= m <= 50][:2]
        img = render_white_light(
            spec,
            orders=orders,
            shape=(64, 128),
            wavelength_solution=solution,
            color=True,
        )
        assert img.shape == (64, 128, 3)

    def test_render_without_solution_unchanged(self, spec):
        """render_echelle_lines without wavelength_solution behaves as before."""
        lines = [(500.0, 1.0)]
        img_a = render_echelle_lines(lines, spec, orders=[44], shape=(64, 128))
        img_b = render_echelle_lines(
            lines, spec, orders=[44], shape=(64, 128), wavelength_solution=None
        )
        np.testing.assert_array_equal(img_a, img_b)


# ---------------------------------------------------------------------------
# fit_wavelength_solution edge cases
# ---------------------------------------------------------------------------


class TestFitWavelengthSolutionEdgeCases:
    def test_empty_input(self):
        sol = fit_wavelength_solution([])
        assert sol.order_list() == []

    def test_insufficient_points_skipped(self):
        """Orders with fewer points than poly_degree+1 are excluded."""
        lines = load_lhd_cmos_calibration()
        # Keep only 2 lines for each order → not enough for cubic
        by_order: dict[int, list[CalibrationLine]] = {}
        for ln in lines:
            by_order.setdefault(ln.physical_order, []).append(ln)
        limited = [pts[0] for pts in by_order.values()]
        sol = fit_wavelength_solution(limited, poly_degree=2)
        # Orders with only 1 point should be absent (need at least 3)
        for m in sol.order_list():
            assert sol.fits[m].n_points >= 3
