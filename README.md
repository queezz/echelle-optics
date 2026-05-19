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

## Notes

- The 13 µm pixel size mentioned in older notes refers to a different (CCD) detector
  and is not a supported instrument configuration.  It appears only as a numerical
  scaling sanity check in the test suite (`test_dispersion_scales_with_pixel_size`),
  confirming that dispersion is proportional to pixel size.

## Docs

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```
