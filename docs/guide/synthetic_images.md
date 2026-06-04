# Synthetic Images

The package can generate synthetic 2D detector images of two kinds:

- **Emission-line images** — discrete spectral lines scattered across the echellogram
- **White-light images** — continuous per-order wavelength-colored bands

Both renderers are in `synthetic.py` and share the same coordinate system.  The x axis
comes from an empirical `WavelengthSolution` when supplied, otherwise from theoretical
grating dispersion.  The y axis comes from detector geometry.

---

## Coordinate system

Each pixel in the synthetic image corresponds to a specific `(wavelength, order)` pair:

- **x axis (dispersion direction)**: wavelength position within an order, computed from
  `WavelengthSolution.pixel_at()` or from `linear_dispersion_nm_per_px`
- **y axis (cross-dispersion direction)**: order center position from either
  `IDEAL_STRAIGHT` uniform spacing or `MEASURED_LHD_CMOS` polynomial traces

The two axes are computed independently and combined only at render time.

---

## Emission-line renderer

`render_echelle_lines()` generates a synthetic calibration-lamp image.

### How it works

For each input wavelength:

1. Iterate over the requested diffraction orders.
2. Convert wavelength to x-pixel using `WavelengthSolution.pixel_at()` when possible,
   otherwise using theoretical dispersion.
3. Look up the y-pixel for that order at that x.
4. Paint a 2D Gaussian PSF centered at `(x, y)`.

### PSF model

The PSF is an elliptical Gaussian with independent x and y widths:

- `psf_sigma_px` — spectral width (dispersion direction), typically 1–3 px
- `psf_sigma_y_px` — spatial/slit width (cross-dispersion), typically 8–15 px

The slit image is taller than it is wide in a typical echelle setup.

### Noise

Optional background and Gaussian read noise can be added:

```python
img = render_echelle_lines(
    lines,
    spec,
    orders=range(30, 59),
    background=50.0,  # ADU floor
    read_noise=5.0,   # Gaussian sigma in ADU
)
```

### Color mode

Pass `color=True` to get an RGB image where each line is colored by its wavelength
using `wavelength_to_rgb()`.  Returns shape `(H, W, 3)` instead of `(H, W)`.

### Example

```python
from echelle_optics import GeometryMode, lhd_cmos_echelle, render_echelle_lines

spec = lhd_cmos_echelle()
lines = [(404.66, 1.0), (435.83, 1.0), (546.07, 1.0), (579.07, 1.0)]

img = render_echelle_lines(
    lines,
    spec,
    orders=range(30, 59),
    geometry=GeometryMode.MEASURED_LHD_CMOS,
    psf_sigma_px=1.5,
    psf_sigma_y_px=12.0,
    background=10.0,
    read_noise=3.0,
)
# img.shape == (2160, 2560)
```

---

## Empirical wavelength rendering

Use the measured lookup table as the x-axis rule by passing a wavelength solution:

```python
from echelle_optics import load_lhd_cmos_wavelength_solution

solution = load_lhd_cmos_wavelength_solution()

img = render_echelle_lines(
    lines,
    spec,
    orders=solution.order_list(),
    geometry=GeometryMode.MEASURED_LHD_CMOS,
    wavelength_solution=solution,
)
```

This is the preferred mode when comparing synthetic calibration frames to real LHD CMOS
data.

---

## White-light renderer

`render_white_light()` fills each order with a continuous band of wavelength-colored
pixels.  It is useful for visualizing order layout and geometry.

For each order:

1. Compute wavelength at every x pixel from `WavelengthSolution.wavelength_at()` or
   theoretical dispersion.
2. Convert each wavelength to an RGB color using `wavelength_to_rgb()`.
3. Paint a Gaussian cross-dispersion profile centered on the order y-position.

### Example

```python
from echelle_optics import GeometryMode, lhd_cmos_echelle, render_white_light

spec = lhd_cmos_echelle()

img = render_white_light(
    spec,
    orders=range(30, 59),
    geometry=GeometryMode.MEASURED_LHD_CMOS,
    psf_sigma_y_px=20,
)
# img.shape == (2160, 2560, 3)
```

---

## GeometryMode and order_spacing_px

When `geometry=GeometryMode.IDEAL_STRAIGHT`, orders are placed at:

\[
y_m = y_0 + (m - m_0) \times \texttt{order\_spacing\_px}
\]

The `order_spacing_px` parameter controls vertical spacing between orders in ideal mode.
It has no effect when `MEASURED_LHD_CMOS` is used, because y-positions come entirely
from the calibration pattern.

---

## Renderer limitations

The synthetic renderer is a forward model for calibration and visualization.  It is not
a full instrument simulator:

| Limitation | Notes |
|---|---|
| No blaze efficiency | All orders rendered with equal intensity |
| No wavelength-dependent throughput | PSF amplitude is constant |
| No optical aberrations beyond geometry | Curvature from data, not from optics |
| No inter-order scattered light | Background is uniform additive noise |
| No detector non-uniformity | Flat gain across the chip |
| Empirical coverage is finite | Rendering falls back to theory outside calibrated ranges |

These simplifications are appropriate for the package's goal: calibration support and
geometry validation, not photometric simulation.

---

## Parameter exploration

See [Synthetic Image Parameters](../examples/synthetic_parameters.md) for a full sweep
of PSF sigma, order spacing, background, read noise, and color mode.
