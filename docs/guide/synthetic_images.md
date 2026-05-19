# Synthetic Images

The package can generate synthetic 2D detector images of two kinds:

- **Emission-line images** — discrete spectral lines scattered across the echellogram
- **White-light images** — continuous per-order wavelength-colored bands

Both renderers are in `synthetic.py` and share the same coordinate system:
x from grating dispersion, y from detector geometry.

---

## Coordinate system

Each pixel in the synthetic image corresponds to a specific (wavelength, order) pair:

- **x axis (dispersion direction)**: wavelength position within an order, computed from
  `linear_dispersion_nm_per_px` and the order's central wavelength
- **y axis (cross-dispersion direction)**: order center position, from either
  `IDEAL_STRAIGHT` uniform spacing or `MEASURED_LHD_CMOS` polynomial traces

The two axes are computed independently and combined only at render time.

---

## Emission-line renderer

`render_echelle_lines()` generates a synthetic calibration-lamp image.

### How it works

For each input wavelength:

1. Compute which order(s) it falls in using `physical_order_from_wavelength()`
2. Convert wavelength to x-pixel within that order using dispersion
3. Look up the y-pixel for that order at that x using `_order_y_position()`
4. Paint a 2D Gaussian PSF centered at (x, y)

### PSF model

The PSF is an elliptical Gaussian with **independent** x and y widths:

- `psf_sigma_x_px` — spectral width (dispersion direction), typically 1–3 px
- `psf_sigma_y_px` — spatial/slit width (cross-dispersion), typically 8–15 px

The slit image is taller than it is wide in a typical echelle setup.

### Noise

Optional background and Gaussian read noise can be added:

```python
img = render_echelle_lines(
    spec, lines,
    background=50.0,       # ADU floor
    read_noise_sigma=5.0,  # Gaussian σ in ADU
)
```

### Color mode

Pass `color=True` to get an RGB image where each line is colored by its wavelength
using `wavelength_to_rgb()`. Returns shape `(H, W, 3)` instead of `(H, W)`.

### Example

```python
from echelle_optics import lhd_cmos_echelle, render_echelle_lines, GeometryMode

spec = lhd_cmos_echelle()
lines = [404.66, 435.83, 546.07, 579.07, 696.54, 706.72, 750.39, 763.51]

img = render_echelle_lines(
    spec, lines,
    geometry_mode=GeometryMode.MEASURED_LHD_CMOS,
    psf_sigma_x_px=1.5,
    psf_sigma_y_px=12.0,
    order_spacing_px=65,
    background=10.0,
    read_noise_sigma=3.0,
)
# img.shape == (2160, 2560)
```

---

## White-light renderer

`render_white_light()` fills each order with a continuous band of wavelength-colored
pixels. It is useful for visualizing order layout and geometry.

### How it works

For each order:

1. Compute the wavelength at every x pixel from dispersion
2. Convert each wavelength to an RGB color using `wavelength_to_rgb()`
3. Paint a vertical stripe of configurable height centered on the order y-position

The result is always an RGB image of shape `(H, W, 3)`.

### Example

```python
from echelle_optics import lhd_cmos_echelle, render_white_light, GeometryMode

spec = lhd_cmos_echelle()

img = render_white_light(
    spec,
    order_min=30, order_max=58,
    geometry_mode=GeometryMode.MEASURED_LHD_CMOS,
    order_spacing_px=65,
    order_width_px=20,
)
# img.shape == (2160, 2560, 3)
```

---

## GeometryMode and order_spacing_px

When `geometry_mode=IDEAL_STRAIGHT`, orders are placed at:

\[
y_m = y_0 + (m - m_0) \times \texttt{order\_spacing\_px}
\]

The `order_spacing_px` parameter controls vertical spacing between orders in ideal mode.
It has no effect when `MEASURED_LHD_CMOS` is used, because y-positions come entirely
from the calibration pattern.

---

## Renderer limitations

The synthetic renderer is a forward model for calibration and visualization. It is
**not** a full instrument simulator:

| Limitation | Notes |
|---|---|
| No blaze efficiency | All orders rendered with equal intensity |
| No wavelength-dependent throughput | PSF amplitude is constant |
| No optical aberrations beyond geometry | Curvature from data, not from optics |
| No inter-order scattered light | Background is uniform additive noise |
| No detector non-uniformity | Flat gain across the chip |
| Dispersion is linear per order | Higher-order dispersion terms not included |

These simplifications are appropriate for the package's goal: calibration support and
geometry validation, not photometric simulation.

---

## Parameter exploration

See [Synthetic Image Parameters](../examples/synthetic_parameters.md) for a full sweep
of PSF sigma, order spacing, background, read noise, and color mode.
