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

import beards  # noqa: E402
import figure as F  # noqa: E402
import hair  # noqa: E402
import headgear  # noqa: E402
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


def head_local_placed(turn=0.0, lean=None):
    """The head bone's transform in the upper body's space, turned by `turn`
    radians, then leant with the upper body if given."""
    c, s_ = math.cos(turn), math.sin(turn)
    b = np.array([[c, 0.0, s_], [0.0, 1.0, 0.0], [-s_, 0.0, c]]) * F.HEAD_SCALE
    m = np.hstack([b, np.array([[0.0], [F.HEAD_Y], [0.0]])])
    return F.compose(lean, m) if lean is not None else m


def face_zone():
    """In the head's own space, the front of the face hair keeps out of."""
    a = math.radians(hair.FACE_ANGLE)
    pts = [(0.0, 0.0), (0.4 * math.sin(-a), -0.4 * math.cos(a)), (0.0, -0.4), (0.4 * math.sin(a), -0.4 * math.cos(a))]
    wedge = CrossSection([pts])
    if wedge.area() <= 0.0:
        wedge = CrossSection([list(reversed(pts))])
    # The section is x across and z along; extrude goes up its third axis.
    solid = wedge.extrude(hair.FACE_TOP + 0.2).rotate([90.0, 0.0, 0.0])
    return solid.translate([0.0, hair.FACE_TOP, 0.0]) - head_local(0.0, 40)


def features():
    """In the head's own space, where the eyes, brows and mouth are printed
    in every mood, which beards keep clear of."""
    eyes = Manifold.cube([0.15, 0.08, 0.2]).translate([-0.075, -0.012, -0.3])
    mouth = Manifold.cylinder(0.2, 1.0, 1.0, 32).scale([0.04, 0.028, 1.0]).translate([0.0, -0.038, -0.3])
    return (eyes + mouth) - head_local(0.0, 40)


def head(grow=0.0):
    """The head the game makes (MeshKit.rounded_cylinder, scaled up), in the
    upper body's space, for keeping pieces out of it. It's round, so turning
    doesn't move it."""
    r, h, edge = F.HEAD_RADIUS * F.HEAD_SCALE + grow, F.HEAD_HEIGHT * F.HEAD_SCALE + grow * 2.0, 0.035 * F.HEAD_SCALE + grow
    section = CrossSection([[(-r, -h * 0.5), (r, -h * 0.5), (r, h * 0.5), (-r, h * 0.5)]])
    section = section.offset(-edge, JoinType.Round, 2.0, 32).offset(edge, JoinType.Round, 2.0, 32)
    section = section ^ CrossSection.square([1.0, 1.0]).translate([0.0, -0.5])
    return section.revolve(SEGMENTS * 2).rotate([-90.0, 0.0, 0.0]).translate([0.0, F.HEAD_Y, 0.0])


def head_local(grow=0.0, segments=SEGMENTS * 2):
    """The head in its own space, before it's scaled up, grown by `grow`."""
    r, h, edge = F.HEAD_RADIUS + grow, F.HEAD_HEIGHT + grow * 2.0, 0.035 + grow
    section = CrossSection([[(-r, -h * 0.5), (r, -h * 0.5), (r, h * 0.5), (-r, h * 0.5)]])
    section = section.offset(-edge, JoinType.Round, 2.0, 32).offset(edge, JoinType.Round, 2.0, 32)
    section = section ^ CrossSection.square([1.0, 1.0]).translate([0.0, -0.5])
    return section.revolve(segments).rotate([-90.0, 0.0, 0.0])


def stud(grow=0.0, segments=SEGMENTS * 2):
    """The stud on top of the head, in the head's own space before it's
    scaled up, or grown by `grow`."""
    w, h = 0.054 + grow, 0.04 + grow
    section = CrossSection([[(-w, 0.0), (w, 0.0), (w, h), (-w, h)]])
    section = section.offset(-0.008, JoinType.Round, 2.0, 32).offset(0.008, JoinType.Round, 2.0, 32)
    section = section ^ CrossSection.square([1.0, 1.0]).translate([0.0, 0.004])
    return section.revolve(segments).rotate([-90.0, 0.0, 0.0]).translate([0.0, F.HEAD_HEIGHT * 0.5 - 0.006, 0.0])


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

    # Hair and raised facial hair, on the head, cut back from it and its
    # stud. Hair has a cut version for under a hat.
    styles["hair"] = {}
    styles["facial_hair"] = {}
    # Kept a little coarse, so the lobes cut back from it stay light.
    head_keepout = head_local(GAP + 0.001, 24) + stud(GAP + 0.001, 24)
    sizes = {}
    for style, make_style in hair.STYLES.items():
        regions = {k: (v - head_keepout).simplify(0.0018) for k, v in make_style().items()}
        whole = union(list(regions.values()))
        cut = hair.cut(regions)
        cut_whole = union(list(cut.values()))
        reach = hair.radius_profile(cut_whole, 0.004)[0]
        profile, top = hair.radius_profile(whole)
        entry = {"bone": "head", "regions": save_regions("hair_" + style, regions, made), "box": box_of(regions.values()), "top": top, "radius_at": profile}
        entry["cut"] = {
            "regions": save_regions("hair_%s_cut" % style, cut, made), "box": box_of(cut.values()),
            "top": hair.CUT_Y, "radius": round(max([r for y, r in reach if y >= hair.CUT_Y - hair.CUT_BAND - 0.001] or [0.0]), 4),
        }
        styles["hair"][style] = entry
        style_solids["hair " + style] = whole
        style_solids["hair %s cut" % style] = cut_whole
        sizes["hair " + style] = (whole.num_tri(), cut_whole.num_tri())
        print("made hair", style, whole.num_tri(), "triangles,", cut_whole.num_tri(), "cut")
    for style, make_style in beards.STYLES.items():
        regions = {k: (v - head_keepout).simplify(0.0008) for k, v in make_style().items()}
        whole = union(list(regions.values()))
        entry = {"bone": "head", "regions": save_regions("facial_hair_" + style, regions, made), "box": box_of(regions.values())}
        styles["facial_hair"][style] = entry
        style_solids["facial_hair " + style] = whole
        sizes["facial_hair " + style] = (whole.num_tri(), 0)
        print("made facial hair", style, whole.num_tri(), "triangles")
    total = sum(a + b for a, b in sizes.values())
    biggest = max(sizes, key=lambda k: sizes[k][0])
    print("hair and facial hair: %d triangles in all, the biggest %s at %d" % (total, biggest, sizes[biggest][0]))

    # Headgear, on the head. Hats over cut hair are also kept out of the band
    # the cut hair fills; what's worn on the hair is fitted to each hairdo.
    styles["headgear"] = {}
    gear = {}
    hat_keepout = head_keepout + Manifold.cylinder(0.3, headgear.INNER - 0.0005, headgear.INNER - 0.0005, 64).rotate([-90.0, 0.0, 0.0]).translate([0.0, headgear.BAND_TOP - 0.3, 0.0])
    bare = head_local(0.0, 40) + stud()
    gear_sizes = {}
    for style, make_style in headgear.STYLES.items():
        mode = headgear.HAIR[style]
        keep = hat_keepout if mode == "cut" else head_keepout
        fits = {}
        if style in headgear.BANDS:
            # One for each hairdo, kept off it, saved as variants "on_<hair>"
            # with the bare head's as the piece itself.
            made_on = {}
            for h in ["none"] + list(hair.STYLES):
                hair_solid = None if h == "none" else style_solids["hair " + h]
                on = headgear.Surface(bare if hair_solid is None else bare + hair_solid)
                cut_from = keep if hair_solid is None else keep + hair_solid
                made_on[h] = {k: v.simplify(0.0016) - cut_from for k, v in make_style(on).items()}
            regions = made_on["none"]
            entry = {"bone": "head", "hair": mode, "regions": save_regions("headgear_" + style, regions, made), "box": box_of(regions.values())}
            for h in hair.STYLES:
                entry["on_" + h] = {"regions": save_regions("headgear_%s_on_%s" % (style, h), made_on[h], made), "box": box_of(made_on[h].values())}
            fits = {h: union(list(r.values())) for h, r in made_on.items()}
            whole = fits["none"]
            gear_sizes[style] = max(sum(v.num_tri() for v in r.values()) for r in made_on.values())
        else:
            regions = {k: (v - keep).simplify(0.0016) for k, v in make_style().items()}
            whole = union(list(regions.values()))
            entry = {"bone": "head", "hair": mode, "regions": save_regions("headgear_" + style, regions, made), "box": box_of(regions.values())}
            gear_sizes[style] = sum(v.num_tri() for v in regions.values())
        if style in headgear.FIT:
            kind = headgear.FIT[style]
            fits["none"] = headgear.fit_to(whole, bare, kind)
            for h in hair.STYLES:
                fits[h] = headgear.fit_to(whole, bare + style_solids["hair " + h], kind)
            missing = [k for k, v in fits.items() if v is None]
            if missing:
                raise SystemExit("headgear %s doesn't fit on %s" % (style, missing))
            entry["fit"] = {k: [round(float(x), 4) for x in v] for k, v in fits.items()}
        styles["headgear"][style] = entry
        gear[style] = (whole, fits)
        print("made headgear", style, mode, gear_sizes[style], "triangles")
    biggest = max(gear_sizes, key=gear_sizes.get)
    print("headgear: %d triangles in all, the biggest %s at %d" % (sum(gear_sizes.values()), biggest, gear_sizes[biggest]))

    clipping(solids, style_solids, gear)

    data = {
        "_comment": "Made by tools/characters/make_characters.py, so change the pieces there. Meshes are in their bone's own space, in metres. 'figure' is the bare figure; 'styles' are the remodelled styles by slot and style. A style's regions are coloured: main in its own colour (shiny metal if it has 'metallic'), dark and light a shade of it, the rest from 'colours' as colour and metallic. Hair has 'top', how high it reaches, and 'radius_at', how far out it reaches at heights up the head, in the head's own space before it's scaled up, for fitting what sits on it, and 'cut', the version under a hat: cut flat at 'top' and kept within 'radius' of the middle for the band under that. Headgear has 'hair', what's shown under it: the cut hair, the full hair or none ('hidden'). Bands worn on the hair have a variant 'on_<hair>' made for each hairdo, their own regions for none; the rest worn on the hair have 'fit', by hairdo ('none' for none), how it's placed to sit on it: [scale across, scale up, lift, move back], scaled from the middle of the head.",
        "colours": dict(necks.COLOURS, **headgear.COLOURS),
        "figure": pieces,
        "styles": styles,
    }
    with open(OUT, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")
    print("%d pieces, %d triangles in all" % (len(pieces), made[0]))


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


HEAD_SLOTS = ("hair", "facial_hair")
# How far the head turns: glancing at a kart alongside, looking about
# standing and looking into a turn.
HEAD_TURNS = [0.0, 0.15, 0.3, 0.35, 0.5, 0.8, 1.05, 1.3]


def _boxes_meet(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    return all(ba[i] <= bb[i + 3] and bb[i] <= ba[i + 3] for i in range(3))


def head_clipping(head_styles, solids, neck_styles, poses, report, still_checks=True):
    """Hair and facial hair against the head, the stud, the face and each
    other on the head, and against the neck, the torso, every neck piece and
    the arms and hands as the head turns in every pose."""
    worst = 0.0

    def note(pose, a, b, volume):
        nonlocal worst
        worst = max(worst, volume)
        if volume > 0.001:
            report.append({"pose": pose, "a": a, "b": b, "cm3": round(volume, 4)})

    still = {"head": head_local(0.0, 40), "stud": stud(), "face": face_zone(), "features": features()}
    for style, solid in (head_styles.items() if still_checks else ()):
        slot = style.split(" ")[0]
        for b in ("head", "stud", "face" if slot == "hair" else "features"):
            note("any pose", style, b, (solid ^ still[b]).volume() * 1e6)
    hairs = [k for k in head_styles if k.startswith("hair ")]
    for beard in [k for k in head_styles if k.startswith("facial_hair ") and still_checks]:
        for h in hairs:
            if _boxes_meet(head_styles[beard], head_styles[h]):
                note("any pose", beard, h, (head_styles[beard] ^ head_styles[h]).volume() * 1e6)
    # Against what's on the upper body and the arms and hands in every pose,
    # as the head turns all the way either side.
    upper = {"torso": solids["torso"], "neck": solids["neck"]}
    upper.update(neck_styles)
    arms = []
    for name, seated, astride, swings, along in poses:
        lean = F.upper_lean(-math.radians(F.ASTRIDE_LEAN) if astride else 0.0)
        placed = posed(solids, seated, astride, swings, along)
        arms.append((name, lean, {b: placed[b] for b in ("arm_l", "arm_r", "hand_l", "hand_r")}))

    def at_turn(solid, turn):
        found = []
        placed = apply(solid, head_local_placed(turn))
        for b, other in upper.items():
            if _boxes_meet(placed, other):
                found.append(("head turned %+.2f" % turn, b, (placed ^ other).volume() * 1e6))
        for name, lean, swung in arms:
            placed = apply(solid, head_local_placed(turn, lean))
            for b, other in swung.items():
                if _boxes_meet(placed, other):
                    found.append(("%s, head turned %+.2f" % (name, turn), b, (placed ^ other).volume() * 1e6))
        return found

    for style, solid in head_styles.items():
        for turn in HEAD_TURNS:
            for pose, b, v in at_turn(solid, turn) + (at_turn(solid, -turn) if turn else []):
                note(pose, style, b, v)
    return worst


def headgear_clipping(gear, head_styles, solids, neck_styles, poses, report):
    """Headgear against the head, the stud and the face, the hair shown under
    it (each hairdo's cut version under a hat, each full hairdo under what's
    fitted to it), the raised facial hair, and as the head turns, against
    the torso, the neck pieces and the arms and hands in every pose. Also
    where a hat leaves the cut hair's top edge showing."""
    worst = 0.0

    def note(pose, a, b, volume):
        nonlocal worst
        worst = max(worst, volume)
        if volume > 0.001:
            report.append({"pose": pose, "a": a, "b": b, "cm3": round(volume, 4)})

    still = {"head": head_local(0.0, 40), "stud": stud(), "face": face_zone()}
    hairs = [k[5:] for k in head_styles if k.startswith("hair ") and not k.endswith(" cut")]
    beards_made = [k for k in head_styles if k.startswith("facial_hair ")]
    checked = {}
    bare_spots = []
    tops = {}
    moving = {}
    for style, (whole, fits) in gear.items():
        name = "headgear " + style
        mode = headgear.HAIR[style]
        if mode == "full":
            if style in headgear.BANDS:
                worn = {h: fits[h] for h in ["none"] + hairs}
            else:
                worn = {h: headgear.placed(whole, fits[h]) for h in ["none"] + hairs}
        else:
            worn = {"": whole}
        for key, solid in worn.items():
            label = name if key == "" else "%s on %s" % (name, key)
            for b in ("head", "stud", "face"):
                note("any pose", label, b, (solid ^ still[b]).volume() * 1e6)
            for beard in beards_made:
                if _boxes_meet(solid, head_styles[beard]):
                    note("any pose", label, beard, (solid ^ head_styles[beard]).volume() * 1e6)
        if mode == "cut":
            reach = headgear.hat_reach(whole)
            checked[style] = []
            for h in hairs:
                cut = head_styles["hair %s cut" % h]
                checked[style].append("hair %s cut" % h)
                if _boxes_meet(whole, cut):
                    note("any pose", name, "hair %s cut" % h, (whole ^ cut).volume() * 1e6)
                if h not in tops:
                    tops[h] = headgear.hair_tops(cut)
                missed = headgear.uncovered(reach, tops[h])
                if missed:
                    bare_spots.append({"headgear": style, "hair": h, "degrees": missed})
        elif mode == "full":
            checked[style] = []
            for h in hairs:
                checked[style].append("hair " + h)
                note("any pose", "%s on %s" % (name, h), "hair " + h, (worn[h] ^ head_styles["hair " + h]).volume() * 1e6)
        else:
            checked[style] = []
        moving[name] = union(list(worn.values()))
    # As the head turns, every way it's worn at once.
    worst = max(worst, head_clipping(moving, solids, neck_styles, poses, report, still_checks=False))
    return worst, checked, bare_spots


def clipping(solids, style_solids, gear):
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
    head_styles = {k: v for k, v in style_solids.items() if k.split(" ")[0] in HEAD_SLOTS}
    style_solids = {k: v for k, v in style_solids.items() if k not in head_styles}
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
    worst = max(worst, head_clipping(head_styles, solids, style_solids, poses, report))
    gear_worst, checked, bare_spots = headgear_clipping(gear, head_styles, solids, style_solids, poses, report)
    worst = max(worst, gear_worst)
    data = {
        "_comment": "Made by tools/characters/make_characters.py: how far the figure's pieces and the styles made there go into each other, in cubic centimetres, in the rig's poses. Only overlaps over 0.001 are listed. 'headgear_hair' lists the hair each headgear was checked against, and 'uncovered' where a hat leaves the top edge of the cut hair under it showing, in degrees round the head.",
        "figure": json.load(open(F.OUT)),
        "limit_cm3": LIMIT_CM3,
        "poses": [p[0] for p in poses],
        "styles": sorted(list(style_solids) + list(head_styles) + ["headgear " + k for k in gear]),
        "headgear_hair": checked,
        "uncovered": bare_spots,
        "worst_cm3": round(worst, 4),
        "overlaps": report,
    }
    data["figure"].pop("_comment", None)
    with open(CLIPPING, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")
    print("clipping: worst %.4f cm3 over %d poses" % (worst, len(poses)))
    for u in bare_spots:
        print("  UNCOVERED %s over hair %s at %s" % (u["headgear"], u["hair"], u["degrees"]))
    for r in report:
        flag = "CLIPS" if r["cm3"] > LIMIT_CM3 else "touch"
        print("  %s %-34s %s / %s %.4f cm3" % (flag, r["pose"], r["a"], r["b"], r["cm3"]))



if __name__ == "__main__":
    F.write()
    make()
