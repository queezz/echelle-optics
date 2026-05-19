# Example: Synthetic Image Parameters

**Notebook**: `examples/04_synthetic_image_parameters.ipynb`

This example systematically sweeps the rendering parameters of `render_echelle_lines()`
to show how each one affects the output image. Useful for calibrating the model to
match a real detector frame.

---

## Display helper

The notebook uses a percentile stretch for consistent display:

```python
import numpy as np
import matplotlib.pyplot as plt

def show(img, ax, title="", pct=99.5):
    vmax = np.percentile(img, pct)
    ax.imshow(img, origin="lower", cmap="gray", vmin=0, vmax=vmax)
    ax.set_title(title)
    ax.axis("off")
```

---

## PSF sigma (spectral direction)

`psf_sigma_x_px` controls the width of each line in the dispersion direction.

Typical values: 1–4 px. Smaller values give sharper lines; larger values approximate
lower spectral resolution or defocus.

```python
for sigma_x in [0.5, 1.5, 3.0, 5.0]:
    img = render_echelle_lines(spec, lines, psf_sigma_x_px=sigma_x, ...)
```

---

## PSF sigma (spatial/slit direction)

`psf_sigma_y_px` controls the height of each line in the cross-dispersion direction.
This models the slit image height.

Typical values: 5–20 px. The default of 12 px corresponds to a ~80 µm slit.

```python
for sigma_y in [3.0, 8.0, 12.0, 20.0]:
    img = render_echelle_lines(spec, lines, psf_sigma_y_px=sigma_y, ...)
```

---

## Order spacing

`order_spacing_px` sets the vertical distance between adjacent orders in
`IDEAL_STRAIGHT` mode. It has no effect with `MEASURED_LHD_CMOS`.

Typical value for the LHD CMOS: 65 px (orders 30–58 span ~1885 px of the 2160 px
detector height).

```python
for spacing in [45, 55, 65, 75]:
    img = render_echelle_lines(spec, lines, order_spacing_px=spacing, ...)
```

---

## Background level

`background` adds a constant offset to the entire image in ADU. Models sky background,
thermal dark current, or a bright plasma continuum.

```python
for bg in [0, 20, 100, 500]:
    img = render_echelle_lines(spec, lines, background=bg, ...)
```

---

## Read noise

`read_noise_sigma` adds Gaussian noise with the given standard deviation. Models
detector read noise.

```python
for noise in [0, 3, 10, 30]:
    img = render_echelle_lines(spec, lines, read_noise_sigma=noise, ...)
```

---

## Color mode

Passing `color=True` returns an `(H, W, 3)` RGB array instead of `(H, W)` grayscale.
Each line is colored by its wavelength using `wavelength_to_rgb()`.

```python
img_gray  = render_echelle_lines(spec, lines, color=False)   # (2160, 2560)
img_color = render_echelle_lines(spec, lines, color=True)    # (2160, 2560, 3)
```

---

## Matching a real frame

To tune the renderer to match a specific real calibration frame:

1. Display the real frame with the same percentile stretch
2. Identify isolated bright lines and measure their pixel width (x) and height (y)
3. Set `psf_sigma_x_px` to ~half the FWHM in x (FWHM ≈ 2.35 σ)
4. Set `psf_sigma_y_px` similarly for y
5. Measure the inter-order spacing from the real frame and set `order_spacing_px`
6. Use `GeometryMode.MEASURED_LHD_CMOS` to match the curvature

The renderer does not attempt automatic fitting to real data — that is out of scope.
