"""Synthetic echelle detector-frame renderer.

Produces a 2-D numpy array (or RGB cube) that mimics what an echelle
spectrometer detector would see for a given list of spectral lines.

Coordinate conventions
----------------------
- x axis  →  dispersion direction  (detector columns)
- y axis  ↓  cross-dispersion      (detector rows, order separation)
- origin (0, 0) is the bottom-left corner when displayed with
  ``imshow(origin='lower')``.

Order layout
------------
Each echelle order is placed at::

    y_order = y_center + (order - reference_order) * order_spacing_px

Higher orders (shorter wavelengths) appear at smaller y (towards the top)
when order_spacing_px > 0.

Wavelength-to-pixel mapping (dispersion axis)
---------------------------------------------
For a line at wavelength λ in order m::

    x_line = x_center + (λ - λ_center_m) / dispersion_m

where λ_center_m and dispersion_m are computed from the spectrometer model.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .color import wavelength_to_rgb
from .grating import central_wavelength_nm, linear_dispersion_nm_per_px
from .spectrometer import EchelleSpectrometer

__all__ = ["render_echelle_lines"]


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
    y_center:
        Row (pixel) at which *reference_order* is placed.
        Defaults to ``height / 2``.
    reference_order:
        Order placed at *y_center*.  Defaults to the median of *orders*.
    order_spacing_px:
        Vertical separation between adjacent orders in pixels.
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

            # Pixel positions
            xp = xc + (lam_nm - lam_c) / disp
            yp = yc + (m - ref_order) * order_spacing_px

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
