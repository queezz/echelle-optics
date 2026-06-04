# Empirical Wavelength Solutions

`echelle_optics` can use the measured LHD CMOS wavelength lookup table as the
dispersion rule for synthetic images. This is separate from the grating equation:
the grating model remains useful for intuition and rough guesses, while the
empirical solution reflects the observed detector calibration.

---

## What is bundled

The LHD CMOS profile includes:

| File | Meaning |
|---|---|
| `data/pattern_CMOS_20240305.txt` | Measured order-center y positions |
| `data/Th_wavelength_CMOS_20240305.txt` | Curated lamp-line table: order, pixel interval, fitted center, wavelength, species |

The wavelength table uses 0-based order labels from the historical
`echelle_spectra` workflow. `echelle_optics` maps those labels to physical
diffraction orders with:

```python
physical_order = order_idx + 30
```

---

## Loading the solution

```python
from echelle_optics import load_lhd_cmos_wavelength_solution

solution = load_lhd_cmos_wavelength_solution(poly_degree=2)
print(solution.summary())
```

The returned `WavelengthSolution` stores one fitted `OrderWavelengthFit` per order.
Each fit exposes:

- `wavelength_at(x, order)` — evaluate wavelength at detector x pixel
- `pixel_at(wavelength_nm, order)` — invert the fit to predict x pixel
- per-order residual diagnostics through `rms_nm` and `residuals_nm`

---

## Rendering with empirical dispersion

Pass the solution into the synthetic renderer:

```python
from echelle_optics import (
    GeometryMode,
    lhd_cmos_echelle,
    load_lhd_cmos_wavelength_solution,
    render_echelle_lines,
)

spec = lhd_cmos_echelle()
solution = load_lhd_cmos_wavelength_solution()

lines = [
    (650.65281, 1.0),  # Ne I
    (653.28822, 1.0),  # Ne I
    (656.27900, 1.0),  # H-alpha
]

img = render_echelle_lines(
    lines,
    spec,
    orders=solution.order_list(),
    geometry=GeometryMode.MEASURED_LHD_CMOS,
    wavelength_solution=solution,
    psf_sigma_px=1.5,
    psf_sigma_y_px=10.0,
)
```

When `wavelength_solution` covers an order, the renderer uses `pixel_at()` for line
positions and `wavelength_at()` for white-light color. If a wavelength is outside the
empirical range for an order, rendering falls back to the theoretical Littrow
dispersion for that line.

---

## Boundary with echelle_spectra

`echelle_optics` owns the lookup-table data structure and evaluation methods. It does
not fit real lamp frames. The execution workflow belongs in `echelle_spectra`:

1. Load a real lamp frame.
2. Extract order spectra using the measured pattern.
3. Fit line centroids.
4. Select high-quality lines.
5. Fit a correction or produce a new lookup table.

That corrected table can then be loaded by `echelle_optics` as another empirical
solution for validation or synthetic-frame generation.
