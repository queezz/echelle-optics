# examples

Worked Jupyter notebooks for the `echelle_optics` package.
All notebooks use `lhd_cmos_echelle()` as the primary instrument.

| Notebook | Purpose |
|---|---|
| `01_lhd_cmos_order_table.ipynb` | Inspect the predicted order table: central wavelengths, dispersion, FSR, and detector coverage for orders 30–58. |
| `02_synthetic_lamp_image.ipynb` | Render a synthetic detector frame from a small list of visible emission lines (Hg, H, He, Ar). |
| `03_dispersion_intuition.ipynb` | Build intuition for the grating equation: derive the Littrow constant, verify `dλ/dpx ≈ 0.392 / m`, and fit the 1/m scaling. |
| `04_synthetic_image_parameters.ipynb` | Explore how PSF size, order spacing, background, and read noise change the synthetic detector image. |

## Running

```bash
source ~/.venvs/echelle-optics/bin/activate
cd examples
jupyter notebook
```

Or execute all notebooks non-interactively:

```bash
source ~/.venvs/echelle-optics/bin/activate
jupyter nbconvert --to notebook --execute --inplace examples/*.ipynb
```
