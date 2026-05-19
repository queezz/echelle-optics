"""Empirical detector trace geometry from calibration pattern files.

This module provides tools for loading real order-center positions measured
on echelle spectrometer detectors and fitting smooth polynomial models to
them.  The resulting geometry can be used by the synthetic renderer to produce
images with realistic order curvature (smile / field distortion).

The geometry here is purely image-plane / detector-space — it encodes
spectrograph optics and projection effects, NOT diffraction physics.

Pattern file format (LHD CMOS)
------------------------------
- Plain text, space-separated integers.
- Each row corresponds to one x pixel (dispersion axis), from x=0 to x=N-1.
- Each column corresponds to one echelle order.
- Values are y pixel coordinates of order centers at that x position.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

__all__ = [
    "GeometryMode",
    "OrderTrace",
    "DetectorGeometry",
    "load_lhd_cmos_pattern",
    "fit_order_traces",
    "load_lhd_cmos_geometry",
]

DATA_DIR = Path(__file__).parent / "data"
LHD_CMOS_PATTERN = DATA_DIR / "pattern_CMOS_20240305.txt"

# Default order range for the LHD CMOS echelle (30–58 inclusive)
LHD_CMOS_ORDER_MIN = 30
LHD_CMOS_ORDER_MAX = 58


class GeometryMode(Enum):
    """Detector geometry mode for rendering."""

    IDEAL_STRAIGHT = "ideal_straight"
    MEASURED_LHD_CMOS = "measured_lhd_cmos"


@dataclass
class OrderTrace:
    """Fitted trace for a single echelle order.

    Attributes
    ----------
    order : int
        Diffraction order number.
    x_pixels : ndarray
        Sampled x positions (dispersion axis), shape (N,).
    y_raw : ndarray
        Raw y pixel positions from the pattern file, shape (N,).
    coefficients : ndarray
        Polynomial coefficients [c0, c1, c2, ...] for the centered/scaled
        model:  y(x) = c0 + c1*x_norm + c2*x_norm^2 + ...
        where x_norm = (x - x_center) / x_scale.
    poly_degree : int
        Degree of the fitted polynomial.
    x_center : float
        Center value used for x normalization.
    x_scale : float
        Scale value used for x normalization.
    """

    order: int
    x_pixels: np.ndarray
    y_raw: np.ndarray
    coefficients: np.ndarray
    poly_degree: int
    x_center: float
    x_scale: float

    def y_at(self, x: np.ndarray | float) -> np.ndarray:
        """Evaluate the fitted trace at arbitrary x positions.

        Parameters
        ----------
        x : array-like
            Detector x pixel coordinates (dispersion axis).

        Returns
        -------
        ndarray
            Fitted y pixel positions (cross-dispersion axis).
        """
        x = np.asarray(x, dtype=np.float64)
        x_norm = (x - self.x_center) / self.x_scale
        return np.polyval(self.coefficients[::-1], x_norm)

    @property
    def y_fitted(self) -> np.ndarray:
        """Fitted y values at the sampled x positions."""
        return self.y_at(self.x_pixels)

    @property
    def residuals(self) -> np.ndarray:
        """Fit residuals (raw - fitted) at sampled x positions."""
        return self.y_raw - self.y_fitted


@dataclass
class DetectorGeometry:
    """Collection of fitted order traces for a complete detector.

    Attributes
    ----------
    traces : list of OrderTrace
        One trace per echelle order, sorted by order number.
    n_pixels_x : int
        Number of x pixels in the detector (dispersion axis).
    n_orders : int
        Number of echelle orders.
    order_min : int
        Lowest order number.
    order_max : int
        Highest order number.
    mode : GeometryMode
        Geometry mode used.
    """

    traces: list[OrderTrace]
    n_pixels_x: int
    n_orders: int
    order_min: int
    order_max: int
    mode: GeometryMode = field(default=GeometryMode.MEASURED_LHD_CMOS)

    def trace_for_order(self, order: int) -> OrderTrace:
        """Get the trace for a specific diffraction order."""
        idx = order - self.order_min
        if idx < 0 or idx >= self.n_orders:
            raise ValueError(
                f"Order {order} not in range [{self.order_min}, {self.order_max}]"
            )
        return self.traces[idx]

    def y_at(self, order: int, x: np.ndarray | float) -> np.ndarray:
        """Evaluate y(x) for a given order."""
        return self.trace_for_order(order).y_at(x)

    def order_numbers(self) -> list[int]:
        """Return list of available order numbers."""
        return [t.order for t in self.traces]


def load_lhd_cmos_pattern(
    path: Optional[str | Path] = None,
    order_min: int = LHD_CMOS_ORDER_MIN,
    order_max: int = LHD_CMOS_ORDER_MAX,
) -> tuple[np.ndarray, np.ndarray]:
    """Load the LHD CMOS pattern file.

    Parameters
    ----------
    path : str or Path, optional
        Path to the pattern file.  Defaults to the bundled
        ``pattern_CMOS_20240305.txt``.
    order_min : int
        Lowest diffraction order (column 0 in the file).
    order_max : int
        Highest diffraction order (last column in the file).

    Returns
    -------
    x_pixels : ndarray, shape (N,)
        X pixel positions (0 to N-1).
    traces_raw : ndarray, shape (N, n_orders)
        Raw y pixel positions, one column per order.
    """
    if path is None:
        path = LHD_CMOS_PATTERN
    path = Path(path)

    data = np.loadtxt(path, dtype=np.float64)
    n_rows, n_cols = data.shape
    expected_orders = order_max - order_min + 1
    if n_cols != expected_orders:
        raise ValueError(
            f"Pattern file has {n_cols} columns but expected {expected_orders} "
            f"orders ({order_min}–{order_max})"
        )

    x_pixels = np.arange(n_rows, dtype=np.float64)
    return x_pixels, data


def fit_order_traces(
    x_pixels: np.ndarray,
    traces_raw: np.ndarray,
    order_min: int = LHD_CMOS_ORDER_MIN,
    poly_degree: int = 2,
) -> list[OrderTrace]:
    """Fit polynomial traces to raw order-center positions.

    Parameters
    ----------
    x_pixels : ndarray, shape (N,)
        X pixel positions.
    traces_raw : ndarray, shape (N, n_orders)
        Raw y positions from the pattern file.
    order_min : int
        Diffraction order number for the first column.
    poly_degree : int
        Polynomial degree for fitting (2=quadratic, 3=cubic).

    Returns
    -------
    list of OrderTrace
        Fitted traces, one per order.
    """
    n_orders = traces_raw.shape[1]
    x_center = x_pixels.mean()
    x_scale = x_pixels.std() if x_pixels.std() > 0 else 1.0
    x_norm = (x_pixels - x_center) / x_scale

    fitted_traces = []
    for i in range(n_orders):
        y_raw = traces_raw[:, i]
        coeffs = np.polyfit(x_norm, y_raw, poly_degree)
        # np.polyfit returns highest-degree first; store as [c0, c1, c2, ...]
        coeffs_ascending = coeffs[::-1]

        trace = OrderTrace(
            order=order_min + i,
            x_pixels=x_pixels.copy(),
            y_raw=y_raw.copy(),
            coefficients=coeffs_ascending,
            poly_degree=poly_degree,
            x_center=x_center,
            x_scale=x_scale,
        )
        fitted_traces.append(trace)

    return fitted_traces


def load_lhd_cmos_geometry(
    path: Optional[str | Path] = None,
    order_min: int = LHD_CMOS_ORDER_MIN,
    order_max: int = LHD_CMOS_ORDER_MAX,
    poly_degree: int = 2,
) -> DetectorGeometry:
    """Load and fit the LHD CMOS detector geometry in one step.

    This is the main entry point for obtaining a complete fitted
    detector geometry model from the bundled calibration pattern.

    Parameters
    ----------
    path : str or Path, optional
        Path to the pattern file.  Defaults to bundled data.
    order_min : int
        Lowest diffraction order.
    order_max : int
        Highest diffraction order.
    poly_degree : int
        Polynomial degree for trace fitting.

    Returns
    -------
    DetectorGeometry
        Complete geometry model with fitted traces.
    """
    x_pixels, traces_raw = load_lhd_cmos_pattern(path, order_min, order_max)
    traces = fit_order_traces(x_pixels, traces_raw, order_min, poly_degree)

    return DetectorGeometry(
        traces=traces,
        n_pixels_x=len(x_pixels),
        n_orders=len(traces),
        order_min=order_min,
        order_max=order_max,
        mode=GeometryMode.MEASURED_LHD_CMOS,
    )
