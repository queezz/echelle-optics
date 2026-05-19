# echelle_optics

**echelle_optics** is a lightweight Python toolkit for cross-dispersed echelle spectrometer
modeling. It covers diffraction physics, order tables, empirical detector geometry, and
synthetic image generation.

The primary target instrument is the **LHD CMOS echelle**: Newport 46.1 gr/mm grating
(32° blaze), Andor Zyla 4.2 sCMOS detector (2560 × 2160 px, 6.5 µm pixel), 304.8 mm
focal length.

---

## Package scope

This package contains:

- Grating dispersion math (Littrow approximation, FSR, linear dispersion)
- Instrument model and per-order tables as pandas DataFrames
- Empirical curved order traces from real detector calibration data
- Synthetic 2D echellogram renderer (emission lines + white-light continuum)
- Wavelength-to-RGB helper for display

This package intentionally does **not** contain:

- Full optical raytrace or Zemax-style simulation
- Wavelength calibration (fitting arc lines to pixel positions)
- Spectral extraction from real frames
- Instrument control or data acquisition

---

## Design philosophy

The repository keeps four concerns strictly separated:

| Layer | What it models |
|---|---|
| **Spectral physics** | Grating equation, order wavelengths, dispersion |
| **Detector geometry** | Empirical curved order positions on the chip |
| **Synthetic rendering** | 2D image generation consuming both layers above |
| **Wavelength calibration** | Not yet implemented — intentionally a separate layer |

See [Architecture](guide/architecture.md) for the module dependency diagram.

---

## Navigation

- [Getting Started](guide/getting_started.md) — install, quickstart
- [Echelle Physics](guide/echelle_physics.md) — grating equation and order tables
- [Detector Geometry](guide/detector_geometry.md) — empirical curved order traces
- [Synthetic Images](guide/synthetic_images.md) — rendering emission lines and continua
- [Architecture](guide/architecture.md) — module map and data flow
- [Examples](examples/index.md) — annotated notebook walkthroughs
- [Development / Agent Notes](development/agent_notes.md) — design rationale for contributors and future agents
- [API Reference](reference.md) — auto-generated from docstrings
