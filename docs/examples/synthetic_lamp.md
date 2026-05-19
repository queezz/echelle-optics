# Example: Synthetic Lamp Image

**Notebook**: `examples/02_synthetic_lamp_image.ipynb`

This example renders a synthetic calibration-lamp echellogram using emission lines
from Hg, H, He, and Ar. The output is a grayscale float array on the full 2560 × 2160
detector.

---

## Setup

```python
from echelle_optics import lhd_cmos_echelle, render_echelle_lines, GeometryMode

spec = lhd_cmos_echelle()
```

---

## Defining calibration lines

```python
# Hg lines (nm)
hg_lines = [404.66, 435.83, 546.07, 576.96, 579.07]

# H Balmer lines
h_lines = [486.13, 656.28]

# He lines
he_lines = [447.15, 501.57, 587.56, 667.82, 706.52]

# Ar lines
ar_lines = [696.54, 706.72, 750.39, 763.51, 772.42, 794.82, 811.53, 826.45]

lines = hg_lines + h_lines + he_lines + ar_lines
```

---

## Rendering

```python
img = render_echelle_lines(
    spec,
    lines,
    geometry_mode=GeometryMode.IDEAL_STRAIGHT,
    psf_sigma_x_px=1.5,
    psf_sigma_y_px=12.0,
    order_spacing_px=65,
)
```

Default rendering uses straight orders. For curved (realistic) orders, pass
`GeometryMode.MEASURED_LHD_CMOS`.

---

## PSF parameters

The two PSF widths model different physical effects:

| Parameter | Default | Models |
|---|---|---|
| `psf_sigma_x_px` | 1.5 px | Instrument line spread function (spectral resolution) |
| `psf_sigma_y_px` | 12 px | Slit image height (spatial extent of the source) |

For a 100 µm slit at f/10, the slit image on the detector is approximately
100 µm / 6.5 µm/px ≈ 15 px tall. The y-sigma of ~12 is a reasonable default.

---

## Displaying the result

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(12, 10))
vmax = np.percentile(img, 99.5)
ax.imshow(img, origin="lower", cmap="gray", vmin=0, vmax=vmax)
ax.set_title("Synthetic lamp image — LHD CMOS echelle")
plt.tight_layout()
plt.show()
```

Using percentile-based scaling (`vmax = np.percentile(img, 99.5)`) prevents bright
isolated lines from washing out the display.

---

## Color version

```python
img_color = render_echelle_lines(
    spec, lines,
    geometry_mode=GeometryMode.IDEAL_STRAIGHT,
    psf_sigma_x_px=1.5,
    psf_sigma_y_px=12.0,
    order_spacing_px=65,
    color=True,
)
# img_color.shape == (2160, 2560, 3)
```

Each line is colored by its wavelength using `wavelength_to_rgb()`. UV and IR lines
outside 380–780 nm appear dark.

---

## Model limitations

| Limitation | Effect |
|---|---|
| No blaze efficiency | All lines rendered at equal amplitude |
| Linear dispersion only | Slight wavelength error near order edges |
| Ideal straight orders | Real orders curve by up to ~15 px |
| No inter-order cross-talk | Each order is fully isolated |
| No optical aberrations | PSF is perfectly elliptical Gaussian |

For realistic geometry, use `GeometryMode.MEASURED_LHD_CMOS` — see the
[Detector Geometry example](detector_geometry.md).
