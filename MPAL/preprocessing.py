import numpy as np
from numpy.matlib import repmat
from scipy.signal import savgol_filter


# Smooth curve using a Savitzky–Golay filter
def _smooth(px, py, pz, smooth_order=2, smooth_window=7):
    x = savgol_filter(px, smooth_window, smooth_order)
    y = savgol_filter(py, smooth_window, smooth_order)
    z = savgol_filter(pz, smooth_window, smooth_order)
    return np.array([x, y, z]).T


# Redistribute points evenly over a curve with arc-length of t cm
# Original MATLAB code translated from https://www.mathworks.com/matlabcentral/fileexchange/34874-interparc
# by John D'Errico
def _interparc(t, px, py, pz):
    t = np.linspace(0, 1, t)
    nt = len(t)
    n = len(px)
    pxyz = np.array([px, py, pz]).T

    pt = np.empty((nt, 3), dtype=float)
    chordlen = np.sqrt(np.sum(np.power(np.diff(pxyz.T), 2), axis=0))
    chordlen = chordlen / np.sum(chordlen)
    cumarc = np.insert(np.cumsum(chordlen), 0, 0)

    tbins = np.digitize(t, cumarc)
    tbins[tbins <= 0] = 1
    tbins[t <= 0] = 1
    tbins[tbins >= n] = n - 1
    tbins[t >= 1] = n - 1
    tbins = tbins - 1

    s = np.divide(t - cumarc[tbins], chordlen[tbins])

    pt = pxyz[tbins, :] + np.multiply(pxyz[tbins + 1, :] - pxyz[tbins, :], repmat(s, 3, 1).T)

    return pt


# Main preprocessing function
# Run smoothing and interpolating function depending on the boolean settings
# Return idx as the lookup table of pre-processed and post-processed time information
def preprocess(x, y, z, smooth=False, smooth_order=2, smooth_window=7, interpolate=False, interdist=0.5):
    idx = np.arange(0, len(x))
    X = np.array([x, y, z]).T

    if smooth:
        X = _smooth(X[:, 0], X[:, 1], X[:, 2], smooth_order=smooth_order, smooth_window=smooth_window)

    if interpolate:
        idx = None
        chordlen = np.sqrt(np.sum(np.power(np.diff(X.T), 2), axis=0))
        chordlen = np.insert(chordlen, 0, 0)
        csum = np.cumsum(chordlen)
        dist = sum(chordlen)
        idx = csum // interdist

        t = round(dist / interdist)

        X = _interparc(t, X[:, 0], X[:, 1], X[:, 2])[1:, :]

    return X, idx
