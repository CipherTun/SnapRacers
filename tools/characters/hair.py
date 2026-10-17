"""Hair, one function a style, like moulded toy hair pieces: a cap over the
head with a soft rounded edge and a few big lobes, with ties and partings
as flat colour regions. Each gives its solids by colour region in the
head's own space (before it's scaled up by HEAD_SCALE), before they're cut
back from the head and the stud.

The head is a rounded cylinder HEAD_RADIUS round from -0.1 to 0.1, facing
-z. Hair keeps out of the face (below FACE_TOP within FACE_ANGLE of the
front), only comes down past the cheeks behind SIDE_ANGLE, where raised
sideburns and beards don't reach, and stops at LOWEST, just under the
head, so it clears the shoulders and what's around the neck however far
the head turns.

Each style also has a cut version for under a hat: what's below CUT_Y,
kept within CUT_RADIUS for CUT_BAND under that, so a hat whose rim comes
down to CUT_Y and fits over CUT_RADIUS covers its top edge.
"""

import math

import numpy as np
from manifold3d import CrossSection, Manifold

import figure as F
from shapes import GAP, angles_round, ball, blob, curve, lathe_at

R0 = F.HEAD_RADIUS
FACE_TOP = 0.068
FACE_ANGLE = 58.0
SIDE_ANGLE = 78.0
LOWEST = -0.105
# Raised beards and sideburns stay within BEARD_ANGLE of the front and
# under BEARD_TOP, a little lower than the hair comes there.
BEARD_ANGLE = 72.0
BEARD_TOP = 0.052
CUT_Y = 0.05
CUT_RADIUS = R0 + 0.02
CUT_BAND = 0.012
# Lobes are this smooth.
SEG = 16


def _value(v):
    return v if callable(v) else (lambda a: v)


def head_outline(grow):
    """The head and its stud from the side, as (radius, height) points from
    under the bottom edge up to the middle of the top, `grow` out from them.
    The rounded edges have few points, set out so the lines between them
    stay outside."""
    def arc(cu, cv, rho, a0, a1, steps):
        out = []
        for k in range(steps + 1):
            t = math.radians(a0 + (a1 - a0) * k / steps)
            far = rho / math.cos(math.radians(abs(a1 - a0) / steps * 0.5)) if 0 < k < steps else rho
            out.append((cu + far * math.cos(t), cv + far * math.sin(t)))
        return out

    pts = arc(0.085, -0.065, 0.035 + grow, -60.0, 0.0, 2)
    pts += arc(0.085, 0.065, 0.035 + grow, 0.0, 90.0, 3)
    pts.append((0.06 + grow, 0.1 + grow))
    pts += arc(0.046, 0.126, 0.008 + grow, 0.0, 90.0, 2)
    pts.append((0.002, 0.134 + grow))
    return pts


def _inside(outline, b, lip_at):
    """The inside of the cap at one angle: along its flat lower edge from
    near the lip in to the head at height b, then over the head along the
    outline. Always the same number of points, so the outline's points
    below b are spread along the lower edge."""
    low = max(b, -0.094)
    above = [p for p in outline if p[1] > low + 1e-9]
    below = len(outline) - len(above)
    if b >= -0.094:
        i = next(k for k in range(len(outline) - 1) if outline[k + 1][1] > low)
        (u0, v0), (u1, v1) = outline[i], outline[i + 1]
        t = (low - v0) / (v1 - v0)
        start = (u0 + (u1 - u0) * t, b)
    else:
        start = (0.106, b)
    edge = [(lip_at + (start[0] - lip_at) * (k + 1) / (below + 1), b) for k in range(below)]
    return edge + [start] + above


# The cap's inside sits this far off the head, more than the gap the lobes
# are cut back by, so cutting doesn't touch it.
INSIDE = GAP + 0.0035


def cap(bottom, radius=0.138, top=0.15, dome=0.012, lip=0.009, corner=0.05, bulge=0.003, extra=(), step=18.0):
    """The cap over the head, hollow inside: its lower edge at `bottom` (a
    number or a function of the angle round the head, 0 at the front),
    `radius` out at the sides, flat-ish on top at `top` rising by `dome` in
    the middle, with a rounded lip and top corner. The top and the corner can
    change round the head too. `bulge` pushes the sides
    out between them. `extra` adds sections at these angles (degrees), where
    the edge drops."""
    bottom, radius, bulge, top_at, corner_at = _value(bottom), _value(radius), _value(bulge), _value(top), _value(corner)
    outline = head_outline(INSIDE)

    def profile(a):
        b, r, g, top, corner = bottom(a), radius(a), bulge(a), top_at(a), corner_at(a)
        # Up the inside from the lower edge, over the head to the middle.
        pts = _inside(outline, b, r - lip)
        # Then from the middle of the top out and down the outside.
        inner = r - corner
        for k in range(3):
            u = inner * k / 3
            pts.append((max(u, 0.002), top + dome * (1.0 - (u / inner) ** 2)))
        for k in range(3):
            t = math.radians(90.0 - 90.0 * k / 2)
            pts.append((r - corner + corner * math.cos(t), top - corner + corner * math.sin(t)))
        # Down the side, bowed out by the bulge.
        for k in (1, 2, 3):
            pts.append((r + g * math.sin(math.pi * k / 4), top - corner + (b + lip - top + corner) * k / 4))
        for k in range(3):
            t = math.radians(0.0 - 90.0 * k / 2)
            pts.append((r - lip + lip * math.cos(t), b + lip + lip * math.sin(t)))
        return pts

    return lathe_at(angles_round(step, extra), profile)


# Extra sections where long hair drops past the cheeks.
DROP = (-84.0, -78.0, -75.0, -72.0, -66.0, 66.0, 72.0, 75.0, 78.0, 84.0)


def face_line(front, side, back, drop_at=SIDE_ANGLE):
    """A lower edge at `front` across the face, coming down no lower than
    BEARD_TOP until BEARD_ANGLE, to `side` over the ears from `drop_at` back,
    and `back` at the back."""
    mid = max(BEARD_TOP, min(front, side + 0.02))
    return lambda a: curve([(0.0, front), (FACE_ANGLE, front), (BEARD_ANGLE, mid), (drop_at, side), (120.0, side * 0.5 + back * 0.5), (180.0, back)], a)


def around(r, degrees, y):
    a = math.radians(degrees)
    return np.array([r * math.sin(a), y, -r * math.cos(a)])


def tuft(base, tip, r0, r1, seg=12):
    """A chunky rounded cone from base to tip."""
    return Manifold.batch_hull([ball(base, r0, seg), ball(tip, r1, seg)])


def lobe(at, radii, along=None, seg=SEG):
    """An ellipsoid, its z radius along `along` if given."""
    turn = None
    if along is not None:
        z = np.asarray(along, float)
        z /= np.linalg.norm(z)
        x = np.cross([0.0, 1.0, 0.0], z) if abs(z[1]) < 0.95 else np.cross([1.0, 0.0, 0.0], z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        turn = np.column_stack([x, y, z])
    return blob(at, radii, seg, turn)


def chain(points, radii, seg=12):
    """Soft lobes hulled one to the next, like a tail or a braid."""
    balls = [ball(p, r, seg) for p, r in zip(points, radii)]
    return union([Manifold.batch_hull([a, b]) for a, b in zip(balls, balls[1:])])


def band(solid, at, along, half):
    """Splits a solid into a flat band across `along` at `at`, `half` either
    side, and the rest, for a hair tie printed on."""
    n = np.asarray(along, float)
    n /= np.linalg.norm(n)
    d = float(n.dot(at))
    slab = solid.trim_by_plane(list(n), d - half).trim_by_plane(list(-n), -(d + half))
    return solid - slab, slab


def parting(solid, x, z0=-0.2, z1=0.05, width=0.006):
    """Splits off a parting line printed along the top at x, from z0 to z1."""
    line = Manifold.cube([width, 0.3, z1 - z0]).translate([x - width * 0.5, 0.1, z0])
    inside = solid ^ line
    return solid - inside, inside


def union(parts):
    from manifold3d import OpType
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return Manifold.batch_boolean(parts, OpType.Add) if parts else Manifold()


# The styles. Each is one shell down over the sides past the ears and down
# the back, its front edge shaped to the style.

def short():
    return {"main": cap(face_line(0.078, -0.025, -0.06))}


def spiky():
    """A few broad spikes with round tips rising from short hair."""
    base = cap(face_line(0.08, -0.02, -0.055), top=0.148)
    spikes = []
    for deg, r, lean, h in ((0.0, 0.05, 0.45, 0.07), (-70.0, 0.075, 0.6, 0.06), (70.0, 0.075, 0.6, 0.06), (180.0, 0.06, 0.6, 0.06)):
        root = around(r, deg, 0.14)
        d = np.array([0.0, 1.0, 0.0]) + around(lean, deg, 0.0)
        spikes.append(tuft(root, root + d / np.linalg.norm(d) * h, 0.05, 0.022, 12))
    return {"main": base + union(spikes)}


def flat_top():
    return {"main": cap(face_line(0.076, -0.005, -0.04), radius=0.136, top=0.172, dome=0.0, corner=0.022, bulge=0.0)}


def head_surface(direction):
    """Where a line from the middle of the head going this way meets its
    surface."""
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    lo, hi = 0.0, 0.3
    for _ in range(30):
        mid = (lo + hi) * 0.5
        x, y, z = d * mid
        q = np.array([max(math.hypot(x, z) - 0.085, 0.0), max(abs(y) - 0.065, 0.0)])
        inside = math.hypot(*q) <= 0.035 and math.hypot(x, z) <= 0.12 and abs(y) <= 0.1
        lo, hi = (mid, hi) if inside else (lo, mid)
    return d * lo


def mohawk():
    """A low cap over the top with one tall soft ridge from the brow to the
    back."""
    base = cap(0.075, radius=0.128, top=0.14, dome=0.004, corner=0.03, bulge=0.0)
    lobes = []
    for deg, h in ((-34.0, 0.036), (-10.0, 0.064), (20.0, 0.07), (50.0, 0.06), (80.0, 0.042)):
        t = math.radians(deg)
        out = np.array([0.0, math.cos(t), math.sin(t)])
        at = head_surface(out) + out * 0.03
        turn = np.column_stack([[1.0, 0.0, 0.0], np.cross(out, [1.0, 0.0, 0.0]), out])
        lobes.append(blob(at + out * (h * 0.3), (0.026, 0.03, h), 12, turn))
    ridge = union([Manifold.batch_hull([a, b]) for a, b in zip(lobes, lobes[1:])])
    return {"main": base + ridge}


def quiff():
    """Short at the sides with a big roll swept up off the brow."""
    base = cap(face_line(0.086, -0.02, -0.06), radius=0.136, top=0.146)
    roll = lobe((0.0, 0.158, -0.082), (0.078, 0.042, 0.06), (0.0, 0.55, -1.0))
    return {"main": base + roll}


def side_part():
    """Parted on the right and swept over to the left in one big wave."""
    line = lambda a: curve([(-180.0, -0.06), (-90.0, -0.03), (-62.0, 0.068), (-30.0, 0.07), (0.0, 0.074), (40.0, 0.088), (62.0, 0.088), (90.0, -0.02), (180.0, -0.06)], a)
    base = cap(line, top=0.148, extra=(-66.0, -62.0, -58.0, 58.0, 62.0, 66.0))
    sweep = Manifold.batch_hull([blob((0.055, 0.156, -0.05), (0.045, 0.024, 0.05), SEG), blob((-0.07, 0.114, -0.09), (0.06, 0.03, 0.05), SEG)])
    main, part = parting(base + sweep, 0.048, -0.15, -0.032)
    return {"main": main, "dark": part}


def bob():
    line = face_line(0.076, -0.09, -0.095)
    return {"main": cap(line, radius=lambda a: curve([(0.0, 0.138), (90.0, 0.144), (180.0, 0.146)], a), bulge=0.005, extra=DROP)}


def long_hair():
    line = face_line(0.09, LOWEST, LOWEST, 78.0)
    base = cap(line, radius=lambda a: curve([(0.0, 0.138), (90.0, 0.148), (180.0, 0.15)], a), bulge=0.008, extra=DROP)
    main, part = parting(base, 0.0, -0.2, -0.02)
    return {"main": main, "dark": part}


def wavy():
    line = lambda a: face_line(0.088, LOWEST + 0.012, LOWEST + 0.012, 78.0)(a) - (0.012 * (0.5 + 0.5 * math.cos(math.radians(math.degrees(abs(a)) * 7.0))) if abs(a) > math.radians(80.0) else 0.0)
    out = lambda a: curve([(0.0, 0.138), (90.0, 0.148), (180.0, 0.15)], a) + (0.006 * math.cos(math.radians(math.degrees(abs(a)) * 7.0)) if abs(a) > math.radians(80.0) else 0.0)
    base = cap(line, radius=out, bulge=0.006, extra=DROP, step=12.0)
    return {"main": base}


def ponytail():
    """Pulled back tight from a high hairline into a tail."""
    base = cap(face_line(0.092, -0.025, -0.04), radius=0.134, top=0.144, bulge=0.0)
    pts = [(0.0, 0.06, 0.13), (0.0, 0.02, 0.19), (0.0, -0.04, 0.215), (0.0, -0.08, 0.205)]
    tail = chain(pts, [0.036, 0.042, 0.036, 0.022])
    tail, tie = band(tail, np.array(pts[0]) + np.array([0.0, -0.012, 0.022]), (0.0, -0.5, 1.0), 0.008)
    return {"main": base + tail, "dark": tie}


def pigtails():
    base = cap(face_line(0.08, -0.02, -0.05))
    main, part = parting(base, 0.0, -0.2, 0.15)
    tails, ties = [], []
    for s in (-1.0, 1.0):
        pts = [(0.128 * s, 0.035, 0.06), (0.155 * s, -0.005, 0.08), (0.165 * s, -0.05, 0.085), (0.16 * s, -0.085, 0.08)]
        tail = chain(pts, [0.03, 0.032, 0.027, 0.017])
        tail, tie = band(tail, np.array(pts[0]) + np.array([0.017 * s, -0.01, 0.003]), (s, -0.6, 0.1), 0.008)
        tails.append(tail)
        ties.append(tie)
    return {"main": main + union(tails), "dark": union(ties)}


def bun():
    base = cap(face_line(0.084, -0.02, -0.05), radius=0.135, bulge=0.0)
    knot = ball((0.0, 0.195, 0.03), 0.05, SEG)
    knot, tie = band(knot, np.array([0.0, 0.16, 0.03]), (0.0, 1.0, 0.0), 0.007)
    return {"main": base + knot, "dark": tie}


def afro():
    """One big round soft mass, wider than the head all round, with the face
    left open."""
    mass = blob((0.0, 0.09, 0.025), (0.19, 0.15, 0.19), 28)
    corners = [ball((x * s, y, z), 0.016, 10) for s in (-1.0, 1.0) for y in (-0.4, 0.07) for x, z in ((0.126, -0.027), (0.33, -0.19), (0.33, -0.4))]
    return {"main": mass - Manifold.batch_hull(corners)}


def curly():
    base = cap(face_line(0.08, -0.02, -0.055), radius=0.138)
    curls = []
    for deg, y in ((-35.0, 0.13), (35.0, 0.13), (-110.0, 0.1), (110.0, 0.1), (180.0, 0.1)):
        curls.append(ball(around(0.115, deg, y), 0.038, 12))
    curls.append(ball((0.0, 0.15, 0.0), 0.045, 12))
    return {"main": base + union(curls)}


def bowl():
    """A straight fringe low over the brow and the same edge all round."""
    line = lambda a: curve([(0.0, 0.07), (FACE_ANGLE, 0.07), (90.0, 0.04), (180.0, 0.03)], a)
    return {"main": cap(line, radius=0.15, top=0.15, corner=0.06, lip=0.016, bulge=0.004)}


def messy():
    """Short hair with three broad tufts flopping different ways."""
    base = cap(face_line(0.08, -0.02, -0.05))
    tufts = []
    for x, z, lx, lz, h in ((-0.045, -0.05, -0.06, -0.045, 0.03), (0.04, -0.03, 0.055, -0.02, 0.04), (0.0, 0.06, 0.02, 0.06, 0.04)):
        tufts.append(tuft((x, 0.14, z), (x + lx, 0.14 + h, z + lz), 0.05, 0.024, 12))
    return {"main": base + union(tufts)}


def princess():
    """Long curls: long hair with big round curls at the ends."""
    line = face_line(0.088, -0.07, -0.07, 78.0)
    base = cap(line, radius=lambda a: curve([(0.0, 0.138), (90.0, 0.146), (180.0, 0.148)], a), bulge=0.006, extra=DROP)
    curls = []
    for deg in (-110.0, 180.0, 110.0):
        curls.append(ball(around(0.15, deg, -0.07), 0.034, 10))
    sweep = lobe((0.03, 0.136, -0.06), (0.09, 0.028, 0.06), (-0.4, 0.3, -1.0))
    return {"main": base + union(curls) + sweep}


def braids():
    base = cap(face_line(0.08, -0.02, -0.05))
    main, part = parting(base, 0.0, -0.2, 0.15)
    plaits, ties = [], []
    for s in (-1.0, 1.0):
        at = [around(0.146, 100.0 * s, y) for y in (0.0, -0.035, -0.07)]
        plaits += [ball(p, 0.024, 10) for p in at]
        plaits.append(Manifold.batch_hull([ball(at[0], 0.018, 10), ball(at[-1], 0.018, 10)]))
        tip = around(0.146, 100.0 * s, -0.094)
        ties.append(ball(tip, 0.013, 10))
    return {"main": main + union(plaits), "dark": union(ties)}


def fringe():
    """A long fringe swept across the brow from the right, down past the
    left eye."""
    base = cap(face_line(0.094, -0.025, -0.06), top=0.148)
    fall = chain([around(0.128, 35.0, 0.122), around(0.134, 0.0, 0.11), around(0.134, -35.0, 0.106), around(0.13, -66.0, 0.09)], [0.03, 0.03, 0.028, 0.018], 14)
    return {"main": base + fall}


STYLES = {
    "short": short,
    "spiky": spiky,
    "flat_top": flat_top,
    "mohawk": mohawk,
    "quiff": quiff,
    "side_part": side_part,
    "bob": bob,
    "long": long_hair,
    "wavy": wavy,
    "ponytail": ponytail,
    "pigtails": pigtails,
    "bun": bun,
    "afro": afro,
    "curly": curly,
    "bowl": bowl,
    "princess": princess,
    "messy": messy,
    "braids": braids,
    "fringe": fringe,
}


def cut(regions):
    """The cut version for under a hat: what's below CUT_Y, kept in to
    CUT_RADIUS over the top CUT_BAND."""
    below = Manifold.cube([1.0, 1.0, 1.0]).translate([-0.5, CUT_Y - 1.0, -0.5])
    rim = Manifold.cylinder(CUT_BAND + 0.001, CUT_RADIUS, CUT_RADIUS, 48).rotate([-90.0, 0.0, 0.0]).translate([0.0, CUT_Y - CUT_BAND, 0.0])
    low = Manifold.cube([1.0, 1.0, 1.0]).translate([-0.5, CUT_Y - CUT_BAND - 1.0, -0.5])
    keep = below ^ (rim + low)
    return {k: v ^ keep for k, v in regions.items()}


def radius_profile(solid, step=0.01):
    """How far out from the middle the hair reaches at heights up the head,
    as [height, radius] pairs, and how high its top is."""
    box = solid.bounding_box()
    out = []
    y = round(math.floor(box[1] / step) * step, 4)
    while y <= box[4]:
        polys = _slice_y(solid, y)
        if polys:
            r = max(math.hypot(p[0], p[1]) for poly in polys for p in poly)
            out.append([round(y, 4), round(r, 4)])
        y = round(y + step, 4)
    return out, round(float(box[4]), 4)


def _slice_y(solid, y):
    # Manifold slices across z, so turn y up to z first.
    turned = solid.rotate([90.0, 0.0, 0.0])
    # After turning, a point (x, y, z) is at (x, -z, y).
    return [list(map(tuple, p)) for p in turned.slice(y).to_polygons()]
