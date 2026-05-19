# Example: Order Table

**Notebook**: `examples/01_lhd_cmos_order_table.ipynb`

This example builds the per-order table for the LHD CMOS echelle, plots four key
physical quantities as a function of order, and renders a white-light overview image.

---

## Instrument setup

```python
from echelle_optics import lhd_cmos_echelle

spec = lhd_cmos_echelle()
```

`lhd_cmos_echelle()` instantiates `EchelleSpectrometer` with:

| Parameter | Value |
|---|---|
| Grooves per mm | 46.1 |
| Blaze angle | 32° |
| Focal length | 304.8 mm |
| Detector | 2560 × 2160 px @ 6.5 µm |

---

## Generating the order table

```python
df = spec.order_table(30, 58)
```

The DataFrame has one row per diffraction order. Key columns:

| Column | Description |
|---|---|
| `order` | Order index m |
| `center_wavelength_nm` | \(\lambda_c = K/m\) |
| `free_spectral_range_nm` | \(\text{FSR} = \lambda_c / m\) |
| `dispersion_nm_per_px` | \(d\lambda/dp \approx 0.392/m\) |
| `detector_span_nm` | \(\Delta\lambda = (d\lambda/dp) \times 2560\) |
| `wavelength_min_nm` | Blue edge of order |
| `wavelength_max_nm` | Red edge of order |

---

## Key physics from the plots

**Central wavelength vs order**: decreases monotonically from ~767 nm (order 30) to
~397 nm (order 58). The Littrow constant K ≈ 23,003 nm is fixed; increasing order
index selects shorter wavelengths.

**Dispersion (nm/px) vs order**: also decreases with order, following \(0.392/m\).
Order 30 has ~13 pm/px; order 58 has ~6.8 pm/px. Higher orders are more
wavelength-compressed per pixel.

**Detector span (nm) vs order**: higher orders span fewer nm. Order 30 covers ~34 nm;
order 58 covers ~17 nm per detector width.

**FSR vs order**: similar trend. Lower orders have larger FSR and wider inter-order gaps
in wavelength space.

---

## White-light overview

```python
from echelle_optics import render_white_light, GeometryMode

img = render_white_light(
    spec,
    order_min=30, order_max=58,
    geometry_mode=GeometryMode.IDEAL_STRAIGHT,
    order_spacing_px=65,
    order_width_px=20,
)
```

This produces an RGB image where each order appears as a horizontal stripe colored
by the wavelength at each x position. Orders appear from red at the bottom (low m)
to blue at the top (high m).

---

## Physics summary

From the notebook's closing notes:

- The relation \(K = 2d\sin\theta_B\) fixes the product \(m\lambda\) for all orders
- Dispersion is \(\approx 0.392/m\) nm/px across all orders
- Red orders (low m) have larger wavelength span and FSR
- Blue orders (high m) are more densely packed in wavelength

These relationships are the foundation for everything else in the package.
