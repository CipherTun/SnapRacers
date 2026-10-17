"""Shapes the driver pieces are made of, as manifold3d solids, in metres."""

import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, Mesh

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


def soft_slab(section, depth, r, steps=6, segments=48):
    """A front view cross-section pushed back `depth`, centred on z = 0, with
    its front and back edges rounded by r. The section has to be convex."""
    layers = []
    for k in range(steps + 1):
        a = math.pi * 0.5 * k / steps
        inset = r * (1.0 - math.cos(a))
        half = depth * 0.5 - r + r * math.sin(a)
        s = section.offset(-inset, JoinType.Round, 2.0, segments) if inset > 1e-6 else section
        for z in (-half, half):
            layers.append(s.extrude(1e-5).translate([0.0, 0.0, z]))
    return Manifold.batch_hull(layers)


def flat(points, depth, z, r=None, steps=6, segments=48):
    """A flat piece lying on the chest: a convex front view outline as (x, y)
    points, `depth` thick, its back at z (so it goes forward to z - depth),
    with soft edges."""
    section = CrossSection([points])
    if section.area() <= 1e-12:
        section = CrossSection([list(reversed(points))])
    r = depth * 0.45 if r is None else r
    return soft_slab(section, depth, r, steps, segments).translate([0.0, 0.0, z - depth * 0.5])


def ring_y(inner, outer, y0, y1, r=0.003, segments=48):
    """A ring around the y axis from y0 to y1, its edges rounded by r."""
    section = CrossSection([[(inner, y0), (outer, y0), (outer, y1), (inner, y1)]])
    section = section.offset(-r, JoinType.Round, 2.0, 12).offset(r, JoinType.Round, 2.0, 12)
    return section.revolve(segments).rotate([-90.0, 0.0, 0.0])


def torus(major, minor, segments=16, sides=10):
    """A torus around the z axis."""
    return CrossSection.circle(minor, sides).translate([major, 0.0]).revolve(segments).rotate([0.0, 0.0, 0.0])


def from_grid(rings, closed=True):
    """A solid from rings of points, [ring][point][xyz], each ring a closed
    loop. With `closed` the last ring joins the first, like a torus,
    otherwise each end is shut with a fan to its middle."""
    rings = np.asarray(rings, float)
    n, m = rings.shape[0], rings.shape[1]
    verts = list(rings.reshape(-1, 3))
    tris = []
    last = n if closed else n - 1
    for i in range(last):
        i2 = (i + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            a, b, c, d = i * m + j, i * m + j2, i2 * m + j2, i2 * m + j
            tris += [(a, b, c), (a, c, d)]
    if not closed:
        for i, flip in ((0, True), (n - 1, False)):
            verts.append(rings[i].mean(axis=0))
            mid = len(verts) - 1
            for j in range(m):
                a, b = i * m + j, i * m + (j + 1) % m
                tris.append((mid, b, a) if flip else (mid, a, b))
    verts = np.asarray(verts, np.float32)
    tris = np.asarray(tris, np.uint32)
    v = verts[tris]
    if np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() < 0.0:
        tris = tris[:, ::-1].copy()
    return Manifold(Mesh(vert_properties=verts, tri_verts=tris))


def ellipse(a, b, sides=8):
    """A profile for sweep: an ellipse a across and b along the normal."""
    return [(a * math.cos(2.0 * math.pi * k / sides), b * math.sin(2.0 * math.pi * k / sides)) for k in range(sides)]


def rounded_rect(u0, u1, v0, v1, r, k=3):
    """A rounded rectangle as a closed list of (u, v) points, k a corner."""
    pts = []
    for cu, cv, a0 in ((u1 - r, v0 + r, -90.0), (u1 - r, v1 - r, 0.0), (u0 + r, v1 - r, 90.0), (u0 + r, v0 + r, 180.0)):
        for i in range(k + 1):
            a = math.radians(a0 + 90.0 * i / k)
            pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return pts


def smooth_path(points, normals, closed, rounds=2):
    """Rounds the corners of a path by cutting them, twice over."""
    p, n = [np.asarray(x, float) for x in points], [np.asarray(x, float) for x in normals]
    for _ in range(rounds):
        out, outn = ([] if closed else [p[0]]), ([] if closed else [n[0]])
        count = len(p) if closed else len(p) - 1
        for i in range(count):
            a, b = p[i], p[(i + 1) % len(p)]
            na, nb = n[i], n[(i + 1) % len(n)]
            out += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
            outn += [na * 0.75 + nb * 0.25, na * 0.25 + nb * 0.75]
        if not closed:
            out.append(p[-1])
            outn.append(n[-1])
        p, n = out, [v / np.linalg.norm(v) for v in outn]
    return p, n


def sweep(points, normals, profile, closed=True, soft_end=0.0):
    """A cord along the points with this profile, (u, v) across and along the
    surface's normal at each point. An open one gets ends rounded off over
    `soft_end`."""
    p = [np.asarray(x, float) for x in points]
    nrm = [np.asarray(x, float) for x in normals]
    count = len(p)
    rings = []
    scales = [1.0] * count

    def tangent(i):
        if closed:
            t = p[(i + 1) % count] - p[i - 1]
        else:
            t = p[min(i + 1, count - 1)] - p[max(i - 1, 0)]
        return t / np.linalg.norm(t)

    frames = []
    for i in range(count):
        t = tangent(i)
        n = nrm[i] - t * nrm[i].dot(t)
        n /= np.linalg.norm(n)
        frames.append((p[i], np.cross(t, n), n, t))
    if not closed and soft_end > 0.0:
        for end, sign in ((0, -1.0), (count - 1, 1.0)):
            at, s, n, t = frames[end]
            extra = [(at + t * sign * soft_end * f, s, n, t) for f in (0.5, 0.85)]
            if end == 0:
                frames = list(reversed(extra)) + frames
                scales = [0.55, 0.85] + scales
            else:
                frames = frames + extra
                scales = scales + [0.85, 0.55]
    for (at, s, n, _), k in zip(frames, scales):
        rings.append([at + s * u * k + n * v * k for u, v in profile])
    return from_grid(rings, closed)


def lathe(profile, sides=40):
    """A ring around the y axis: `profile(angle)` gives its cross-section as
    a closed list of (radius, y) points, the same count at every angle (angle
    0 at the front, toward +x)."""
    rings = []
    for k in range(sides):
        a = 2.0 * math.pi * k / sides
        rings.append([(r * math.sin(a), y, -r * math.cos(a)) for r, y in profile(a)])
    return from_grid(rings, True)


def apply(solid, m):
    return solid.transform(np.asarray(m, float))


def _add():
    from manifold3d import OpType
    return OpType.Add
