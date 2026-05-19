# Future Work

Planned directions for `echelle_optics`, organized by layer. Items marked as
**in scope** belong in this package. Items marked **downstream** belong in
`echelle_spectra` or other packages that consume this one.

---

## Instrument profile system

**Status**: partial — LHD CMOS is the only profile

The current code supports multiple instruments architecturally but has no formal
profile registry. A cleaner system would:

- Define a protocol or base class for instrument profiles
- Bundle each profile's geometry data in a dedicated subfolder under `data/`
- Provide discovery (`list_profiles()`) and selection (`load_profile("lhd_cmos")`)
- Document how to add a new instrument profile

This is the most important structural addition. Every other extension (calibration,
extraction) depends on clean multi-instrument support.

**In scope for `echelle_optics`.**

---

## Multi-date geometry support

**Status**: not started

Currently one calibration date is bundled per instrument. The architecture should
support loading geometry by date or selecting the most recent calibration before a
given observation timestamp.

Planned:
- Multiple `data/pattern_<instrument>_<date>.txt` files per instrument
- `load_geometry(instrument, date=None)` — defaults to most recent
- Geometry drift visualization between two calibration dates

**In scope for `echelle_optics`.**

---

## Wavelength calibration primitives

**Status**: not started

This package should provide the **data structures and mappings** for wavelength
calibration — not the full arc-fitting pipeline. Concretely:

- `WavelengthSolution` — stores per-order polynomial \(\lambda(x)\), residuals,
  fit uncertainty
- `wavelength_at(x, order)` — evaluates the solution at a pixel position
- `pixel_at(wavelength, order)` — inverse mapping
- Support for global 2D solutions \(\lambda(x, y)\) interpolated across orders

The fitting of arc-lamp centroid positions to produce a `WavelengthSolution` is the
responsibility of `echelle_spectra`. The data structures and evaluation methods live here.

**In scope for `echelle_optics`.**

---

## 2D pixel → wavelength mapping

**Status**: not started

The full mapping \((x, y) \rightarrow \lambda\) combines:

- Per-order wavelength solution from `WavelengthSolution`
- Order trace positions from `DetectorGeometry`
- Interpolation between orders for off-trace pixels

This mapping is the key primitive consumed by extraction and calibration validation.

**In scope for `echelle_optics`.**

---

## Synthetic extraction validation

**Status**: partial (renderer exists; extraction not available)

The intended validation loop:

1. Generate a synthetic arc frame with known line positions, PSF, curvature, noise
2. Pass to an extraction pipeline (in `echelle_spectra`)
3. Fit a wavelength solution using the extracted line centroids
4. Compare solution to ground truth
5. Quantify systematics from curvature, PSF shape, background

The synthetic renderer is already capable of step 1. Steps 2–5 require the extraction
and calibration infrastructure.

**Rendering stays in `echelle_optics`; extraction and fitting go in `echelle_spectra`.**

---

## Calibration residual utilities

**Status**: not started

After fitting a wavelength solution, standard diagnostics include:

- 2D residual map across the detector
- Per-order residual vs wavelength
- Residual vs line brightness (blended lines, saturation)
- Drift between two calibration epochs

Lightweight plotting helpers for these diagnostics could live here alongside the
`WavelengthSolution` structures.

**In scope for `echelle_optics`.**

---

## Blaze efficiency model

**Status**: deliberately excluded for now

The Littrow approximation gives equal amplitude to all orders. A realistic blaze
efficiency model would modulate intensities by wavelength distance from the blaze
peak, which matters for:

- Synthetic frame realism (relative line brightnesses)
- Sensitivity calibration support

This could be added as an optional amplitude weight in `render_echelle_lines()` without
touching the existing interface.

**In scope for `echelle_optics`** when needed.

---

## SpectroCube interoperability

**Status**: not started (depends on wavelength calibration)

Once `echelle_spectra` can produce calibrated extracted spectra, those results should be
serialized as [SpectroCube](https://github.com/queezz/spectrocube) files:

- `intensity` — extracted 1D or 2D spectrum
- `wavelength` — coordinate from the wavelength solution
- Required metadata: `instrument_id`, `calibration_type`, `intensity_units`, etc.

`echelle_optics` may provide helpers to construct the metadata block from an instrument
profile. SpectroCube file I/O is handled by the `spectrocube` package.

**Metadata helpers may live here; file production belongs in `echelle_spectra`.**

---

## What should NOT be added to this package

| Item | Where it belongs |
|---|---|
| Arc-line fitting against real detector frames | `echelle_spectra` |
| Spectral extraction (order summing, background subtraction) | `echelle_spectra` |
| Full reduction workflows | `echelle_spectra` |
| GUI or interactive visualization | `spectroview` |
| SpectroCube file read/write | `spectrocube` |
| Full optical raytrace | Out of scope for this ecosystem |
| Hardware / instrument control | Separate instrument software |
