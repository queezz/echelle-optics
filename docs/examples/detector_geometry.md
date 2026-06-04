# Example: Detector Geometry

**Notebook**: `examples/05_detector_geometry.ipynb`

This example loads the empirical order curvature data for the LHD CMOS detector,
fits polynomial traces to each order, examines residuals, and compares straight vs
curved synthetic white-light images.

---

## Background

Real echelle orders on the LHD CMOS detector are not straight horizontal lines.
They curve by several pixels across the detector width. This curvature must be
accounted for in spectral extraction and wavelength calibration.

The pattern file `data/pattern_CMOS_20240305.txt` contains measured y-positions of
each order center at every x pixel, captured on 2024-03-05.

---

## Loading the raw pattern

```python
from echelle_optics.geometry import load_lhd_cmos_pattern

pattern = load_lhd_cmos_pattern()
# pattern.shape == (2560, 29)  — rows: x pixels, columns: orders 30–58
```

Plotting the raw data shows the measured integer y-position for each order.
The values are integers because they come from a peak-finding step applied to
a calibration frame.

---

## Fitting polynomial traces

```python
from echelle_optics.geometry import load_lhd_cmos_geometry

geo = load_lhd_cmos_geometry()
```

`load_lhd_cmos_geometry()` calls `fit_order_traces()` internally with degree 2
(quadratic). Each order gets an `OrderTrace` with:

- `coefficients`: \([c_0, c_1, c_2]\) in normalized x ∈ [−1, 1]
- `y_at(x)`: evaluates the polynomial at a given x pixel
- `residuals`: fit residuals in pixels

### Example: inspect order 46

```python
trace = geo.trace_for_order(46)

print(trace.coefficients)
# e.g. [1083.4, 3.2, -8.7]  — c0 is center y, c1 is tilt, c2 is curvature

print(trace.residuals.max())
# typically < 1 pixel
```

---

## Curvature magnitude

The curvature \(c_2\) quantifies how many pixels the order bends from center to edge.
The total deflection across the detector width is approximately:

\[
\Delta y = c_2 \times \left(1 - (-1)\right)^2 / 4 \approx c_2
\]

For the LHD CMOS, \(|c_2|\) is typically 5–15 px depending on the order.

Plotting \(\Delta y(x) = y(x) - y(1280)\) shows the curvature shape as a deviation
from the center. The orders bow downward or upward symmetrically, consistent with
a cross-disperser introducing a quadratic distortion.

---

## Side-by-side comparison

The notebook renders white-light images in both geometry modes and displays them
side by side:

```python
from echelle_optics import GeometryMode, render_white_light

img_ideal = render_white_light(
    spec,
    orders=range(30, 59),
    geometry=GeometryMode.IDEAL_STRAIGHT,
    order_spacing_px=65,
)

img_curved = render_white_light(
    spec,
    orders=range(30, 59),
    geometry=GeometryMode.MEASURED_LHD_CMOS,
)
```

In the ideal image, all orders appear as perfectly straight horizontal bands.
In the curved image, the same orders follow their measured polynomial traces.
The difference is visually obvious in a zoomed-in view of any single order.

---

## Polynomial coefficients table

The notebook prints the coefficients for all orders:

```python
for order in range(30, 59):
    trace = geo.trace_for_order(order)
    c0, c1, c2 = trace.coefficients
    print(f"order {order}: y0={c0:.1f}, tilt={c1:.2f}, curve={c2:.2f}")
```

`c0` increases roughly linearly with order index (orders are stacked vertically).
`c1` (tilt) is small but nonzero. `c2` (curvature) is the physically interesting term.

---

## Key takeaways

- All 29 orders (30–58) have measurable curvature — none are truly straight
- Quadratic fits capture the shape with sub-pixel residuals
- The curvature varies smoothly across order index
- The calibration file must be re-measured if the detector is repositioned or
  if the instrument is reconfigured

For more on how this geometry feeds into the renderer, see
[Synthetic Images](../guide/synthetic_images.md) and
[Detector Geometry](../guide/detector_geometry.md).
