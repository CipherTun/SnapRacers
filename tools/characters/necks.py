"""What's worn around the neck: scarves, ties, necklaces, collars and the
rest, one function a style. Each gives its solids by colour region, in the
upper body's space (see figure.py), before they're cut back from the torso,
the neck and the head.

There's only 3 cm between the top of the torso and the head, so what goes
around the neck is low and flat, and anything bigger hangs on the chest
below the head.
"""

import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

import figure as F
from shapes import GAP, ball, blob, chain, flat, rbox, ring_y, tube

TOP = F.HIPS_TOP + F.TORSO_HEIGHT
HEAD_BOTTOM = F.NECK_Y + 0.015
CHEST = -F.TORSO_DEPTH * 0.5
FRONT = CHEST - GAP
# The torso's top front edge is rounded around this line (y, z), this much.
EDGE_Y, EDGE_Z, EDGE_R = TOP - 0.03, CHEST + 0.03, 0.03

# Colours that don't follow the piece's own: (colour, metallic).
COLOURS = {
    "white": ["#f2f2f2", 0.0],
    "gold": ["#c9a227", 0.6],
    "silver": ["#c8ccd0", 0.6],
    "ink": ["#3c3f44", 0.0],
    "gem": ["#3a8dde", 0.0],
    "yellow": ["#f2cd37", 0.0],
    "pink": ["#d86cb0", 0.0],
    "green": ["#4b9f4a", 0.0],
    "orange": ["#e8782b", 0.0],
    "grey": ["#9aa0a6", 0.0],
}


def around(r, angle, y):
    """A point r out from the neck at an angle (0 at the front, toward +x)."""
    return np.array([r * math.sin(angle), y, -r * math.cos(angle)])


def basis_up(n):
    """A basis whose y is n."""
    y = np.asarray(n, float) / np.linalg.norm(n)
    x = np.array([1.0, 0.0, 0.0]) if abs(y[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
    x = x - y * x.dot(y)
    x /= np.linalg.norm(x)
    return np.column_stack([x, y, np.cross(x, y)])


def necklace(r, off, dip, angle=math.radians(55.0), x_end=0.0, steps=10):
    """Points and the surface's normals along a loop that lies on the top of
    the torso around the back of the neck, comes over the front edge and down
    the chest to `dip` in a V (or to +-x_end). `off` is how far the path's
    middle is off the surface. It runs from the left end round to the right."""
    pts, normals = [], []
    rho = EDGE_R + off

    def side(sign):
        out = []
        x_e = r * math.sin(angle) * sign
        out.append((np.array([x_end * sign, dip, CHEST - off]), (0.0, 0.0, -1.0)))
        out.append((np.array([x_e * 0.9, EDGE_Y - 0.01, CHEST - off]), (0.0, 0.0, -1.0)))
        for a in (0.0, 30.0, 60.0, 90.0):
            t = math.radians(a)
            out.append((np.array([x_e, EDGE_Y + rho * math.sin(t), EDGE_Z - rho * math.cos(t)]), (0.0, math.sin(t), -math.cos(t))))
        return out

    for p, n in side(-1.0):
        pts.append(p)
        normals.append(n)
    for k in range(steps + 1):
        a = -angle - (2.0 * math.pi - 2.0 * angle) * k / steps
        pts.append(around(r, a, TOP + off))
        normals.append((0.0, 1.0, 0.0))
    for p, n in reversed(side(1.0)):
        pts.append(p)
        normals.append(n)
    return pts, normals


def resample(points, normals, spacing):
    """Points every `spacing` along a path, with normals."""
    out, outn = [np.asarray(points[0], float)], [np.asarray(normals[0], float)]
    left = spacing
    for a, b, na, nb in zip(points, points[1:], normals, normals[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        length = float(np.linalg.norm(b - a))
        at = 0.0
        while length - at >= left:
            at += left
            t = at / length
            out.append(a + (b - a) * t)
            n = np.asarray(na, float) * (1.0 - t) + np.asarray(nb, float) * t
            outn.append(n / np.linalg.norm(n))
            left = spacing
        left -= length - at
    return out, outn


def band(points, normals, width, thick, segments=16):
    """A flat ribbon along the points, lying on surfaces with these
    normals."""
    discs = [blob(p, (width * 0.5, thick * 0.5, width * 0.5), segments, basis_up(n)) for p, n in zip(points, normals)]
    return Manifold.batch_boolean([Manifold.batch_hull([a, b]) for a, b in zip(discs, discs[1:])], _add())


def _add():
    from manifold3d import OpType
    return OpType.Add


def union(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return Manifold.batch_boolean(parts, _add()) if parts else Manifold()


def stripes(solid, cuts, axis=1):
    """Splits a solid into what's inside the bands (lo, hi) along an axis and
    the rest."""
    bands = []
    for lo, hi in cuts:
        size = [2.0, 2.0, 2.0]
        size[axis] = hi - lo
        at = [-1.0, -1.0, -1.0]
        at[axis] = lo
        bands.append(Manifold.cube(size).translate(at))
    inside = solid ^ union(bands)
    return solid - inside, inside


def dots(solid, centres, r):
    """Splits a flat solid on the chest into round dots through it and the
    rest."""
    holes = union([tube((x, y, -0.3), (x, y, 0.0), r, r, 20) for x, y in centres])
    inside = solid ^ holes
    return solid - inside, inside


def lanyard(bottom, r=0.004, ring=0.078, ends=0.006):
    """A cord around the neck and down the chest in a V to `bottom`."""
    pts, _ = necklace(ring, GAP + r, bottom, math.radians(50.0), ends)
    return chain(pts, r)


def scarf_roll():
    """A soft roll around the neck, lying on the shoulders, with a knot at the
    front left."""
    section = CrossSection.circle(1.0, 20).scale([0.037, 0.0135]).translate([0.084, TOP + 0.0145])
    roll = section.revolve(48).rotate([-90.0, 0.0, 0.0])
    knot = blob((-0.045, TOP - 0.016, FRONT - 0.016), (0.026, 0.02, 0.016))
    return roll + knot


def scarf_tail(x0, x1, top, bottom, lean, z=FRONT, depth=0.013):
    """A flat end of scarf hanging down, `lean` across at the bottom, with
    two stripes near its end."""
    # On the back, z is where its front lies against the torso.
    tail = flat([(x0, top), (x1, top), (x1 + lean, bottom), (x0 + lean, bottom)], depth, z + depth if z > 0.0 else z)
    plain, striped = stripes(tail, [(bottom + 0.018, bottom + 0.028), (bottom + 0.038, bottom + 0.048)])
    return plain, striped


def scarf():
    plain, striped = scarf_tail(-0.075, -0.03, TOP - 0.02, TOP - 0.15, 0.012)
    return {"main": scarf_roll() + plain, "dark": striped}


def long_scarf():
    front, front_stripes = scarf_tail(-0.075, -0.03, TOP - 0.02, TOP - 0.2, 0.01)
    # Over the right shoulder and down the back.
    back, back_stripes = scarf_tail(0.03, 0.078, TOP - 0.012, TOP - 0.24, -0.012, z=-CHEST + GAP)
    over = Manifold.batch_hull([blob((0.055, TOP + 0.008, 0.07), (0.024, 0.008, 0.012)), blob((0.055, TOP - 0.02, -CHEST + GAP + 0.007), (0.024, 0.012, 0.007))])
    return {"main": scarf_roll() + front + back + over, "dark": front_stripes + back_stripes}


def tie():
    knot = flat([(-0.02, TOP + 0.004), (0.02, TOP + 0.004), (0.013, TOP - 0.03), (-0.013, TOP - 0.03)], 0.018, FRONT + 0.004)
    blade = flat([(-0.011, TOP - 0.026), (0.011, TOP - 0.026), (0.025, TOP - 0.19), (0.0, TOP - 0.215), (-0.025, TOP - 0.19)], 0.008, FRONT)
    # Stripes across the blade, slanting.
    slants = union([Manifold.cube([0.2, 0.009, 0.2]).translate([-0.1, -0.0045, -0.25]).rotate([0.0, 0.0, -30.0]).translate([0.0, y, 0.0]) for y in (TOP - 0.07, TOP - 0.11, TOP - 0.15)])
    striped = blade ^ slants
    return {"main": knot + (blade - striped), "dark": striped}


def bow_tie():
    y = TOP - 0.015
    wings = []
    for s in (-1.0, 1.0):
        wings.append(flat([(0.006 * s, y - 0.009), (0.006 * s, y + 0.009), (0.052 * s, y + 0.021), (0.052 * s, y - 0.021)], 0.016, FRONT, 0.006))
    knot = rbox(-0.011, y - 0.012, FRONT - 0.021, 0.011, y + 0.012, FRONT, 0.006)
    return {"main": union(wings), "dark": knot}


def neckerchief():
    band_ring = ring_y(0.048, 0.064, TOP + 0.009, TOP + 0.024, 0.004)
    tri = flat([(-0.07, TOP - 0.006), (0.07, TOP - 0.006), (0.0, TOP - 0.115)], 0.008, FRONT, 0.003)
    # The cloth comes from the band over the front edge to the triangle.
    over = Manifold.batch_hull([
        ring_y(0.048, 0.064, TOP + 0.009, TOP + 0.02, 0.004) ^ Manifold.cube([0.12, 0.1, 0.065]).translate([-0.06, TOP, -0.1]),
        flat([(-0.064, TOP - 0.012), (0.064, TOP - 0.012), (0.06, TOP - 0.022), (-0.06, TOP - 0.022)], 0.008, FRONT, 0.003),
    ])
    knot = ball((0.0, TOP - 0.006, FRONT - 0.012), 0.013)
    cloth = band_ring + tri + over + knot
    rest, spots = dots(tri, [(-0.032, TOP - 0.03), (0.032, TOP - 0.03), (0.0, TOP - 0.05), (-0.016, TOP - 0.078), (0.016, TOP - 0.078), (0.0, TOP - 0.1), (-0.05, TOP - 0.016), (0.05, TOP - 0.016)], 0.0055)
    return {"main": cloth - spots, "white": spots}


def medal():
    pts, normals = necklace(0.078, GAP + 0.002, TOP - 0.1, math.radians(50.0), 0.009)
    ribbon = band(pts, normals, 0.018, 0.004)
    y = TOP - 0.135
    disc = CrossSection.circle(0.03, 40)
    plate = flat_round(disc, 0.007, FRONT - 0.002).translate([0.0, y, 0.0])
    rim = (flat_round(disc, 0.004, FRONT - 0.009) - flat_round(CrossSection.circle(0.023, 40), 0.006, FRONT - 0.007)).translate([0.0, y, 0.0])
    star = flat_star(5, 0.014, 0.006, 0.003, FRONT - 0.009).translate([0.0, y, 0.0])
    loop = rbox(-0.009, y + 0.025, FRONT - 0.008, 0.009, TOP - 0.098, FRONT - 0.001, 0.003)
    return {"main": ribbon, "gold": plate + rim + star + loop}


def flat_round(section, depth, z):
    """A round flat piece, its back at z."""
    return flat_section(section, depth, z, depth * 0.4)


def flat_section(section, depth, z, r):
    from shapes import soft_slab
    return soft_slab(section, depth, r).translate([0.0, 0.0, z - depth * 0.5])


def flat_star(points, outer, inner, depth, z):
    out = []
    for k in range(points):
        a0 = math.pi * 2.0 * k / points
        tip = (outer * math.sin(a0), outer * math.cos(a0))
        sides = [(inner * math.sin(a0 + d), inner * math.cos(a0 + d)) for d in (-math.pi / points, math.pi / points)]
        out.append(flat([(0.0, 0.0), sides[0], tip, sides[1]], depth, z, depth * 0.3))
    return union(out)


def beads(rb, dip, colours, r=0.084):
    pts, normals = necklace(r, GAP + rb, dip, math.radians(55.0))
    at, _ = resample(pts, normals, rb * 2.05)
    if np.linalg.norm(at[-1] - at[0]) < rb * 2.0:
        at.pop()
    regions = {c: [] for c in colours}
    for k, p in enumerate(at):
        regions[colours[k % len(colours)]].append(ball(p, rb, 12))
    return {c: union(v) for c, v in regions.items()}


def shoulder_ring(inner, outer, height):
    """A flat collar lying on the shoulders around the neck, wide enough to
    show past the head."""
    return ring_y(inner, outer, TOP + GAP, TOP + GAP + height, 0.005)


def spiked_collar():
    collar = shoulder_ring(0.07, 0.118, 0.017)
    spikes = []
    for k in range(12):
        a = math.pi * 2.0 * (k + 0.5) / 12
        base = around(0.11, a, TOP + GAP + 0.0085)
        tip = around(0.146, a, TOP + GAP + 0.0085)
        spikes.append(tube(base, tip, 0.0075, 0.0024, 16) + ball(tip, 0.0024, 12))
    return {"main": collar, "silver": union(spikes)}


def ruff():
    pleats = []
    count = 26
    for k in range(count):
        a = 360.0 * k / count
        inner = blob((0.056, TOP + 0.016, 0.0), (0.008, 0.008, 0.007), 12)
        outer = blob((0.118, TOP + 0.014, 0.0), (0.008, 0.0115, 0.0155), 12)
        pleats.append(Manifold.batch_hull([inner, outer]).rotate([0.0, a, 0.0]))
    return {"white": union(pleats)}


def whistle():
    cord = lanyard(TOP - 0.085)
    y = TOP - 0.1
    body = tube((-0.012, y, FRONT - 0.012), (0.022, y, FRONT - 0.012), 0.012, 0.012, 24)
    body = body + ball((-0.012, y, FRONT - 0.012), 0.012, 24)
    mouth = rbox(0.018, y - 0.004, FRONT - 0.018, 0.046, y + 0.012, FRONT - 0.004, 0.003)
    hole = rbox(0.004, y + 0.006, FRONT - 0.03, 0.014, y + 0.02, FRONT + 0.01, 0.002)
    ring = torus_y((-0.004, y + 0.016, FRONT - 0.006), 0.007, 0.0022)
    return {"main": cord, "silver": (body - hole) + mouth + ring}


def torus_y(at, major, minor):
    """A small ring standing up facing the front, like a key ring."""
    t = CrossSection.circle(minor, 10).translate([major, 0.0]).revolve(24)
    return t.translate(list(at))


def race_pass():
    cord = lanyard(TOP - 0.07)
    clip = rbox(-0.008, TOP - 0.09, FRONT - 0.008, 0.008, TOP - 0.068, FRONT - 0.001, 0.003)
    top, bottom = TOP - 0.086, TOP - 0.17
    card = rbox(-0.032, bottom, FRONT - 0.005, 0.032, top, FRONT, 0.002)
    stripe = card ^ Manifold.cube([0.1, 0.016, 0.1]).translate([-0.05, top - 0.018, -0.2])
    photo = card ^ Manifold.cube([0.022, 0.026, 0.1]).translate([-0.025, bottom + 0.03, -0.2])
    lines = card ^ union([Manifold.cube([0.026, 0.005, 0.1]).translate([0.0, bottom + y, -0.2]) for y in (0.046, 0.034)])
    white = card - stripe - photo - lines
    return {"main": cord + stripe, "white": white, "silver": clip, "grey": photo, "ink": lines}


def gold_chain():
    pts, normals = necklace(0.078, GAP + 0.003, TOP - 0.085, math.radians(50.0), 0.0)
    at, _ = resample(pts, normals, 0.0115)
    links = []
    for k in range(len(at) - 1):
        t = at[k + 1] - at[k]
        t /= np.linalg.norm(t)
        up = np.array([0.0, 1.0, 0.0]) if abs(t[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
        side = np.cross(t, up)
        side /= np.linalg.norm(side)
        n = np.cross(side, t) if k % 2 == 0 else side
        m = np.column_stack([t, n, np.cross(t, n)])
        link = CrossSection.circle(0.0022, 5).translate([0.0045, 0.0]).revolve(8).scale([1.35, 1.0, 1.0])
        # The torus is around z, so its ring is in the link's x-y plane.
        links.append(link.transform(np.hstack([m, ((at[k] + at[k + 1]) * 0.5).reshape(3, 1)])))
    y = TOP - 0.107
    pendant = flat_round(CrossSection.circle(0.017, 32), 0.007, FRONT).translate([0.0, y, 0.0])
    bail = torus_y((0.0, y + 0.02, FRONT - 0.004), 0.005, 0.002)
    return {"main": union(links) + pendant + bail}


def brooch():
    y = TOP - 0.035
    z = FRONT
    scallops = union([ball((0.022 * math.sin(a), y + 0.022 * math.cos(a), z - 0.004), 0.0065, 12) for a in np.linspace(0.0, math.pi * 2.0, 12, endpoint=False)])
    setting = flat_round(CrossSection.circle(0.022, 40), 0.006, z).translate([0.0, y, 0.0]) + (scallops - Manifold.cube([1.0, 1.0, 1.0]).translate([-0.5, -0.5, z]))
    prongs = union([ball((0.015 * math.sin(a), y + 0.015 * math.cos(a), z - 0.008), 0.0035, 12) for a in np.linspace(math.pi * 0.25, math.pi * 2.25, 4, endpoint=False)])
    # A cut stone: a low dome with few sides, so it catches the light.
    gem = Manifold.sphere(1.0, 8).scale([0.015, 0.015, 0.009]).rotate([0.0, 0.0, 22.5]).translate([0.0, y, z - 0.006])
    gem = gem - Manifold.cube([1.0, 1.0, 1.0]).translate([-0.5, -0.5, z - 0.006])
    return {"gold": setting + prongs, "main": gem}


def lei():
    pts, normals = necklace(0.094, GAP + 0.007, TOP - 0.06, math.radians(60.0), 0.0)
    at, nat = resample(pts, normals, 0.027)
    if np.linalg.norm(at[-1] - at[0]) < 0.02:
        at.pop()
        nat.pop()
    colours = ["main", "yellow", "white", "pink"]
    regions = {c: [] for c in colours + ["orange", "green"]}
    for k, (p, n) in enumerate(zip(at, nat)):
        b = basis_up(n)
        petals = []
        for j in range(5):
            a = math.pi * 2.0 * (j + 0.25 * k) / 5
            d = b[:, 0] * math.cos(a) + b[:, 2] * math.sin(a)
            petals.append(blob(p + d * 0.0085, (0.0075, 0.004, 0.0075), 8, b))
        regions[colours[k % 4]].append(union(petals))
        regions["orange"].append(blob(p + b[:, 1] * 0.003, (0.0045, 0.003, 0.0045), 8, b))
        if k + 1 < len(at):
            mid = (p + at[k + 1]) * 0.5
            t = at[k + 1] - p
            t /= np.linalg.norm(t)
            leaf_dir = np.cross(b[:, 1], t)
            regions["green"].append(blob(mid + leaf_dir * 0.008 - b[:, 1] * 0.001, (0.007, 0.0025, 0.0035), 8, np.column_stack([leaf_dir, b[:, 1], np.cross(leaf_dir, b[:, 1])])))
    return {c: union(v) for c, v in regions.items()}


def headphones():
    # The band goes round the back of the neck on the shoulders and comes
    # forward to the cups, which rest on the chest under the chin.
    cups = []
    pads = []
    pts, normals = [], []
    for k in range(13):
        a = math.radians(70.0 + 220.0 * k / 12)
        pts.append(around(0.088, a, TOP + GAP + 0.006))
        normals.append((0.0, 1.0, 0.0))
    for sign in (-1.0, 1.0):
        x = 0.074 * sign
        y = TOP - 0.026
        pads.append(flat_round(CrossSection.circle(0.026, 40), 0.006, FRONT).translate([x, y, 0.0]))
        cups.append(flat_round(CrossSection.circle(0.025, 40), 0.016, FRONT - 0.006).translate([x, y, 0.0]))
    left = [np.array([-0.07, TOP - 0.004, FRONT - 0.012]), np.array([-0.08, TOP + GAP + 0.004, CHEST + 0.02]), around(0.088, math.radians(-70.0), TOP + GAP + 0.006)]
    right = [around(0.088, math.radians(70.0), TOP + GAP + 0.006), np.array([0.08, TOP + GAP + 0.004, CHEST + 0.02]), np.array([0.07, TOP - 0.004, FRONT - 0.012])]
    path = left + list(reversed(pts)) + right
    strap = chain(path, 0.006, 14)
    return {"ink": strap + union(pads), "main": union(cups)}


def choker():
    collar = shoulder_ring(0.076, 0.104, 0.011)
    bail = torus_y((0.0, TOP + 0.001, -0.107), 0.005, 0.002)
    # A cut drop, its few sides catching the light.
    gem = Manifold.sphere(1.0, 10).scale([0.012, 0.015, 0.008]).translate([0.0, TOP - 0.018, FRONT - 0.008])
    return {"main": collar, "gold": bail, "gem": gem}


def bell():
    collar = shoulder_ring(0.072, 0.112, 0.016)
    # A round bell hanging under the chin, with its slot printed on.
    x, y, z = 0.0, TOP - 0.036, FRONT - 0.021
    tab = chain([np.array([0.0, TOP + 0.01, -0.106]), np.array([0.0, y + 0.03, z])], 0.0045, 14)
    body = ball((x, y, z), 0.021, 32)
    slot = rbox(x - 0.015, y - 0.009, z - 0.03, x + 0.015, y - 0.005, z, 0.0015)
    slot = slot + ball((x - 0.015, y - 0.007, z - 0.018), 0.0035, 12) + ball((x + 0.015, y - 0.007, z - 0.018), 0.0035, 12)
    slot = body ^ slot
    loop = torus_y((x, y + 0.024, z), 0.006, 0.0022)
    return {"main": collar + tab, "gold": (body - slot) + loop, "ink": slot}


def big_bow():
    y = TOP - 0.035
    z = FRONT
    wings = []
    for s in (-1.0, 1.0):
        knot_end = blob((0.012 * s, y, z - 0.012), (0.006, 0.012, 0.009))
        far = blob((0.066 * s, y + 0.01, z - 0.012), (0.012, 0.03, 0.011))
        loop = Manifold.batch_hull([knot_end, far])
        # The loop's hole, pressed in.
        dent = blob((0.044 * s, y + 0.006, z - 0.026), (0.016, 0.016, 0.008))
        wings.append(loop - dent)
        tail = flat([(0.004 * s, y - 0.006), (0.016 * s, y - 0.006), (0.04 * s, y - 0.07), (0.022 * s, y - 0.074)], 0.007, z)
        wings.append(tail)
    knot = blob((0.0, y, z - 0.014), (0.015, 0.015, 0.013))
    return {"main": union(wings), "dark": knot}


STYLES = {
    "scarf": scarf,
    "long_scarf": long_scarf,
    "tie": tie,
    "bow_tie": bow_tie,
    "neckerchief": neckerchief,
    "medal": medal,
    "beads": lambda: beads(0.0115, TOP - 0.08, ["main", "light"]),
    "pearls": lambda: beads(0.0085, TOP - 0.1, ["white"]),
    "spiked_collar": spiked_collar,
    "ruff": ruff,
    "whistle": whistle,
    "pass": race_pass,
    "gold_chain": gold_chain,
    "brooch": brooch,
    "lei": lei,
    "headphones": headphones,
    "choker": choker,
    "bell": bell,
    "big_bow": big_bow,
}
# Styles whose own colour is shiny metal.
METAL = {"gold_chain": 0.6}
