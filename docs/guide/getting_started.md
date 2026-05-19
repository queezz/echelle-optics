# Getting Started

## Requirements

- Python 3.10 or later
- A virtual environment is recommended

---

## Create a virtual environment

```bash
python -m venv ~/.venvs/echelle-optics
source ~/.venvs/echelle-optics/bin/activate
```

---

## Install

Clone the repository and install in editable mode with development extras:

```bash
git clone https://github.com/queezz/echelle_optics
cd echelle_optics
pip install -e ".[dev]"
```

To also install documentation dependencies:

```bash
pip install -e ".[docs]"
```

---

## Verify the install

```bash
pytest
```

All tests should pass. The test suite covers grating formulas, order table output,
detector geometry loading, and synthetic image shapes.

---

## Quickstart

### Build an instrument model

```python
from echelle_optics import lhd_cmos_echelle

spec = lhd_cmos_echelle()
```

`lhd_cmos_echelle()` returns an `EchelleSpectrometer` pre-configured for the LHD CMOS
instrument: 46.1 gr/mm, 32° blaze, 304.8 mm focal length, 2560 × 2160 @ 6.5 µm.

### Generate an order table

```python
df = spec.order_table(30, 58)
print(df)
```

Each row covers one diffraction order and includes:

| Column | Description |
|---|---|
| `order` | Diffraction order m |
| `center_wavelength_nm` | Central wavelength \( \lambda_c = K / m \) |
| `free_spectral_range_nm` | FSR = \( \lambda_c / m \) |
| `dispersion_nm_per_px` | Linear dispersion at detector center |
| `detector_span_nm` | Wavelength range covered by detector width |
| `wavelength_min_nm` | Blue edge of order on detector |
| `wavelength_max_nm` | Red edge of order on detector |

### Render a synthetic emission-line image

```python
from echelle_optics import render_echelle_lines, GeometryMode

# Hg/Ar calibration lines (nm)
lines = [404.66, 435.83, 546.07, 579.07, 696.54, 706.72, 750.39, 763.51]

img = render_echelle_lines(
    spec,
    lines,
    geometry_mode=GeometryMode.MEASURED_LHD_CMOS,
    psf_sigma_x_px=1.5,
    psf_sigma_y_px=12.0,
    order_spacing_px=65,
)
```

`img` is a 2560 × 2160 float array. Use matplotlib to display it:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 10))
ax.imshow(img, origin="lower", cmap="gray", vmin=0, vmax=img.max() * 0.5)
plt.tight_layout()
plt.show()
```

---

## Run the example notebooks

```bash
cd examples
jupyter lab
```

Open notebooks in order:

| Notebook | Topic |
|---|---|
| `01_lhd_cmos_order_table.ipynb` | Order table and white-light overview |
| `02_synthetic_lamp_image.ipynb` | Emission-line synthetic image |
| `03_dispersion_intuition.ipynb` | Low-level grating dispersion |
| `04_synthetic_image_parameters.ipynb` | PSF and rendering parameter sweeps |
| `05_detector_geometry.ipynb` | Empirical curved order geometry |

---

## Serve the documentation locally

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000` in your browser.
