# Example: Dispersion Intuition

**Notebook**: `examples/03_dispersion_intuition.ipynb`

This example uses the low-level `echelle_optics.grating` functions directly, without
constructing a spectrometer object. The goal is to build intuition for what each
formula computes.

---

## Groove spacing and Littrow constant

```python
from echelle_optics.grating import groove_spacing_nm, littrow_constant_nm

d = groove_spacing_nm(46.1)         # → 21 691.97 nm
K = littrow_constant_nm(46.1, 32.0) # → ~23 003 nm
```

The Littrow constant K = 2d sin(θ_B) is the key number for the LHD CMOS echelle.
It sets the wavelength scale for all orders: λ_c(m) = K / m.

---

## Central wavelengths

```python
from echelle_optics.grating import central_wavelength_nm

for m in [30, 40, 46, 58]:
    lam = central_wavelength_nm(m, 46.1, 32.0)
    print(f"order {m}: {lam:.1f} nm")
```

Output:
```
order 30: 766.8 nm
order 40: 575.1 nm
order 46: 500.1 nm
order 58: 396.6 nm
```

---

## Wavelength to fractional order

A given wavelength may appear in multiple orders simultaneously. The "physical order"
at a wavelength is:

```python
from echelle_optics.grating import physical_order_from_wavelength

m_frac = physical_order_from_wavelength(532.0, 46.1, 32.0)
# → ~43.2  (falls near order 43)
```

The integer part is the order in which this wavelength is brightest (assuming flat
blaze profile).

---

## Dispersion scaling

The dispersion follows \(d\lambda/dp \approx 0.392 / m\) nm/px. This is well
approximated as linear in 1/m:

```python
from echelle_optics.grating import linear_dispersion_nm_per_px

orders = range(30, 59)
disp = [
    linear_dispersion_nm_per_px(m, 46.1, 32.0, 32.0, 304.8, 6.5)
    for m in orders
]
```

A linear fit of dispersion vs 1/m passes through the origin with slope ≈ 0.392.
This slope is set by the grating constant K and detector parameters and is fixed
for the instrument.

---

## Key takeaway

The entire dispersion model reduces to two numbers:

- \(K \approx 23\,003\) nm — fixed by grating and blaze angle
- Pixel scale — fixed by focal length and pixel size

Everything else (per-order wavelength, dispersion, FSR, span) follows from these
two numbers and the order index.
