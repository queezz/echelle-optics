# Detector Geometry

This page explains how order positions on the detector are handled in the package,
and why the approach is empirical rather than derived from optics.

---

## Why orders curve

In an ideal echelle with perfect on-axis geometry, diffraction orders appear as
**straight horizontal stripes** on the detector. In practice, real instruments produce
**curved orders** — a phenomenon sometimes called "smile" or "order curvature".

Curvature arises from a combination of:

- The cross-disperser introducing oblique illumination
- Anamorphic effects and off-axis aberrations in the camera optics
- Physical tilt of the detector relative to the focal plane

For the LHD CMOS echelle, the curvature is **measurable and reproducible**. It is
characterized empirically from calibration exposures (typically a white-light flat or
arc lamp image) rather than computed from a raytrace.

!!! note
    The package does not attempt to model smile from first principles. The curvature
    data bundled in `data/pattern_CMOS_20240305.txt` was measured on the actual
    instrument on 2024-03-05.

---

## The calibration pattern file

The file `src/echelle_optics/data/pattern_CMOS_20240305.txt` contains the measured
center-of-order y-positions across the detector:

- Shape: 2560 rows × 29 columns
- Rows: x pixel coordinate (0 … 2559)
- Columns: diffraction orders 30 … 58
- Values: integer y pixel of the order center at that x position

This table is the ground truth for the LHD CMOS detector geometry. It was extracted
from a real calibration frame.

---

## GeometryMode

The package exposes two geometry modes via the `GeometryMode` enum:

| Mode | Behavior |
|---|---|
| `IDEAL_STRAIGHT` | Orders are placed at evenly-spaced constant y positions. No curvature. |
| `MEASURED_LHD_CMOS` | Order y-positions are loaded from the calibration pattern file and fit with polynomials. |

`IDEAL_STRAIGHT` is useful for testing, parameter sweeps, and understanding the
dispersion model in isolation. `MEASURED_LHD_CMOS` produces realistic detector images.

---

## Polynomial fits to order traces

Loading the raw integer y-positions directly would be noisy. Instead, the package fits
a **quadratic polynomial** to each order trace using `numpy.polyfit` on normalized
x-coordinates \( x' \in [-1, 1] \):

\[
y(x') = c_0 + c_1 x' + c_2 x'^2
\]

The `OrderTrace` object stores the coefficients and provides a `y_at(x)` method.
Residuals are typically sub-pixel.

```python
from echelle_optics import load_lhd_cmos_geometry

geo = load_lhd_cmos_geometry()

# y position of order 46 at x=1280 (detector center)
y = geo.y_at(46, 1280)
```

---

## Curvature magnitude

The curvature is small but not negligible. Across the full detector width (2560 px),
the center-to-edge vertical displacement is typically **5–15 pixels**, depending on
the order. This is significant relative to the order width and matters for:

- Synthetic image realism
- Spectral extraction (must trace the curved order)
- Wavelength calibration (arc line positions shift with y)

---

## DetectorGeometry API

```python
from echelle_optics.geometry import load_lhd_cmos_geometry, GeometryMode

geo = load_lhd_cmos_geometry()          # loads pattern, fits polynomials
trace = geo.trace_for_order(46)         # OrderTrace for order 46
y_center = trace.y_at(1280)             # y at x=1280
coeffs = trace.coefficients             # [c0, c1, c2]
residuals = trace.residuals             # array of fit residuals
```

---

## Relationship to the rest of the package

The geometry layer is **independent of spectral physics**. It only answers: "at x pixel
\(p\), what y pixel does order \(m\) lie on?"

The synthetic renderer (`synthetic.py`) consumes both:

- x-positions from grating dispersion (wavelength → x pixel)
- y-positions from detector geometry (order + x → y pixel)

These two inputs are kept separate by design. Mixing them would make the architecture
harder to extend when real wavelength calibration is added.

See [Architecture](architecture.md) for the full data-flow diagram.

---

## Replacing the geometry for a different instrument

To use the package with a different echelle instrument, implement a new
`DetectorGeometry` by providing your own calibration pattern and calling
`fit_order_traces()`. The `synthetic.py` renderer accepts any `DetectorGeometry`
object, so no changes to the rendering code are needed.
