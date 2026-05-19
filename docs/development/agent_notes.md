# Agent Notes

This page is written for future contributors and AI coding agents working on
`echelle_optics`. Read it before making structural changes.

---

## Repository purpose

`echelle_optics` is a **reusable toolkit for cross-dispersed echelle spectrometer
modeling and calibration support**. It provides:

1. Echelle diffraction physics (Littrow approximation, dispersion, FSR, order tables)
2. Instrument profile system — interchangeable geometry and calibration datasets per instrument
3. Detector geometry layer — empirical order traces, polynomial fits, curvature characterization
4. Wavelength calibration primitives — mappings between pixel space and wavelength space
5. Synthetic detector image generation — for algorithm development and calibration validation

**LHD CMOS** (Newport 46.1 gr/mm, Andor Zyla 4.2, f = 304.8 mm) is the first implemented
instrument profile. It is not the permanent target — the architecture is designed for
multiple instruments sharing the same physics and rendering layers.

See [Ecosystem](ecosystem.md) for how this package relates to `echelle_spectra`,
`spectrocube`, and `spectroview`.

---

## What this is NOT

| Out of scope | Reason |
|---|---|
| Full optical raytrace | Not Zemax, not OSLO — physics is Littrow approximation only |
| Spectral extraction pipelines | Summing counts along order traces belongs in `echelle_spectra` |
| Production calibration execution | Full arc-fitting workflows belong in `echelle_spectra` |
| Real-time instrument control | Hardware layer is entirely separate |
| Flux / throughput model | No blaze efficiency, QE, or atmospheric transmission |

**Wavelength calibration primitives are in scope.** This includes: pixel→wavelength
mappings, arc-line position models, residual structures, and the abstractions that
extraction pipelines consume. What belongs in `echelle_spectra` is the execution of
those pipelines against real detector frames.

---

## Instrument profile concept

The package is profile-driven. An instrument profile is the combination of:

- A configured `EchelleSpectrometer` (grating, detector, focal length, beta angle)
- A `DetectorGeometry` — empirical order traces from a calibration measurement
- Optionally: a wavelength solution (future)

The LHD CMOS profile is accessed via `lhd_cmos_echelle()` and
`load_lhd_cmos_geometry()`. A different instrument would provide its own factory
functions and calibration data, reusing all the same physics and rendering code.

**Do not hardcode LHD CMOS assumptions into shared modules.** Any parameter that
differs across instruments (groove count, pixel size, focal length, calibration file)
must be passed as an argument, not embedded as a constant.

---

## Architectural boundaries — do not cross

### Physics is separate from geometry

`grating.py` and `spectrometer.py` model diffraction physics. They answer:
*"What wavelength does order m cover, and at what dispersion?"*

`geometry.py` models detector-space positions. It answers:
*"At x pixel p, what y pixel does order m lie on?"*

**Do not add pixel y-positions or curvature logic to `EchelleSpectrometer`.**
**Do not add wavelength or dispersion logic to `DetectorGeometry`.**

The only place both are combined is `synthetic.py` (rendering) and, in the future,
a calibration mapping module.

### Geometry is empirical

Order traces come from measured calibration data, not from computed optics.
The polynomial fit in `geometry.py` is a smoothing step, not a physical model.

**Do not replace bundled calibration files with computed approximations.**
The real instrument curvature cannot be predicted from the grating equation. If a new
instrument is added, provide its own measured calibration data.

**Do not hardcode a single calibration date.** The data file is named
`pattern_CMOS_20240305.txt` — the date is part of the filename because geometry drifts
over time. Future architecture should support multiple calibration dates per instrument.

### Synthetic rendering does not fit calibrations

`synthetic.py` generates 2D images. It does not identify lines, optimize solutions,
or fit polynomials to real frame data. That logic belongs in `echelle_spectra` or in
a future `calibration.py` module inside this package.

**Do not add arc-line fitting or detector optimization to `synthetic.py`.**

### `IDEAL_STRAIGHT` is for testing

Straight orders are not the physical reality. `GeometryMode.IDEAL_STRAIGHT` exists to
isolate the dispersion model in tests and parameter sweeps. Never use it as a default
in production analysis and never silently fall back to it.

---

## Module responsibilities

| Module | Does | Does NOT |
|---|---|---|
| `grating.py` | Diffraction math, Littrow, FSR, dispersion | Pixel positions, curvature |
| `detector.py` | Pixel count, pixel size, mm dimensions | Wavelengths, geometry |
| `spectrometer.py` | Instrument model, order table, instrument factories | Geometry, rendering, calibration |
| `geometry.py` | Load calibration pattern, fit traces, `y_at(order, x)` | Wavelengths, rendering |
| `synthetic.py` | Combine physics + geometry into 2D images | Physics derivations, calibration fitting |
| `color.py` | Wavelength → linear RGB for display | Anything else |

---

## Data flow

### Synthetic emission-line rendering

```
lines (nm)
    → physical_order_from_wavelength()           [grating.py]
    → wavelength → x pixel (dispersion)          [spectrometer.py]
    → (order, x) → y pixel                       [geometry.py]
    → Gaussian PSF at (x, y)                     [synthetic.py]
    → 2D float array (H × W)
```

### Intended calibration flow (partially future)

```
arc frame (real detector image)           [echelle_spectra]
    → line centroid detection             [echelle_spectra]
    → (order, x, y) centroids
    → match to line list                  [calibration module, future]
    → fit wavelength solution             [calibration module, future]
    → wavelength_at(x, order) callable    [echelle_optics, future]
    → SpectroCube output                  [echelle_spectra → spectrocube]
```

---

## Bundled calibration data

`src/echelle_optics/data/pattern_CMOS_20240305.txt`

- Shape: 2560 rows × 29 columns
- Rows: x pixel (0–2559)
- Columns: diffraction orders 30–58
- Values: integer y pixel of the order center
- Date: 2024-03-05
- Instrument: LHD CMOS echelle (Andor Zyla 4.2, Newport 46.1 gr/mm)

If the instrument is realigned or the detector is moved, measure a new calibration frame
and add a new data file. Do not overwrite the existing file — old files document the
instrument history and are needed for reprocessing older observations.

---

## Testing

```
tests/
├── test_hello.py       ← grating formulas, order table, color, synthetic render shapes
└── test_geometry.py    ← pattern load (2560×29), fit residuals < 1 px, curved ≠ ideal
```

When adding new modules, add corresponding tests. Tests are the minimal guarantee that
the physics and geometry layers have not been silently broken.

---

## Style conventions

- Line length: 100 characters (`black`, `ruff`)
- Docstring style: NumPy format
- Type annotations on all public functions
- Physical units in variable names or docstrings: nm, px, mm, degrees
- No non-standard abbreviations in public API names (`px` is fine, `sg` is not)
- Instrument-specific factory functions are named `<instrument_id>_echelle()` or
  `load_<instrument_id>_geometry()` — follow the LHD CMOS pattern for new instruments

---

## Allowed future growth inside this package

The following additions are **in scope** for `echelle_optics`:

- Additional instrument profiles (new factory functions + calibration data)
- Wavelength calibration primitives: pixel→wavelength mapping structures,
  polynomial wavelength solutions, residual containers
- Multi-date geometry support: loading and selecting calibration by date
- Improved synthetic rendering: blaze efficiency weighting, realistic noise models
- Calibration validation utilities: comparing synthetic vs real arc positions

The following must remain **outside this package**:

- Full extraction pipelines → `echelle_spectra`
- Production calibration execution against real frames → `echelle_spectra`
- SpectroCube file production → `echelle_spectra` (consumes this package's outputs)
- GUI or interactive visualization → `spectroview`
