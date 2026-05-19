# Agent Notes

This page is written for future contributors and AI coding agents working on
`echelle_optics`. It explains the design rationale, what the repository is for,
and what must not be changed without good reason.

---

## Repository purpose

`echelle_optics` is a **calibration support and geometry modeling toolkit** for a
specific cross-dispersed echelle spectrometer at LHD (Large Helical Device). It is
not a general-purpose optics simulator.

The primary use cases are:

1. Computing per-order wavelength ranges and dispersions
2. Characterizing empirical detector geometry (order curvature)
3. Generating synthetic detector images for algorithm development and validation
4. Serving as a dependency for future wavelength calibration and extraction tools

---

## What this is NOT

Do not let scope creep turn this into any of the following:

- A full optical raytrace (not Zemax, not OSLO, not ray-by-ray)
- A wavelength calibration solver (fitting arc lines to pixel positions — separate concern)
- A spectral extraction pipeline (summing counts along orders — separate concern)
- A general echelle package for arbitrary instruments (LHD CMOS is the target)
- A photometric simulator (no blaze efficiency, no throughput curves, no QE)

These are intentionally out of scope. If a future agent or contributor is tempted
to add them here, they should instead create a separate package that **consumes**
`echelle_optics` outputs.

---

## Architectural boundaries — do not cross

### 1. Physics is separate from geometry

`spectrometer.py` and `grating.py` model diffraction physics. They do not know
about pixel y-positions or order curvature. `geometry.py` knows about pixel positions
but not about wavelengths or dispersions.

**Do not add curvature logic to `EchelleSpectrometer`.**
**Do not add grating equations to `DetectorGeometry`.**

The only place these two layers are combined is `synthetic.py`.

### 2. Geometry is empirical

The order traces in `geometry.py` come from a measured calibration file, not from
any physical model. The polynomial fit is a smoothing step, not a physical derivation.

**Do not replace the calibration file with a computed approximation.**
The real instrument has curvature that cannot be predicted from the grating equation
alone. If you need to model a different instrument, provide its own calibration data.

### 3. Rendering does not compute calibration

`synthetic.py` generates images. It does not fit wavelength solutions, identify lines,
or optimize detector parameters. Future wavelength calibration code should:

- Accept a `DetectorGeometry` and an `EchelleSpectrometer` as inputs
- Fit arc-line positions independently
- Live in a separate module or package

**Do not add calibration fitting to `synthetic.py`.**

### 4. `GeometryMode.IDEAL_STRAIGHT` is for testing only

Straight orders are not the physical reality. `IDEAL_STRAIGHT` exists to:

- Simplify tests that do not need curvature
- Isolate the dispersion model from geometry effects

Do not use `IDEAL_STRAIGHT` as a default in any production analysis. Do not silently
fall back to it.

---

## Module responsibilities (quick reference)

| Module | Does | Does NOT |
|---|---|---|
| `grating.py` | Diffraction math, Littrow, FSR | Pixel positions, geometry |
| `detector.py` | Pixel count, pixel size, mm dimensions | Wavelengths, curvature |
| `spectrometer.py` | Instrument model, order table DataFrame | Geometry, rendering |
| `geometry.py` | Load calibration pattern, fit + evaluate traces | Wavelengths, rendering |
| `synthetic.py` | Combine physics + geometry into 2D images | Physics derivations, calibration |
| `color.py` | Wavelength → RGB | Anything else |

---

## Data flow

```
lines (nm)
    → physical_order_from_wavelength()           [grating.py]
    → wavelength → x pixel (dispersion)          [spectrometer.py]
    → (order, x) → y pixel                       [geometry.py]
    → 2D Gaussian PSF at (x, y)                  [synthetic.py]
    → float array (H × W)
```

This pipeline should remain linear and unidirectional. Do not introduce feedback
loops or circular imports.

---

## Bundled calibration data

`src/echelle_optics/data/pattern_CMOS_20240305.txt`

- 2560 rows × 29 columns
- Rows = x pixel (0–2559), Columns = diffraction orders 30–58
- Values = integer y pixel of the order center
- Date: 2024-03-05
- Instrument: LHD CMOS echelle (Andor Zyla 4.2, Newport 46.1 gr/mm)

If the instrument is realigned or the detector is moved, a new calibration frame must
be measured and this file must be updated. Do not attempt to compute a substitute
from the grating equation.

---

## Testing

Tests live in `tests/`. Key coverage:

- `test_hello.py`: grating formulas, order table, color, synthetic render shapes
- `test_geometry.py`: pattern load shape (2560×29), fit residuals < 1 px,
  curved vs ideal rendering are different

When adding new modules, add corresponding tests. The tests are the minimal guarantee
that the physics formulas and geometry loading have not been broken.

---

## Style conventions

- Line length: 100 characters (black/ruff)
- Docstring style: NumPy format
- Type annotations: present on public functions
- Physical units in variable names or docstrings (nm, px, mm, degrees)
- No abbreviations in public API names that are not standard (e.g. `px` is fine, `sg` is not)

---

## Planned future additions

See [Future Work](future_work.md) for the roadmap. The highest-priority items are:

1. Wavelength calibration module (arc line → pixel, polynomial fit, residual analysis)
2. Spectrocube interoperability (output calibrated spectra as `SpectroCube` objects)
3. Improved synthetic generation for extraction validation

None of these should be merged into the existing four layers. Each is a new layer
on top.
