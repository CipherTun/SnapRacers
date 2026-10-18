#!/usr/bin/env python3
"""Builds the stock karts, bikes and trikes in data/karts/stock, one JSON
file each.

They're written out part by part here instead of by hand in the JSON, because
most parts come in pairs, one on each side. `pair()` puts a part down and its
mirror image across the middle of the kart, the same way Mirror does in the
garage.

The build area is 20 studs across, 30 plates high and 24 studs long, and the
kart faces toward -Z (the low end of the third number). A position is the
front left bottom corner of the part's box once it's turned, in studs,
plates and studs. They can be part way, like 2.5 plates up, since the parts
join by their connectors and not only on the grid. `fine()` takes the fine
unit instead (a stud is 20 and a plate 8), for bikes. Rot is quarter turns
clockwise seen from above.

New wheels go on by their hub, so a wheel's middle has to be level with a
spot it clips onto. A chassis plate 2.5 plates up takes wheels 3 plates
across (like w_kart) right on its sides.

Run it from anywhere, then check them with:
  tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . -s tools/stock-karts/report.gd
"""

import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
PARTS = json.load(open(os.path.join(ROOT, "data", "parts.json")))["parts"]
PARTS.update(json.load(open(os.path.join(ROOT, "data", "parts_made.json")))["parts"])
OUT = os.path.join(ROOT, "data", "karts", "stock")
STUD = 20
PLATE = 8
WIDTH = 20 * STUD


def fine_size(part):
    p = PARTS[part]
    if "fine_size" in p:
        return tuple(p["fine_size"])
    s = p["size"]
    return (s[0] * STUD, s[1] * PLATE, s[2] * STUD)


def turned_size(part, rot):
    s = fine_size(part)
    return (s[2], s[1], s[0]) if rot % 2 else s


def origin(part, at, rot):
    """Where the part's own origin goes for the corner of its turned box to
    be at `at`, all in the fine unit."""
    sx, sy, sz = fine_size(part)
    x, y, z = at
    return {0: (x, y, z), 1: (x + sz, y, z), 2: (x + sx, y, z + sz), 3: (x, y, z + sx)}[rot % 4]


def new_wheel(part):
    return PARTS[part]["kind"] == "wheel" and "connectors" in PARTS[part]


class Kart:
    def __init__(self, key, name, about):
        self.key = key
        self.name = name
        self.about = about
        self.parts = []

    def fine(self, part, x, y, z, rot=0, colour=None):
        """Puts a part down with its corner here, in the fine unit."""
        pos = [round(v, 2) for v in origin(part, (x, y, z), rot)]
        entry = {"id": part, "pos": pos, "turn": rot % 4}
        if colour:
            entry["color"] = colour
        self.parts.append(entry)
        return self

    def add(self, part, x, y, z, rot=0, colour=None):
        """Puts a part down with its corner here, in studs, plates and studs."""
        return self.fine(part, x * STUD, y * PLATE, z * STUD, rot, colour)

    def pair_fine(self, part, x, y, z, rot=0, colour=None):
        self.fine(part, x, y, z, rot, colour)
        # A new wheel's twin is turned right round, so its hub faces in.
        twin_rot = (rot + 2) % 4 if new_wheel(part) else (4 - rot) % 4
        twin = PARTS[part].get("mirror", part)
        sx = turned_size(twin, twin_rot)[0]
        return self.fine(twin, WIDTH - x - sx, y, z, twin_rot, colour)

    def pair(self, part, x, y, z, rot=0, colour=None):
        """Puts a part down on the left and its mirror image on the right."""
        return self.pair_fine(part, x * STUD, y * PLATE, z * STUD, rot, colour)

    def wheels(self, part, z, y=0, x_left=None):
        """A pair of wheels on the chassis sides, the left one ending at x 7.
        An old wheel's z is its corner. A new wheel's is the middle of the
        stud its hub clips onto."""
        w = turned_size(part, 0)[0] / STUD
        x = 7 - w if x_left is None else x_left
        if new_wheel(part):
            radius = fine_size(part)[2] / 2
            return self.pair_fine(part, x * STUD, y * PLATE, z * STUD - radius, 0)
        return self.pair(part, x, y, z)

    def save(self):
        lines = ",\n".join("\t\t" + json.dumps(p) for p in self.parts)
        text = '{\n\t"name": %s,\n\t"about": %s,\n\t"parts": [\n%s\n\t]\n}\n' % (json.dumps(self.name), json.dumps(self.about, ensure_ascii=False), lines)
        with open(os.path.join(OUT, self.key + ".json"), "w") as f:
            f.write(text)


karts = []


def kart(key, name, about):
    k = Kart(key, name, about)
    karts.append(k)
    return k


RED = "#c4281c"
BLUE = "#0d69ab"
YELLOW = "#f2cd37"
WHITE = "#f2f3f2"
BLACK = "#1b2a34"
DARK = "#1b1b1b"
GREY = "#635f61"
SILVER = "#a3a2a4"
ORANGE = "#da8540"
TEAL = "#36aebf"
GREEN = "#237841"
LIME = "#a4bd46"
MUD = "#694030"
RUST = "#7b2e2f"
PURPLE = "#6b3fa0"
KART_GREEN = "#4b9f4a"
TAN = "#d7c599"


def radius(wheel):
    return fine_size(wheel)[1] / 2


def chassis(k, front, back, z0, length, colour, extra_front=()):
    """A kart's chassis: an axle plate at the front and back with the wheels
    on their pins, and 6 wide plates along the top of both. When the back
    wheels are bigger, plates on the front axle plate bring it level.
    `extra_front` puts more axles of front wheels further back, for the
    Six-wheeler. Returns the top of the chassis, in plates."""
    level = max(radius(front), radius(back)) - 4
    axles = [(front, z0)] + [(front, z) for z in extra_front] + [(back, z0 + length - 2)]
    for wheel, z in axles:
        base = radius(wheel) - 4
        k.fine("p_kart_axle_plate", 6 * STUD, base, z * STUD, colour=DARK)
        k.pair_fine(wheel, 7 * STUD - turned_size(wheel, 0)[0], 0, z * STUD + STUD - fine_size(wheel)[2] / 2)
        y = base + PLATE
        while y < level + PLATE - 0.01:
            k.fine("p_plate_2x6", 7 * STUD, y, z * STUD, rot=1, colour=DARK)
            y += PLATE
    z = z0
    for size in {6: [6], 8: [8], 10: [10], 12: [12], 20: [12, 8]}[length]:
        k.fine("p_plate_6x%d" % size, 7 * STUD, level + PLATE, z * STUD, colour=colour)
        z += size
    return (level + 2 * PLATE) / PLATE


def racer(k, front, back, z0, length, colour=DARK, arches=2, width=6):
    """The new racers' black chassis: an axle plate at the front and back
    with the wheels on their pins out at the corners, and plates `width`
    wide (6, or 4 for a slim formula car) along the top, levelled like
    chassis(). Arches mount by their end cells, so `arches` (2 or 3, how
    wide they are) puts plates out beside the chassis under both ends of an
    arch 6 long centred on each wheel: one under the chassis reaching out,
    and one on it at chassis level. 0 leaves them off, for open wheels.
    When two plates along the top meet between two arches, the arch plates
    behind the front wheels reach a row further, under the seam (and do for
    the back arch too when the arches touch). Returns the top of the
    chassis, in plates."""
    assert width in (4, 6) and arches in (0, 2, 3)
    assert not arches or length >= 8, "arches need a chassis 8 or more long"
    assert arches + width <= 8, "arches 3 wide only fit the wide chassis"
    edge = 10 - width // 2
    axle = {6: "p_kart_axle_plate", 4: "p_kart_axle_plate_4"}[width]
    level = max(radius(front), radius(back)) - 4
    for wheel, z in ((front, z0), (back, z0 + length - 2)):
        base = radius(wheel) - 4
        assert (level - base) % PLATE == 0, "%s and %s aren't whole plates apart" % (front, back)
        k.fine(axle, (edge - 1) * STUD, base, z * STUD, colour=colour)
        k.pair_fine(wheel, edge * STUD - turned_size(wheel, 0)[0], 0, z * STUD + STUD - fine_size(wheel)[2] / 2)
        y = base + PLATE
        while y < level + PLATE - 0.01:
            k.fine("p_plate_2x%d" % width, edge * STUD, y, z * STUD, rot=1, colour=colour)
            y += PLATE
    # An arch 6 long sits centred on the wheel, so its end cells are 2 studs
    # before the axle plate and 1 after it.
    ends = [r for a in (z0, z0 + length - 2) for r in (a - 2, a + 3)] if arches else []
    bridge = None
    start = z0 - 2 if arches else z0
    end = z0 + length + 2 if arches else z0 + length
    sizes = range(width, 2 * width + 1, 2)
    if end - start in sizes:
        k.fine("p_plate_%dx%d" % (width, end - start), edge * STUD, level + PLATE, start * STUD, colour=colour)
    else:
        # Two plates butted together. Plates side by side don't join, so the
        # join goes over the middle of an axle plate, or a 2×2 plate under
        # it holds them together.
        axles = (z0, z0 + length - 2)
        rows = [(a, 2) for a in axles]
        if edge + arches > 9:
            # The arches' plates under the chassis reach the middle too.
            rows += [(r, 1) for a in axles for r in (a - 2, a + 3)] if arches else []
        for first in sizes:
            seam = start + first
            if end - seam not in sizes:
                continue
            on_axle = any(seam == a + 1 for a in axles)
            clear = all(seam + 1 <= r or seam - 1 >= r + n for r, n in rows)
            # Or the arch plates under the row before the seam reach a row
            # further, across it, when that row's free or the next arch's.
            free = all(seam + 1 <= r or seam >= r + n for r, n in rows) or seam in ends
            if not (on_axle or clear) and seam - 1 in ends and free:
                bridge = seam - 1
            if on_axle or clear or bridge is not None:
                break
        else:
            raise ValueError("no way to join a chassis %d long" % (end - start))
        k.fine("p_plate_%dx%d" % (width, first), edge * STUD, level + PLATE, start * STUD, colour=colour)
        k.fine("p_plate_%dx%d" % (width, end - seam), edge * STUD, level + PLATE, seam * STUD, colour=colour)
        if not on_axle and bridge is None:
            k.fine("p_plate_2x2", 9 * STUD, level, (seam - 1) * STUD, colour=colour)
    for r in sorted(set(ends)):
        if bridge is not None and r == bridge + 1:
            continue
        n = 2 if r == bridge else 1
        k.pair_fine("p_plate_%dx%d" % (n, 2 * arches), (edge - arches) * STUD, level, r * STUD, rot=1, colour=colour)
        k.pair_fine("p_plate_%dx%d" % (n, arches), (edge - arches) * STUD, level + PLATE, r * STUD, rot=1, colour=colour)
    return (level + 2 * PLATE) / PLATE


# 1. The one everyone starts with.
k = kart("starter", "Starter", "A bit of everything. It's a good kart to learn on and to build from.")
T = chassis(k, "w_kart", "w_kart_wide", 7, 10, SILVER)
(k.add("p_nose_4x6_lights", 8, T, 4, colour=RED)
    .pair("p_curve_1x3", 7, T, 7, colour=YELLOW)
    .add("steering_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .pair("p_curve_2x6", 7, T, 10, colour=RED)
    .add("engine_small", 9, T, 14)
    .add("ducktail", 7, T + 3, 15, colour=YELLOW)
    .pair("d_taillight_1x2", 7, T + 5, 15)
    .pair("p_tile_1x2", 7, T, 16, rot=1, colour=DARK))

# 2. As light as a kart can be.
k = kart("featherlight", "Featherlight", "Light and low, with skinny wheels at the front, handlebars for quick hands and a little rotary engine that revs and revs.")
T = chassis(k, "w_scooter", "w_kart", 7, 10, WHITE)
(k.add("p_nose_4x6_lights", 8, T, 4, colour=BLUE)
    .pair("p_tile_1x2", 7, T, 7, colour=BLUE)
    .add("handlebars", 8, T, 10)
    .add("s_racing_seat", 9, T, 11)
    .pair("p_curve_1x4", 7, T, 11, colour=BLUE)
    .add("engine_rotary", 9, T, 14)
    .add("p_curve_2x2", 9, T + 2, 14, rot=2, colour=BLUE)
    .pair("p_tile_1x2", 7, T, 15, colour=WHITE))

# 3. Heavy, flat fronted and hard to push around.
k = kart("bruiser", "Bruiser", "A heavy slab with a diesel and a ram. Slow to get going, but it shoves everyone else out of the way.")
T = chassis(k, "wheel_big_wide", "wheel_big_wide", 6, 10, GREY)
(k.add("ram_plate", 7, T, 6)
    .pair("d_light_1x1", 7, T + 3, 6)
    .pair("p_brick_2x4", 7, T, 7, colour=RUST)
    .pair("ballast", 7, T + 3, 7, colour=RUST)
    .pair("p_curve_2x2", 7, T + 6, 7, colour=RUST)
    .pair("p_curve_2x2", 7, T + 3, 9, rot=2, colour=RUST)
    .add("steering_wheel", 9, T, 9)
    .add("s_seat", 9, T, 10)
    .add("engine_diesel", 8, T, 12)
    .pair("p_curve_1x2", 7, T, 12, rot=2, colour=RUST)
    .pair("d_exhaust", 7, T, 14))

# 4. A long dragster, with skinny wheels up front and slicks at the back.
k = kart("slingshot", "Slingshot", "A dragster with the driver lying down, a V8 in the back and big slicks right at the tail. It's heavy and nothing turns worse, but it's quick down a straight.")
T = chassis(k, "w_scooter", "w_slick", 3, 20, BLACK)
(k.add("p_nose_4x6_lights", 8, T, 0, colour=ORANGE)
    .add("p_tile_2x6", 9, T, 6, colour=ORANGE)
    .pair("p_curve_2x6", 7, T, 6, colour=ORANGE)
    .pair("p_curve_2x4", 7, T, 12, colour=BLACK)
    .add("yoke", 9, T, 14)
    .add("s_lay_down_seat", 9, T, 15)
    .pair("p_tile_2x2", 7, T, 16, colour=ORANGE)
    .add("engine_v8", 9, T, 19)
    .pair("d_exhaust", 7, T, 19)
    .add("rear_wing_6x2", 7, T + 3, 21, colour=ORANGE))

# 5. Smooth all over, for top speed.
k = kart("streamliner", "Streamliner", "Faired in from nose to tail with the driver lying down under a bubble. The fastest thing on a long straight, and a handful in the corners.")
T = chassis(k, "w_kart", "w_kart_wide", 6, 12, SILVER)
(k.add("p_nose_4x6_lights", 8, T, 3, colour=WHITE)
    .add("p_brick_1x1", 8, T, 9, colour=WHITE).add("p_brick_1x1", 11, T, 9, colour=WHITE)
    .add("p_brick_1x1", 8, T, 14, colour=WHITE).add("p_brick_1x1", 11, T, 14, colour=WHITE)
    .add("d_canopy", 8, T + 3, 9)
    .add("racing_wheel", 9, T, 10)
    .add("s_lay_down_seat", 9, T, 11)
    .pair("p_curve_1x4", 7, T, 9, colour=WHITE)
    .pair("p_tile_1x2", 7, T, 13, colour=WHITE)
    .add("engine_rotary", 9, T, 15)
    .add("p_curve_2x2", 9, T + 2, 15, rot=2, colour=WHITE)
    .pair("p_curve_2x2", 7, T, 15, rot=2, colour=WHITE))

# 6. For grass and dirt.
k = kart("mudlark", "Mudlark", "Knobbly tires and a diesel, sitting up high. It's slow on the road and happy anywhere else.")
T = chassis(k, "w_offroad", "w_offroad", 7, 10, MUD)
(k.add("p_nose_4x6", 8, T, 4, colour=LIME)
    .pair("d_light_1x1", 7, T, 7)
    .pair("p_curve_1x2", 7, T, 8, colour=LIME)
    .add("steering_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .pair("p_curve_2x2", 7, T, 10, colour=LIME)
    .pair("d_exhaust", 7, T, 12)
    .add("engine_diesel", 8, T, 13))

# 7. Three wheels and a battery.
k = kart("trike", "Trike", "One wheel at the front and an electric motor at the back. Light and eager, and tippy if you push it.")
(k.add("plate_2x4", 7, 3, 4, colour=WHITE).add("plate_2x4", 11, 3, 4, colour=WHITE)
    .add("wheel_small_wide", 9, 0, 4)
    .pair("p_tile_2x2", 7, 4, 4, colour=TEAL)
    .pair("d_light_1x1", 7, 4, 6))
k.fine("p_kart_axle_plate", 6 * STUD, 24, 15 * STUD, colour=DARK)
k.pair_fine("w_racing", 7 * STUD - 28, 0, 16 * STUD - 28)
k.add("p_plate_6x10", 7, 4, 7, colour=WHITE)
T = 5
(k.pair("p_curve_2x2", 7, T, 7, colour=TEAL)
    .add("handlebars", 8, T, 9)
    .add("s_racing_seat", 9, T, 10)
    .pair("p_curve_1x4", 7, T, 10, colour=TEAL)
    .add("electric_big", 9, T, 13)
    .add("p_curve_2x2", 9, T + 2, 14, rot=2, colour=TEAL)
    .pair("p_curve_2x2", 7, T, 14, rot=2, colour=WHITE)
    .pair("p_tile_1x2", 7, T, 16, rot=1, colour=TEAL))

# 8. Four little wheels steering at the front.
k = kart("six_wheeler", "Six-wheeler", "Four small wheels steer at the front, so it grips like nothing else, with a low flat four at the back.")
T = chassis(k, "w_kart", "w_kart_wide", 4, 12, BLACK, extra_front=(7,))
(k.add("p_nose_4x6_lights", 8, T, 1, colour=GREEN)
    .pair("p_curve_1x3", 7, T, 4, colour=GREEN)
    .pair("p_curve_2x6", 7, T, 7, colour=GREEN)
    .add("steering_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .add("engine_flat4", 8, T, 13)
    .pair("p_tile_1x2", 7, T, 13, colour=GREEN)
    .add("spoiler_6", 7, T + 2, 14, colour=YELLOW))

# 9. Huge wheels.
k = kart("monster", "Monster", "Monster wheels and a hybrid engine. It rolls over everything, and over itself if you corner too hard.")
T = chassis(k, "wheel_monster", "wheel_monster", 6, 10, DARK)
(k.add("p_slope_2x2", 7, T, 6, colour=PURPLE).add("p_slope_2x2", 9, T, 6, colour=PURPLE).add("p_slope_2x2", 11, T, 6, colour=PURPLE)
    .pair("d_light_1x1", 7, T + 3, 7)
    .pair("p_brick_2x2", 7, T, 8, colour=PURPLE)
    .pair("p_curve_2x2", 7, T + 3, 8, colour=PURPLE)
    .add("steering_wheel", 9, T, 9)
    .add("s_seat", 9, T, 10)
    .pair("p_curve_2x2", 7, T, 10, colour=PURPLE)
    .add("engine_hybrid", 9, T, 12)
    .pair("p_round_brick_2x2", 7, T, 12, colour=PURPLE)
    .pair("p_curve_2x2", 7, T, 14, rot=2, colour=PURPLE))

# 10. Pushed along by a jet.
k = kart("rocket", "Rocket", "A jet engine, slicks and wings. Slow off the line, then very, very fast, and it keeps pushing on the grass.")
T = chassis(k, "wheel_slick", "wheel_slick", 7, 10, WHITE)
(k.add("front_wing_6x2", 7, T, 7, colour=RED)
    .add("p_nose_4x6_lights", 8, T + 1, 4, colour=RED)
    .pair("p_curve_2x4", 7, T, 10, colour=WHITE)
    .add("steering_wheel", 9, T, 10)
    .add("s_racing_seat", 9, T, 11)
    .add("jet", 9, T, 14)
    .pair("p_curve_2x2", 7, T, 14, rot=2, colour=RED)
    .add("rear_wing_6x2", 7, T + 3, 16, colour=RED))

# 11. A proper go-kart, all frame.
k = kart("classic", "Classic", "A proper go-kart, with a nose cone, a little engine off to one side and handlebars. Light, simple and quick in the twisty bits.")
T = chassis(k, "w_kart", "w_kart_wide", 7, 10, YELLOW)
(k.add("p_nose_4x6_lights", 8, T, 4, colour=DARK)
    .pair("p_tile_1x2", 7, T, 7, colour=DARK)
    .add("handlebars", 8, T, 10)
    .add("s_bucket_seat", 9, T, 11)
    .add("p_curve_1x4", 7, T, 10, colour=DARK).add("p_curve_1x3", 12, T, 10, colour=DARK)
    .add("engine_small", 11, T, 13)
    .add("d_exhaust", 12, T + 3, 13)
    .add("p_curve_2x2", 8, T, 15, rot=2, colour=DARK).add("p_tile_1x2", 10, T, 15, colour=DARK))

# 12. Wings everywhere.
k = kart("downforce", "Downforce", "Big wings front and back, and slicks at the back. The faster it goes the harder it grips, so it flies through fast corners.")
T = chassis(k, "w_kart", "wheel_slick", 7, 10, BLACK)
(k.add("front_wing_6x2", 7, T, 7, colour=YELLOW)
    .add("p_nose_4x6_lights", 8, T + 1, 4, colour=BLACK)
    .pair("p_curve_2x6", 7, T, 10, colour=BLACK)
    .add("steering_wheel", 9, T, 10)
    .add("s_racing_seat", 9, T, 11)
    .add("engine_small", 9, T, 14)
    .add("rear_wing_6x2", 7, T + 3, 15, colour=YELLOW))

# 13. Bricks on bricks.
k = kart("brick_tank", "Brick Tank", "Thick armour all around and a diesel. It takes a beating and keeps going.")
T = chassis(k, "w_kart_wide", "w_kart_wide", 7, 10, GREY)
(k.pair("p_brick_2x4", 7, T, 7, colour=GREY)
    .pair("p_curve_2x4", 7, T + 3, 7, colour=GREY)
    .add("p_slope_2x2", 9, T, 7, colour=GREY)
    .add("d_light_1x1", 9, T + 3, 8).add("d_light_1x1", 10, T + 3, 8)
    .add("steering_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .pair("p_brick_1x6", 7, T, 11, colour=GREY)
    .pair("p_tile_1x6", 7, T + 3, 11, colour=GREY)
    .add("engine_diesel", 9, T, 14))

# 14. The all rounder, with a battery.
k = kart("sparky", "Sparky", "An electric all rounder. Quick away from the line, and easy to drive.")
T = chassis(k, "w_kart", "w_kart_wide", 7, 10, WHITE)
(k.add("p_nose_4x6_lights", 8, T, 4, colour=TEAL)
    .pair("p_curve_1x3", 7, T, 7, colour=WHITE)
    .add("racing_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .pair("p_curve_2x4", 7, T, 10, colour=TEAL)
    .add("electric_motor", 9, T, 14)
    .add("p_curve_2x2", 9, T + 2, 14, rot=2, colour=TEAL)
    .pair("p_curve_2x2", 7, T, 14, rot=2, colour=WHITE))

# 15. Engine out front, big wheels out back.
k = kart("hot_rod", "Hot Rod", "A V8 out in front and big wheels at the back. Loud, heavy and very fast, if you can keep it pointing the right way.")
T = chassis(k, "w_kart", "wheel_big_wide", 5, 10, DARK)
(k.add("engine_v8", 9, T, 5)
    .pair("d_light_1x1", 7, T, 5)
    .pair("d_exhaust", 7, T, 6)
    .add("steering_wheel", 9, T, 10)
    .add("s_seat", 9, T, 11)
    .pair("p_curve_2x6", 7, T, 9, colour=RED)
    .add("ducktail", 7, T + 3, 13, colour=DARK))

# 16. Rolls forever.
k = kart("soapbox", "Soapbox", "Tall thin wheels, a nose cone and a little rotary engine. Not much push, but hardly anything holds it back either.")
T = chassis(k, "wheel_big", "wheel_big", 5, 12, TAN)
(k.add("p_nose_4x6_lights", 8, T, 2, colour=RED)
    .add("d_screen_2", 9, T, 8)
    .pair("p_curve_1x4", 7, T, 8, colour=RED)
    .add("racing_wheel", 9, T, 10)
    .add("s_lay_down_seat", 9, T, 11)
    .add("engine_rotary", 11, T, 13)
    .add("p_curve_2x2", 9, T, 15, rot=2, colour=RED))


# 17. A formula racer, open wheels and wings.
k = kart("redline", "Redline", "A formula racer with open wheels, wings at both ends and a little engine behind the driver. Light and quick through the fast corners.")
T = racer(k, "w_kart_wide", "w_slick", 3, 12, arches=0, width=4)
(k.add("d_front_wing_8x2", 6, T - 1, 0, colour=WHITE)
    .add("p_nose_cone_2x6", 9, T, 0, colour=RED)
    .pair("p_curve_1x4", 8, T, 3, colour=RED)
    .add("racing_wheel", 9, T, 6)
    .add("s_lay_down_seat", 9, T, 7)
    .pair("p_curve_2x4", 7, T, 7, rot=2, colour=RED)
    .add("engine_small", 9, T, 11, colour=DARK)
    .add("p_curve_2x2", 9, T + 3, 11, rot=2, colour=RED)
    .add("d_roll_hoop", 8, T, 11, colour=SILVER)
    .pair("d_open_exhausts", 8, T, 13)
    .add("p_brick_2x2", 9, T, 13, colour=DARK)
    .add("d_rear_wing_8", 6, T + 3, 13, colour=RED))


def arches(k, T, axles, colour, sides=None, part="p_arch_2x6_smooth"):
    """Smooth arches 2 wide over each pair of wheels of a slim racer()
    chassis (width 4, arches 2), `axles` being where its axle plates start.
    A gap between two arches gets a plate reaching out under the chassis and
    a brick 2×2 in `sides` on it, with a tile level with the arch ends.
    racer() has the front arch's back plates reach into the gap's first row
    already."""
    for a in axles:
        k.pair(part, 6, T, a - 2, colour=colour)
    if sides:
        z = axles[0] + 4
        assert axles[1] - 2 - z == 2, "the gap between arches has to be 2 long"
        (k.pair("p_plate_1x4", 6, T - 2, z + 1, rot=1, colour=DARK)
            .pair("p_plate_1x2", 6, T - 1, z + 1, rot=1, colour=DARK)
            .pair("p_brick_2x2", 6, T, z, colour=sides)
            .pair("p_tile_2x2", 6, T + 3, z, colour=sides))


# 18. A muscle car, low and long with black stripes nose to tail.
k = kart("big_block", "Big Block", "A muscle car with a big engine under a long striped bonnet. Heavy and strong, and quick once it gets going.")
T = racer(k, "w_slick", "w_slick", 3, 10, width=4)
arches(k, T, (3, 11), ORANGE, sides=ORANGE)
(k.add("p_plate_4x6", 8, T, 1, colour=ORANGE)
    .add("p_bonnet_4x6_black_stripes", 8, T + 1, 1, colour=ORANGE)
    .add("p_scoop_2x3", 9, T + 4, 4, colour=SILVER)
    .add("p_tile_1x1", 8, T + 4, 6, colour=BLACK).add("p_tile_1x1", 11, T + 4, 6, colour=BLACK)
    .add("p_brick_1x4", 8, T, 7, rot=1, colour=DARK)
    .add("windscreen_4", 8, T + 3, 7)
    .add("steering_wheel", 9, T, 8)
    .add("s_racing_seat", 9, T, 9)
    .pair("p_brick_1x4", 8, T, 11, colour=ORANGE)
    .add("engine_v8", 9, T, 11, colour=SILVER)
    .add("p_tile_1x4", 8, T + 3, 11, colour=BLACK).add("p_tile_1x4", 11, T + 3, 11, colour=BLACK)
    .add("p_tile_2x2", 9, T + 3, 11, colour=ORANGE)
    .add("d_rear_wing_8", 6, T + 3, 13, colour=DARK))

# 19. A stock car for the oval, a cab in the middle and a number on the roof.
k = kart("oval_ace", "Oval Ace", "A stock car built for long fast bends, with a roof over the driver and a spoiler on the boot. Steady and easy to drive.")
T = racer(k, "w_racing", "w_racing", 3, 8, width=4)
arches(k, T, (3, 9), BLUE, part="p_arch_2x6_yellow_stripe")
(k.add("p_plate_4x4", 8, T, 1, colour=BLUE)
    .add("p_curve_4x4", 8, T + 1, 1, colour=BLUE)
    .add("p_tile_1x4", 8, T + 4, 4, rot=1, colour=BLUE)
    .pair("p_brick_1x6", 8, T, 5, colour=BLUE)
    .add("steering_wheel", 9, T, 6)
    .add("s_racing_seat", 9, T, 7)
    .add("p_cab_4x6", 8, T + 3, 5, colour=BLUE)
    .add("p_round_tile_2x2", 9, T + 9, 7, colour=WHITE)
    .pair("p_brick_1x2", 8, T, 11, colour=BLUE)
    .add("engine_small", 9, T, 11, colour=SILVER)
    .add("p_plate_2x4", 8, T + 3, 11, rot=1, colour=BLUE)
    .add("p_tile_1x4", 8, T + 4, 11, rot=1, colour=BLUE)
    .add("d_front_wing_8x2", 6, T + 4, 12, colour=YELLOW))

# 20. A little go-kart: an open frame, a small nose, side pods and the
# engine beside the seat.
k = kart("kart_kid", "Kart Kid", "A proper little go-kart, light and nippy with the engine beside the seat. Easy to learn on.")
T = racer(k, "w_kart", "w_kart_wide", 1, 10, arches=0, width=4)
(k.add("p_curve_2x4", 9, T, 0, colour=KART_GREEN)
    .add("p_tile_1x2", 9, T + 3, 3, rot=1, colour=YELLOW)
    .add("steering_wheel", 9, T, 4)
    .add("p_tile_1x2", 9, T, 5, rot=1, colour=DARK)
    .pair("p_tile_1x4", 8, T, 4, colour=DARK)
    .pair("p_tile_1x2", 8, T, 8, colour=DARK)
    .add("p_tile_2x2", 9, T, 8, colour=DARK)
    .add("p_tile_1x4", 8, T, 10, rot=1, colour=DARK)
    .add("s_bucket_seat", 9, T, 6, colour=DARK)
    .pair("p_plate_2x3", 6, T - 2, 4, rot=1, colour=KART_GREEN)
    .add("p_plate_2x8", 6, T - 2, 6, rot=1, colour=KART_GREEN)
    .add("p_tile_2x2", 6, T - 1, 4, colour=KART_GREEN)
    .add("engine_small", 6, T - 1, 6, colour=SILVER)
    .add("p_tile_2x2", 6, T + 2, 6, colour=SILVER)
    .add("p_tile_2x4", 12, T - 1, 4, colour=KART_GREEN))

# 21. A rally car in white with red and blue stripes, lamps on the bonnet,
# a light pod on the roof and mud flaps.
k = kart("gravel_rat", "Gravel Rat", "A rally car on knobbly tires with four lamps on the bonnet. At home on dirt and gravel and fine on the road too.")
T = racer(k, "w_offroad", "w_offroad", 3, 8, width=4)
arches(k, T, (3, 9), WHITE)
(k.add("p_plate_4x4", 8, T, 1, colour=WHITE)
    .add("p_plate_4x4", 8, T + 1, 1, colour=WHITE)
    .pair("d_spotlights", 8, T + 2, 1, colour=YELLOW)
    .add("p_tile_1x4", 8, T + 2, 2, rot=1, colour=WHITE)
    .add("p_tile_1x2", 8, T + 2, 3, colour=WHITE).add("p_tile_1x2", 11, T + 2, 3, colour=WHITE)
    .add("p_tile_1x2", 9, T + 2, 3, colour=RED).add("p_tile_1x2", 10, T + 2, 3, colour=BLUE)
    .pair("p_brick_1x6", 8, T, 5, colour=WHITE)
    .add("steering_wheel", 9, T, 6)
    .add("s_racing_seat", 9, T, 7)
    .add("p_cab_4x6", 8, T + 3, 5, colour=WHITE)
    .add("d_spotlights", 9, T + 9, 7, colour=WHITE)
    .add("p_tile_1x2", 9, T + 9, 8, rot=1, colour=BLUE)
    .pair("p_brick_1x2", 8, T, 11, colour=WHITE)
    .add("engine_small", 9, T, 11, colour=SILVER)
    .add("p_tile_1x2", 8, T + 3, 11, colour=WHITE).add("p_tile_1x2", 11, T + 3, 11, colour=WHITE)
    .add("p_tile_1x2", 9, T + 3, 11, colour=RED).add("p_tile_1x2", 10, T + 3, 11, colour=BLUE))
# The flaps hang from the arch plates under the chassis, behind each wheel.
for z in (6, 12):
    k.pair_fine("d_mud_flap", 6 * STUD, (T - 2) * PLATE - 12, z * STUD, colour=RED)

# 22. An endurance racer, pinched in the middle under a bubble, with a lime
# stripe nose to tail.
k = kart("night_shift", "Night Shift", "An endurance racer with the driver lying down under a bubble and a wide wing over the gearbox. Fast and smooth, and it doesn't mind a long race.")
T = racer(k, "w_racing", "w_racing", 3, 10, width=4)
arches(k, T, (3, 11), BLUE)
(k.add("p_plate_4x4", 8, T, 1, colour=BLUE)
    .add("p_bonnet_4x4_lime_stripe", 8, T + 1, 1, colour=BLUE)
    .add("d_canopy_high_back", 8, T + 4, 5))
# The bubble stands on posts a brick and a plate high, clear of the wheel.
for x in (8, 11):
    for z in (5, 10):
        k.add("p_brick_1x1", x, T, z, colour=BLUE).add("p_plate_1x1", x, T + 3, z, colour=BLUE)
(k
    .add("racing_wheel", 9, T, 5)
    .add("s_lay_down_seat", 9, T, 6)
    .add("p_plate_4x4", 8, T, 11, colour=BLUE)
    .add("p_bonnet_4x4_lime_stripe", 8, T + 1, 11, rot=2, colour=BLUE)
    .add("p_plate_2x3", 9, T - 3, 14, colour=DARK)
    .add("engine_small", 9, T - 2, 15, colour=DARK)
    .add("d_rear_wing_8", 6, T + 1, 15, colour=DARK))

# 23. A dragster: a long thin flamed body, slicks at the back with a blower
# V8 in front of them, a wing up high and a wheelie bar. It's built by hand,
# low at the nose and a step up at the back for the big wheels.
k = kart("quarter_mile", "Quarter Mile", "A dragster with a blower V8, huge slicks and a wheelie bar. Unbeatable in a straight line, and it hates corners.")
(k.add("p_kart_axle_plate_4", 7, 2.5, 0, colour=DARK)
    .pair_fine("w_drag_front", 8 * STUD - fine_size("w_drag_front")[0], 24 - radius("w_drag_front"), STUD - fine_size("w_drag_front")[2] / 2)
    .add("p_plate_2x10", 9, 2.5, 2, colour=DARK)
    .add("p_plate_2x6", 9, 2.5, 12, colour=DARK)
    .pair("p_tile_1x2", 8, 3.5, 0, colour=DARK)
    .add("p_drag_body_2x10_flames", 9, 3.5, 0, colour=PURPLE)
    .add("racing_wheel", 9, 3.5, 10)
    .add("s_racing_seat", 9, 3.5, 11)
    .add("p_plate_2x4", 9, 3.5, 14, colour=DARK)
    .add("p_kart_axle_plate_4", 7, 4.5, 16, colour=DARK)
    .pair_fine("w_drag_slick", 8 * STUD - fine_size("w_drag_slick")[0], 0, 16 * STUD + STUD - fine_size("w_drag_slick")[2] / 2)
    .add("p_jumper_1x2", 9, 5.5, 16, colour=DARK)
    .add("e_blower_v8", 8.5, 6.5, 13, colour=RED)
    .add("d_wheelie_bar", 9, 3.5, 17)
    .pair("p_brick_1x1", 8, 5.5, 17, colour=DARK)
    .add("p_plate_2x4", 8, 8.5, 17, rot=1, colour=DARK)
    .pair("p_tile_1x2", 8, 9.5, 17, colour=DARK)
    .add("d_rear_wing_8", 6, 9.5, 17, colour=PURPLE))

# 24. A hot rod: a blower V8 out front over little wheels, a flamed tub for
# the driver and big slicks at the back, with open pipes down both sides.
# It's built by hand so the engine and driver sit low: a plate 4×8 hangs
# off the back axle plate and reaches forward to the front one, with tiles
# either side of the engine joining the two.
k = kart("flathead", "Flathead", "A hot rod with a blower V8 out in the open and fat tires at the back. Loads of pull, and a bit of a handful.")
(k.add("p_kart_axle_plate_4", 7, 2.5, 1, colour=DARK)
    .pair_fine("w_kart", 8 * STUD - fine_size("w_kart")[0], 0, 2 * STUD - fine_size("w_kart")[2] / 2)
    .add("p_plate_4x8", 8, 2.5, 3, colour=DARK)
    .add("p_kart_axle_plate_4", 7, 3.5, 9, colour=DARK)
    .pair_fine("w_slick", 8 * STUD - fine_size("w_slick")[0], 0, 10 * STUD - fine_size("w_slick")[2] / 2)
    .add("d_hot_rod_grille", 9, 2.5, 0)
    .pair("p_tile_1x4", 8, 3.5, 1, colour=DARK)
    .add("p_jumper_1x2", 9, 3.5, 2, colour=DARK).add("p_jumper_1x2", 9, 3.5, 3, colour=DARK)
    .add("e_blower_v8", 8.5, 4.5, 1, colour=RED)
    .pair("p_plate_2x3", 7, 3.5, 5, colour=DARK)
    .pair("d_open_exhausts", 7, 4.5, 4)
    .pair("p_tub_side_1x6_flames", 8, 4.5, 5, colour=TEAL)
    .add("windscreen_tall", 9, 3.5, 5)
    .add("steering_wheel", 9, 3.5, 6)
    .add("s_racing_seat", 9, 3.5, 7)
    .add("p_plate_2x2", 9, 4.5, 9, colour=TEAL)
    .add("p_curve_2x2", 9, 5.5, 9, rot=2, colour=TEAL))

# 25. A dune buggy: knobbly tires, a short yellow nose, a roll cage with
# lamps on top and the engine out the back.
k = kart("sandhopper", "Sandhopper", "A dune buggy on big knobbly tires with a roll cage and lamps on top. Happiest off the road, in sand and on grass.")
T = racer(k, "w_offroad", "w_offroad", 1, 8, arches=0, width=4)
(k.add("p_bonnet_4x4", 8, T, 0, colour=YELLOW)
    .pair("p_tile_1x2", 8, T, 5, colour=YELLOW)
    .add("d_roll_cage_4x4", 8, T, 4, colour=DARK)
    .add("d_light_1x1", 8.5, T + 11.8, 6, colour=YELLOW).add("d_light_1x1", 9.5, T + 11.8, 6, colour=YELLOW).add("d_light_1x1", 10.5, T + 11.8, 6, colour=YELLOW)
    .add("steering_wheel", 9, T, 4)
    .add("s_racing_seat", 9, T, 5)
    .add("engine_small", 9, T, 8, colour=SILVER)
    .add("p_tile_2x2", 9, T + 3, 8, colour=SILVER)
    .pair("d_exhaust", 8, T, 8))

# 26. An electric racer in white with teal stripes, smooth over the wheels,
# with an open cockpit and a wing at each end.
k = kart("volt", "Volt", "An electric racer, smooth and light, with wings at both ends. Quick away and easy to drive.")
T = racer(k, "w_racing", "w_racing", 4, 10, width=4)
arches(k, T, (4, 12), WHITE, sides=WHITE, part="p_arch_2x6_teal_stripe")
(k.add("d_front_wing_8x2", 6, T - 1, 0, colour=BLUE)
    .add("p_plate_4x4", 8, T, 0, colour=WHITE)
    .add("p_bonnet_4x4", 8, T + 1, 0, colour=WHITE)
    .add("windscreen_2", 9, T, 4)
    .add("racing_wheel", 9, T, 5)
    .add("s_lay_down_seat", 9, T, 6)
    .pair("p_brick_1x6", 8, T, 4, colour=WHITE)
    .pair("p_tile_1x2", 8, T + 3, 4, colour=WHITE)
    .pair("p_tile_1x4", 8, T + 3, 6, colour=BLUE)
    .add("p_plate_4x4", 8, T, 10, colour=WHITE)
    .add("p_bonnet_4x4", 8, T + 1, 10, rot=2, colour=WHITE)
    .add("electric_motor", 9, T, 14, colour=DARK)
    .pair("p_tile_1x2", 8, T, 14, colour=WHITE)
    .add("d_rear_wing_8", 6, T + 2, 14, colour=BLUE))


# Bikes and trikes, built the way toy motorbikes are: a frame in one piece
# with the engine, tank, seat and swingarm in it, a fork with the bars on
# top, a wheel at each end and a fairing if it's a sports bike. They're built
# round the middle of the build area in the fine unit.

MID = WIDTH / 2
ZF = 80


def moto(key, name, about, frame, fork, wheel, colour, trim, fairing=False, back_wheel=None):
    k = kart(key, name, about)
    back_wheel = back_wheel or wheel
    r = radius(wheel)
    wide = 80 if frame == "b_frame_trike" else 0
    k.fine(frame, MID - 20 - wide, max(r - 4, 16), ZF, colour=colour)
    k.fine(fork, MID - 40, r - 3.6, ZF)
    k.fine(wheel, MID - fine_size(wheel)[0] / 2, 0, ZF + 10 - r)
    axle = [c for c in PARTS[frame]["connectors"] if c["type"] == "axle"][0]
    back = axle["at"][2]
    rb = radius(back_wheel)
    if wide:
        k.pair_fine(back_wheel, MID - 20 - wide, r - rb, ZF + back - rb)
    else:
        k.fine(back_wheel, MID - fine_size(back_wheel)[0] / 2, r - rb, ZF + back - rb)
    if fairing:
        k.fine("b_moto_fairing", MID - 20, 2 * r + 2, ZF - 30, colour=trim)
    return k


moto("superbike", "Superbike", "A light sports bike with a fairing and a twin. Quick away and quick to flick about, but it can't hold a bend like a kart, and it gets knocked about.",
     "b_frame_sport", "b_moto_fork", "w_moto", RED, WHITE, fairing=True)
moto("dirt_bike", "Dirt Bike", "Knobbly tires and a light little engine. Happy on grass and gravel and nimble in tight turns, but slow on the road.",
     "b_frame_dirt", "b_moto_fork_dirt", "w_moto_trail", YELLOW, BLACK)
moto("chopper", "Chopper", "Long and low with a big engine. It rumbles along at a fair old lick, but it's slow to turn.",
     "b_frame_cruiser", "b_moto_fork", "w_moto", DARK, SILVER)
moto("scooter", "Scooter", "Little wheels and a quiet electric motor. Nippy and quick off the line, but light enough to get bumped right off the road.",
     "b_frame_scooter", "b_moto_fork_scooter", "w_scooter", TEAL, WHITE)
moto("tourer", "Tourer", "A big touring trike with two wheels at the back. Steadier than a bike, and in no hurry to turn.",
     "b_frame_trike", "b_moto_fork", "w_moto", BLUE, SILVER)
moto("trikester", "Trikester", "A trike with a knobbly tire up front, a bike's front end and two wheels at the back. Good on gravel, and a bit of a handful on the road.",
     "b_frame_trike", "b_moto_fork_dirt", "w_moto_trail", ORANGE, BLACK, back_wheel="w_moto")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k in karts:
        k.save()
    print("Wrote %d to %s" % (len(karts), os.path.normpath(OUT)))
