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

import figure as F
from hair import BEARD_ANGLE, BEARD_TOP, band, union
from shapes import ball, blob, curve, lathe_at, angles_round

def jaw(top, thick, ends=(BEARD_ANGLE - 6.0, BEARD_ANGLE), chin=0.006):
    """A moulded shell over the jaw from one side to the other, `thick` off
    the head (a function of the angle round the head, 0 at the front), its
    top at `top`, round under the chin along the head's bottom edge, with
    soft edges. Past `ends` it thins into the head, where it's cut away."""
    start, stop = ends
    # The head's bottom edge is rounded about (0.085, -0.065), 0.035 round.
    cu, cv, rho = 0.085, -0.065, 0.035

    def profile(a):
        d = abs(math.degrees(a))
        t, g = top(a), thick(a) + chin * max(0.0, math.cos(a)) ** 4
        if d > stop:
            # Tucked inside the head, cut away later.
            return [(0.06 + 0.005 * math.cos(math.radians(225.0 - 360.0 * k / 13)), -0.04 + 0.005 * math.sin(math.radians(225.0 - 360.0 * k / 13))) for k in range(13)]
        if d > start:
            g *= 1.0 - (d - start) / (stop - start) * 0.9
        e = min(0.008, g * 0.6)
        # Where the top meets the outside, starting partway round the chin
        # when the top is below the side.
        q0 = math.asin(max(-0.95, min(0.0, (t - 2.0 * e - cv) / (rho + g))))
        r = cu + (rho + g) * math.cos(q0) if q0 < 0.0 else F.HEAD_RADIUS + g
        pts = [(0.06, min(-0.08, t - 0.02)), (0.06, t - 0.01), (0.1, t)]
        # The soft top edge.
        for k in range(3):
            q = math.radians(90.0 - 90.0 * k / 2)
            pts.append((r - e + e * math.cos(q), t - e + e * math.sin(q)))
        # Down the cheek and round under the chin.
        pts.append((r, min((t + cv) * 0.5, t - 1.5 * e)))
        for k in range(5):
            q = q0 + (-math.pi / 3 - q0) * k / 4
            pts.append((cu + (rho + g) * math.cos(q), cv + (rho + g) * math.sin(q)))
        # Back in under the head's edge.
        pts.append((0.075, -0.09))
        return pts

    extra = []
    for d in (start, (start + stop) * 0.5, stop, stop + 2.0):
        extra += [d, -d]
    return lathe_at(angles_round(9.0, extra), profile)


def full():
    """Round the chin under the mouth and up the cheeks, the moustache
    printed over the mouth."""
    top = lambda a: curve([(0.0, -0.07), (18.0, -0.064), (36.0, -0.036), (50.0, -0.004), (62.0, 0.03), (BEARD_ANGLE, 0.04)], a)
    return {"main": jaw(top, lambda a: 0.014)}


def long_beard():
    """The full beard with a long soft point hanging from the chin."""
    beard = full()["main"]
    tip = Manifold.batch_hull([blob((0.0, -0.1, -0.13), (0.055, 0.02, 0.012), 16), ball((0.0, -0.2, -0.14), 0.01, 10)])
    return {"main": beard + tip}


def braided():
    """A shorter beard with a braid hanging from the chin."""
    top = lambda a: curve([(0.0, -0.072), (18.0, -0.068), (36.0, -0.045), (50.0, -0.02), (62.0, 0.012), (BEARD_ANGLE, 0.022)], a)
    beard = jaw(top, lambda a: 0.012)
    pts = [(0.0, -0.118, -0.138), (0.0, -0.152, -0.148), (0.0, -0.186, -0.152)]
    plait = union([ball(p, r, 12) for p, r in zip(pts, (0.024, 0.022, 0.02))])
    plait = plait + Manifold.batch_hull([ball(pts[0], 0.016, 10), ball(pts[-1], 0.016, 10)])
    end = ball((0.0, -0.212, -0.152), 0.013, 10)
    plait, tie = band(plait + end, np.array([0.0, -0.2, -0.152]), (0.0, 1.0, 0.0), 0.006)
    return {"main": beard + plait, "dark": tie}


def sideburns():
    """Two strips down from the hairline in front of where the ears would
    be, close on the head."""
    strips = []
    for side in (-1.0, 1.0):
        ends = []
        for deg, y, w in ((63.0, BEARD_TOP - 0.012, 0.014), (61.0, -0.03, 0.011)):
            a = math.radians(deg * side)
            out = np.array([math.sin(a), 0.0, -math.cos(a)])
            across = np.array([math.cos(a), 0.0, math.sin(a)])
            turn = np.column_stack([across, [0.0, 1.0, 0.0], out])
            ends.append(blob(out * (F.HEAD_RADIUS + 0.002) + np.array([0.0, y, 0.0]), (w, 0.012, 0.01), 14, turn))
        strips.append(Manifold.batch_hull(ends))
    return {"main": union(strips)}


STYLES = {
    "full": full,
    "long": long_beard,
    "braided": braided,
    "sideburns": sideburns,
}
