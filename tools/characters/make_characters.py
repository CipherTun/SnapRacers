#!/usr/bin/env python3
"""Makes the driver pieces: one OBJ per piece per colour region in
characters/meshes, data/characters/pieces_made.json listing them, and
data/characters/clipping.json, how much the pieces go into each other in the
rig's poses.

  uv run --with manifold3d --with numpy tools/characters/make_characters.py

Each mesh is in its bone's own space (see figure.py), so the rig puts it on
its bone as it is. Left and right pieces are both made here, never mirrored.
After making them, run the Godot import (tools/run-tests.sh does it first
thing). A mesh that came out empty once stays marked broken in Godot until
its .obj.import file is deleted.
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "parts"))

import figure as F  # noqa: E402
import necks  # noqa: E402
from kit import save_obj, union  # noqa: E402
from manifold3d import CrossSection, JoinType, Manifold  # noqa: E402
from shapes import GAP, SEGMENTS, apply, ball, rbox, soft_slab, tube  # noqa: E402

GAME = F.GAME
MESHES = "characters/meshes"
OUT = os.path.join(GAME, "data", "characters", "pieces_made.json")
CLIPPING = os.path.join(GAME, "data", "characters", "clipping.json")
# The pieces of the bare figure.

def hips():
    """One block, with a groove down the front and under it where the legs
    split, and no seam on the sides."""
    w, d = 0.38, F.TORSO_DEPTH
    block = rbox(-w * 0.5, 0.0, -d * 0.5, w * 0.5, F.HIPS_TOP, d * 0.5, 0.022)
    groove = Manifold.cube([0.006, 0.055, 0.012]).translate([-0.003, -0.01, -d * 0.5 - 0.008])
    under = Manifold.cube([0.006, 0.012, d + 0.02]).translate([-0.003, -0.008, -d * 0.5 - 0.01])
    return block - groove - under


def torso_section():
    """The torso from the front: wider at the bottom, the sides bowing out a
    little, rounded shoulders."""
    bottom, top = F.HIPS_TOP, F.HIPS_TOP + F.TORSO_HEIGHT
    right = []
    steps = 12
    for k in range(steps + 1):
        t = k / steps
        y = bottom + F.TORSO_HEIGHT * t
        right.append((F.half_width(y) + 0.007 * math.sin(math.pi * t), y))
    points = right + [(-x, y) for x, y in reversed(right)]
    section = CrossSection([points])
    # Rounded shoulders, and softer bottom corners.
    shoulders = section.offset(-0.04, JoinType.Round, 2.0, 64).offset(0.04, JoinType.Round, 2.0, 64)
    lower = section.offset(-0.012, JoinType.Round, 2.0, 32).offset(0.012, JoinType.Round, 2.0, 32)
    cut = CrossSection.square([1.0, 1.0]).translate([-0.5, bottom + F.TORSO_HEIGHT * 0.5])
    return (shoulders ^ cut) + (lower - cut)


def torso(grow=0.0):
    """The torso, or with `grow` the space around it pieces are kept out of."""
    section = torso_section()
    if grow > 0.0:
        section = section.offset(grow, JoinType.Round, 2.0, 32)
    body = soft_slab(section, F.TORSO_DEPTH + grow * 2.0, 0.03 + grow)
    top = F.HIPS_TOP + F.TORSO_HEIGHT
    # The round collar the neck sits in, moulded into the top.
    collar = CrossSection([[(0.046, -0.004), (0.068, -0.004), (0.068, 0.006), (0.046, 0.006)]])
    collar = collar.offset(-0.003, JoinType.Round, 2.0, 24).offset(0.003, JoinType.Round, 2.0, 24)
    if grow > 0.0:
        collar = collar.offset(grow, JoinType.Round, 2.0, 24)
    ring = collar.revolve(SEGMENTS * 2).rotate([-90.0, 0.0, 0.0]).translate([0.0, top, 0.0])
    return body + ring


def neck(grow=0.0):
    """A slim post in the collar, which the head sits on."""
    top = F.HIPS_TOP + F.TORSO_HEIGHT
    head_bottom = F.NECK_Y + 0.015
    r = 0.043 + grow
    return Manifold.cylinder(head_bottom - top, r, r, SEGMENTS * 2).rotate([-90.0, 0.0, 0.0]).translate([0.0, top, 0.0])


def head(grow=0.0):
    """The head the game makes (MeshKit.rounded_cylinder, scaled up), in the
    upper body's space, for keeping pieces out of it. It's round, so turning
    doesn't move it."""
    r, h, edge = F.HEAD_RADIUS * F.HEAD_SCALE + grow, F.HEAD_HEIGHT * F.HEAD_SCALE + grow * 2.0, 0.035 * F.HEAD_SCALE + grow
    section = CrossSection([[(-r, -h * 0.5), (r, -h * 0.5), (r, h * 0.5), (-r, h * 0.5)]])
    section = section.offset(-edge, JoinType.Round, 2.0, 32).offset(edge, JoinType.Round, 2.0, 32)
    section = section ^ CrossSection.square([1.0, 1.0]).translate([0.0, -0.5])
    return section.revolve(SEGMENTS * 2).rotate([-90.0, 0.0, 0.0]).translate([0.0, F.HEAD_Y, 0.0])


def stud():
    """The stud on top of the head, in the head's own space before it's
    scaled up."""
    section = CrossSection([[(-0.054, 0.0), (0.054, 0.0), (0.054, 0.04), (-0.054, 0.04)]])
    section = section.offset(-0.008, JoinType.Round, 2.0, 32).offset(0.008, JoinType.Round, 2.0, 32)
    section = section ^ CrossSection.square([1.0, 1.0]).translate([0.0, 0.004])
    return section.revolve(SEGMENTS * 2).rotate([-90.0, 0.0, 0.0]).translate([0.0, F.HEAD_HEIGHT * 0.5 - 0.006, 0.0])


SHOE_LINE = -F.LEG_LENGTH + 0.045
# Where the colour bands of a leg change, as shares of its length from the
# hip, for shorts, socks and boots.
BAND_CUTS = [0.4, 0.55, 0.65]


def leg_standing(side):
    """A leg standing: a block a little narrower at the ankle, with the toe
    turned forward."""
    x = F.LEG_X * F.side_sign(side)
    r = 0.022
    top, bottom = -0.004, -F.LEG_LENGTH
    corners = []
    for y, half in ((top - r, 0.085 - r), (bottom + r, 0.079 - r)):
        for sx in (-1, 1):
            for z in (-0.065 + r, 0.065 - r):
                corners.append(ball((x + sx * half, y, z), r).scale([1, 1, 1]))
    shin = Manifold.batch_hull(corners)
    toe = rbox(x - 0.079, bottom, -0.135, x + 0.079, bottom + 0.062, -0.02, 0.022)
    return shin + toe


def leg_regions(solid):
    """Cuts a standing leg into its colour bands and the foot."""
    foot_zone = Manifold.cube([1.0, SHOE_LINE + 1.0, 2.0]).translate([-0.5, -1.0, -1.0])
    toe_zone = Manifold.cube([1.0, 1.0, 1.0]).translate([-0.5, -F.LEG_LENGTH - 0.5, -1.067])
    foot = solid ^ (foot_zone + toe_zone)
    rest = solid - foot
    cuts = [0.0] + [-F.LEG_LENGTH * c for c in BAND_CUTS] + [SHOE_LINE]
    out = {}
    for k in range(len(cuts) - 1):
        slab = Manifold.cube([1.0, cuts[k] - cuts[k + 1], 2.0]).translate([-0.5, cuts[k + 1], -1.0])
        if k == 0:
            slab = Manifold.cube([1.0, 1.0, 2.0]).translate([-0.5, cuts[1], -1.0])
        out["b%d" % k] = rest ^ slab
    out["foot"] = foot
    return out


def seated_from_standing():
    """Turns a standing leg forward so it sticks straight out, its back on
    the seat."""
    b = F.rot_x(math.pi * 0.5)
    return np.hstack([b, np.array([[0.0], [0.065], [0.0]])])


def leg_keepout():
    """What a seated leg is cut back from: the hips and the bottom of the
    torso, as they are and leant forward astride (in the legs' own astride
    space), so the leg comes out in front of them."""
    hip = rbox(-0.2, -0.02, -F.TORSO_DEPTH * 0.5 - GAP, 0.2, F.HIPS_TOP + 0.002, F.TORSO_DEPTH * 0.5, 0.02)
    body = Manifold.cube([0.5, 0.5, F.TORSO_DEPTH + GAP]).translate([-0.25, F.HIPS_TOP - 0.002, -F.TORSO_DEPTH * 0.5 - GAP])
    straight = hip + body
    lean = F.upper_lean(-math.radians(F.ASTRIDE_LEAN))
    legs = F.legs_astride()
    to_legs = np.hstack([legs[:, :3].T, (-legs[:, :3].T @ legs[:, 3]).reshape(3, 1)])
    astride = apply(hip, to_legs) + apply(body, F.compose(to_legs, lean))
    return straight + astride


def arm(side):
    """One piece from the rounded shoulder down to the fixed bend at the
    elbow and on to the wrist, thicker at the shoulder. Its end has a socket
    the hand's wrist goes into."""
    s = F.side_sign(side)
    elbow = F.elbow(side)
    d = F.forearm_dir(side)
    end = F.wrist(side) - d * 0.013
    shoulder = ball((0.017 * s, -0.004, 0.0), 0.047)
    knee = ball(elbow, 0.042)
    # The forearm goes forward from the elbow before it turns in to the
    # wrist, so it clears the front corner of the torso.
    mid = elbow + (F.wrist(side) - elbow) * 0.6
    mid[0] = elbow[0]
    bend = ball(mid, 0.039)
    cuff = tube(end - d * 0.012, end, 0.037, 0.035)
    solid = Manifold.batch_hull([shoulder, knee]) + Manifold.batch_hull([knee, bend]) + Manifold.batch_hull([bend, cuff])
    socket = tube(end - d * 0.026, end + d * 0.01, 0.0215, 0.0215)
    return solid - socket


def arm_regions(side, solid):
    """Cuts an arm into the shoulder (a short sleeve's length), the upper arm
    and the forearm."""
    elbow = F.elbow(side)
    d = F.forearm_dir(side)
    upper_dir = elbow / np.linalg.norm(elbow)
    n = upper_dir + d
    n /= np.linalg.norm(n)
    fore = solid.trim_by_plane(list(n), float(n.dot(elbow)))
    upper = solid - fore
    shoulder = upper.trim_by_plane([0.0, 1.0, 0.0], -0.055)
    return {"shoulder": shoulder, "upper": upper - shoulder, "fore": fore}


def hand(side):
    """A fat C shaped hand around its grip, the hole along z and the gap away
    from the wrist (+y), with the wrist that plugs into the arm."""
    outer, inner, half = 0.042, 0.02, 0.0215
    section = CrossSection([[(inner, -half), (outer, -half), (outer, half), (inner, half)]])
    section = section.offset(-0.007, JoinType.Round, 2.0, 32).offset(0.007, JoinType.Round, 2.0, 32)
    ring = section.revolve(SEGMENTS * 2, 280.0).rotate([0.0, 0.0, -50.0])
    stub = tube((0.0, 0.034, 0.0), (0.0, F.HAND_SIZE + 0.03, 0.0), 0.019, 0.019)
    return ring + stub


# Making them.

def rel(path):
    return "res://%s/%s" % (MESHES, path)


def save_regions(name, regions, made):
    """Saves each region of a piece and returns their paths by region."""
    out = {}
    for region, solid in regions.items():
        if solid.is_empty() or solid.volume() < 1e-9:
            continue
        file = "%s_%s.obj" % (name, region)
        made[0] += save_obj(solid, (0.0, 0.0, 0.0), os.path.join(GAME, MESHES, file), 35.0)
        out[region] = rel(file)
    return out


def box_of(solids):
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for s in solids:
        b = s.bounding_box()
        lo = np.minimum(lo, b[:3])
        hi = np.maximum(hi, b[3:])
    return [round(float(v), 4) for v in list(lo) + list(hi)]


def make():
    made = [0]
    pieces = {}
    solids = {}

    def piece(name, bone, regions, **extra):
        entry = {"bone": bone, "offset": [0.0, 0.0, 0.0], "regions": save_regions(name, regions, made), "box": box_of(regions.values())}
        entry.update(extra)
        pieces[name] = entry
        solids[name] = union(list(regions.values()))
        print("made", name)

    piece("hips", "legs", {"main": hips()})
    keepout = leg_keepout()
    seat = seated_from_standing()
    for side, name in ((0, "leg_l"), (1, "leg_r")):
        standing = leg_regions(leg_standing(side))
        seated = {k: apply(v, seat) - keepout for k, v in standing.items()}
        entry_seated = save_regions(name + "_seated", seated, made)
        piece(name, "legs", standing, seated={"regions": entry_seated, "box": box_of(seated.values())})
        solids[name + "_seated"] = union(list(seated.values()))
    piece("torso", "upper", {"main": torso()})
    piece("neck", "upper", {"skin": neck()})
    piece("stud", "head", {"skin": stud()})
    for side, suffix in ((0, "l"), (1, "r")):
        piece("arm_" + suffix, "arm_" + suffix, arm_regions(side, arm(side)))
        piece("hand_" + suffix, "hand_" + suffix, {"main": hand(side)})

    # What's worn, by slot and style. Each is cut back from the figure's
    # pieces on its bone, a hairline off them.
    styles = {"neck": {}}
    style_solids = {}
    upper_keepout = torso(GAP) + neck(GAP) + head(GAP)
    for style, make_style in necks.STYLES.items():
        regions = {k: v - upper_keepout for k, v in make_style().items()}
        entry = {"bone": "upper", "regions": save_regions("neck_" + style, regions, made), "box": box_of(regions.values())}
        if style in necks.METAL:
            entry["metallic"] = necks.METAL[style]
        styles["neck"][style] = entry
        style_solids["neck " + style] = union(list(regions.values()))
        print("made neck", style)

    data = {
        "_comment": "Made by tools/characters/make_characters.py, so change the pieces there. Meshes are in their bone's own space, in metres. 'figure' is the bare figure; 'styles' are the remodelled styles by slot and style. A style's regions are coloured: main in its own colour (shiny metal if it has 'metallic'), dark and light a shade of it, the rest from 'colours' as colour and metallic.",
        "colours": necks.COLOURS,
        "figure": pieces,
        "styles": styles,
    }
    with open(OUT, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")
    print("%d pieces, %d triangles in all" % (len(pieces), made[0]))
    clipping(solids, style_solids)


# Clipping.

# Rests the rig puts the hands in, as targets in the rig's space (see
# CharacterRig.rest_hands()).
STANDING_REST = [tuple(F.STANDING_REST[0]), tuple(F.STANDING_REST[1])]
SEATED_REST = [tuple(F.SEATED_REST[0]), tuple(F.SEATED_REST[1])]
# More than this many cubic centimetres into each other counts as clipping.
LIMIT_CM3 = 0.05


def posed(solids, seated, astride=False, swings=None, along=(0.0, 0.0, -1.0)):
    """The pieces placed for a pose, in the rig's space."""
    lean = F.upper_lean(-math.radians(F.ASTRIDE_LEAN) if astride else 0.0)
    out = {"hips": solids["hips"], "torso": apply(solids["torso"], lean), "neck": apply(solids["neck"], lean)}
    legs = F.legs_astride() if astride else np.hstack([np.eye(3), np.zeros((3, 1))])
    for name in ("leg_l", "leg_r"):
        out[name] = apply(solids[name + ("_seated" if seated else "")], legs)
    for side, suffix in ((0, "l"), (1, "r")):
        angle, spread = swings[side]
        arm_m, hand_m = F.arm_pose(side, angle, spread, along)
        out["arm_" + suffix] = apply(solids["arm_" + suffix], F.compose(lean, arm_m))
        out["hand_" + suffix] = apply(solids["hand_" + suffix], F.compose(lean, hand_m))
    return out


PAIRS = [
    ("hips", "leg_l"), ("hips", "leg_r"), ("leg_l", "leg_r"), ("torso", "leg_l"), ("torso", "leg_r"),
    ("torso", "arm_l"), ("torso", "arm_r"), ("hips", "arm_l"), ("hips", "arm_r"),
    ("torso", "hand_l"), ("torso", "hand_r"), ("hips", "hand_l"), ("hips", "hand_r"),
    ("leg_l", "hand_l"), ("leg_r", "hand_r"), ("leg_l", "arm_l"), ("leg_r", "arm_r"),
    ("arm_l", "hand_l"), ("arm_r", "hand_r"), ("torso", "neck"),
]


# What each worn style is checked against: the pieces on its own bone, which
# don't move against it, and the ones that swing past it.
STYLE_STILL = {"neck": ["torso", "neck", "head"]}
STYLE_MOVING = {"neck": ["arm_l", "arm_r", "hand_l", "hand_r"]}


def clipping(solids, style_solids):
    poses = []

    def rest(targets, astride=False):
        return [F.swing_to(side, targets[side], astride) for side in (0, 1)]

    poses.append(("standing, hands resting", False, False, rest(STANDING_REST), (0.0, 0.0, -1.0)))
    for sway in (-0.06, 0.06):
        swings = [(a + sway * (1 if side == 0 else -1), s) for side, (a, s) in enumerate(rest(STANDING_REST))]
        poses.append(("standing, arms swaying %+.2f" % sway, False, False, swings, (0.0, 0.0, -1.0)))
    poses.append(("seated, hands resting", True, False, rest(SEATED_REST), (0.0, 0.0, -1.0)))
    # Holding a wheel or bars anywhere from just over the lap to up high.
    for degrees in range(45, 121, 15):
        a = math.radians(degrees)
        poses.append(("seated, arms swung %d degrees" % degrees, True, False, [(a, 0.0), (a, 0.0)], (0.0, 0.0, 1.0)))
    for degrees in (55, 75, 100):
        a = math.radians(degrees)
        poses.append(("astride, arms swung %d degrees" % degrees, True, True, [(a, 0.3), (a, 0.3)], (0.0, 0.0, 1.0)))
    poses.append(("cheering", True, False, [(math.pi * 0.6, 0.0), (math.pi * 0.6, 0.0)], (0.0, 1.0, 0.0)))

    report = []
    worst = 0.0
    still = dict(solids)
    still["head"] = head()
    for style, solid in style_solids.items():
        for b in STYLE_STILL[style.split(" ")[0]]:
            volume = (solid ^ still[b]).volume() * 1e6
            worst = max(worst, volume)
            if volume > 0.001:
                report.append({"pose": "any pose", "a": style, "b": b, "cm3": round(volume, 4)})
    for name, seated, astride, swings, along in poses:
        placed = posed(solids, seated, astride, swings, along)
        pairs = list(PAIRS)
        lean = F.upper_lean(-math.radians(F.ASTRIDE_LEAN) if astride else 0.0)
        for style, solid in style_solids.items():
            placed[style] = apply(solid, lean)
            pairs += [(style, b) for b in STYLE_MOVING[style.split(" ")[0]]]
        for a, b in pairs:
            volume = (placed[a] ^ placed[b]).volume() * 1e6
            worst = max(worst, volume)
            if volume > 0.001:
                report.append({"pose": name, "a": a, "b": b, "cm3": round(volume, 4)})
    data = {
        "_comment": "Made by tools/characters/make_characters.py: how far the figure's pieces and the styles made there go into each other, in cubic centimetres, in the rig's poses. Only overlaps over 0.001 are listed.",
        "figure": json.load(open(F.OUT)),
        "limit_cm3": LIMIT_CM3,
        "poses": [p[0] for p in poses],
        "styles": sorted(style_solids),
        "worst_cm3": round(worst, 4),
        "overlaps": report,
    }
    data["figure"].pop("_comment", None)
    with open(CLIPPING, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")
    print("clipping: worst %.4f cm3 over %d poses" % (worst, len(poses)))
    for r in report:
        flag = "CLIPS" if r["cm3"] > LIMIT_CM3 else "touch"
        print("  %s %-34s %s / %s %.4f cm3" % (flag, r["pose"], r["a"], r["b"], r["cm3"]))


if __name__ == "__main__":
    F.write()
    make()
