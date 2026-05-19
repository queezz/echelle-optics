"""Empirical wavelength calibration from measured calibration lamp spectra.

This module provides per-order polynomial wavelength solutions λ(x) fitted
from real calibration lamp line positions measured on the LHD CMOS echelle
detector.  Lines were identified for Ar I/II, Ne I, Th I, Hg I/II, and H₂
calibration lamps.

Architecture
------------
Separation of concerns is maintained::

    calibration.py  ←  empirical λ(x) per order
    grating.py      ←  theoretical dispersion physics
    geometry.py     ←  detector y-trace geometry
    synthetic.py    ←  rendering (can use any of the above)

Order numbering
---------------
The calibration file uses 0-indexed order labels (0–28) that correspond to
physical diffraction orders 30–58 via::

    physical_order = label + order_offset   (default offset = 30)

Calibration file format
-----------------------
Plain text, tab-separated, one line per calibration measurement::

    order_idx   from_px   to_px   center_px   wavelength_nm   species

Lines beginning with ``#`` are comments.  Inline comments after ``#`` within
a data line are stripped before parsing.

Data source
-----------
Bundled file ``data/Th_wavelength_CMOS_20240305.txt`` (LHD CMOS, 2024-03-05).
Lamps used: ThAr, Ne, Hg, H₂.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
from scipy.optimize import brentq

__all__ = [
    "CalibrationLine",
    "OrderWavelengthFit",
    "WavelengthSolution",
    "load_lhd_cmos_calibration",
    "fit_wavelength_solution",
    "load_lhd_cmos_wavelength_solution",
]

DATA_DIR = Path(__file__).parent / "data"
LHD_CMOS_CALIBRATION = DATA_DIR / "Th_wavelength_CMOS_20240305.txt"

# Physical order = file label + offset  (0-indexed labels 0–28 → orders 30–58)
LHD_CMOS_CAL_ORDER_OFFSET = 30


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CalibrationLine:
    """A single pixel ↔ wavelength calibration measurement.

    Attributes
    ----------
    order_idx : int
        0-indexed order label as written in the calibration file (0–28).
    physical_order : int
        Physical diffraction order (= ``order_idx + order_offset``).
    pixel_from : float
        Left edge of the detected line feature in detector pixels.
    pixel_to : float
        Right edge of the detected line feature in detector pixels.
    center_pixel : float
        Fitted centroid pixel position along the dispersion axis.
    wavelength_nm : float
        Known reference wavelength in nm.
    species : str
        Line identification string (e.g. ``"ArI"``, ``"NeI"``, ``"ThI"``).
    """

    order_idx: int
    physical_order: int
    pixel_from: float
    pixel_to: float
    center_pixel: float
    wavelength_nm: float
    species: str


@dataclass
class OrderWavelengthFit:
    """Per-order polynomial wavelength solution λ(x).

    The polynomial is evaluated on normalised pixel coordinates::

        x_norm = (x − x_center) / x_scale
        λ(x)   = c₀ + c₁·x_norm + c₂·x_norm² + …

    with coefficients stored in ascending-power order (c₀, c₁, c₂, …).

    Attributes
    ----------
    physical_order : int
        Physical diffraction order number.
    points : list of CalibrationLine
        Calibration measurements used for this fit.
    coefficients : ndarray
        Polynomial coefficients ``[c0, c1, c2, ...]`` (ascending powers).
    poly_degree : int
        Degree of the fitted polynomial.
    x_center : float
        Centre pixel used for x normalisation.
    x_scale : float
        Scale pixel used for x normalisation.
    pixel_min : float
        Minimum calibration pixel (left bound of calibrated range).
    pixel_max : float
        Maximum calibration pixel (right bound of calibrated range).
    """

    physical_order: int
    points: list[CalibrationLine]
    coefficients: np.ndarray
    poly_degree: int
    x_center: float
    x_scale: float
    pixel_min: float
    pixel_max: float

    # --- Evaluation ----------------------------------------------------------

    def wavelength_at(self, x: float | np.ndarray) -> np.ndarray:
        """Evaluate λ(x) in nm at pixel coordinate(s) x.

        Parameters
        ----------
        x : float or array-like
            Detector x pixel coordinate(s) along the dispersion axis.

        Returns
        -------
        ndarray
            Wavelength(s) in nm (same shape as *x*).
        """
        x = np.asarray(x, dtype=np.float64)
        x_norm = (x - self.x_center) / self.x_scale
        # coefficients stored ascending: polyval needs descending
        return np.polyval(self.coefficients[::-1], x_norm)

    def pixel_at(self, wavelength_nm: float) -> float:
        """Return the pixel x coordinate for a given wavelength.

        The polynomial is inverted via root-finding over an extended bracket
        around the calibrated pixel range.

        Parameters
        ----------
        wavelength_nm : float
            Reference wavelength in nm.

        Returns
        -------
        float
            Pixel x coordinate.

        Raises
        ------
        ValueError
            If *wavelength_nm* cannot be bracketed within the search interval.
        """
        span = max(self.pixel_max - self.pixel_min, 1.0)
        ext = 0.25 * span
        x_lo = self.pixel_min - ext
        x_hi = self.pixel_max + ext

        def _residual(x: float) -> float:
            return float(self.wavelength_at(np.asarray(x))) - wavelength_nm

        r_lo = _residual(x_lo)
        r_hi = _residual(x_hi)

        # Extend bracket further if needed (up to ±full span)
        if r_lo * r_hi > 0:
            x_lo = self.pixel_min - span
            x_hi = self.pixel_max + span
            r_lo = _residual(x_lo)
            r_hi = _residual(x_hi)

        if r_lo * r_hi > 0:
            lam_lo = float(self.wavelength_at(np.asarray(self.pixel_min)))
            lam_hi = float(self.wavelength_at(np.asarray(self.pixel_max)))
            raise ValueError(
                f"Cannot find pixel for λ={wavelength_nm:.3f} nm in order "
                f"{self.physical_order}.  Calibrated range: "
                f"{min(lam_lo, lam_hi):.3f}–{max(lam_lo, lam_hi):.3f} nm "
                f"(pixels {self.pixel_min:.0f}–{self.pixel_max:.0f})."
            )

        return float(brentq(_residual, x_lo, x_hi))

    # --- Diagnostics ---------------------------------------------------------

    @property
    def residuals_nm(self) -> np.ndarray:
        """Fit residuals (fitted − measured) in nm for each calibration point."""
        pixels = np.array([p.center_pixel for p in self.points])
        measured = np.array([p.wavelength_nm for p in self.points])
        return self.wavelength_at(pixels) - measured

    @property
    def rms_nm(self) -> float:
        """RMS wavelength residual in nm."""
        return float(np.sqrt(np.mean(self.residuals_nm**2)))

    @property
    def n_points(self) -> int:
        """Number of calibration lines in this fit."""
        return len(self.points)

    @property
    def wavelength_min_nm(self) -> float:
        """Minimum wavelength covered by calibration range."""
        lam_lo = float(self.wavelength_at(np.asarray(self.pixel_min)))
        lam_hi = float(self.wavelength_at(np.asarray(self.pixel_max)))
        return min(lam_lo, lam_hi)

    @property
    def wavelength_max_nm(self) -> float:
        """Maximum wavelength covered by calibration range."""
        lam_lo = float(self.wavelength_at(np.asarray(self.pixel_min)))
        lam_hi = float(self.wavelength_at(np.asarray(self.pixel_max)))
        return max(lam_lo, lam_hi)


@dataclass
class WavelengthSolution:
    """Collection of per-order polynomial wavelength solutions λ(x).

    Attributes
    ----------
    fits : dict
        Mapping from physical diffraction order (int) to
        :class:`OrderWavelengthFit`.
    """

    fits: dict[int, OrderWavelengthFit] = field(default_factory=dict)

    # --- Accessors -----------------------------------------------------------

    def has_order(self, order: int) -> bool:
        """Return ``True`` if *order* has a wavelength solution."""
        return order in self.fits

    def order_list(self) -> list[int]:
        """Return sorted list of physical orders with fitted solutions."""
        return sorted(self.fits.keys())

    def wavelength_at(self, x: float | np.ndarray, order: int) -> np.ndarray:
        """Evaluate λ(x) in nm for the given physical *order*.

        Parameters
        ----------
        x : float or array-like
            Detector x pixel coordinate(s).
        order : int
            Physical diffraction order.

        Returns
        -------
        ndarray
            Wavelength(s) in nm.
        """
        if order not in self.fits:
            raise KeyError(f"No wavelength solution for order {order}.")
        return self.fits[order].wavelength_at(x)

    def pixel_at(self, wavelength_nm: float, order: int) -> float:
        """Return pixel x for a given *wavelength_nm* and physical *order*.

        Parameters
        ----------
        wavelength_nm : float
            Reference wavelength in nm.
        order : int
            Physical diffraction order.

        Returns
        -------
        float
            Detector x pixel coordinate.
        """
        if order not in self.fits:
            raise KeyError(f"No wavelength solution for order {order}.")
        return self.fits[order].pixel_at(wavelength_nm)

    def summary(self) -> str:
        """Return a formatted text summary of per-order fit statistics."""
        rows = [
            f"WavelengthSolution: {len(self.fits)} orders fitted",
            f"{'order':>6}  {'n_pts':>5}  {'rms [pm]':>9}  {'λ range [nm]':>25}",
            "-" * 54,
        ]
        for m, fit in sorted(self.fits.items()):
            lam_lo = fit.wavelength_min_nm
            lam_hi = fit.wavelength_max_nm
            rows.append(
                f"{m:>6}  {fit.n_points:>5}  {fit.rms_nm * 1000:>9.2f}  "
                f"{lam_lo:>11.3f}–{lam_hi:>10.3f}"
            )
        return "\n".join(rows)


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------


def load_lhd_cmos_calibration(
    path: Optional[str | Path] = None,
    order_offset: int = LHD_CMOS_CAL_ORDER_OFFSET,
) -> list[CalibrationLine]:
    """Parse the LHD CMOS Th/Ar/Ne/Hg calibration line table.

    Parameters
    ----------
    path : str or Path, optional
        Path to the calibration file.  Defaults to the bundled
        ``Th_wavelength_CMOS_20240305.txt``.
    order_offset : int
        Physical order = file label + offset.  Default ``30`` maps
        file labels 0–28 to physical orders 30–58.

    Returns
    -------
    list of CalibrationLine
        All active (uncommented) calibration lines in file order.
    """
    if path is None:
        path = LHD_CMOS_CALIBRATION
    path = Path(path)

    cal_lines: list[CalibrationLine] = []
    with path.open() as fh:
        for raw in fh:
            # Strip inline comments then whitespace
            stripped = raw.split("#")[0].strip()
            if not stripped:
                continue
            tokens = stripped.split()
            if len(tokens) < 5:
                continue
            try:
                order_idx = int(tokens[0])
                pixel_from = float(tokens[1])
                pixel_to = float(tokens[2])
                center_pixel = float(tokens[3])
                wavelength_nm = float(tokens[4])
                species = tokens[5] if len(tokens) > 5 else ""
            except (ValueError, IndexError):
                continue

            cal_lines.append(
                CalibrationLine(
                    order_idx=order_idx,
                    physical_order=order_idx + order_offset,
                    pixel_from=pixel_from,
                    pixel_to=pixel_to,
                    center_pixel=center_pixel,
                    wavelength_nm=wavelength_nm,
                    species=species,
                )
            )

    return cal_lines


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------


def fit_wavelength_solution(
    calibration_lines: Sequence[CalibrationLine],
    poly_degree: int = 2,
) -> WavelengthSolution:
    """Fit per-order polynomial wavelength solutions λ(x).

    For each physical order present in *calibration_lines*, a polynomial is
    fitted to the measured (center_pixel → wavelength_nm) pairs.

    Parameters
    ----------
    calibration_lines : sequence of CalibrationLine
        Calibration measurements (from :func:`load_lhd_cmos_calibration`).
    poly_degree : int
        Polynomial degree.  ``2`` (quadratic) is usually sufficient;
        ``3`` (cubic) may reduce residuals for orders with wide wavelength
        span.  Orders with fewer than ``poly_degree + 1`` points are skipped.

    Returns
    -------
    WavelengthSolution
        Fitted solution with one :class:`OrderWavelengthFit` per order.
    """
    by_order: dict[int, list[CalibrationLine]] = {}
    for pt in calibration_lines:
        by_order.setdefault(pt.physical_order, []).append(pt)

    fits: dict[int, OrderWavelengthFit] = {}
    for m, pts in sorted(by_order.items()):
        if len(pts) < poly_degree + 1:
            continue

        pixels = np.array([p.center_pixel for p in pts], dtype=np.float64)
        wavelengths = np.array([p.wavelength_nm for p in pts], dtype=np.float64)

        x_center = pixels.mean()
        x_scale = pixels.std()
        if x_scale < 1.0:
            x_scale = 1.0
        x_norm = (pixels - x_center) / x_scale

        # np.polyfit returns highest-degree first → reverse to ascending
        coeffs_asc = np.polyfit(x_norm, wavelengths, poly_degree)[::-1]

        fits[m] = OrderWavelengthFit(
            physical_order=m,
            points=pts,
            coefficients=coeffs_asc,
            poly_degree=poly_degree,
            x_center=x_center,
            x_scale=x_scale,
            pixel_min=float(pixels.min()),
            pixel_max=float(pixels.max()),
        )

    return WavelengthSolution(fits=fits)


def load_lhd_cmos_wavelength_solution(
    path: Optional[str | Path] = None,
    poly_degree: int = 2,
    order_offset: int = LHD_CMOS_CAL_ORDER_OFFSET,
) -> WavelengthSolution:
    """Load and fit the LHD CMOS wavelength solution in one call.

    This is the primary entry point for empirical wavelength calibration.

    Parameters
    ----------
    path : str or Path, optional
        Path to the calibration file.  Defaults to bundled data.
    poly_degree : int
        Polynomial degree for λ(x) fitting (2 or 3 recommended).
    order_offset : int
        File label → physical order offset (default 30).

    Returns
    -------
    WavelengthSolution

    Examples
    --------
    >>> from echelle_optics import load_lhd_cmos_wavelength_solution
    >>> sol = load_lhd_cmos_wavelength_solution()
    >>> lam = sol.wavelength_at(1280.0, order=44)
    >>> x   = sol.pixel_at(520.0, order=44)
    """
    lines = load_lhd_cmos_calibration(path, order_offset=order_offset)
    return fit_wavelength_solution(lines, poly_degree=poly_degree)
