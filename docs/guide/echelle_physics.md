# Echelle Physics

This page explains the diffraction physics used in the package. The treatment is
Littrow-approximation only — no full raytrace. The goal is enough physics to build
an order table and compute detector positions.

---

## Grating equation

The grating equation in the general case:

\[
m \lambda = d (\sin\alpha + \sin\beta)
\]

where:

- \(m\) — diffraction order (integer, positive for echelle)
- \(\lambda\) — wavelength (nm)
- \(d\) — groove spacing (nm)
- \(\alpha\) — angle of incidence
- \(\beta\) — angle of diffraction

For the LHD CMOS echelle, the grating is used in near-Littrow configuration.

---

## Littrow approximation

In Littrow geometry \(\alpha \approx \beta \approx \theta_B\) (blaze angle).
This gives the **Littrow constant**:

\[
K = 2 d \sin\theta_B
\]

The central wavelength of order \(m\) is then:

\[
\lambda_c(m) = \frac{K}{m}
\]

For the LHD CMOS echelle (\(d = 1/46.1\) mm = 21,692 nm, \(\theta_B = 32°\)):

\[
K = 2 \times 21692 \times \sin(32°) \approx 23\,003 \text{ nm}
\]

So order 30 centers near 767 nm, order 58 centers near 397 nm.

---

## Groove spacing

```python
from echelle_optics.grating import groove_spacing_nm

d = groove_spacing_nm(46.1)  # → 21 691.97 nm
```

---

## Linear dispersion

The linear dispersion (nm per pixel) at detector center in the Littrow approximation:

\[
\frac{d\lambda}{dp} = \frac{d \cos\beta \cdot p_\text{px}}{m \cdot f}
\]

where \(p_\text{px}\) is the pixel size (µm, converted to mm) and \(f\) is the focal length (mm).

For the LHD CMOS echelle this evaluates to approximately:

\[
\frac{d\lambda}{dp} \approx \frac{0.392}{m} \text{ nm/px}
\]

Higher orders have smaller dispersion per pixel — they pack more wavelength per pixel.

```python
from echelle_optics.grating import linear_dispersion_nm_per_px

d_lambda = linear_dispersion_nm_per_px(
    order=46, grooves_per_mm=46.1, blaze_deg=32.0,
    beta_deg=32.0, focal_length_mm=304.8, pixel_size_um=6.5
)
```

---

## Free spectral range

The FSR sets the wavelength interval over which one order does not overlap the next:

\[
\text{FSR}(m) = \frac{\lambda_c}{m}
\]

Lower orders have larger FSR. The cross-disperser separates orders spatially on the
detector so that each order occupies its own horizontal stripe.

---

## Detector span per order

The detector covers a fixed angular range. The wavelength span of one order on the
detector is:

\[
\Delta\lambda_\text{det} = \frac{d\lambda}{dp} \times W_\text{px}
\]

where \(W_\text{px}\) is the detector width in pixels (2560 for the LHD CMOS). Higher
orders have smaller dispersion, so they cover a narrower wavelength interval — but the
orders are also spaced closer together in wavelength.

---

## Order table

`EchelleSpectrometer.order_table()` computes all of the above for a range of orders and
returns a pandas DataFrame. See the [Order Table example](../examples/order_table.md)
for a full walkthrough.

```python
from echelle_optics import lhd_cmos_echelle

spec = lhd_cmos_echelle()
df = spec.order_table(30, 58)
```

---

## What this package does NOT model

- Blaze efficiency as a function of wavelength
- Cross-disperser (prism or second grating) angular deviation
- Optical aberrations, smile from optics
- Anamorphic magnification
- Slit image width and orientation

The package models **diffraction-order positions and dispersions** only. Detector
geometry (order curvature, y-positions) is handled separately and empirically — see
[Detector Geometry](detector_geometry.md).
