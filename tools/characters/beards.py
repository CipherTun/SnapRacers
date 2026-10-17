"""Raised facial hair: the full beard, long and braided beards and
sideburns, moulded like a toy's beard piece. The rest of the facial hair is
printed on the face (scripts/character/face_print.gd), and so is the
moustache over a raised beard. Each gives its solids by colour region in the
head's own space (see hair.py), before they're cut back from the head.

They keep within BEARD_ANGLE of the front and under BEARD_TOP, where hair
doesn't come, and keep under the mouth and clear of the eyes so every mood
still shows.
"""

import math

import numpy as np
from manifold3d import Manifold

from hair import BEARD_ANGLE, BEARD_TOP, band, union
from shapes import ball, blob, curve, lathe_at, angles_round

def jaw(top, radius, bottom=-0.11, ends=(BEARD_ANGLE - 4.0, BEARD_ANGLE), corner=0.012):
    """A moulded band around the jaw from one side to the other: its top at
    `top` and out to `radius` (functions of the angle round the head, 0 at
    the front), its bottom under the chin, with rounded edges. Past `ends`
    it tapers into the head, where it's cut away."""
    start, stop = ends

    def profile(a):
        d = abs(math.degrees(a))
        r, t = radius(a), top(a)
        if d > stop:
            # Tucked inside the head, cut away later.
            return [(0.055 + 0.005 * math.cos(math.radians(225.0 - 360.0 * k / 12)), -0.04 + 0.005 * math.sin(math.radians(225.0 - 360.0 * k / 12))) for k in range(12)]
        if d > start:
            k = (d - start) / (stop - start)
            r = r - (r - 0.11) * k
            t = t - (t + 0.02) * k * 0.5
        pts = [(0.05, -0.05), (0.05, t)]
        for k in range(4):
            q = math.radians(90.0 - 90.0 * k / 3)
            pts.append((r - corner + corner * math.cos(q), t - corner + corner * math.sin(q)))
        # Fuller round the chin, its front bowed out.
        pts.append((r + 0.006, (t + bottom) * 0.5))
        for k in range(4):
            q = math.radians(-90.0 * k / 3)
            pts.append((r - corner + corner * math.cos(q), bottom + corner + corner * math.sin(q)))
        pts.append((0.106, bottom))
        return pts

    extra = []
    for d in (start, (start + stop) * 0.5, stop, stop + 2.0):
        extra += [d, -d]
    return lathe_at(angles_round(9.0, extra), profile)


def full():
    """Round the chin under the mouth and up the cheeks, the moustache
    printed over the mouth."""
    top = lambda a: curve([(0.0, -0.07), (18.0, -0.064), (36.0, -0.036), (50.0, -0.004), (62.0, 0.03), (BEARD_ANGLE, 0.04)], a)
    return {"main": jaw(top, lambda a: curve([(0.0, 0.14), (40.0, 0.137), (72.0, 0.132)], a))}


def long_beard():
    """The full beard with a long soft point hanging from the chin."""
    beard = full()["main"]
    tip = Manifold.batch_hull([blob((0.0, -0.1, -0.143), (0.072, 0.03, 0.018), 16), ball((0.0, -0.215, -0.142), 0.012, 10)])
    return {"main": beard + tip}


def braided():
    """A shorter beard with a braid hanging from the chin."""
    top = lambda a: curve([(0.0, -0.072), (18.0, -0.068), (36.0, -0.045), (50.0, -0.02), (62.0, 0.012), (BEARD_ANGLE, 0.022)], a)
    beard = jaw(top, lambda a: curve([(0.0, 0.136), (40.0, 0.134), (72.0, 0.13)], a))
    pts = [(0.0, -0.118, -0.142), (0.0, -0.152, -0.142), (0.0, -0.186, -0.142)]
    plait = union([ball(p, r, 12) for p, r in zip(pts, (0.024, 0.022, 0.02))])
    plait = plait + Manifold.batch_hull([ball(pts[0], 0.016, 10), ball(pts[-1], 0.016, 10)])
    end = ball((0.0, -0.212, -0.142), 0.013, 10)
    plait, tie = band(plait + end, np.array([0.0, -0.2, -0.142]), (0.0, 1.0, 0.0), 0.006)
    return {"main": beard + plait, "dark": tie}


def sideburns():
    pads = []
    for s in (-1.0, 1.0):
        a = math.radians(62.0 * s)
        at = np.array([0.122 * math.sin(a), -0.005, -0.122 * math.cos(a)])
        out = np.array([math.sin(a), 0.0, -math.cos(a)])
        side = np.array([math.cos(a), 0.0, math.sin(a)])
        turn = np.column_stack([side, [0.0, 1.0, 0.0], out])
        pads.append(Manifold.sphere(1.0, 16).scale([0.02, 0.05, 0.014]).transform(np.hstack([turn, at.reshape(3, 1)])))
    return {"main": union(pads)}


STYLES = {
    "full": full,
    "long": long_beard,
    "braided": braided,
    "sideburns": sideburns,
}
