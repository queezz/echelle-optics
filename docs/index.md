# echelle_optics

**echelle_optics** is a lightweight Python toolkit for cross-dispersed echelle spectrometer
modeling. It covers diffraction physics, order tables, empirical detector geometry, and
synthetic image generation.

The package is designed for multiple instruments through an interchangeable profile
system. **LHD CMOS** (Newport 46.1 gr/mm, Andor Zyla 4.2 sCMOS, 304.8 mm) is the
first implemented profile.

---

## Package scope

This package contains:

- Grating dispersion math (Littrow approximation, FSR, linear dispersion)
- Instrument model and per-order tables as pandas DataFrames
- Empirical curved order traces from real detector calibration data
- Empirical wavelength lookup-table primitives for pixel-to-wavelength mapping
- Synthetic 2D echellogram renderer (emission lines + white-light continuum)
- Wavelength-to-RGB helper for display

This package intentionally does **not** contain:

- Full optical raytrace or Zemax-style simulation
- Production wavelength-calibration execution against real lamp frames
- Spectral extraction from real frames
- Instrument control or data acquisition

---

## Design philosophy

The repository keeps five concerns strictly separated:

| Layer | What it models |
|---|---|
| **Spectral physics** | Grating equation, order wavelengths, dispersion |
| **Detector geometry** | Empirical curved order positions — per instrument profile |
| **Synthetic rendering** | 2D image generation consuming physics + geometry |
| **Wavelength calibration primitives** | Pixel→wavelength lookup structures and residuals |
| **Pipeline execution** | Arc fitting, extraction, SpectroCube production → `echelle_spectra` |

See [Architecture](guide/architecture.md) for the module dependency diagram and
[Ecosystem](development/ecosystem.md) for how this package relates to `echelle_spectra`,
`spectrocube`, and `spectroview`.

---

## Navigation

- [Getting Started](guide/getting_started.md) — install, quickstart
- [Echelle Physics](guide/echelle_physics.md) — grating equation and order tables
- [Detector Geometry](guide/detector_geometry.md) — empirical curved order traces
- [Empirical Wavelengths](guide/empirical_wavelengths.md) — lookup-table dispersion
- [Synthetic Images](guide/synthetic_images.md) — rendering emission lines and continua
- [Architecture](guide/architecture.md) — module map and data flow
- [Examples](examples/index.md) — annotated notebook walkthroughs
- [Agent Notes](development/agent_notes.md) — design rationale for contributors and future agents
- [Ecosystem](development/ecosystem.md) — how this package relates to the rest of the stack
- [API Reference](reference.md) — auto-generated from docstrings
