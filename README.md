# echelle_optics

Lightweight Python toolkit for cross-dispersed echelle spectrometer modeling.
Covers dispersion calculations, order tables, empirical detector geometry, and synthetic detector images.

Primary target: **LHD CMOS echelle** — Newport 46.1 gr/mm, Andor Zyla 4.2 sCMOS, f = 304.8 mm.

**[Documentation](https://queezz.github.io/echelle-optics)**

---

## Virtual environment


```bash
python -m venv ~/.venvs/echelle-optics
source ~/.venvs/echelle-optics/bin/activate
```


```powershell
python -m venv $HOME\.venvs\echelle-optics
$HOME\.venvs\echelle-optics\Scripts\Activate.ps1
```

---

## Install

```bash
pip install -e ".[dev]"
pytest
```