"""Simple wavelength-to-RGB mapping for synthetic spectral images.

Uses a piecewise linear approximation of the CIE visible spectrum.
Output is linear (not gamma-corrected) float RGB in [0, 1].
"""

__all__ = ["wavelength_to_rgb"]


def wavelength_to_rgb(lambda_nm: float) -> tuple[float, float, float]:
    """Return an approximate (R, G, B) colour for a visible wavelength.

    Parameters
    ----------
    lambda_nm:
        Wavelength in nanometres.  Values outside 380–780 nm return black.

    Returns
    -------
    (R, G, B) each in [0.0, 1.0], linear (no gamma correction).
    """
    lam = float(lambda_nm)

    if lam < 380.0 or lam > 780.0:
        return (0.0, 0.0, 0.0)

    # Piecewise linear approximation
    if lam < 440.0:
        r = -(lam - 440.0) / (440.0 - 380.0)
        g = 0.0
        b = 1.0
    elif lam < 490.0:
        r = 0.0
        g = (lam - 440.0) / (490.0 - 440.0)
        b = 1.0
    elif lam < 510.0:
        r = 0.0
        g = 1.0
        b = -(lam - 510.0) / (510.0 - 490.0)
    elif lam < 580.0:
        r = (lam - 510.0) / (580.0 - 510.0)
        g = 1.0
        b = 0.0
    elif lam < 645.0:
        r = 1.0
        g = -(lam - 645.0) / (645.0 - 580.0)
        b = 0.0
    else:
        r = 1.0
        g = 0.0
        b = 0.0

    # Intensity roll-off at spectral limits
    if lam < 420.0:
        factor = 0.3 + 0.7 * (lam - 380.0) / (420.0 - 380.0)
    elif lam > 700.0:
        factor = 0.3 + 0.7 * (780.0 - lam) / (780.0 - 700.0)
    else:
        factor = 1.0

    return (r * factor, g * factor, b * factor)
