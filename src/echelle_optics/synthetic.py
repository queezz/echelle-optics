"""Synthetic echelle detector-frame renderer.

Produces a 2-D numpy array (or RGB cube) that mimics what an echelle
spectrometer detector would see for a given list of spectral lines.

Architecture: physics vs. detector mapping
-------------------------------------------
The renderer separates two concerns:

1. **Ideal spectral physics** — where a line *should* appear based on
   the grating equation (order, dispersion, central wavelength).
   This determines the x-position of each line.

2. **Detector geometry / projection** — how the order traces map onto
   the detector plane.  In the ideal case, orders are straight horizontal
   lines.  In the real case (measured geometry), orders follow curved
   traces caused by spectrograph optics, aberrations, and camera
   distortion (commonly called "smile" or field curvature).

Coordinate conventions
----------------------
- x axis  →  dispersion direction  (detector columns)
- y axis  ↓  cross-dispersion      (detector rows, order separation)
- origin (0, 0) is the bottom-left corner when displayed with
  ``imshow(origin='lower')``.

Geometry modes
--------------
- ``GeometryMode.IDEAL_STRAIGHT``: constant-y orders (legacy behaviour).
- ``GeometryMode.MEASURED_LHD_CMOS``: empirical curved traces from
  the LHD CMOS calibration pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

import numpy as np

from .color import wavelength_to_rgb
from .geometry import DetectorGeometry, GeometryMode, load_lhd_cmos_geometry
from .grating import central_wavelength_nm, linear_dispersion_nm_per_px
from .spectrometer import EchelleSpectrometer

if TYPE_CHECKING:
    from .calibration import WavelengthSolution

__all__ = ["render_echelle_lines", "render_white_light"]


def _resolve_geometry(
    geometry: Optional[DetectorGeometry | GeometryMode],
) -> Optional[DetectorGeometry]:
    """Resolve a geometry argument into a DetectorGeometry or None (ideal)."""
    if geometry is None:
        return None
    if isinstance(geometry, DetectorGeometry):
        return geometry
    if isinstance(geometry, GeometryMode):
        if geometry == GeometryMode.IDEAL_STRAIGHT:
            return None
        if geometry == GeometryMode.MEASURED_LHD_CMOS:
            return load_lhd_cmos_geometry()
    raise TypeError(f"Invalid geometry argument: {geometry!r}")


def _order_y_position(
    order: int,
    x: float | np.ndarray,
    yc: float,
    ref_order: int,
    order_spacing_px: float,
    geometry: Optional[DetectorGeometry],
) -> float | np.ndarray:
    """Compute y position(s) for an order at given x position(s).

    With geometry=None (ideal mode), returns a constant.
    With a DetectorGeometry, evaluates the empirical trace.
    """
    if geometry is None:
        return yc + (order - ref_order) * order_spacing_px
    return geometry.y_at(order, x)


def render_echelle_lines(
    lines: Sequence[tuple[float, float]],
    spectrometer: EchelleSpectrometer,
    orders: Sequence[int],
    shape: tuple[int, int] | None = None,
    x_center: float | None = None,
    y_center: float | None = None,
    reference_order: int | None = None,
    order_spacing_px: float = 55.0,
    psf_sigma_px: float = 1.5,
    psf_sigma_y_px: float | None = None,
    color: bool = False,
    background: float = 0.0,
    read_noise: float = 0.0,
    seed: int | None = None,
    geometry: Optional[DetectorGeometry | GeometryMode] = None,
    wavelength_solution: Optional["WavelengthSolution"] = None,
) -> np.ndarray:
    """Render spectral lines onto a synthetic echelle detector frame.

    Parameters
    ----------
    lines:
        Sequence of ``(wavelength_nm, intensity)`` pairs.
    spectrometer:
        :class:`~echelle_optics.spectrometer.EchelleSpectrometer` instance.
    orders:
        Diffraction orders to render.
    shape:
        ``(height, width)`` of the output array in pixels.  Defaults to
        ``(detector.height_px, detector.width_px)``.
    x_center:
        Column (pixel) at which the central wavelength of *reference_order*
        is placed.  Defaults to ``width / 2``.
        Ignored for orders covered by *wavelength_solution*.
    y_center:
        Row (pixel) at which *reference_order* is placed.
        Defaults to ``height / 2``.  Ignored when using measured geometry.
    reference_order:
        Order placed at *y_center*.  Defaults to the median of *orders*.
        Ignored when using measured geometry.
    order_spacing_px:
        Vertical separation between adjacent orders in pixels.
        Ignored when using measured geometry.
    psf_sigma_px:
        Gaussian PSF standard deviation along the **dispersion** axis (x) in
        pixels.  Also used for the cross-dispersion axis when
        *psf_sigma_y_px* is ``None``.
    psf_sigma_y_px:
        Gaussian PSF standard deviation along the **cross-dispersion** axis
        (y) in pixels.  Defaults to *psf_sigma_px* (symmetric PSF).

        Set this larger than *psf_sigma_px* to simulate a slit that is
        taller than it is wide — the typical appearance of echelle orders
        on a real detector where the spatial (slit-height) direction maps
        onto the cross-dispersion axis.
    color:
        If ``True`` return a ``(H, W, 3)`` float32 RGB array; otherwise
        return a ``(H, W)`` float32 grey array.
    background:
        Uniform background level added to every pixel.
    read_noise:
        Gaussian read-noise standard deviation (in the same units as
        *intensity*).  Set to 0 to disable.
    seed:
        Random seed for reproducible noise.
    geometry:
        Detector geometry mode or instance.  ``None`` or
        ``GeometryMode.IDEAL_STRAIGHT`` for constant-y orders;
        ``GeometryMode.MEASURED_LHD_CMOS`` or a ``DetectorGeometry``
        instance for empirical curved traces.
    wavelength_solution:
        Optional empirical :class:`~echelle_optics.calibration.WavelengthSolution`.
        When provided, the x-pixel position of each line is determined by
        inverting the fitted polynomial λ(x) rather than the theoretical
        Littrow dispersion formula.  Falls back to theory for orders not
        covered by the solution or wavelengths outside its range.
        Best used with the full detector size (2560 × 2160 px).

    Returns
    -------
    numpy.ndarray
        Float32 array of shape ``(H, W)`` or ``(H, W, 3)``.
    """
    sig_x = psf_sigma_px
    sig_y = psf_sigma_y_px if psf_sigma_y_px is not None else psf_sigma_px

    det = spectrometer.detector
    h, w = shape if shape is not None else (det.height_px, det.width_px)
    xc = x_center if x_center is not None else w / 2.0
    yc = y_center if y_center is not None else h / 2.0
    ref_order = reference_order if reference_order is not None else int(np.median(orders))

    geom = _resolve_geometry(geometry)
    rng = np.random.default_rng(seed)

    # Pre-compute per-order optical parameters
    order_params: dict[int, tuple[float, float]] = {}
    for m in orders:
        lam_c = central_wavelength_nm(
            m, spectrometer.grating.grooves_per_mm, spectrometer.grating.blaze_deg
        )
        disp = linear_dispersion_nm_per_px(
            m,
            spectrometer.grating.grooves_per_mm,
            spectrometer.beta_deg,  # type: ignore[arg-type]
            spectrometer.focal_length_mm,
            det.pixel_size_um,
        )
        order_params[m] = (lam_c, disp)

    # Separate kernel radii for x and y
    kernel_rx = int(np.ceil(4.0 * sig_x))
    kernel_ry = int(np.ceil(4.0 * sig_y))
    kx = np.arange(2 * kernel_rx + 1) - kernel_rx
    ky = np.arange(2 * kernel_ry + 1) - kernel_ry

    # Output buffer(s)
    if color:
        frame = np.full((h, w, 3), background, dtype=np.float32)
    else:
        frame = np.full((h, w), background, dtype=np.float32)

    # Scatter lines
    for lam_nm, intensity in lines:
        rgb = wavelength_to_rgb(lam_nm) if color else None

        for m in orders:
            lam_c, disp = order_params[m]
            if disp == 0.0:
                continue

            # x position: empirical calibration if available, else theory
            if wavelength_solution is not None and wavelength_solution.has_order(m):
                try:
                    xp = wavelength_solution.pixel_at(lam_nm, m)
                except (ValueError, KeyError):
                    xp = xc + (lam_nm - lam_c) / disp
            else:
                xp = xc + (lam_nm - lam_c) / disp
            # y position from detector geometry
            yp = float(_order_y_position(m, xp, yc, ref_order, order_spacing_px, geom))

            # Integer centres; sub-pixel offset carried into Gaussian
            xi = int(round(xp))
            yi = int(round(yp))

            # Bounding box on detector
            x0, x1 = xi - kernel_rx, xi + kernel_rx + 1
            y0, y1 = yi - kernel_ry, yi + kernel_ry + 1

            # Clip to detector
            ax0 = max(x0, 0)
            ax1 = min(x1, w)
            ay0 = max(y0, 0)
            ay1 = min(y1, h)
            if ax0 >= ax1 or ay0 >= ay1:
                continue

            kx0 = ax0 - x0
            kx1 = ax1 - x0
            ky0 = ay0 - y0
            ky1 = ay1 - y0

            # Sub-pixel shift
            dx = xp - xi
            dy = yp - yi
            gx = np.exp(-0.5 * ((kx + dx) / sig_x) ** 2)
            gy = np.exp(-0.5 * ((ky + dy) / sig_y) ** 2)
            psf_patch = np.outer(gy[ky0:ky1], gx[kx0:kx1]) * float(intensity)

            if color:
                for c, cv in enumerate(rgb):  # type: ignore[arg-type]
                    frame[ay0:ay1, ax0:ax1, c] += psf_patch * cv
            else:
                frame[ay0:ay1, ax0:ax1] += psf_patch

    # Add read noise
    if read_noise > 0.0:
        noise = rng.normal(0.0, read_noise, size=frame.shape).astype(np.float32)
        frame += noise

    return frame


def render_white_light(
    spectrometer: EchelleSpectrometer,
    orders: Sequence[int],
    shape: tuple[int, int] | None = None,
    x_center: float | None = None,
    y_center: float | None = None,
    reference_order: int | None = None,
    order_spacing_px: float = 55.0,
    psf_sigma_y_px: float = 12.0,
    color: bool = True,
    background: float = 0.0,
    geometry: Optional[DetectorGeometry | GeometryMode] = None,
    wavelength_solution: Optional["WavelengthSolution"] = None,
) -> np.ndarray:
    """Render a white-light (continuum) frame showing the span of every order.

    Each echelle order appears as a band filled with uniform intensity
    (grayscale) or wavelength-dependent colour (colour mode).  The cross-
    dispersion profile is a Gaussian with width *psf_sigma_y_px*, centered
    on the order trace.

    When using measured geometry, the order trace varies with x (curved),
    producing the characteristic "smile" pattern seen in real instruments.

    Parameters
    ----------
    spectrometer:
        :class:`~echelle_optics.spectrometer.EchelleSpectrometer` instance.
    orders:
        Diffraction orders to render.
    shape:
        ``(height, width)`` of the output array.  Defaults to the detector size.
    x_center:
        Column at which each order's central wavelength is placed.
        Defaults to ``width / 2``.
        Ignored for orders covered by *wavelength_solution*.
    y_center:
        Row at which *reference_order* is placed.  Defaults to ``height / 2``.
        Ignored when using measured geometry.
    reference_order:
        Order placed at *y_center*.  Defaults to the median of *orders*.
        Ignored when using measured geometry.
    order_spacing_px:
        Cross-dispersion separation between adjacent orders in pixels.
        Ignored when using measured geometry.
    psf_sigma_y_px:
        Gaussian cross-dispersion profile standard deviation in pixels.
    color:
        If ``True`` (default) return an ``(H, W, 3)`` float32 RGB array where
        each column is tinted by the wavelength it carries.  If ``False``
        return a ``(H, W)`` float32 greyscale array.
    background:
        Uniform background level added to every pixel.
    geometry:
        Detector geometry mode or instance.  ``None`` or
        ``GeometryMode.IDEAL_STRAIGHT`` for constant-y orders;
        ``GeometryMode.MEASURED_LHD_CMOS`` or a ``DetectorGeometry``
        instance for empirical curved traces.
    wavelength_solution:
        Optional empirical :class:`~echelle_optics.calibration.WavelengthSolution`.
        When provided, per-column wavelength is read from the fitted polynomial
        λ(x) rather than the Littrow formula.  Falls back to theory for orders
        not covered by the solution.

    Returns
    -------
    numpy.ndarray
        Float32 array of shape ``(H, W)`` or ``(H, W, 3)``.
    """
    det = spectrometer.detector
    h, w = shape if shape is not None else (det.height_px, det.width_px)
    xc = x_center if x_center is not None else w / 2.0
    yc = y_center if y_center is not None else h / 2.0
    ref_order = reference_order if reference_order is not None else int(np.median(orders))

    geom = _resolve_geometry(geometry)

    if color:
        frame = np.full((h, w, 3), background, dtype=np.float32)
    else:
        frame = np.full((h, w), background, dtype=np.float32)

    y_idx = np.arange(h, dtype=np.float32)  # (h,)
    x_idx = np.arange(w, dtype=np.float32)  # (w,)

    for m in orders:
        lam_c = central_wavelength_nm(
            m, spectrometer.grating.grooves_per_mm, spectrometer.grating.blaze_deg
        )
        disp = linear_dispersion_nm_per_px(
            m,
            spectrometer.grating.grooves_per_mm,
            spectrometer.beta_deg,  # type: ignore[arg-type]
            spectrometer.focal_length_mm,
            det.pixel_size_um,
        )
        if disp == 0.0:
            continue

        # Order trace y position: either constant or x-dependent
        y_trace = _order_y_position(m, x_idx, yc, ref_order, order_spacing_px, geom)
        y_trace = np.broadcast_to(
            np.asarray(y_trace, dtype=np.float32), (w,)
        ).copy()  # shape (w,)

        # Cross-dispersion Gaussian: y_idx (h,) vs y_trace (w,) → (h, w)
        # dy[row, col] = y_idx[row] - y_trace[col]
        dy = y_idx[:, np.newaxis] - y_trace[np.newaxis, :]  # (h, w)
        gy = np.exp(-0.5 * (dy / psf_sigma_y_px) ** 2)  # (h, w)

        # Wavelength at every detector column
        if wavelength_solution is not None and wavelength_solution.has_order(m):
            lam_at_x = wavelength_solution.wavelength_at(x_idx, m).astype(np.float32)
        else:
            lam_at_x = lam_c + (x_idx - xc) * disp  # (w,)

        if color:
            rgb_at_x = np.array(
                [wavelength_to_rgb(float(l)) for l in lam_at_x], dtype=np.float32
            )  # (w, 3)
            # gy (h, w) × rgb (w, 3) → (h, w, 3)
            frame += gy[:, :, np.newaxis] * rgb_at_x[np.newaxis, :, :]
        else:
            frame += gy

    return frame
