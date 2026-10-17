"""Every part made by the tool. Each part is a function that builds its shape
and says where its connectors are.

A connector is a spot where the part joins another, with a type and the way
it faces out. Studs face up out of the top and sockets face down out of the
bottom. Bars, axles and hinge pins are lines, given from one end with how
long they are, and a clip, wheel hub or hole joins anywhere along one. See
scripts/parts/connectors.gd for which types go together.
"""

import math

from kit import BRICK, EDGE, FINE, PLATE, STUD, STUD_HEIGHT, STUD_RADIUS, box, cut, cylinder, front, grid_cells, plan_y, profile_x, push_x, push_z, rounded, side, studs, union

# Colours, the classic brick ones.
RED = "#c4281c"
BLUE = "#0d69ab"
YELLOW = "#f2cd37"
WHITE = "#f2f3f2"
BLACK = "#1b2a34"
DARK_GREY = "#635f61"
LIGHT_GREY = "#a3a2a4"
GREEN = "#237841"
ORANGE = "#da8540"
TYRE = "#202020"
METAL = "#9aa0a6"
GLASS = "#8fd3f4"
TRANS_RED = "#c4281c"
TRANS_CLEAR = "#e8f4f8"
TRANS_AMBER = "#f5a623"

# Mass for each cubic metre of a part's box, the same as the first parts.
DENSITY = 12.0


class Part:
    def __init__(self, id, name, kind, group, size, solid, connectors, color, **stats):
        self.id = id
        self.name = name
        self.kind = kind
        self.group = group
        # The box it fills, in metres (x across, y up, z along).
        self.size = size
        self.solid = solid
        self.connectors = connectors
        self.color = color
        self.stats = stats
        # A second piece in its own colour that isn't painted, like a tire or
        # a lens: (solid, colour, finish).
        self.trim = stats.pop("trim", None)
        # Clear lenses that shine when the lights are on, for a part whose
        # trim is something else: (solid, colour).
        self.lamp = stats.pop("lamp", None)
        self.finish = stats.pop("finish", "plastic")
        volume = size[0] * size[1] * size[2]
        self.stats.setdefault("mass", round(max(volume * DENSITY, 0.05), 2))
        self.stats.setdefault("strength", round(400 + volume * 2000, 0))


def c(type, at, axis, length=0.0):
    out = {"type": type, "at": list(at), "axis": list(axis)}
    if length:
        out["length"] = length
    return out


def top_studs(cells, top):
    return [c("stud", ((i + 0.5) * STUD, top, (k + 0.5) * STUD), (0, 1, 0)) for i, k in cells]


def sockets(cells, bottom=0.0):
    return [c("socket", ((i + 0.5) * STUD, bottom, (k + 0.5) * STUD), (0, -1, 0)) for i, k in cells]


PARTS = []


def part(fn):
    PARTS.append(fn)
    return fn


# Plates, bricks and tiles.

def _block(id, name, kind, group, across, along, plates, color, stud=True, aero=None):
    h = plates * PLATE
    cells = grid_cells(across, along)
    solid = box(0, 0, 0, across * STUD, h, along * STUD)
    connectors = sockets(cells)
    if stud:
        solid = union([solid, studs(cells, h)])
        connectors += top_studs(cells, h)
    stats = {}
    if aero:
        stats["aero"] = aero
    return Part(id, name, kind, group, (across * STUD, h, along * STUD), solid, connectors, color, **stats)


for _a, _b in [(1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 8), (2, 2), (2, 3), (2, 4), (2, 6), (2, 8), (2, 10), (4, 4), (4, 6), (4, 8), (6, 6), (6, 8), (6, 10), (6, 12)]:
    part((lambda a, b: lambda: _block("p_plate_%dx%d" % (a, b), "Plate %d×%d" % (a, b), "plate", "plates", a, b, 1, LIGHT_GREY if a >= 4 else RED))(_a, _b))

for _a, _b in [(1, 1), (1, 2), (1, 4), (1, 6), (2, 2), (2, 4)]:
    part((lambda a, b: lambda: _block("p_brick_%dx%d" % (a, b), "Brick %d×%d" % (a, b), "brick", "bricks", a, b, 3, RED))(_a, _b))

for _a, _b in [(1, 1), (1, 2), (1, 4), (1, 6), (2, 2), (2, 4), (2, 6), (1, 8), (2, 8)]:
    part((lambda a, b: lambda: _block("p_tile_%dx%d" % (a, b), "Tile %d×%d" % (a, b), "plate", "tiles", a, b, 1, BLACK, stud=False, aero={"front": 0.9, "back": 0.9}))(_a, _b))


@part
def round_plate_1x1():
    solid = union([cylinder(STUD * 0.5 - 0.004, PLATE - 0.002, "y", (STUD * 0.5, 0.001, STUD * 0.5)), studs([(0, 0)], PLATE)])
    return Part("p_round_plate_1x1", "Round plate 1×1", "plate", "plates", (STUD, PLATE, STUD), solid, sockets([(0, 0)]) + top_studs([(0, 0)], PLATE), YELLOW)


@part
def round_plate_2x2():
    solid = union([cylinder(STUD - 0.004, PLATE - 0.002, "y", (STUD, 0.001, STUD), 28), studs(grid_cells(2, 2), PLATE)])
    return Part("p_round_plate_2x2", "Round plate 2×2", "plate", "plates", (2 * STUD, PLATE, 2 * STUD), solid, sockets(grid_cells(2, 2)) + top_studs(grid_cells(2, 2), PLATE), WHITE)


@part
def round_tile_2x2():
    solid = cylinder(STUD - 0.004, PLATE - 0.002, "y", (STUD, 0.001, STUD), 28)
    return Part("p_round_tile_2x2", "Round tile 2×2", "plate", "tiles", (2 * STUD, PLATE, 2 * STUD), solid, sockets(grid_cells(2, 2)), BLACK)


@part
def round_brick_2x2():
    solid = union([cylinder(STUD - 0.004, BRICK - 0.002, "y", (STUD, 0.001, STUD), 28), studs(grid_cells(2, 2), BRICK)])
    return Part("p_round_brick_2x2", "Round brick 2×2", "brick", "bricks", (2 * STUD, BRICK, 2 * STUD), solid, sockets(grid_cells(2, 2)) + top_studs(grid_cells(2, 2), BRICK), DARK_GREY)


@part
def grille_tile_1x2():
    body = box(0, 0, 0, STUD, PLATE, 2 * STUD)
    slots = union([box(0.04, PLATE * 0.6, 0.06 + k * 0.08, STUD - 0.04, PLATE * 1.2, 0.09 + k * 0.08, edge=0) for k in range(5)])
    return Part("p_grille_1x2", "Grille tile 1×2", "plate", "tiles", (STUD, PLATE, 2 * STUD), cut(body, slots), sockets(grid_cells(1, 2)), DARK_GREY)


# Slopes and curves, all with their slope or curve at the front (-z).

def _slope(id, name, across, along, plates, flat, color, aero):
    """A slope that rises from a thin lip at the front to full height, with
    `flat` studs of flat top at the back."""
    h = plates * PLATE
    l = along * STUD
    lip = 0.04
    pts = [(0, 0), (0, lip), (l - flat * STUD, h), (l, h), (l, 0)]
    solid = profile_x(pts, 0.002, across * STUD - 0.002)
    cells_top = [(i, k) for i in range(across) for k in range(along - flat, along)]
    if flat:
        solid = union([solid, studs(cells_top, h)])
    return Part(id, name, "body", "slopes", (across * STUD, h, l), solid, sockets(grid_cells(across, along)) + top_studs(cells_top, h), color, aero=aero)


def _curve(id, name, across, along, plates, flat, color, aero):
    """A curved slope: a quarter of a smooth curve up from the front to full
    height, with `flat` studs of flat top at the back (or none)."""
    h = plates * PLATE
    l = along * STUD
    run = l - flat * STUD
    pts = [(0.0, 0.0)]
    for k in range(17):
        t = k / 16.0
        pts.append((run * t, 0.03 + (h - 0.03) * math.sin(t * math.pi * 0.5)))
    pts += [(l, h), (l, 0.0)]
    solid = profile_x(pts, 0.002, across * STUD - 0.002)
    cells_top = [(i, k) for i in range(across) for k in range(along - flat, along)]
    if flat:
        solid = union([solid, studs(cells_top, h)])
    return Part(id, name, "body", "curves", (across * STUD, h, l), solid, sockets(grid_cells(across, along)) + top_studs(cells_top, h), color, aero=aero)


part(lambda: _slope("p_cheese_1x1", "Cheese slope 1×1", 1, 1, 2, 0, YELLOW, {"front": 0.6, "back": 1.0}))
part(lambda: _slope("p_cheese_1x2", "Cheese slope 1×2", 1, 2, 2, 0, YELLOW, {"front": 0.5, "back": 1.0}))
part(lambda: _slope("p_slope_1x2", "Slope 1×2", 1, 2, 3, 1, RED, {"front": 0.55, "back": 1.0}))
part(lambda: _slope("p_slope_2x2", "Slope 2×2", 2, 2, 3, 1, RED, {"front": 0.55, "back": 1.0}))
part(lambda: _slope("p_slope_1x3", "Slope 1×3", 1, 3, 3, 1, RED, {"front": 0.45, "back": 1.0}))
part(lambda: _slope("p_slope_2x4", "Long slope 2×4", 2, 4, 3, 1, RED, {"front": 0.4, "back": 1.0}))
part(lambda: _curve("p_curve_1x2", "Curved slope 1×2", 1, 2, 2, 0, RED, {"front": 0.4, "back": 1.0}))
part(lambda: _curve("p_curve_1x3", "Curved slope 1×3", 1, 3, 2, 0, RED, {"front": 0.38, "back": 1.0}))
part(lambda: _curve("p_curve_1x4", "Curved slope 1×4", 1, 4, 2, 0, RED, {"front": 0.35, "back": 1.0}))
part(lambda: _curve("p_curve_2x2", "Curved slope 2×2", 2, 2, 2, 0, RED, {"front": 0.4, "back": 1.0}))
part(lambda: _curve("p_curve_2x4", "Curved slope 2×4", 2, 4, 3, 1, RED, {"front": 0.35, "back": 1.0}))
part(lambda: _curve("p_curve_2x6", "Curved slope 2×6", 2, 6, 3, 1, RED, {"front": 0.3, "back": 1.0}))
part(lambda: _curve("p_curve_2x8", "Long curved slope 2×8", 2, 8, 3, 2, RED, {"front": 0.28, "back": 1.0}))
part(lambda: _curve("p_curve_4x4", "Wide curved slope 4×4", 4, 4, 3, 1, RED, {"front": 0.33, "back": 1.0}))


@part
def inverted_curve_1x2():
    h = 2 * PLATE
    l = 2 * STUD
    pts = [(0.0, h), (0.0, h - 0.03)] + [(l * (k / 16.0), (h - 0.03) * (1 - math.sin((k / 16.0) * math.pi * 0.5))) for k in range(1, 17)] + [(l, h)]
    solid = union([profile_x(pts, 0.002, STUD - 0.002), studs(grid_cells(1, 2), h)])
    return Part("p_inverted_curve_1x2", "Inverted curve 1×2", "body", "curves", (STUD, h, l), solid, top_studs(grid_cells(1, 2), h) + sockets([(0, 1)]), RED, aero={"front": 0.7, "back": 1.0})


@part
def bow_1x4():
    """An arch-shaped curved brick, highest in the middle, for wheel arches
    and rounded noses."""
    h = 2 * PLATE
    l = 4 * STUD
    pts = [(0.0, 0.0)]
    for k in range(25):
        t = k / 24.0
        pts.append((l * t, 0.03 + (h - 0.03) * math.sin(t * math.pi)))
    pts.append((l, 0.0))
    solid = profile_x(pts, 0.002, STUD - 0.002)
    return Part("p_bow_1x4", "Bow 1×4", "body", "curves", (STUD, h, l), solid, sockets([(0, 0), (0, 3)]), RED, aero={"front": 0.45, "back": 0.45, "side": 0.8})


def _wedge(id, name, side, color):
    """A wedge plate, square at the back and cut away to a point at the front
    on one side."""
    w = 3 * STUD
    l = 2 * STUD
    if side == "left":
        pts = [(0.0, l), (w, l), (w, 0.0), (w - STUD, 0.0)]
    else:
        pts = [(0.0, l), (w, l), (STUD, 0.0), (0.0, 0.0)]
    solid = plan_y([(x, z) for x, z in pts], 0.001, PLATE - 0.001)
    cells = [(2, 0), (0, 1), (1, 1), (2, 1)] if side == "left" else [(0, 0), (0, 1), (1, 1), (2, 1)]
    solid = union([solid, studs(cells, PLATE)])
    return Part(id, name, "plate", "plates", (w, PLATE, l), solid, sockets(cells) + top_studs(cells, PLATE), color, mirror=("p_wedge_3x2_right" if side == "left" else "p_wedge_3x2_left"))


part(lambda: _wedge("p_wedge_3x2_left", "Wedge plate 3×2 left", "left", WHITE))
part(lambda: _wedge("p_wedge_3x2_right", "Wedge plate 3×2 right", "right", WHITE))


@part
def wheel_arch_1x4():
    """A mudguard arch over a wheel, two plates thick at the ends."""
    l = 4 * STUD
    h = 3 * PLATE
    outer = []
    for k in range(25):
        t = k / 24.0
        outer.append((l * 0.5 - math.cos(t * math.pi) * l * 0.5, h * math.sin(t * math.pi)))
    inner = [(l * 0.5 - math.cos(t * math.pi) * (l * 0.5 - 0.06), (h - 0.06) * math.sin(t * math.pi)) for t in [k / 24.0 for k in range(24, -1, -1)]]
    pts = outer + [(l - 0.06, 0.0)] + inner[1:-1] + [(0.06, 0.0)]
    solid = profile_x(pts, 0.002, STUD - 0.002)
    return Part("p_arch_1x4", "Wheel arch 1×4", "body", "arches", (STUD, h, l), solid, sockets([(0, 0), (0, 3)]), BLACK, aero={"front": 0.6, "back": 0.6, "side": 0.9})


# Bars and clips. A bar is a fifth of a stud across, the same as the round
# bit of a clip holds.

BAR = 0.05  # radius


def _bar(id, name, studs_long, color):
    l = studs_long * STUD
    solid = cylinder(BAR, l - 0.004, "z", (BAR, BAR, 0.002), 12)
    return Part(id, name, "body", "bars", (2 * BAR, 2 * BAR, l), solid, [c("bar", (BAR, BAR, 0.0), (0, 0, 1), l)], color)


for _n in (2, 3, 4, 6):
    part((lambda n: lambda: _bar("p_bar_%d" % n, "Bar %d long" % n, n, LIGHT_GREY))(_n))


@part
def plate_clip_1x1():
    """A plate 1×1 with a clip on its front edge that holds a bar across."""
    plate = union([box(0, 0, 0, STUD, PLATE, STUD), studs([(0, 0)], PLATE)])
    ring = cut(cylinder(BAR + 0.025, 0.12, "x", (0.065, PLATE * 0.5, -BAR - 0.01), 14), cylinder(BAR, 0.14, "x", (0.055, PLATE * 0.5, -BAR - 0.01), 14))
    solid = union([plate, ring, box(0.065, 0.0, -0.04, 0.185, PLATE, 0.01, edge=0.004)])
    con = sockets([(0, 0)]) + top_studs([(0, 0)], PLATE) + [c("clip", (STUD * 0.5, PLATE * 0.5, -BAR - 0.01), (1, 0, 0))]
    return Part("p_plate_clip_1x1", "Plate 1×1 with clip", "plate", "bars", (STUD, PLATE, STUD), solid, con, LIGHT_GREY, solids=[[0, 0, 0, STUD, PLATE, STUD]])


@part
def plate_handle_1x2():
    """A plate 1×2 with a bar handle along the top, for clips to hold."""
    plate = box(0, 0, 0, STUD, PLATE, 2 * STUD)
    handle = union([cylinder(BAR * 0.8, 0.08, "y", (STUD * 0.5, PLATE, 0.06), 10), cylinder(BAR * 0.8, 0.08, "y", (STUD * 0.5, PLATE, 2 * STUD - 0.06), 10),
                    cylinder(BAR, 2 * STUD - 0.08, "z", (STUD * 0.5, PLATE + 0.08, 0.04), 12)])
    con = sockets(grid_cells(1, 2)) + [c("bar", (STUD * 0.5, PLATE + 0.08, 0.06), (0, 0, 1), 2 * STUD - 0.12)]
    return Part("p_plate_handle_1x2", "Plate 1×2 with handle", "plate", "bars", (STUD, PLATE + 0.08 + BAR, 2 * STUD), union([plate, handle]), con, BLACK, solids=[[0, 0, 0, STUD, PLATE, 2 * STUD]])


@part
def bar_holder_clip():
    """A round 1×1 bar holder with a clip, to hang things off bars at any
    angle."""
    body = cylinder(STUD * 0.5 - 0.004, BRICK * 0.5, "y", (STUD * 0.5, 0.0, STUD * 0.5), 16)
    ring = cut(cylinder(BAR + 0.025, 0.12, "x", (0.065, BRICK * 0.25, -BAR - 0.01), 14), cylinder(BAR, 0.14, "x", (0.055, BRICK * 0.25, -BAR - 0.01), 14))
    con = sockets([(0, 0)]) + [c("clip", (STUD * 0.5, BRICK * 0.25, -BAR - 0.01), (1, 0, 0)), c("stud", (STUD * 0.5, BRICK * 0.5, STUD * 0.5), (0, 1, 0))]
    return Part("p_bar_holder", "Bar holder with clip", "body", "bars", (STUD, BRICK * 0.5, STUD), union([body, ring, studs([(0, 0)], BRICK * 0.5)]), con, DARK_GREY, solids=[[0, 0, 0, STUD, BRICK * 0.5, STUD]])


# Beams, pins and axles. Holes go across (x) through beams a stud
# apart, and pins and axles go through them.

HOLE = 0.06  # radius of a pin hole
BEAM_H = 0.225


def _beam(id, name, n, color):
    l = n * STUD
    pts = []
    r = BEAM_H * 0.5
    for k in range(13):
        a = math.pi * 0.5 + k * math.pi / 12.0
        pts.append((r + math.cos(a) * r, r + math.sin(a) * r))
    for k in range(13):
        a = -math.pi * 0.5 + k * math.pi / 12.0
        pts.append((l - r + math.cos(a) * r, r + math.sin(a) * r))
    solid = profile_x(pts, 0.004, STUD - 0.004)
    holes = [cylinder(HOLE, STUD + 0.02, "x", (-0.01, r, (k + 0.5) * STUD), 14) for k in range(n)]
    con = [c("hole", (0.0, r, (k + 0.5) * STUD), (1, 0, 0), STUD) for k in range(n)]
    return Part(id, name, "body", "technic", (STUD, BEAM_H, l), cut(solid, *holes), con, color)


for _n in (3, 5, 7, 9):
    part((lambda n: lambda: _beam("p_beam_%d" % n, "Beam %d long" % n, n, LIGHT_GREY))(_n))


@part
def technic_brick_1x4():
    solid = union([box(0, 0, 0, STUD, BRICK, 4 * STUD), studs(grid_cells(1, 4), BRICK)])
    holes = [cylinder(HOLE, STUD + 0.02, "x", (-0.01, 0.17, (k + 1) * STUD), 14) for k in range(3)]
    con = sockets(grid_cells(1, 4)) + top_studs(grid_cells(1, 4), BRICK) + [c("hole", (0.0, 0.17, (k + 1) * STUD), (1, 0, 0), STUD) for k in range(3)]
    return Part("p_technic_brick_1x4", "Brick 1×4 with holes", "brick", "technic", (STUD, BRICK, 4 * STUD), cut(solid, *holes), con, BLACK)


@part
def pin():
    """A pin two studs long, half in one hole and half in the next."""
    solid = union([cylinder(HOLE - 0.006, 2 * STUD - 0.01, "x", (0.005, HOLE, HOLE), 14), cylinder(HOLE + 0.01, 0.02, "x", (STUD - 0.01, HOLE, HOLE), 14)])
    return Part("p_pin", "Pin", "body", "technic", (2 * STUD, 2 * HOLE, 2 * HOLE), solid, [c("pin", (0.0, HOLE, HOLE), (1, 0, 0), 2 * STUD)], BLACK, solids=[])


def _axle(id, name, n, color):
    l = n * STUD
    w = 0.03
    cross = union([box(0.002, HOLE - w, HOLE - 0.055, l - 0.002, HOLE + w, HOLE + 0.055, edge=0.0), box(0.002, HOLE - 0.055, HOLE - w, l - 0.002, HOLE + 0.055, HOLE + w, edge=0.0)])
    return Part(id, name, "body", "technic", (l, 2 * HOLE, 2 * HOLE), cross, [c("axle", (0.0, HOLE, HOLE), (1, 0, 0), l)], color, solids=[])


for _n in (2, 3, 4, 6, 8):
    part((lambda n: lambda: _axle("p_axle_%d" % n, "Axle %d long" % n, n, DARK_GREY))(_n))


@part
def wheel_holder_2x2():
    """A plate 2×2 with a pin out of each side for a wheel to go on."""
    plate = union([box(STUD, 0, 0, 3 * STUD, PLATE, 2 * STUD), studs([(1, 0), (2, 0), (1, 1), (2, 1)], PLATE)])
    pins = cylinder(HOLE - 0.006, 4 * STUD, "x", (0.0, PLATE * 0.5, STUD), 14)
    cells = [(1, 0), (2, 0), (1, 1), (2, 1)]
    con = sockets(cells) + top_studs(cells, PLATE) + [c("pin", (0.0, PLATE * 0.5, STUD), (1, 0, 0), STUD), c("pin", (3 * STUD, PLATE * 0.5, STUD), (1, 0, 0), STUD)]
    return Part("p_wheel_holder_2x2", "Wheel holder 2×2", "plate", "technic", (4 * STUD, PLATE, 2 * STUD), union([plate, pins]), con, BLACK, solids=[[STUD, 0, 0, 3 * STUD, PLATE, 2 * STUD]])


@part
def axle_plate_2x6():
    """A long plate 2×6 with an axle across underneath at each end, for a
    kart's front and back wheels."""
    plate = union([box(STUD, 0.06, 0, 3 * STUD, 0.06 + PLATE, 6 * STUD), studs([(i, k) for i in (1, 2) for k in range(6)], 0.06 + PLATE)])
    axles = [box(0.0, 0.0, z - 0.04, 4 * STUD, 0.08, z + 0.04, edge=0.0) for z in (STUD * 0.5, 5.5 * STUD)]
    cells = [(i, k) for i in (1, 2) for k in range(6)]
    con = top_studs(cells, 0.06 + PLATE) + [c("axle", (0.0, 0.04, z), (1, 0, 0), STUD) for z in (STUD * 0.5, 5.5 * STUD)] + [c("axle", (3 * STUD, 0.04, z), (1, 0, 0), STUD) for z in (STUD * 0.5, 5.5 * STUD)]
    return Part("p_axle_plate_2x6", "Axle plate 2×6", "plate", "technic", (4 * STUD, 0.06 + PLATE, 6 * STUD), union([plate] + axles), con, DARK_GREY, solids=[[STUD, 0.0, 0, 3 * STUD, 0.06 + PLATE, 6 * STUD]])


# Hinges and joints.

@part
def hinge_base_1x2():
    """The bottom half of a hinge: a plate 1×2 with the knuckle at its front
    edge, turning about a line across."""
    plate = union([box(0, 0, 0, STUD, PLATE, 2 * STUD), studs([(0, 1)], PLATE)])
    knuckle = union([cylinder(PLATE * 0.5, 0.07, "x", (0.0, PLATE * 0.5, 0.0), 14), cylinder(PLATE * 0.5, 0.07, "x", (STUD - 0.07, PLATE * 0.5, 0.0), 14)])
    con = sockets(grid_cells(1, 2)) + top_studs([(0, 1)], PLATE) + [c("hinge_a", (0.0, PLATE * 0.5, 0.0), (1, 0, 0), STUD)]
    return Part("p_hinge_base", "Hinge base 1×2", "plate", "hinges", (STUD, PLATE, 2 * STUD), union([plate, knuckle]), con, LIGHT_GREY)


@part
def hinge_top_1x2():
    """The top half of a hinge, a plate 1×2 with the finger at its back edge."""
    plate = union([box(0, 0, 0, STUD, PLATE, 2 * STUD), studs(grid_cells(1, 2), PLATE)])
    finger = cylinder(PLATE * 0.5, STUD - 0.15, "x", (0.075, PLATE * 0.5, 2 * STUD), 14)
    con = sockets([(0, 0)]) + top_studs(grid_cells(1, 2), PLATE) + [c("hinge_b", (0.0, PLATE * 0.5, 2 * STUD), (1, 0, 0), STUD)]
    return Part("p_hinge_top", "Hinge top 1×2", "plate", "hinges", (STUD, PLATE, 2 * STUD), union([plate, finger]), con, LIGHT_GREY)


@part
def ball_plate_1x2():
    plate = union([box(0, 0, 0, STUD, PLATE, 2 * STUD), studs([(0, 1)], PLATE)])
    ball = union([cylinder(0.03, 0.06, "-z", (STUD * 0.5, PLATE * 0.5, 0.0), 10), Manifold_sphere(0.075, (STUD * 0.5, PLATE * 0.5, -0.1))])
    con = sockets(grid_cells(1, 2)) + top_studs([(0, 1)], PLATE) + [c("ball", (STUD * 0.5, PLATE * 0.5, -0.1), (0, 0, -1))]
    return Part("p_ball_plate", "Plate 1×2 with ball", "plate", "hinges", (STUD, PLATE, 2 * STUD), union([plate, ball]), con, LIGHT_GREY, solids=[[0, 0, 0, STUD, PLATE, 2 * STUD]])


@part
def cup_plate_1x2():
    plate = union([box(0, 0, 0, STUD, PLATE, 2 * STUD), studs([(0, 1)], PLATE)])
    cup = cut(Manifold_sphere(0.1, (STUD * 0.5, PLATE * 0.5, -0.1)), Manifold_sphere(0.076, (STUD * 0.5, PLATE * 0.5, -0.1)), box(0.0, -0.1, -0.25, STUD, 0.3, -0.13, edge=0))
    con = sockets(grid_cells(1, 2)) + top_studs([(0, 1)], PLATE) + [c("cup", (STUD * 0.5, PLATE * 0.5, -0.1), (0, 0, -1))]
    return Part("p_cup_plate", "Plate 1×2 with cup", "plate", "hinges", (STUD, PLATE, 2 * STUD), union([plate, cup]), con, LIGHT_GREY, solids=[[0, 0, 0, STUD, PLATE, 2 * STUD]])


def Manifold_sphere(r, at):
    from manifold3d import Manifold
    return Manifold.sphere(r, 16).translate(list(at))


# Brackets, for studs facing forward or to the side.

@part
def bracket_1x2():
    """A plate 1×2 with a plate standing up at its front, studs facing
    forward."""
    flat = box(0, 0, 0, 2 * STUD, PLATE, STUD)
    up = box(0, 0, -PLATE, 2 * STUD, 2 * STUD, 0.0)
    front_studs = union([cylinder(STUD_RADIUS, STUD_HEIGHT, "-z", ((i + 0.5) * STUD, STUD * 1.5, -PLATE + 0.001), 12) for i in range(2)])
    con = sockets([(0, 0), (1, 0)]) + top_studs([(0, 0), (1, 0)], PLATE) + [c("stud", ((i + 0.5) * STUD, STUD * 1.5, -PLATE), (0, 0, -1)) for i in range(2)]
    solid = union([flat, up, studs([(0, 0), (1, 0)], PLATE), front_studs])
    return Part("p_bracket_1x2", "Bracket 1×2", "plate", "brackets", (2 * STUD, 2 * STUD, STUD + PLATE), solid.translate([0, 0, PLATE]), [_shift(x, (0, 0, PLATE)) for x in con], WHITE)


def _shift(conn, by):
    out = dict(conn)
    out["at"] = [conn["at"][0] + by[0], conn["at"][1] + by[1], conn["at"][2] + by[2]]
    return out


@part
def side_stud_brick_1x1():
    """A brick 1×1 with a stud on its front as well as its top."""
    solid = union([box(0, 0, 0, STUD, BRICK, STUD), studs([(0, 0)], BRICK), cylinder(STUD_RADIUS, STUD_HEIGHT, "-z", (STUD * 0.5, BRICK * 0.5, 0.001), 12)])
    con = sockets([(0, 0)]) + top_studs([(0, 0)], BRICK) + [c("stud", (STUD * 0.5, BRICK * 0.5, 0.0), (0, 0, -1))]
    return Part("p_side_stud_brick", "Brick 1×1 with side stud", "brick", "brackets", (STUD, BRICK, STUD), solid, con, WHITE)


@part
def headlight_brick():
    """A brick 1×1 with a sunken stud on its front, the classic way to turn
    a light or grille sideways."""
    solid = cut(union([box(0, 0, 0, STUD, BRICK, STUD), studs([(0, 0)], BRICK)]), box(0.03, 0.06, -0.01, STUD - 0.03, BRICK - 0.04, 0.05, edge=0))
    solid = union([solid, cylinder(STUD_RADIUS, STUD_HEIGHT + 0.03, "-z", (STUD * 0.5, BRICK * 0.5, 0.05), 12)])
    con = sockets([(0, 0)]) + top_studs([(0, 0)], BRICK) + [c("stud", (STUD * 0.5, BRICK * 0.5, 0.0), (0, 0, -1))]
    return Part("p_headlight_brick", "Headlight brick", "brick", "brackets", (STUD, BRICK, STUD), solid, con, WHITE)


# Wheels. The rim is the part's own colour and the tire is black. A wheel
# goes onto a pin or an axle through the middle of its hub, which runs
# across (x).

def _revolve_x(points, at, sides=36):
    """Spins a side view round the x axis. Points are (along x, out from the
    axis)."""
    from manifold3d import CrossSection
    from kit import _anticlockwise
    section = CrossSection([_anticlockwise([(r, x) for x, r in points])])
    solid = section.revolve(sides)
    # Revolving goes round z with the section's x as the radius and y along
    # z, so turn z onto x.
    return solid.rotate([0, 90, 0]).translate(list(at))


def _wheel(id, name, radius, width, rim_radius, grip, rolling, offroad=0.0, lugs=0, color=LIGHT_GREY, about="", deep=None, finish="plastic", shoulder=None, **stats):
    """A wheel. `deep` is (lugs round, how tall, half their length) for a
    chunky tread whose tops reach `radius`, with the tire under them."""
    w = width
    body = radius - deep[1] if deep else radius
    shoulder = shoulder or min(0.06, w * 0.25)
    tire = [(0.0, rim_radius * 0.92), (0.0, body - shoulder), (shoulder * 0.4, body - shoulder * 0.2), (shoulder, body),
            (w - shoulder, body), (w - shoulder * 0.4, body - shoulder * 0.2), (w, body - shoulder), (w, rim_radius * 0.92)]
    tire_solid = _revolve_x(tire, (0.0, radius, radius))
    if lugs:
        tire_solid = union([tire_solid] + _lugs(lugs, radius, w))
    if deep:
        tire_solid = union([tire_solid] + _lugs(deep[0], body, w, deep[1] + 0.03, deep[2], 0.03, radius))
    hub = HOLE + 0.02
    rim = [(0.004, hub), (0.004, rim_radius * 0.6), (w * 0.3, rim_radius * 0.75), (w * 0.3, rim_radius), (w - 0.004, rim_radius), (w - 0.004, hub)]
    rim_solid = _revolve_x(rim, (0.0, radius, radius), 28)
    con = [c("hub", (0.0, radius, radius), (1, 0, 0), w)]
    stats.update({"radius": radius, "width": w, "grip": grip, "rolling": rolling, "trim": (tire_solid, TYRE, "plastic")})
    if offroad:
        stats["offroad"] = offroad
    if about:
        stats["about"] = about
    if finish != "plastic":
        stats["finish"] = finish
    return Part(id, name, "wheel", "wheels", (w, 2 * radius, 2 * radius), rim_solid, con, color, **stats)


def _lugs(n, radius, w, height=0.06, half=0.045, sink=0.035, centre=None):
    """Two staggered rings of tread blocks round a tire of this radius,
    `height` tall from `sink` under its surface, on a wheel whose middle is
    `centre` high and back (the radius if not given)."""
    centre = radius if centre is None else centre
    out = []
    for k in range(n):
        for side in (0, 1):
            a = (k + 0.5 * side) * 360.0 / n
            x0 = 0.01 + side * w * 0.5
            lug = box(x0, radius - sink, -half, x0 + w * 0.45, radius - sink + height, half, edge=0.006)
            out.append(lug.rotate([a, 0, 0]).translate([0, centre, centre]))
    return out


part(lambda: _wheel("w_kart", "Kart wheel", 0.3, 0.25, 0.2, 1.0, 0.015, color=LIGHT_GREY))
part(lambda: _wheel("w_kart_wide", "Wide kart wheel", 0.3, 0.45, 0.2, 1.2, 0.022, color=LIGHT_GREY))
part(lambda: _wheel("w_racing", "Racing tire", 0.35, 0.35, 0.27, 1.15, 0.018, color=WHITE))
part(lambda: _wheel("w_slick", "Big slick", 0.4, 0.5, 0.28, 1.35, 0.028, color=DARK_GREY))
part(lambda: _wheel("w_offroad", "Off-road wheel", 0.42, 0.4, 0.25, 1.05, 0.03, offroad=0.6, lugs=14, color=YELLOW))
# Motorbike tires are thin, so they don't hold a bend as well as a kart's.
part(lambda: _wheel("w_moto", "Motorbike wheel", 0.45, 0.2, 0.34, 0.95, 0.014, color=BLACK))
part(lambda: _wheel("w_moto_trail", "Trail bike wheel", 0.45, 0.22, 0.32, 0.88, 0.02, offroad=0.5, lugs=16, color=RED))
part(lambda: _wheel("w_scooter", "Scooter wheel", 0.3, 0.18, 0.2, 0.95, 0.016, color=WHITE))
# Wheels for the bigger stock vehicles. Their weight and strength go by
# their size, like the first wheels.
part(lambda: _wheel("w_drag_slick", "Dragster slick", 0.5, 0.6, 0.28, 1.5, 0.03, offroad=-0.35, color=METAL, finish="metal", mass=9.0, strength=1400.0,
                    about="A huge soft slick for the back of a dragster. It grips the road like nothing else, and is hopeless on grass."))
# The dragster front wheel is as small as a wheel can be on an axle plate
# and still leave two plates under the plate.
part(lambda: _wheel("w_drag_front", "Dragster front wheel", 0.26, 0.12, 0.2, 0.9, 0.01, color=METAL, finish="metal", mass=1.2, strength=900.0,
                    about="Tiny and thin, for the front of a dragster. It rolls easily but barely grips."))
part(lambda: _wheel("w_monster", "Monster truck wheel", 0.6, 0.7, 0.32, 1.2, 0.042, offroad=0.75, color=LIGHT_GREY, deep=(16, 0.07, 0.075), shoulder=0.09,
                    mass=16.0, strength=1700.0, about="Huge, with deep tread. It climbs over anything, but lifts the truck up high where it rolls in corners."))
part(lambda: _wheel("w_truck", "Truck tire", 0.45, 0.5, 0.26, 1.1, 0.032, offroad=0.65, color=WHITE, deep=(16, 0.045, 0.055), shoulder=0.07,
                    mass=8.0, strength=1450.0, about="A chunky knobbly tire for trucks. Good on dirt and grass, a little slow on the road."))
part(lambda: _wheel("w_quad", "Quad wheel", 0.28, 0.4, 0.17, 1.1, 0.03, offroad=0.6, color=WHITE, deep=(12, 0.04, 0.045), shoulder=0.09,
                    mass=4.5, strength=1250.0, about="Small, fat and knobbly, for quads. It grips well on dirt."))


@part
def mudguard_2x4():
    """A mudguard arch two studs wide that clips over a wheel, with a plate
    to fix it at each end."""
    l = 4 * STUD
    h = 3 * PLATE
    outer = [(l * 0.5 - math.cos(t * math.pi) * l * 0.5, h * math.sin(t * math.pi)) for t in [k / 24.0 for k in range(25)]]
    inner = [(l * 0.5 - math.cos(t * math.pi) * (l * 0.5 - 0.05), (h - 0.05) * math.sin(t * math.pi)) for t in [k / 24.0 for k in range(24, -1, -1)]]
    arch = profile_x(outer + [(l - 0.05, 0.0)] + inner[1:-1] + [(0.05, 0.0)], 0.002, 2 * STUD - 0.002)
    cells = [(0, 0), (1, 0), (0, 3), (1, 3)]
    return Part("p_mudguard_2x4", "Mudguard 2×4", "body", "arches", (2 * STUD, h, l), arch, sockets(cells), RED, aero={"front": 0.5, "back": 0.6, "side": 0.9})


# Bike parts.

@part
def front_fork():
    """A motorbike's front fork: a crown with studs on top and two legs down
    to an axle the wheel goes on. From the axle to the bottom of the crown is
    a brick more than on the swingarm, so with the same wheels a brick (or an
    engine as tall) on the swingarm brings it level with the crown. It turns
    with the wheel in it when that's a steered wheel."""
    top = 0.7
    crown = union([box(0, top, 0, 2 * STUD, top + PLATE, STUD), studs(grid_cells(2, 1), top + PLATE)])
    legs = [box(x, 0.0, 0.07, x + 0.08, top + 0.01, 0.18, edge=0.01) for x in (0.03, 2 * STUD - 0.11)]
    axle = cylinder(0.03, 2 * STUD - 0.06, "x", (0.03, 0.045, 0.125), 10)
    con = top_studs(grid_cells(2, 1), top + PLATE) + sockets(grid_cells(2, 1), top) + [c("axle", (0.11, 0.045, 0.125), (1, 0, 0), 2 * STUD - 0.22)]
    solids = [[0, top, 0, 2 * STUD, top + PLATE, STUD], [0.03, 0.0, 0.07, 0.11, top + 0.01, 0.18], [2 * STUD - 0.11, 0.0, 0.07, 2 * STUD - 0.03, top + 0.01, 0.18]]
    return Part("b_fork", "Front fork", "body", "bike", (2 * STUD, top + PLATE, STUD), union([crown, axle] + legs), con, METAL, finish="metal", solids=solids, steers=True)


@part
def swingarm():
    """The back fork of a motorbike that holds the back wheel, reaching back
    from a plate with studs on top."""
    base = union([box(0, 0.4, 0, 2 * STUD, 0.4 + PLATE, 2 * STUD), studs(grid_cells(2, 2), 0.4 + PLATE)])
    arms = [box(x, 0.02, 0.3, x + 0.07, 0.42, 1.0, edge=0.01) for x in (0.03, 2 * STUD - 0.1)]
    axle = cylinder(0.03, 2 * STUD - 0.06, "x", (0.03, 0.045, 0.875), 10)
    con = top_studs(grid_cells(2, 2), 0.4 + PLATE) + sockets(grid_cells(2, 2), 0.4) + [c("axle", (0.1, 0.045, 0.875), (1, 0, 0), 2 * STUD - 0.2)]
    solids = [[0, 0.4, 0, 2 * STUD, 0.4 + PLATE, 2 * STUD], [0.03, 0.02, 0.3, 0.1, 0.42, 1.0], [2 * STUD - 0.1, 0.02, 0.3, 2 * STUD - 0.03, 0.42, 1.0]]
    return Part("b_swingarm", "Swingarm", "body", "bike", (2 * STUD, 0.4 + PLATE, 1.0), union([base, axle] + arms), con, BLACK, solids=solids)


@part
def fuel_tank():
    """A rounded motorbike tank, 2×2, for under the bars."""
    l = 2 * STUD
    h = 2 * PLATE + 0.06
    pts = [(0.0, 0.0), (0.0, h * 0.5)] + [(l * 0.5 - math.cos(t * math.pi) * l * 0.5, h * 0.5 + h * 0.5 * math.sin(t * math.pi)) for t in [k / 16.0 for k in range(1, 16)]] + [(l, h * 0.5), (l, 0.0)]
    side = profile_x(pts, 0.03, 2 * STUD - 0.03)
    return Part("b_tank", "Fuel tank", "body", "bike", (2 * STUD, h, l), side, sockets(grid_cells(2, 2)), RED, aero={"front": 0.5, "back": 0.6, "side": 0.8})


@part
def saddle():
    """A motorbike saddle, 2×3. You sit astride it."""
    l = 3 * STUD
    h = 2 * PLATE
    pts = [(0.0, 0.0), (0.0, h * 0.7), (0.15, h), (l - 0.1, h * 0.95), (l, h * 0.6), (l, 0.0)]
    solid = profile_x(pts, 0.02, 2 * STUD - 0.02)
    return Part("b_saddle", "Saddle", "seat", "bike", (2 * STUD, h, l), solid, sockets(grid_cells(2, 3)), BLACK, control=1.05, driver_height=7, astride=True)


@part
def bike_bars():
    """Motorbike handlebars on a stem at the front, swept back over a tank
    toward the rider, with grips. They turn about the stem."""
    high = PLATE + 0.3
    back = 3 * STUD - 0.05
    stem = union([box(STUD * 1.5, 0, 0, STUD * 2.5, PLATE, STUD), cylinder(0.035, 0.3 + 0.025, "y", (2 * STUD, PLATE, STUD * 0.5), 10)])
    riser = cylinder(0.025, back - STUD * 0.5, "z", (2 * STUD, high, STUD * 0.5), 10)
    bar = cylinder(0.025, 0.7, "x", (2 * STUD - 0.35, high, back), 10)
    grips = [cylinder(0.04, 0.14, "x", (x, high, back), 10) for x in (2 * STUD - 0.42, 2 * STUD + 0.28)]
    con = sockets([(1, 0), (2, 0)])
    return Part("b_bars", "Bike bars", "steering", "bike", (4 * STUD, PLATE + 0.34, 3 * STUD), union([stem, riser, bar]), con, METAL, finish="metal", control=1.15, style="bikebars",
                trim=(union(grips), BLACK, "plastic"), solids=[[STUD * 1.5, 0, 0, STUD * 2.5, PLATE, STUD]])


@part
def footpegs():
    plate = union([box(STUD, 0, 0, 3 * STUD, PLATE, STUD), studs([(1, 0), (2, 0)], PLATE)])
    pegs = cylinder(0.03, 4 * STUD, "x", (0.0, PLATE * 0.5, STUD * 0.5), 10)
    return Part("b_footpegs", "Footpegs", "plate", "bike", (4 * STUD, PLATE, STUD), union([plate, pegs]), sockets([(1, 0), (2, 0)]) + top_studs([(1, 0), (2, 0)], PLATE), METAL,
                finish="metal", solids=[[STUD, 0, 0, 3 * STUD, PLATE, STUD]])


@part
def nose_fairing():
    """A rounded front fairing for a motorbike, with a headlight in it."""
    l = 2 * STUD
    h = 0.45
    pts = [(0.0, 0.05)] + [(l * 0.9 * (1 - math.sin(t * math.pi * 0.5)), 0.05 + (h - 0.05) * t) for t in [k / 12.0 for k in range(13)]] + [(l, h), (l, 0.0), (0.2, 0.0)]
    shell = profile_x(pts, 0.03, 2 * STUD - 0.03)
    lamp = cylinder(0.08, 0.04, "-z", (STUD, 0.22, 0.17), 16)
    return Part("b_nose", "Front fairing", "body", "bike", (2 * STUD, h, l), shell, sockets([(0, 1), (1, 1)]), WHITE, aero={"front": 0.35, "back": 1.0, "side": 0.8},
                trim=(lamp, TRANS_CLEAR, "glass"), light="head")


def _capsule(a, b, r):
    """A rod with round ends from a to b, like a frame tube."""
    from manifold3d import Manifold
    return Manifold.batch_hull([Manifold.sphere(r, 10).translate(list(a)), Manifold.sphere(r, 10).translate(list(b))])


# Bodywork made for karts.

@part
def nose_4x6():
    """A racing nose, 4 wide at the back and narrowing to 2 at the tip,
    curving up from a thin tip to 3 plates high."""
    w = 4 * STUD
    l = 6 * STUD
    h = 3 * PLATE
    plan = plan_y([(STUD, 0.0), (3 * STUD, 0.0), (w, 2.5 * STUD), (w, l), (0.0, l), (0.0, 2.5 * STUD)], 0.0, h + 0.01)
    side = [(0.0, 0.0)] + [(l * 0.8 * t, 0.04 + (h - 0.04) * math.sin(t * math.pi * 0.5)) for t in [k / 16.0 for k in range(17)]] + [(l, h), (l, 0.0)]
    body = profile_x(side, 0.002, w - 0.002) ^ plan
    cells = [(1, 0), (2, 0), (1, 1), (2, 1)] + [(i, k) for i in range(4) for k in range(3, 6)] + [(0, 2), (1, 2), (2, 2), (3, 2)]
    return Part("p_nose_4x6", "Racing nose 4×6", "body", "curves", (w, h, l), body, sockets(cells), RED, aero={"front": 0.25, "back": 1.0, "side": 0.7},
                solids=[[STUD, 0, 0, 3 * STUD, h, 2 * STUD], [0, 0, 2 * STUD, w, h, l]])


@part
def nose_4x6_lights():
    """The racing nose with a pair of round headlights set into its front,
    either side of the tip."""
    base = nose_4x6()
    lenses = union([cylinder(0.045, 0.22, "-z", (x, 0.11, 0.4), 18) for x in (0.24, 0.76)])
    return Part("p_nose_4x6_lights", "Racing nose 4×6 with lights", "body", "curves", base.size, base.solid, base.connectors, RED,
                aero={"front": 0.25, "back": 1.0, "side": 0.7}, solids=base.stats["solids"], trim=(lenses, TRANS_CLEAR, "glass"), light="head")


@part
def cowl_2x6():
    """An engine cowl, rounded over the top and sloping down at the back."""
    w = 2 * STUD
    l = 6 * STUD
    h = 3 * PLATE
    from manifold3d import CrossSection
    arch = [(w * 0.5 + w * 0.5 * math.cos(t * math.pi), h * 0.35 + h * 0.65 * math.sin(t * math.pi)) for t in [k / 16.0 for k in range(17)]]
    across = CrossSection([[(0.002, 0.0), (w - 0.002, 0.0)] + [(x, y) for x, y in arch]]).extrude(l)
    side = [(0.0, 0.0), (0.0, h), (l * 0.45, h)] + [(l * 0.45 + l * 0.55 * t, h * (1.0 - 0.75 * t * t)) for t in [k / 12.0 for k in range(1, 13)]] + [(l, 0.0)]
    body = across ^ profile_x(side, 0.0, w)
    return Part("p_cowl_2x6", "Engine cowl 2×6", "body", "curves", (w, h, l), body, sockets(grid_cells(2, 6)), RED, aero={"front": 1.0, "back": 0.4, "side": 0.8})


# Car and truck bodywork: a few big smooth pieces, the way small racing sets
# build a car. Hollow pieces (cabs, the engine cover) have a sill down each
# side to fix them by, and solid boxes only where they're solid, so a seat,
# steering or engine fits inside.

def _d_section(hw, h, r, cx, bottom=0.0, n=6):
    """A cross-section with a flat bottom and its top corners rounded by r,
    hw either side of cx."""
    r = max(0.002, min(r, hw - 0.001, h - bottom - 0.001))
    pts = [(cx - hw, bottom), (cx + hw, bottom)]
    for k in range(n + 1):
        a = k / n * math.pi * 0.5
        pts.append((cx + hw - r + r * math.cos(a), h - r + r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi * 0.5 + k / n * math.pi * 0.5
        pts.append((cx - hw + r + r * math.cos(a), h - r + r * math.sin(a)))
    return pts


def _loft(stations, bottom=0.0):
    """A smooth body through cross-sections along z. Each station is
    (z, middle x, half width, height, corner radius); neighbours are joined
    by their hull, so each step has to be convex."""
    from manifold3d import Manifold
    slices = []
    for k, (z, cx, hw, h, r) in enumerate(stations):
        sl = front(_d_section(hw, h, r, cx, bottom)).extrude(0.0005)
        slices.append(sl.translate([0, 0, z - (0.0005 if k == len(stations) - 1 else 0.0)]))
    return union([Manifold.batch_hull([slices[k], slices[k + 1]]) for k in range(len(slices) - 1)])


def _skin(body, boxes):
    """A thin layer over the top of a body inside the boxes, for stripes."""
    over = body.translate([0, 0.003, 0]) - body
    return over ^ union(boxes)


def _bonnet(id, name, along, plates, stripes=False):
    """A bonnet 6 wide, curving up from a thin lip at the front, rounded
    along both sides, with a row of studs along the flat back edge. With
    `stripes` it has two racing stripes down the middle."""
    w = 6 * STUD
    l = along * STUD
    h = plates * PLATE
    lip = 0.05
    run = l - STUD
    stations = []
    for k in range(17):
        t = k / 16.0
        y = lip + (h - lip) * math.sin(t * math.pi * 0.5)
        stations.append((0.002 + (run - 0.002) * t, w * 0.5, w * 0.5 - 0.002, y, min(0.07, y * 0.6)))
    stations.append((l - 0.002, w * 0.5, w * 0.5 - 0.002, h, 0.07))
    body = _loft(stations)
    cells = [(i, along - 1) for i in range(6)]
    stats = {}
    if stripes:
        lanes = [box(x0, 0.0, -0.1, x0 + 0.2, h + 0.1, l + 0.1, edge=0) for x0 in (w * 0.5 - 0.28, w * 0.5 + 0.08)]
        stats["trim"] = (_skin(body, lanes), WHITE, "plastic")
    solid = union([body, studs(cells, h)])
    return Part(id, name, "body", "curves", (w, h, l), solid, sockets(grid_cells(6, along)) + top_studs(cells, h), RED,
                aero={"front": 0.3, "back": 1.0, "side": 0.8}, **stats)


part(lambda: _bonnet("p_bonnet_6x4", "Curved bonnet 6×4", 4, 2))
part(lambda: _bonnet("p_bonnet_6x6", "Curved bonnet 6×6", 6, 3))
part(lambda: _bonnet("p_bonnet_6x6_stripes", "Striped bonnet 6×6", 6, 3, stripes=True))


def _shell(side_pts, front_pts, w, l, t, r_side, r_front):
    """A hollow body open underneath: the side view pushed across, cut to the
    front view pushed back, with walls t thick. Returns the outside, the
    shell and the middle of its walls (for glass)."""
    sv = rounded(side(side_pts), r_side)
    fv = rounded(front(front_pts), r_front)
    floor = box(-1, -1, -1, 3, 0.0, 3, edge=0)

    def solid(d):
        return (push_x(sv.offset(-d), -0.5, w + 0.5) ^ push_z(fv.offset(-d), -0.5, l + 0.5)) - floor

    outer = solid(0.0)
    inner = solid(t)
    return outer, outer - inner, solid(t * 0.35) - inner


def _sills(outer, w, l, across):
    """A plate high strip down each side to fix a hollow body by."""
    return outer ^ union([box(0, 0, 0, STUD, PLATE, l, edge=0), box(w - STUD, 0, 0, w, PLATE, l, edge=0)])


@part
def car_cab():
    """A car's cab 4×6 with a sloping windscreen and back window and two
    windows down each side. The driver sits inside."""
    w, l, h = 4 * STUD, 6 * STUD, 0.6
    sv = [(0.0, -0.3), (0.0, 0.08), (0.55, h), (1.12, h), (l, 0.12), (l, -0.3)]
    fv = [(0.002, -0.3), (w - 0.002, -0.3), (w - 0.002, 0.12), (w - 0.09, h), (0.09, h), (0.002, 0.12)]
    outer, shell, glass_layer = _shell(sv, fv, w, l, 0.04, 0.05, 0.08)
    side_view = (rounded(side(sv), 0.05).offset(-0.08) - side([(-1, -1), (-1, 0.16), (3, 0.16), (3, -1)])) - side([(0.74, -1), (0.74, 2), (0.82, 2), (0.82, -1)])
    cutters = union([
        push_x(side_view, -0.1, 0.3), push_x(side_view, w - 0.3, w + 0.1),
        box(0.13, 0.14, -0.2, w - 0.13, h - 0.07, 0.5, edge=0),
        box(0.15, 0.18, 1.18, w - 0.15, h - 0.08, l + 0.2, edge=0),
    ])
    roof = [(1, 2), (2, 2), (1, 3), (2, 3)]
    body = union([shell - cutters, _sills(outer, w, l, 4), studs(roof, h)])
    cells = [(i, k) for i in (0, 3) for k in range(6)]
    return Part("p_cab_4x6", "Car cab 4×6", "body", "curves", (w, h, l), body, sockets(cells) + top_studs(roof, h), WHITE,
                trim=(glass_layer ^ cutters, GLASS, "glass"), aero={"front": 0.45, "back": 0.6, "side": 0.8}, mass=4.0, strength=900.0,
                solids=[[0, 0, 0, STUD, PLATE, l], [w - STUD, 0, 0, w, PLATE, l], [0, h - PLATE, 0.55, w, h, 1.12]])


@part
def truck_cab():
    """A tall boxy truck cab 6×4 with a big windscreen, side windows and a
    small back window, and studs on the roof for lights."""
    w, l, h = 6 * STUD, 4 * STUD, 0.8
    sv = [(0.0, -0.3), (0.0, 0.32), (0.12, h), (l, h), (l, -0.3)]
    fv = [(0.002, -0.3), (w - 0.002, -0.3), (w - 0.002, 0.3), (w - 0.04, h), (0.04, h), (0.002, 0.3)]
    outer, shell, glass_layer = _shell(sv, fv, w, l, 0.04, 0.04, 0.06)
    cutters = union([
        box(0.13, 0.38, -0.2, w - 0.13, h - 0.08, 0.2, edge=0),
        box(-0.1, 0.38, 0.26, 0.3, h - 0.08, l - 0.1, edge=0), box(w - 0.3, 0.38, 0.26, w + 0.1, h - 0.08, l - 0.1, edge=0),
        box(0.42, 0.46, l - 0.2, w - 0.42, h - 0.12, l + 0.2, edge=0),
    ])
    roof = [(i, k) for i in range(1, 5) for k in range(1, 4)]
    body = union([shell - cutters, _sills(outer, w, l, 6), studs(roof, h)])
    cells = [(i, k) for i in (0, 5) for k in range(4)]
    return Part("p_truck_cab_6x4", "Truck cab 6×4", "body", "curves", (w, h, l), body, sockets(cells) + top_studs(roof, h), WHITE,
                trim=(glass_layer ^ cutters, GLASS, "glass"), aero={"front": 0.8, "back": 1.0, "side": 0.9}, mass=6.0, strength=1100.0,
                solids=[[0, 0, 0, STUD, PLATE, l], [w - STUD, 0, 0, w, PLATE, l], [0, h - PLATE, 0.12, w, h, l]])


def _big_arch(id, name, across):
    """A big wheel arch 6 long with flat ends 4 plates high and studs on
    them, humped over the opening. The opening clears a wheel up to 0.45 m
    across with its middle a plate or two under the arch's bottom."""
    w = across * STUD
    l = 6 * STUD
    base = 4 * PLATE
    hump = 0.08
    a, b = 0.5, 0.36
    top = []
    for k in range(33):
        z = l * k / 32.0
        u = min(1.0, max(0.0, (z - STUD) / (l - 2 * STUD)))
        top.append((z, base + hump * math.sin(u * math.pi)))
    sv = side([(0.0, 0.0)] + top + [(l, 0.0)])
    hole = side([(l * 0.5 + a * math.cos(k / 24.0 * math.pi), b * math.sin(k / 24.0 * math.pi)) for k in range(25)] + [(l * 0.5 - a, -0.1), (l * 0.5 + a, -0.1)])
    fv = rounded(front([(0.002, -0.1), (w - 0.002, -0.1), (w - 0.002, base + hump), (0.002, base + hump)]), 0.05)
    body = push_x(sv - hole, 0.0, w) ^ push_z(fv, 0.002, l - 0.002)
    ends = [(i, k) for i in range(across) for k in (0, 5)]
    return Part(id, name, "body", "arches", (w, base + hump, l), union([body, studs(ends, base)]), sockets(ends) + top_studs(ends, base), RED,
                aero={"front": 0.5, "back": 0.6, "side": 0.9}, mass=round(0.7 * across, 1), strength=500.0 + 100.0 * across,
                solids=[[0, 0, 0, w, base, STUD], [0, 0, l - STUD, w, base, l], [0, b, STUD, w, base + hump, l - STUD]])


part(lambda: _big_arch("p_arch_2x6", "Big wheel arch 2×6", 2))
part(lambda: _big_arch("p_arch_3x6", "Big wheel arch 3×6", 3))


@part
def nose_cone_2x6():
    """A long formula nose, 2 wide at the back, tapering and dropping to a
    low rounded tip."""
    w, l, h = 2 * STUD, 6 * STUD, 3 * PLATE
    stations = []
    for k in range(17):
        t = k / 16.0
        z = 0.002 + (l - 0.004) * t
        u = min(1.0, z / (4.5 * STUD))
        hw = 0.08 + (w * 0.5 - 0.082) * math.sin(u * math.pi * 0.5)
        y = 0.09 + (h - 0.09) * math.sin(u * math.pi * 0.5)
        if k == 0:
            hw, y = 0.05, 0.06
        stations.append((z, w * 0.5, hw, y, min(hw, y) * 0.9))
    return Part("p_nose_cone_2x6", "Formula nose 2×6", "body", "curves", (w, h, l), _loft(stations), sockets(grid_cells(2, 6)), RED,
                aero={"front": 0.2, "back": 1.0, "side": 0.6})


@part
def front_wing_8x2():
    """A front wing 8×2 with a flap and an endplate at each end, on a plate
    2×2 in the middle with studs for a nose."""
    w, l = 8 * STUD, 2 * STUD
    main = profile_x([(0.0, 0.01), (0.02, 0.0), (0.32, 0.0), (0.33, 0.04), (0.06, 0.05), (0.0, 0.035)], 0.04, w - 0.04)
    flap = profile_x([(0.3, 0.045), (0.32, 0.03), (0.49, 0.11), (0.5, 0.14), (0.47, 0.145)], 0.04, w - 0.04)
    plate = [(0.0, 0.0), (0.0, 0.1), (0.1, 0.2), (l, 0.2), (l, 0.0)]
    ends = [profile_x(plate, x, x + 0.04) for x in (0.002, w - 0.042)]
    middle = [(3, 0), (4, 0), (3, 1), (4, 1)]
    mount = union([box(3 * STUD, 0, 0, 5 * STUD, PLATE, l), studs(middle, PLATE)])
    return Part("d_front_wing_8x2", "Front wing with endplates 8×2", "wing", "details", (w, 0.2, l), union([main, flap, mount] + ends),
                sockets(middle) + top_studs(middle, PLATE), RED, lift_area=0.35, aero={"front": 0.8, "back": 0.8}, mass=1.3, strength=300.0,
                solids=[[3 * STUD, 0, 0, 5 * STUD, PLATE, l], [0, 0, 0, w, 0.05, l], [0, 0, 0, 0.04, 0.2, l], [w - 0.04, 0, 0, w, 0.2, l]])


@part
def rear_wing_8():
    """A big rear wing 8 wide with a flap and tall endplates, up on two
    struts from a plate 2×2 in the middle."""
    w, l = 8 * STUD, 2 * STUD
    lift = 0.42
    main = profile_x([(0.0, 0.02), (0.03, 0.0), (0.34, 0.01), (0.35, 0.05), (0.08, 0.07), (0.0, 0.05)], 0.04, w - 0.04).translate([0, lift, 0])
    flap = profile_x([(0.3, 0.07), (0.33, 0.05), (0.49, 0.15), (0.5, 0.19), (0.47, 0.19)], 0.04, w - 0.04).translate([0, lift, 0])
    plate = rounded(side([(0.0, 0.3), (0.0, 0.66), (l, 0.7), (l, 0.3)]), 0.03)
    ends = [push_x(plate, x, x + 0.04) for x in (0.002, w - 0.042)]
    struts = [push_x(rounded(side([(0.14, PLATE - 0.01), (0.2, lift + 0.03), (0.34, lift + 0.03), (0.34, PLATE - 0.01)]), 0.01), x, x + 0.04) for x in (0.8, 1.16)]
    middle = [(3, 0), (4, 0), (3, 1), (4, 1)]
    foot = box(3 * STUD, 0, 0, 5 * STUD, PLATE, l)
    return Part("d_rear_wing_8", "Big rear wing 8 wide", "wing", "details", (w, 0.7, l), union([main, flap, foot] + ends + struts),
                sockets(middle), RED, lift_area=0.7, aero={"front": 0.9, "back": 0.9}, mass=2.0, strength=350.0,
                solids=[[3 * STUD, 0, 0, 5 * STUD, PLATE, l], [0.04, lift, 0, w - 0.04, lift + 0.2, l], [0, 0.3, 0, 0.04, 0.7, l], [w - 0.04, 0.3, 0, w, 0.7, l]])


@part
def bonnet_scoop():
    """An air scoop 2×3 for a bonnet, tall at the front with a dark intake,
    sloping down to the back."""
    w, l, h = 2 * STUD, 3 * STUD, 0.24
    stations = []
    for k in range(9):
        t = k / 8.0
        stations.append((0.002 + (l - 0.004) * t, w * 0.5, w * 0.5 - 0.02, h - (h - 0.08) * t * t, 0.05))
    intake = box(0.07, 0.04, -0.1, w - 0.07, h - 0.06, 0.12, edge=0)
    inside = box(0.075, 0.045, 0.03, w - 0.075, h - 0.065, 0.13, edge=0)
    return Part("p_scoop_2x3", "Bonnet scoop 2×3", "body", "curves", (w, h, l), _loft(stations) - intake, sockets(grid_cells(2, 3)), RED,
                trim=(inside, BLACK, "plastic"), aero={"front": 0.9, "back": 0.5, "side": 0.8})


@part
def fin_cover_4x6():
    """A long engine cover 4×6 with a fin along the top, like an endurance
    racer's. It's hollow, so an engine 2 wide and 3 plates high fits under
    its front, between the sills."""
    w, l, h, low = 4 * STUD, 6 * STUD, 0.4, 0.18

    def height(z):
        u = min(1.0, max(0.0, (z - 1.0) / (l - 1.0)))
        return low + (h - low) * (1 + math.cos(u * math.pi)) * 0.5

    def stations(d):
        out = []
        for k in range(21):
            z = d + 0.002 + (l - 2 * d - 0.004) * k / 20.0
            y = height(z) - d
            if k == 0:
                y -= 0.04
            out.append((z, w * 0.5, w * 0.5 - 0.002 - d, y, 0.12 - d))
        return out

    outer = _loft(stations(0.0))
    inner = _loft(stations(0.04), bottom=-0.1)
    fin = profile_x([(0.35, h - 0.03), (1.0, h - 0.03), (l, low - 0.03), (l, 0.68), (l - 0.12, 0.7)], w * 0.5 - 0.02, w * 0.5 + 0.02)
    body = union([outer - inner, _sills(outer, w, l, 4), fin])
    cells = [(i, k) for i in (0, 3) for k in range(6)]
    return Part("p_fin_cover_4x6", "Engine cover with fin 4×6", "body", "curves", (w, 0.7, l), body, sockets(cells), RED,
                aero={"front": 1.0, "back": 0.4, "side": 0.8}, mass=4.0, strength=800.0,
                solids=[[0, 0, 0, STUD, PLATE, l], [w - STUD, 0, 0, w, PLATE, l], [0, h - PLATE, 0, w, h, 1.0], [w * 0.5 - 0.02, h, 0.35, w * 0.5 + 0.02, 0.7, l]])


def _pinstripe(id, name, along):
    """A smooth tile 2 wide with two thin white stripes down it."""
    w, l = 2 * STUD, along * STUD
    tile = box(0, 0, 0, w, PLATE, l)
    lines = union([box(x, PLATE - 0.006, 0.01, x + 0.035, PLATE + 0.004, l - 0.01, edge=0) for x in (0.07, w - 0.105)])
    return Part(id, name, "plate", "tiles", (w, PLATE, l), tile, sockets(grid_cells(2, along)), BLUE, trim=(lines, WHITE, "plastic"),
                aero={"front": 0.9, "back": 0.9})


part(lambda: _pinstripe("p_pinstripe_2x4", "Pinstripe tile 2×4", 4))
part(lambda: _pinstripe("p_pinstripe_2x6", "Pinstripe tile 2×6", 6))


# Motorbikes, the way toy motorbikes come: a frame in one piece with the
# engine, tank, seat and swingarm in it, a front fork with its bars on top
# that turns as one, and a fairing that clips on the front. Everything is in
# the fine unit, measured from the ground with the wheels on, from the front
# of the fork (where the front axle is, 10 back) and across the frame.


def _f(*v):
    return [x * FINE for x in v]


def _tube(a, b, r):
    """A tube from a to b, r across, all in the fine unit."""
    return _capsule(_f(*a), _f(*b), r * FINE)


def _moto_frame(id, name, style, color, twin, power, push, about):
    """A motorbike's frame. `style` is "sport", "dirt", "cruiser",
    "scooter" or "trike". The front wheel's middle is at R and its top at
    2R, with the fork crown just over it and the frame's head on that. The
    back axle is at `back`."""
    R = 24 if style == "scooter" else 36
    top = 2 * R
    back = {"sport": 170, "dirt": 170, "cruiser": 190, "scooter": 140, "trike": 150}[style]
    seat = {"sport": top + 10, "dirt": top + 16, "cruiser": top + 4, "scooter": top + 10, "trike": top + 10}[style]
    low = max(R - 4, 16)
    head = (top + 10, top + 30)
    wide = 80 if style == "trike" else 0
    x0, x1 = -wide, 40 + wide
    parts = []
    trim = []
    solids = []
    # The head over the fork crown, and the spine back to the seat.
    parts.append(box(*_f(2, head[0], 0, 38, head[1], 20), edge=0.02))
    solids.append([2, head[0], 0, 38, head[1], 20])
    trim.append(_tube((20, head[0] + 4, 14), (20, low + 8, 60), 2.6))
    trim.append(_tube((20, head[1] - 4, 16), (20, seat - 6, 84), 2.6))
    if style == "scooter":
        # An apron in front of the legs and a floor to put the feet on.
        parts.append(box(*_f(2, R + 26, 20, 38, head[1], 28), edge=0.015))
        parts.append(box(*_f(2, R + 12, 36, 38, R + 20, 84), edge=0.015))
        solids += [[2, R + 26, 20, 38, head[1], 28], [2, R + 12, 36, 38, R + 20, 84]]
    else:
        # The tank, sloping down from the head to the seat.
        tl = 44
        th = {"sport": 24, "dirt": 18, "cruiser": 22, "trike": 24}[style]
        pts = [(0.0, 0.0)] + [(tl * t, th * (1.0 - 0.45 * t * t) * (0.55 + 0.45 * math.sin(math.pi * min(1.0, t * 1.6)))) for t in [k / 16.0 for k in range(17)]] + [(tl, 0.0)]
        tank = profile_x([(z * FINE, y * FINE) for z, y in pts], 4 * FINE, 36 * FINE).translate(_f(0, top + 4, 21))
        parts.append(tank)
        solids.append([4, top + 4, 21, 36, top + 4 + th, 21 + tl])
    # The engine, low between the wheels, with its cylinders and fins.
    if style == "scooter":
        parts.append(box(*_f(6, low, 84, 34, seat - 8, 112), edge=0.03))
        solids.append([6, low, 84, 34, seat - 8, 112])
    else:
        e0, e1 = 48, 96
        parts.append(box(*_f(5, low, e0, 35, top - 12, e1), edge=0.03))
        solids.append([5, low, e0, 35, top - 12, e1])
        cylinders = {"sport": 2, "dirt": 1, "cruiser": 2, "trike": 2}[style]
        for k in range(cylinders):
            z = e0 + 12 + k * 22 if cylinders > 1 else e0 + 20
            lean = -10 if (style == "cruiser" and k == 0) else 6
            trim.append(_tube((20, low + 14, z), (20, top - 6, z + lean), 4.0))
            for fin in range(4):
                y = low + 18 + fin * 7
                trim.append(box(*_f(7, y, z - 7 + lean * fin / 6.0, 33, y + 1.6, z + 7 + lean * fin / 6.0), edge=0.004))
        # Footpegs out each side.
        trim.append(_tube((-8, low + 12, 64), (48, low + 12, 64), 1.8))
    # The seat, and the tail behind it.
    s0 = 76
    parts.append(box(*_f(4, seat - 8, s0, 36, seat, 122), edge=0.03))
    solids.append([4, seat - 8, s0, 36, seat, 122])
    under = box(*_f(6, top - 12, 84, 34, seat - 8, 122), edge=0.02)
    parts.append(under)
    tail_end = back - 10 if style != "trike" else back + 30
    # It rises clear of the back wheel.
    under_tail = max(seat - 14, top + 4)
    tail = profile_x([(z * FINE, y * FINE) for z, y in [(122, under_tail), (tail_end, seat + 2), (tail_end, seat + 8), (122, seat)]], 8 * FINE, 32 * FINE)
    parts.append(tail)
    solids.append([8, under_tail, 122, 32, seat + 2, tail_end])
    trim.append(box(*_f(10, seat + 1, tail_end - 4, 30, seat + 7, tail_end), edge=0.008))
    # The swingarm back to the axle, or for a trike an axle across.
    if style == "trike":
        housing = box(*_f(-20, R - 6, back - 8, 60, R + 6, back + 8), edge=0.02)
        parts.append(housing)
        solids.append([-20, R - 6, back - 8, 60, R + 6, back + 8])
        trim.append(_tube((20, low + 10, 96), (20, R, back - 8), 3.0))
        for side in (-1, 1):
            x = 20 + side * 70
            fender = cut(cylinder((R + 10) * FINE, 22 * FINE, "x", (0, 0, 0), 24).translate(_f(x - 11, R, back)),
                         cylinder((R + 6) * FINE, 30 * FINE, "x", (0, 0, 0), 24).translate(_f(x - 15, R, back)),
                         box(*_f(x - 20, -10, back - 60, x + 20, R + 4, back + 60), edge=0))
            parts.append(fender)
        axle = c("axle", _f(-wide, R, back), (1, 0, 0), (40 + 2 * wide) * FINE)
    else:
        for x in (2, 32):
            arm = box(*_f(x, R - 5, 96, x + 6, R + 5, back + 6), edge=0.01)
            parts.append(arm)
            solids.append([x, R - 5, 96, x + 6, R + 5, back + 6])
        axle = c("axle", _f(8.8, R, back), (1, 0, 0), 22.4 * FINE)
        # A mudguard over the back wheel, and the exhaust along the right.
        guard = cut(cylinder((R + 7) * FINE, 20 * FINE, "x", (0, 0, 0), 24).translate(_f(10, R, back)),
                    cylinder((R + 3) * FINE, 30 * FINE, "x", (0, 0, 0), 24).translate(_f(5, R, back)),
                    box(*_f(0, -10, back - 60, 40, R + 6, back + 60), edge=0), box(*_f(0, -10, back - 60, 40, R + 60, back - 10), edge=0))
        parts.append(guard)
        if style == "scooter":
            trim.append(_tube((34, low + 6, 110), (34, R + 6, back + 10), 2.6))
        else:
            trim.append(_tube((36, low + 6, 90), (36, R + 6, back + 14), 2.6))
            trim.append(cylinder(0.04, 16 * FINE, "z", tuple(_f(36, R + 6, back + 6)), 12))
    con = [c("socket", _f(x, head[0], 10), (0, -1, 0)) for x in (10, 30)]
    con += [c("side", _f(x, head[0] + 10, 0), (0, 0, -1)) for x in (10, 30)]
    con.append(axle)
    zmax = max(back + 30, tail_end)
    hi = max(head[1], seat + 8, top + 4 + 24)
    shift = [-x0 * FINE, -low * FINE, 0]
    body = union(parts + trim[:0]).translate(shift)
    trimmed = union(trim).translate(shift)
    for co in con:
        co["at"] = [co["at"][0] + shift[0], co["at"][1] + shift[1], co["at"][2]]
    solids = [[(a - x0) * FINE, (b - low) * FINE, cc * FINE, (d - x0) * FINE, (e - low) * FINE, g * FINE] for a, b, cc, d, e, g in solids]
    seat_box = [(4 - x0) * FINE, (seat - 8 - low) * FINE, s0 * FINE, (36 - x0) * FINE, (seat - low) * FINE, 122 * FINE]
    return Part(id, name, "seat", "bike", ((x1 - x0) * FINE, (hi - low) * FINE, zmax * FINE), body, con, color, about=about,
                trim=(trimmed, METAL, "metal"), solids=solids, seat_box=seat_box, engine_twin=twin, aero={"front": 0.6, "back": 0.7, "side": 0.8}, power=power, max_force=push, astride=True, driver_height=7,
                control=1.05, recline=0)


# A bike's narrow, so its engine is smaller than a kart's for the same speed,
# and it's light, so it still pulls away quickly.
part(lambda: _moto_frame("b_frame_sport", "Sports bike frame", "sport", RED, "engine_twin", 6500.0, 1300.0,
                         "A sports bike frame with a twin in it, and the seat and swingarm. Put a fork on the front, a fairing too if you like, and wheels on both ends."))
part(lambda: _moto_frame("b_frame_dirt", "Dirt bike frame", "dirt", YELLOW, "engine_micro", 6200.0, 1300.0,
                         "A dirt bike frame, light, with a little single and a tall seat. Put a fork on the front and wheels on both ends."))
part(lambda: _moto_frame("b_frame_cruiser", "Cruiser frame", "cruiser", BLACK, "engine_big", 6500.0, 1400.0,
                         "A long, low cruiser frame with a big twin. Put a fork on the front and wheels on both ends."))
part(lambda: _moto_frame("b_frame_scooter", "Scooter frame", "scooter", WHITE, "electric_motor", 4500.0, 1600.0,
                         "A scooter with an electric motor under the seat and a floor for your feet. Put the scooter fork on the front and small wheels on both ends."))
part(lambda: _moto_frame("b_frame_trike", "Trike frame", "trike", BLUE, "engine_big", 9000.0, 1600.0,
                         "A trike frame with an axle across the back for two wheels. Put a fork on the front and wheels on all three."))


def _moto_fork(id, name, style, about):
    """A front fork with the bars on top, which turns as one about the front
    axle. Its crown sits just over the wheel, under the frame's head, and the
    bars sweep back over the tank to the rider's hands."""
    R = 24 if style == "scooter" else 36
    top = 2 * R
    crown = (top + 2, top + 10)
    bar = top + 40 if style != "dirt" else top + 46
    reach = 66
    parts = [box(*_f(20, crown[0], 0, 60, crown[1], 20), edge=0.015)]
    for x in (22.4, 51.2):
        parts.append(box(*_f(x, R - 3.6, 5, x + 6.4, crown[0] + 1, 15), edge=0.01))
    parts.append(cylinder(0.03, 22.4 * FINE, "x", tuple(_f(28.8, R, 10)), 10))
    # The steerer up through the head, then the bars.
    parts.append(cylinder(0.035, (bar - crown[1]) * FINE, "y", tuple(_f(40, crown[1], 10)), 12))
    parts.append(_tube((40, bar, 10), (40, bar, reach - 10), 2.2))
    parts.append(_tube((16, bar, reach), (64, bar, reach), 2.2))
    for x in (16, 64):
        parts.append(_tube((40 + (x - 40) * 0.5, bar, reach - 10), (x, bar, reach), 2.0))
    grips = [_tube((x, bar, reach), (x + d * 9, bar, reach), 3.2) for x, d in ((22, -1), (58, 1))]
    if style == "dirt":
        guard = cut(cylinder((R + 6) * FINE, 18 * FINE, "x", (0, 0, 0), 24).translate(_f(31, R, 10)),
                    cylinder((R + 2) * FINE, 30 * FINE, "x", (0, 0, 0), 24).translate(_f(25, R, 10)),
                    box(*_f(20, -10, -60, 60, R + 8, 80), edge=0))
        parts.append(guard)
    # A round headlamp in a black shell, out in front of the frame's head.
    lamp_y = bar - 6 if style == "scooter" else crown[1] + 12
    lamp_r = 0.05 if style == "scooter" else 0.065
    grips.append(cylinder(lamp_r + 0.01, 0.06, "-z", tuple(_f(40, lamp_y, 1)), 16))
    lamp = cylinder(lamp_r, 0.012, "-z", tuple(_f(40, lamp_y, 1 - 0.06 / FINE)), 16)
    low = R - 3.6
    hi = bar + 4
    shift = [0, -low * FINE, 0]
    con = [c("stud", _f(x, crown[1], 10), (0, 1, 0)) for x in (30, 50)] + [c("axle", _f(28.8, R, 10), (1, 0, 0), 22.4 * FINE)]
    for co in con:
        co["at"] = [co["at"][0], co["at"][1] + shift[1], co["at"][2]]
    solids = [[20, crown[0], 0, 60, crown[1], 20], [22.4, R - 3.6, 5, 28.8, crown[0], 15], [51.2, R - 3.6, 5, 57.6, crown[0], 15]]
    solids = [[a * FINE, (b - low) * FINE, cc * FINE, d * FINE, (e - low) * FINE, g * FINE] for a, b, cc, d, e, g in solids]
    return Part(id, name, "steering", "bike", (80 * FINE, (hi - low) * FINE, (reach + 4) * FINE), union(parts).translate(shift), con, METAL, finish="metal",
                about=about, style="bikebars", control=1.15, grip_reach=0.3, mass=2.5, strength=900.0, trim=(union(grips).translate(shift), BLACK, "plastic"), solids=solids,
                lamp=(lamp.translate(shift), TRANS_CLEAR), light="head")


part(lambda: _moto_fork("b_moto_fork", "Motorbike fork", "road",
                        "A front fork with the bars on top, for a motorbike frame. The bars and the front wheel turn together."))
part(lambda: _moto_fork("b_moto_fork_dirt", "Dirt bike fork", "dirt",
                        "A dirt bike's fork with high bars and a mudguard up high over the wheel."))
part(lambda: _moto_fork("b_moto_fork_scooter", "Scooter fork", "scooter",
                        "A short fork with bars and a lamp, for the scooter frame and small wheels."))


@part
def moto_fairing():
    """A sports bike's fairing, with a headlight and a screen, that clips
    onto the front of the frame's head and stays put while the bars turn."""
    top = 72
    l = 30
    h0, h1 = top + 2, top + 40
    h = h1 - h0
    tip = 12.0
    pts = [(l, 0.0), (l, h)] + [(l * (1 - t), tip + (h - tip) * math.cos(t * math.pi * 0.5)) for t in [k / 12.0 for k in range(1, 13)]] + [(6.0, 0.0)]
    shell = profile_x([(z * FINE, y * FINE) for z, y in pts], 2 * FINE, 38 * FINE)
    lamp = cylinder(0.06, 0.06, "-z", tuple(_f(20, 18, 7)), 16)
    screen = profile_x([(z * FINE, y * FINE) for z, y in [(14, h1 - h0 - 2), (l, h1 - h0 + 12), (l + 2, h1 - h0 + 12), (18, h1 - h0 - 2)]], 6 * FINE, 34 * FINE)
    con = [c("clip", _f(x, 18, l), (0, 0, 1)) for x in (10, 30)]
    return Part("b_moto_fairing", "Sports fairing", "body", "bike", (40 * FINE, (h1 - h0 + 12) * FINE, (l + 2) * FINE), shell, con, WHITE,
                aero={"front": 0.3, "back": 1.0, "side": 0.8}, trim=(screen, TRANS_CLEAR, "glass"), lamp=(lamp, TRANS_CLEAR), light="head", solids=[[2 * FINE, 0, 0, 38 * FINE, (h1 - h0) * FINE, l * FINE]])


# Kart chassis and seats.

@part
def kart_axle_plate():
    """A plate 6×2 with a pin out of each side for a wheel, for the front or
    back of a kart. Any wheel goes on the pins right up against the plate."""
    cells = [(i, k) for i in range(1, 7) for k in range(2)]
    plate = union([box(STUD, 0, 0, 7 * STUD, PLATE, 2 * STUD), studs(cells, PLATE)])
    pins = [cylinder(HOLE - 0.006, STUD, "x", (x, PLATE * 0.5, STUD), 14) for x in (0.0, 7 * STUD)]
    con = sockets(cells) + top_studs(cells, PLATE) + [c("pin", (x, PLATE * 0.5, STUD), (1, 0, 0), STUD) for x in (0.0, 7 * STUD)]
    return Part("p_kart_axle_plate", "Kart axle plate 6×2", "plate", "technic", (8 * STUD, PLATE, 2 * STUD), union([plate] + pins), con, BLACK,
                solids=[[STUD, 0, 0, 7 * STUD, PLATE, 2 * STUD]], mass=2.0, strength=2500.0)


def _seat(id, twin, across, plates, along, recline, back, color, bolsters=True):
    """A seat with a cushion filling its box, which the driver sits on top
    of, and a backrest rising behind them leaning back by `recline` degrees.
    It weighs the same and works the same as `twin`, one of the first seats."""
    w = across * STUD
    h = plates * PLATE
    l = along * STUD
    cushion = box(0.01, 0, 0.01, w - 0.01, h, l - 0.01, edge=0.025)
    rest = box(0.02, 0.0, -0.06, w - 0.02, back, 0.0, edge=0.025).rotate([recline, 0, 0]).translate([0, h - 0.02, l - 0.01])
    parts = [cushion, rest]
    if bolsters:
        for x in (0.0, w - 0.06):
            parts.append(box(x, h - 0.02, 0.06, x + 0.06, h + 0.07, l - 0.02, edge=0.02))
    return Part(id, "", "seat", "seats", (w, h, l), union(parts), sockets(grid_cells(across, along)), color, twin=twin)


part(lambda: _seat("s_seat", "seat", 2, 3, 2, 8, 0.3, BLACK, bolsters=False))
part(lambda: _seat("s_bucket_seat", "bucket_seat", 2, 2, 2, 25, 0.3, BLACK))
part(lambda: _seat("s_racing_seat", "racing_seat", 2, 2, 2, 15, 0.34, RED))
part(lambda: _seat("s_lay_down_seat", "lay_down_seat", 2, 1, 4, 62, 0.3, BLACK))


# Details.

@part
def headlight_1x1():
    lens = cylinder(STUD * 0.5 - 0.02, PLATE - 0.002, "y", (STUD * 0.5, 0.001, STUD * 0.5), 18)
    return Part("d_light_1x1", "Round light 1×1", "plate", "details", (STUD, PLATE, STUD), lens, sockets([(0, 0)]), TRANS_CLEAR, finish="glass", light="head")


@part
def taillight_1x2():
    lens = box(0, 0, 0, STUD, PLATE, 2 * STUD, edge=0.015)
    return Part("d_taillight_1x2", "Tail light 1×2", "plate", "details", (STUD, PLATE, 2 * STUD), lens, sockets(grid_cells(1, 2)), TRANS_RED, finish="glass", light="tail")


@part
def amber_1x1():
    """A round amber light, like a beacon or an indicator."""
    lens = cylinder(STUD * 0.5 - 0.02, PLATE - 0.002, "y", (STUD * 0.5, 0.001, STUD * 0.5), 18)
    return Part("d_amber_1x1", "Amber light 1×1", "plate", "details", (STUD, PLATE, STUD), lens, sockets([(0, 0)]), TRANS_AMBER, finish="glass", light="amber")


@part
def light_bar():
    """A bar of four round lamps along its front, for a roll cage or a bumper."""
    bar = union([box(0, 0, 0.02, 4 * STUD, BRICK, STUD, edge=0.02)])
    lenses = union([cylinder(0.09, 0.04, "-z", ((i + 0.5) * STUD, BRICK * 0.5, 0.025), 16) for i in range(4)])
    return Part("d_light_bar", "Light bar", "brick", "details", (4 * STUD, BRICK, STUD), bar, sockets(grid_cells(4, 1)) + top_studs(grid_cells(4, 1), BRICK), BLACK,
                light="head", trim=(lenses, TRANS_CLEAR, "glass"))


@part
def spotlights():
    """Two big round spotlights on a brick, facing forward."""
    body = union([box(0, 0, 0.04, 2 * STUD, BRICK, STUD, edge=0.02)] + [cylinder(0.11, 0.06, "-z", ((i + 0.5) * STUD, BRICK * 0.5, 0.05), 18) for i in range(2)])
    lenses = union([cylinder(0.1, 0.03, "-z", ((i + 0.5) * STUD, BRICK * 0.5, 0.0), 18) for i in range(2)])
    return Part("d_spotlights", "Spotlights", "brick", "details", (2 * STUD, BRICK, STUD), body, sockets(grid_cells(2, 1)), DARK_GREY,
                light="head", trim=(lenses, TRANS_CLEAR, "glass"))


@part
def round_lamp_2x2():
    """A big round headlamp in its own housing, facing forward."""
    housing = union([box(0, 0, 0.1, 2 * STUD, 0.08, 2 * STUD, edge=0.01), cylinder(0.22, 0.2, "-z", (STUD, 0.27, 0.32), 24)])
    lens = cylinder(0.2, 0.03, "-z", (STUD, 0.27, 0.12), 24)
    return Part("d_round_lamp_2x2", "Round lamp 2×2", "plate", "details", (2 * STUD, 0.5, 2 * STUD), housing, sockets(grid_cells(2, 2)), METAL,
                finish="metal", light="head", trim=(lens, TRANS_CLEAR, "glass"))


@part
def exhaust():
    """A chrome exhaust pipe on a plate, sticking out behind."""
    plate = union([box(0, 0, 0, STUD, PLATE, 2 * STUD), studs([(0, 0)], PLATE)])
    pipe = cut(cylinder(0.06, 0.6, "z", (STUD * 0.5, PLATE + 0.06, 0.1), 16), cylinder(0.045, 0.2, "z", (STUD * 0.5, PLATE + 0.06, 0.55), 16))
    return Part("d_exhaust", "Exhaust", "body", "details", (STUD, PLATE + 0.12, 0.7), union([plate, pipe]), sockets(grid_cells(1, 2)), METAL, finish="metal",
                solids=[[0, 0, 0, STUD, PLATE, 2 * STUD]])


@part
def mirror():
    """A wing mirror on a stalk."""
    base = box(0, 0, 0, STUD, PLATE, STUD)
    stalk = cylinder(0.02, 0.18, "y", (STUD * 0.5, PLATE, STUD * 0.5), 8)
    head = box(STUD * 0.5 - 0.1, PLATE + 0.14, STUD * 0.5 - 0.03, STUD * 0.5 + 0.1, PLATE + 0.26, STUD * 0.5 + 0.03, edge=0.015)
    return Part("d_mirror", "Mirror", "body", "details", (STUD, PLATE + 0.26, STUD), union([base, stalk, head]), sockets([(0, 0)]), BLACK, solids=[[0, 0, 0, STUD, PLATE, STUD]])


@part
def spoiler_4():
    """A rear wing 4 studs wide on two stands."""
    w = 4 * STUD
    blade_pts = [(0.0, 0.0), (0.03, 0.03), (STUD * 1.4, 0.05), (STUD * 1.5, 0.02), (STUD * 1.5, 0.0)]
    blade = profile_x(blade_pts, 0.002, w - 0.002).translate([0, 0.3, 0])
    stands = [box(x, 0, 0.1, x + 0.06, 0.32, 0.25, edge=0.008) for x in (STUD * 0.5, w - STUD * 0.5 - 0.06)]
    feet = [box(x - 0.09, 0, 0, x + 0.15, PLATE, STUD, edge=0.008) for x in (STUD * 0.5, w - STUD * 0.5 - 0.06)]
    return Part("d_spoiler", "Spoiler", "wing", "details", (w, 0.36, STUD * 1.5), union([blade] + stands + feet), sockets([(0, 0), (3, 0)]), BLACK, lift_area=0.25, aero={"front": 0.7, "back": 0.8},
                solids=[[0, 0.28, 0, w, 0.36, STUD * 1.5], [0, 0, 0, STUD, PLATE, STUD], [w - STUD, 0, 0, w, PLATE, STUD]])


def _screen(id, name, across, h, color=GLASS):
    """A windscreen leaning back from its bottom front edge."""
    l = 2 * STUD
    shell = profile_x([(0.0, 0.0), (0.04, 0.0), (l - 0.02, h - 0.02), (l - 0.06, h)], 0.004, across * STUD - 0.004)
    return Part(id, name, "screen", "details", (across * STUD, h, l), shell, sockets([(i, 0) for i in range(across)]), color, finish="glass", aero={"front": 0.5, "back": 1.0})


part(lambda: _screen("d_screen_2", "Windscreen 2 wide", 2, 0.35))
part(lambda: _screen("d_screen_4", "Windscreen 4 wide", 4, 0.4))


@part
def canopy():
    """A bubble canopy 4×6 that closes right over the driver."""
    l = 6 * STUD
    w = 4 * STUD
    h = 0.55
    from manifold3d import Manifold
    dome = Manifold.sphere(1.0, 36).scale([w * 0.5 - 0.01, h, l * 0.5 - 0.01]).translate([w * 0.5, 0.0, l * 0.5])
    dome = dome - box(-1, -2, -1, 2, 0.0, 2, edge=0)
    hollow = Manifold.sphere(1.0, 36).scale([w * 0.5 - 0.04, h - 0.03, l * 0.5 - 0.04]).translate([w * 0.5, 0.0, l * 0.5])
    shell = (dome - hollow) - box(-1, -2, -1, 2, 0.0, 2, edge=0)
    rim = cut(box(0, 0, 0, w, PLATE * 0.5, l, edge=0.01), box(0.06, -0.1, 0.06, w - 0.06, 0.2, l - 0.06, edge=0))
    cells = [(0, 0), (3, 0), (0, 5), (3, 5)]
    return Part("d_canopy", "Canopy", "screen", "details", (w, h, l), union([shell.translate([0, PLATE * 0.5, 0]), rim]), sockets(cells), GLASS, finish="glass",
                aero={"front": 0.35, "back": 0.6, "side": 0.6},
                solids=[[0, 0, 0, w, PLATE * 0.5, 0.06], [0, 0, l - 0.06, w, PLATE * 0.5, l], [0, 0, 0, 0.06, PLATE * 0.5, l], [w - 0.06, 0, 0, w, PLATE * 0.5, l]])


# Engines and mechanical parts for the bigger stock vehicles.

def _rods(points, r):
    """Tubes joining the points one after another, like a bent pipe."""
    return union([_capsule(points[k], points[k + 1], r) for k in range(len(points) - 1)])


@part
def blower_v8():
    """A V8 with a supercharger and an air scoop on top, for hot rods and
    muscle cars. The block is painted and the rocker covers, blower, scoop
    and pulleys are chrome."""
    w, l, h = 3 * STUD, 4 * STUD, 0.7
    from manifold3d import Manifold
    mid = w * 0.5
    base = box(0.02, 0.0, 0.03, w - 0.02, 0.08, l - 0.03, edge=0.01)
    block = box(0.13, 0.06, 0.06, w - 0.13, 0.3, l - 0.06, edge=0.03)
    manifold = box(mid - 0.12, 0.26, 0.12, mid + 0.12, 0.4, l - 0.12, edge=0.02)

    def cover(sign):
        c = box(-0.08, -0.045, 0.08, 0.08, 0.045, l - 0.08, edge=0.03).rotate([0, 0, -35 * sign])
        return c.translate([mid + sign * 0.2, 0.31, 0])

    blower = box(mid - 0.16, 0.38, 0.1, mid + 0.16, 0.56, l - 0.14, edge=0.035)
    ribs = union([box(mid - 0.165, y, 0.14, mid + 0.165, y + 0.015, l - 0.18, edge=0.004) for y in (0.42, 0.46, 0.5)])
    hat = box(mid - 0.12, 0.55, 0.22, mid + 0.12, 0.58, l - 0.26, edge=0.01)
    scoop = profile_x([(0.2, 0.57), (0.22, h), (0.3, h), (l - 0.25, 0.6), (l - 0.25, 0.57)], mid - 0.1, mid + 0.1)
    mouth = box(mid - 0.075, 0.6, 0.15, mid + 0.075, h - 0.025, 0.36, edge=0)
    pulleys = union([cylinder(0.075, 0.05, "-z", (mid, 0.47, 0.1), 20), cylinder(0.09, 0.04, "-z", (mid, 0.17, 0.06), 20),
                     box(mid - 0.04, 0.17, 0.035, mid + 0.04, 0.47, 0.055, edge=0.01)])
    painted = union([base, block, manifold])
    chrome = union([cover(1), cover(-1), blower, ribs, hat, scoop - mouth, pulleys])
    return Part("e_blower_v8", "Blower V8", "engine", "engines", (w, h, l), painted, sockets(grid_cells(3, 4)), RED,
                trim=(chrome, METAL, "metal"), sound="engine_v8", power=18000.0, max_force=2300.0, mass=52.0, strength=1500.0,
                about="A V8 with a blower on top. A huge shove off the line and lots of power, but it's heavy.",
                solids=[[0, 0, 0, w, 0.4, l], [mid - 0.16, 0.4, 0.04, mid + 0.16, h, l - 0.14]])


@part
def open_exhausts():
    """Four short chrome pipes on a plate 1×4, sweeping up and back, to go
    beside an engine. Use one each side."""
    w, l, h = STUD, 4 * STUD, 0.36
    plate = box(0, 0, 0, w, PLATE, l)
    pipes = []
    for k in range(4):
        z = 0.08 + k * 0.21
        pipe = _capsule((w * 0.5, PLATE, z), (w * 0.5, h - 0.04, z + 0.16), 0.035)
        end = cylinder(0.024, 0.2, "y", (0, 0, 0), 12).rotate([45, 0, 0]).translate([w * 0.5, h - 0.04, z + 0.16])
        pipes.append(pipe - end)
    return Part("d_open_exhausts", "Open exhaust pipes", "body", "details", (w, h, l), union([plate] + pipes), sockets(grid_cells(1, 4)), METAL, finish="metal",
                aero={"front": 0.6, "back": 0.8}, mass=1.2, strength=500.0)


@part
def exhaust_stack():
    """A tall chrome exhaust stack for a big rig, on a plate 1×2, with a
    pipe in along the bottom and a slanted top."""
    w, l, h = STUD, 2 * STUD, 1.3
    plate = box(0, 0, 0, w, PLATE, l)
    stack = cylinder(0.07, h - PLATE, "y", (w * 0.5, PLATE, 0.375), 20)
    stack = stack - box(-1, 0, -1, 1, 1, 1, edge=0).rotate([-25, 0, 0]).translate([0, h - 0.05, 0.375])
    stack = stack - cylinder(0.05, 0.5, "y", (w * 0.5, h - 0.4, 0.375), 16)
    elbow = _rods([(w * 0.5, 0.17, 0.06), (w * 0.5, 0.17, 0.32), (w * 0.5, 0.25, 0.375)], 0.055)
    shield = cylinder(0.085, 0.36, "y", (w * 0.5, 0.45, 0.375), 20)
    clamps = union([cylinder(0.09, 0.03, "y", (w * 0.5, y, 0.375), 20) for y in (0.42, 0.82)])
    return Part("d_exhaust_stack", "Exhaust stack", "body", "details", (w, h, l), union([plate, stack, elbow, shield, clamps]), sockets(grid_cells(1, 2)), METAL,
                finish="metal", aero={"front": 0.6, "back": 0.8}, mass=1.5, strength=600.0,
                solids=[[0, 0, 0, w, PLATE, l], [0, PLATE, STUD, w, h, l], [0, PLATE, 0, w, 0.26, STUD]])


TUBE = 0.035  # radius of a cage or bar tube


@part
def roll_hoop():
    """A roll hoop 4 wide to go behind the driver, with braces back down to
    its feet."""
    w, l, h = 4 * STUD, 2 * STUD, 0.86
    feet = [box(x, 0, 0, x + STUD, PLATE, l) for x in (0.0, w - STUD)]
    top = h - TUBE
    hoop = _rods([(STUD * 0.5, PLATE, 0.14), (STUD * 0.5, top - 0.12, 0.14), (STUD * 0.5 + 0.1, top, 0.14),
                  (w - STUD * 0.5 - 0.1, top, 0.14), (w - STUD * 0.5, top - 0.12, 0.14), (w - STUD * 0.5, PLATE, 0.14)], TUBE)
    braces = [_capsule((x, top - 0.14, 0.14), (x, PLATE, l - 0.1), TUBE) for x in (STUD * 0.5, w - STUD * 0.5)]
    cells = [(i, k) for i in (0, 3) for k in range(2)]
    return Part("d_roll_hoop", "Roll hoop", "body", "details", (w, h, l), union(feet + [hoop] + braces), sockets(cells), BLACK,
                aero={"front": 0.5, "back": 0.8}, mass=1.5, strength=1200.0,
                solids=[[0, 0, 0, STUD, PLATE, l], [w - STUD, 0, 0, w, PLATE, l], [0, PLATE, 0.08, STUD, h, l], [w - STUD, PLATE, 0.08, w, h, l], [0, h - 0.1, 0.08, w, h, 0.22]])


@part
def roll_cage():
    """A dune buggy's roll cage 6×7, open all round, over the seat and
    steering. Pillars lean back from the front feet to the roof, and down to
    the back feet, with a cross brace behind. A plate across the front of
    the roof takes lights."""
    roof = 1.08
    w, l, h = 6 * STUD, 7 * STUD, roof + PLATE
    zf, za, zb, zr = STUD * 0.5, 0.75, 1.25, l - STUD * 0.5
    sides = []
    for x in (STUD * 0.5, w - STUD * 0.5):
        sides.append(_rods([(x, PLATE, zf), (x, roof - 0.06, za - 0.04), (x, roof, za + 0.06), (x, roof, zb - 0.06), (x, roof - 0.06, zb + 0.04), (x, PLATE, zr)], TUBE))
    x0, x1 = STUD * 0.5, w - STUD * 0.5
    bars = [_capsule((x0, roof, za + 0.06), (x1, roof, za + 0.06), TUBE), _capsule((x0, roof, zb - 0.06), (x1, roof, zb - 0.06), TUBE),
            _capsule((x0, roof - 0.06, zb + 0.04), (x1, PLATE + 0.1, zr), TUBE), _capsule((x1, roof - 0.06, zb + 0.04), (x0, PLATE + 0.1, zr), TUBE)]
    feet = [box(x, 0, z, x + STUD, PLATE, z + STUD) for x in (0.0, w - STUD) for z in (0.0, l - STUD)]
    lights = [(i, 3) for i in range(1, 5)]
    plate = union([box(STUD, roof, 3 * STUD, 5 * STUD, roof + PLATE, 4 * STUD), studs(lights, roof + PLATE)])
    cells = [(i, k) for i in (0, 5) for k in (0, 6)]
    tube = [[0, PLATE, 0, STUD, roof + TUBE, l], [w - STUD, PLATE, 0, w, roof + TUBE, l]]
    return Part("d_roll_cage", "Roll cage", "body", "details", (w, h, l), union(sides + bars + feet + [plate]), sockets(cells) + top_studs(lights, roof + PLATE), BLACK,
                aero={"front": 0.5, "back": 0.8}, mass=4.0, strength=1800.0,
                solids=[[x, 0, z, x + STUD, PLATE, z + STUD] for x in (0.0, w - STUD) for z in (0.0, l - STUD)]
                + tube + [[STUD, roof - TUBE, za, w - STUD, h, zb], [STUD, PLATE + 0.05, zb + 0.1, w - STUD, roof, zr]])


@part
def bull_bar():
    """A tubular bull bar 6 wide for the front of a truck. Its two tabs
    press onto the front row of studs and the bars hang down in front."""
    w, l, h = 6 * STUD, 2 * STUD, 0.6
    tab_y = 0.2
    tabs = [union([box(x, tab_y, STUD, x + STUD, tab_y + PLATE, l), _capsule((x + STUD * 0.5, tab_y + 0.05, STUD + 0.05), (x + STUD * 0.5, tab_y + 0.05, STUD * 0.5), TUBE)])
            for x in (STUD, 4 * STUD)]
    z = STUD * 0.5
    ups = [_capsule((x, 0.04, z), (x, h - 0.05, z), TUBE + 0.005) for x in (1.5 * STUD, 4.5 * STUD)]
    hoop = _rods([(0.06, 0.18, z), (0.08, 0.42, z), (0.22, h - TUBE - 0.01, z), (w - 0.22, h - TUBE - 0.01, z), (w - 0.08, 0.42, z), (w - 0.06, 0.18, z)], TUBE)
    bars = [_capsule((0.06, 0.18, z), (w - 0.06, 0.18, z), TUBE), _capsule((1.5 * STUD, 0.36, z), (4.5 * STUD, 0.36, z), TUBE)]
    cells = [(1, 1), (4, 1)]
    return Part("d_bull_bar", "Bull bar", "body", "details", (w, h, l), union(tabs + ups + [hoop] + bars), sockets(cells, tab_y), METAL, finish="metal",
                aero={"front": 0.5, "back": 0.8}, mass=2.5, strength=2200.0,
                solids=[[STUD, tab_y, STUD, 2 * STUD, tab_y + PLATE, l], [4 * STUD, tab_y, STUD, 5 * STUD, tab_y + PLATE, l], [0, 0, 0, w, h, STUD]])


@part
def wheelie_bar():
    """A dragster's wheelie bar: a plate 2×1 that sits on the back of the
    chassis, with two rails sloping back and down to a pair of little
    rollers that stop it flipping over."""
    w, l, h = 2 * STUD, 7 * STUD, 0.3
    top = 0.2
    plate = box(0, top, 0, w, top + PLATE, STUD)
    zr = l - 0.08
    rails = [_capsule((x, top + 0.03, 0.15), (x, 0.08, zr), 0.025) for x in (0.12, w - 0.12)]
    braces = [_capsule((0.12, 0.08 + (top - 0.05) * t, 0.15 + (zr - 0.15) * (1 - t)), (w - 0.12, 0.08 + (top - 0.05) * t, 0.15 + (zr - 0.15) * (1 - t)), 0.018) for t in (0.3, 0.65)]
    axle = cylinder(0.02, w - 0.02, "x", (0.01, 0.07, zr), 10)
    rollers = union([cylinder(0.07, 0.07, "x", (x, 0.07, zr), 18) for x in (0.002, w - 0.072)])
    return Part("d_wheelie_bar", "Wheelie bar", "body", "details", (w, h, l), union([plate, axle] + rails + braces) - rollers, sockets(grid_cells(2, 1), top), METAL,
                finish="metal", trim=(rollers, TYRE, "plastic"), aero={"front": 0.5, "back": 0.8}, mass=1.5, strength=700.0,
                solids=[[0, top, 0, w, h, STUD], [0, 0, STUD, w, top + 0.05, l]])
