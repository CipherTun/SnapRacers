"""The driver's rig: where the joints are and how the arms swing, the same
numbers as scripts/character/character_rig.gd. Running it writes them to
data/characters/figure.json, and the rig checks it matches.

  uv run --with numpy tools/characters/figure.py

Everything is in metres in the rig's own space: the origin is where the
driver sits, in the middle of the bottom of the hips, y is up and they face
-z. Arms are side 0 (left, -x) and side 1 (right, +x).
"""

import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(GAME, "data", "characters", "figure.json")

HIPS_TOP = 0.08
TORSO_HEIGHT = 0.34
TORSO_BOTTOM_WIDTH = 0.4
TORSO_TAPER = 0.78
TORSO_DEPTH = 0.2
NECK_Y = HIPS_TOP + TORSO_HEIGHT + 0.015
HEAD_RADIUS = 0.12
HEAD_HEIGHT = 0.2
HEAD_SCALE = 1.2
LEG_X = 0.095
LEG_LENGTH = 0.3
SHOULDER_Y = HIPS_TOP + TORSO_HEIGHT - 0.045
# How far the shoulder pivot is out from the side of the torso.
SHOULDER_OUT = 0.038
UPPER_ARM = 0.14
FOREARM = 0.12
ELBOW_BEND = 35.0  # degrees
FOREARM_IN = 0.25
# The elbow sits this far out from under the shoulder, so the upper arm
# follows the torso's side down.
ELBOW_OUT = 0.03
HAND_SIZE = 0.045
ASTRIDE_LEGS = 25.0  # degrees
ASTRIDE_LEAN = 30.0  # degrees
MOST_SPREAD = 60.0  # degrees
# Where the hands rest, standing and seated, left then right.
STANDING_REST = [[-0.2, 0.2, -0.3], [0.2, 0.2, -0.3]]
SEATED_REST = [[-0.15, 0.19, -0.2], [0.15, 0.19, -0.2]]

NAMES = [
    "HIPS_TOP", "TORSO_HEIGHT", "TORSO_BOTTOM_WIDTH", "TORSO_TAPER", "TORSO_DEPTH", "NECK_Y",
    "HEAD_RADIUS", "HEAD_HEIGHT", "HEAD_SCALE", "LEG_X", "LEG_LENGTH", "SHOULDER_Y", "SHOULDER_OUT",
    "UPPER_ARM", "FOREARM", "ELBOW_BEND", "FOREARM_IN", "ELBOW_OUT", "HAND_SIZE",
    "ASTRIDE_LEGS", "ASTRIDE_LEAN", "MOST_SPREAD", "STANDING_REST", "SEATED_REST",
]

# Where the head's middle is, which grows up from where it sits on the neck.
HEAD_Y = NECK_Y + 0.015 + HEAD_HEIGHT * 0.5 * HEAD_SCALE
FEET_BELOW = LEG_LENGTH


def half_width(y):
    """Half the torso's width at a height, without its bowed sides."""
    t = (y - HIPS_TOP) / TORSO_HEIGHT
    return TORSO_BOTTOM_WIDTH * 0.5 * (1.0 + (TORSO_TAPER - 1.0) * t)


def side_sign(side):
    return -1.0 if side == 0 else 1.0


def shoulder(side):
    return np.array([(half_width(SHOULDER_Y) + SHOULDER_OUT) * side_sign(side), SHOULDER_Y, 0.0])


def elbow(side):
    """The elbow in the arm's own space, whose origin is the shoulder."""
    return np.array([ELBOW_OUT * side_sign(side), -UPPER_ARM, 0.0])


def wrist(side):
    """The wrist in the arm's own space. It's where a straight upper arm with
    the forearm bent forward and in by ELBOW_BEND and FOREARM_IN puts it."""
    s = side_sign(side)
    bent = np.array([-s * FOREARM_IN, -math.cos(math.radians(ELBOW_BEND)), -math.sin(math.radians(ELBOW_BEND))])
    return np.array([0.0, -UPPER_ARM, 0.0]) + bent / np.linalg.norm(bent) * FOREARM


def forearm_dir(side):
    d = wrist(side) - elbow(side)
    return d / np.linalg.norm(d)


def grip_local(side):
    """Where the hand holds, in the arm's own space."""
    return wrist(side) + forearm_dir(side) * HAND_SIZE


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def spread_basis(side, spread):
    return rot_z(spread * (1.0 if side == 1 else -1.0))


def swing_to(side, target, astride=False):
    """The swing (and spread, astride) that brings the hand closest to a
    target in the upper body's space, the way the rig does it."""
    pivot = shoulder(side)
    reach = grip_local(side)
    want = np.asarray(target, dtype=float) - pivot
    spread = 0.0
    if astride:
        out = (abs(target[0]) - abs(pivot[0])) / np.linalg.norm(reach)
        spread = min(math.asin(min(max(out, 0.0), 1.0)), math.radians(MOST_SPREAD))
        want = spread_basis(side, spread).T @ want
    angle = math.atan2(want[2], want[1]) - math.atan2(reach[2], reach[1])
    return angle, spread


def arm_pose(side, angle, spread=0.0, along=(0.0, 0.0, 1.0)):
    """The arm's and the hand's transforms (3x4, in the upper body's space)
    for a swing, with the hand holding along `along`."""
    pivot = shoulder(side)
    swing = spread_basis(side, spread) @ rot_x(angle)
    arm = np.hstack([swing, pivot.reshape(3, 1)])
    y = -(swing @ forearm_dir(side))
    along = np.asarray(along, dtype=float)
    z = along - y * along.dot(y)
    if np.linalg.norm(z) < 0.01:
        f = np.array([0.0, 0.0, -1.0])
        z = f - y * f.dot(y)
    z = z / np.linalg.norm(z)
    x = np.cross(y, z)
    x = x / np.linalg.norm(x)
    at = pivot + swing @ grip_local(side)
    hand = np.hstack([np.column_stack([x, y, z]), at.reshape(3, 1)])
    return arm, hand


def upper_lean(angle):
    """The upper body's transform for leaning back by `angle` (forward when
    negative), about the top of the hips."""
    b = rot_x(angle)
    pivot = np.array([0.0, HIPS_TOP, 0.0])
    return np.hstack([b, (pivot - b @ pivot).reshape(3, 1)])


def legs_astride():
    """The astride legs' transform, swung down about the hip."""
    b = rot_x(-math.radians(ASTRIDE_LEGS))
    hip = np.array([0.0, HIPS_TOP * 0.5, 0.0])
    return np.hstack([b, (hip - b @ hip).reshape(3, 1)])


# How the legs ride, on top of the astride legs bone: each thigh swings down
# a little more and out to the side, and the shin bends down at the knee.
# "astride" has the knees down by the tank and the feet under the rider,
# "forward" the feet out in front on a chopper's pegs. Degrees.
RIDES = {
    "astride": {"down": 10.0, "splay": 40.0, "bend": 85.0},
    "forward": {"down": -5.0, "splay": 12.0, "bend": 15.0},
}
# Where the knee is along a seated leg, from the hip.
KNEE_Z = -0.17
# How far out from the leg's middle its outside is, which it swings out about.
LEG_OUT = 0.085


def _about(b, pivot):
    pivot = np.asarray(pivot, dtype=float)
    return np.hstack([b, (pivot - b @ pivot).reshape(3, 1)])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def ride_leg(side, ride, top):
    """The thigh's and the shin's transforms (3x4) for a seated leg riding,
    in the legs bone's space. `top` is how high the seated leg's top (its
    front standing) is, where the knee bends about."""
    r = RIDES[ride]
    s = side_sign(side)
    down = _about(rot_x(-math.radians(r["down"])), [0.0, HIPS_TOP * 0.5, 0.0])
    splay = _about(rot_y(-s * math.radians(r["splay"])), [s * (LEG_X + LEG_OUT), 0.0, 0.0])
    thigh = compose(splay, down)
    bend = _about(rot_x(-math.radians(r["bend"])), [0.0, top, KNEE_Z])
    # The shin a hair narrower, so where it tucks into the thigh behind the
    # knee their sides don't fight.
    narrow = _about(np.diag([0.985, 1.0, 1.0]), [s * LEG_X, 0.0, 0.0])
    return thigh, compose(thigh, compose(bend, narrow))


def compose(a, b):
    """a then b, as 3x4 transforms: a * b."""
    return np.hstack([a[:, :3] @ b[:, :3], (a[:, :3] @ b[:, 3] + a[:, 3]).reshape(3, 1)])


def write():
    data = {"_comment": "Made by tools/characters/figure.py. The rig's numbers, which scripts/character/character_rig.gd checks it matches. Metres, angles in degrees."}
    for name in NAMES:
        value = globals()[name]
        data[name] = value if isinstance(value, list) else round(value, 6)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent="\t")
        f.write("\n")


if __name__ == "__main__":
    write()
    print("wrote", OUT)
