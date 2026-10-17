"""Shapes the driver pieces are made of, as manifold3d solids, in metres."""

import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

# A hairline gap between pieces that sit against each other.
GAP = 0.002
SEGMENTS = 28


def rbox(x0, y0, z0, x1, y1, z1, r):
    """A box from one corner to the other with all its edges rounded by r."""
    r = min(r, (x1 - x0) * 0.49, (y1 - y0) * 0.49, (z1 - z0) * 0.49)
    ball = Manifold.sphere(r, 16)
    return Manifold.batch_hull([ball.translate([x, y, z]) for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r) for z in (z0 + r, z1 - r)])


def tube(p0, p1, r0, r1, sides=SEGMENTS):
    """A cone from p0 to p1, radius r0 at p0 and r1 at p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    z = d / length
    x = np.cross([0.0, 1.0, 0.0] if abs(z[1]) < 0.9 else [1.0, 0.0, 0.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    m = np.column_stack([x, y, z, p0])
    return Manifold.cylinder(length, r0, r1, sides).transform(m)


def ball(at, r, segments=SEGMENTS):
    return Manifold.sphere(r, segments).translate(list(at))


def blob(at, radii, segments=SEGMENTS, turn=None):
    """An ellipsoid with these radii along x, y and z, turned by a 3x3 basis
    if given, centred on `at`."""
    s = Manifold.sphere(1.0, segments).scale(list(radii))
    if turn is not None:
        s = s.transform(np.hstack([np.asarray(turn, float), np.zeros((3, 1))]))
    return s.translate(list(at))


def chain(points, r, segments=16):
    """A round cord through the points, radius r, or a list of radii."""
    radii = r if isinstance(r, (list, tuple)) else [r] * len(points)
    balls = [ball(p, rr, segments) for p, rr in zip(points, radii)]
    return Manifold.batch_boolean([Manifold.batch_hull([a, b]) for a, b in zip(balls, balls[1:])], _add())


def soft_slab(section, depth, r, steps=6):
    """A front view cross-section pushed back `depth`, centred on z = 0, with
    its front and back edges rounded by r. The section has to be convex."""
    layers = []
    for k in range(steps + 1):
        a = math.pi * 0.5 * k / steps
        inset = r * (1.0 - math.cos(a))
        half = depth * 0.5 - r + r * math.sin(a)
        s = section.offset(-inset, JoinType.Round, 2.0, 48) if inset > 1e-6 else section
        for z in (-half, half):
            layers.append(s.extrude(1e-5).translate([0.0, 0.0, z]))
    return Manifold.batch_hull(layers)


def flat(points, depth, z, r=None):
    """A flat piece lying on the chest: a convex front view outline as (x, y)
    points, `depth` thick, its back at z (so it goes forward to z - depth),
    with soft edges."""
    section = CrossSection([points])
    if section.area() <= 1e-12:
        section = CrossSection([list(reversed(points))])
    r = depth * 0.45 if r is None else r
    return soft_slab(section, depth, r).translate([0.0, 0.0, z - depth * 0.5])


def ring_y(inner, outer, y0, y1, r=0.003, segments=48):
    """A ring around the y axis from y0 to y1, its edges rounded by r."""
    section = CrossSection([[(inner, y0), (outer, y0), (outer, y1), (inner, y1)]])
    section = section.offset(-r, JoinType.Round, 2.0, 12).offset(r, JoinType.Round, 2.0, 12)
    return section.revolve(segments).rotate([-90.0, 0.0, 0.0])


def torus(major, minor, segments=16, sides=10):
    """A torus around the z axis."""
    return CrossSection.circle(minor, sides).translate([major, 0.0]).revolve(segments).rotate([0.0, 0.0, 0.0])


def apply(solid, m):
    return solid.transform(np.asarray(m, float))


def _add():
    from manifold3d import OpType
    return OpType.Add
