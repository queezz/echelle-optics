# echelle_optics

Lightweight Python toolkit for simulating cross-dispersed echelle spectrometer optics.
Covers dispersion calculations, order tables, and synthetic detector images.
The primary target instrument is the **LHD CMOS echelle** (Newport 46.1 gr/mm,
Andor Zyla 4.2 sCMOS, f = 304.8 mm).

## Install

```bash
python -m pip install -e ".[dev]"
pytest
```

## Quickstart

### Order table

```python
from echelle_optics import lhd_cmos_echelle

spec = lhd_cmos_echelle()
df = spec.order_table(30, 58)
print(df.to_string(index=False))
```

Sample output (abbreviated):

```
 order  center_wavelength_nm  free_spectral_range_nm  dispersion_nm_per_px  detector_span_nm  wavelength_min_nm  wavelength_max_nm
    30                720.47                   24.02                0.01307            33.46             703.74             737.20
    40                540.35                   13.51                0.00981            25.10             527.80             552.90
    58                372.66                    6.43                0.00676            17.31             364.00             381.31
```

### Synthetic detector image

```python
import matplotlib.pyplot as plt
from echelle_optics import lhd_cmos_echelle, render_echelle_lines

spec = lhd_cmos_echelle()
orders = list(range(30, 59))

# A handful of test emission lines (wavelength nm, intensity)
lines = [
    (656.3, 1.0),   # H-alpha
    (589.0, 0.8),   # Na D
    (546.1, 0.9),   # Hg green
    (435.8, 0.6),   # Hg blue
    (404.7, 0.4),   # Hg violet
]

img = render_echelle_lines(
    lines,
    spec,
    orders=orders,
    shape=(800, 1024),
    order_spacing_px=20.0,
    psf_sigma_px=1.5,
    color=True,
)

plt.figure(figsize=(12, 8))
plt.imshow(img, origin="upper", aspect="auto")
plt.title("LHD CMOS echelle — synthetic detector frame")
plt.xlabel("dispersion axis (px)")
plt.ylabel("cross-dispersion axis (px)")
plt.tight_layout()
plt.show()
```

### Detector geometry (order curvature)

Real echelle spectrographs produce curved order traces on the detector due to
camera optics aberrations and image-plane projection — commonly called "smile"
or field curvature.  This is **not** a diffraction physics effect; it is purely
a detector/image-plane geometry property.

The package includes empirical order-center positions measured from the LHD CMOS
echelle calibration lamp and can render synthetic images with realistic curvature:

```python
from echelle_optics import lhd_cmos_echelle, render_white_light, GeometryMode

spec = lhd_cmos_echelle()
orders = list(range(30, 59))

# Render with measured curved detector geometry
img = render_white_light(
    spec, orders,
    psf_sigma_y_px=12.0,
    color=True,
    geometry=GeometryMode.MEASURED_LHD_CMOS,
)
```

Two geometry modes are available:
- `GeometryMode.IDEAL_STRAIGHT` — constant-y orders (legacy / pedagogical)
- `GeometryMode.MEASURED_LHD_CMOS` — empirical curved traces from calibration

The geometry module also provides direct access to trace data and polynomial
coefficients:

```python
from echelle_optics import load_lhd_cmos_geometry

geom = load_lhd_cmos_geometry(poly_degree=2)
trace = geom.trace_for_order(44)
y_at_center = trace.y_at(1280.0)  # y position at detector center
```

See `examples/05_detector_geometry.ipynb` for detailed visualizations.

## Notes

- The 13 µm pixel size mentioned in older notes refers to a different (CCD) detector
  and is not a supported instrument configuration.  It appears only as a numerical
  scaling sanity check in the test suite (`test_dispersion_scales_with_pixel_size`),
  confirming that dispersion is proportional to pixel size.

- Order curvature is an empirical detector-space model derived from calibration data.
  This is NOT a Zemax/raytracing simulation — it provides believable detector
  geometry for pedagogical and development purposes.

## Docs

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```
