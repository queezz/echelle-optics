# Future Work

This page documents planned directions for `echelle_optics`. Items are organized by
the layer they would add or extend.

Each item should remain **separate from the existing four layers** (physics, geometry,
rendering, color). New capabilities should be implemented as new modules or packages
that consume the existing API.

---

## Wavelength calibration

**Status**: not started

The most natural next layer. Given a set of arc-lamp line positions (measured in pixel
coordinates from a real frame) and the theoretical wavelength of each line, fit a
wavelength solution — typically a polynomial per order.

Planned scope:

- Accept detected line centroids (x, order) from a real frame
- Accept theoretical wavelengths from a line list
- Fit a polynomial \(\lambda(x, m)\) per order
- Return residuals and uncertainty estimates
- Expose a `wavelength_at(x, order)` callable

This module would import `EchelleSpectrometer` for initial guesses but would be
independent of `geometry.py` and `synthetic.py`.

**What NOT to do**: do not add line-fitting code to `spectrometer.py` or
`synthetic.py`. Calibration is a separate concern.

---

## Detector + wavelength mapping

**Status**: not started

A combined mapping \((x, y) \rightarrow \lambda\) that uses both the order
dispersion and the geometry traces. This is the full 2D pixel-to-wavelength solution.

Requires:
- Wavelength calibration (per-order 1D solution)
- Detector geometry (order trace y positions)
- Interpolation between orders

This mapping would be the key output consumed by extraction pipelines.

---

## Spectral extraction

**Status**: not started, out of scope for this package

Extracting a 1D spectrum from a 2D echellogram means:
- Tracing the order center using geometry
- Summing (or optimal-weighting) pixels across the order profile
- Subtracting inter-order background

This is a full pipeline step and should live in a separate package. It would
consume `DetectorGeometry` for the trace and the wavelength solution for calibration.

---

## Synthetic lamp generation for extraction validation

**Status**: partial (line renderer exists, extraction not yet available)

The current synthetic renderer produces realistic images. Once an extraction pipeline
exists, synthetic frames can validate it end-to-end:

1. Generate a synthetic frame with known line positions and intensities
2. Run extraction
3. Compare extracted vs input wavelengths and intensities
4. Quantify systematics from curvature, PSF shape, background

This validation loop is a key intended use of `render_echelle_lines()`.

---

## Calibration residual analysis

**Status**: not started

After fitting a wavelength solution, visualizing residuals is important:

- Residual map across the detector (2D)
- Per-order residual vs wavelength
- Residual vs line intensity (blended lines)
- Drift tracking across multiple calibration frames

This would be a visualization/reporting utility consuming the calibration output.

---

## SpectroCube interoperability

**Status**: not started

The [`spectrocube`](https://github.com/queezz/spectrocube) package defines a standard
for calibrated spectroscopic datasets. Once wavelength calibration is available,
`echelle_optics` should be able to produce `SpectroCube` objects from extracted,
wavelength-calibrated spectra.

The output would be a `SpectroCube` with:
- `intensity` array (wavelength dimension from the order extraction)
- `wavelength` coordinate from the calibration solution
- Required metadata: `instrument_id = "lhd_cmos_echelle"`, `calibration_type`, etc.

This connects `echelle_optics` to the broader analysis ecosystem.

---

## Multi-calibration-date geometry

**Status**: not started

Currently only one calibration date is bundled (`20240305`). Future work could:

- Store multiple pattern files with different dates
- Track which pattern was current for a given observation date
- Detect geometric drift between calibration dates

---

## Improved blaze efficiency model

**Status**: deliberately excluded for now

The Littrow approximation gives equal intensity to all orders. A realistic blaze
efficiency model would modulate line intensities by wavelength distance from the
blaze peak. This is not needed for the current use cases (geometry and calibration
support) but could be added as an optional amplitude weight in `render_echelle_lines()`.

---

## What should NOT be added here

- Full optical raytrace
- Cross-disperser modeling
- PSF from wavefront error
- Multi-fiber or multi-slit support
- Real-time instrument control

These belong in dedicated instrument software, not in a geometry and calibration
support toolkit.
