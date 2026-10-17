class_name ArmLooks
extends RefCounted

## An arm, one piece from the rounded shoulder down to the fixed bend at the
## elbow and on to the wrist, then the C shaped hand, both made in
## tools/characters. Sleeves and the like are
## printed on it in their own colours, the way a toy figure's are. How long
## the sleeves are, what's on the hands and extras like cuffs, bracers, pads or
## a watch come from the arms piece's settings in pieces.json.

const WHITE := Color("#f2f2f2")
const DARK := Color("#3c3f44")


static func build(rig: CharacterRig, arm: Node3D, hand: Node3D, side: int) -> void:
	var d := rig.design
	var c := d.color_of("arms")
	var skin := d.skin()
	var metal := d.has("arms", "metal")
	var shine := 0.5 if metal else 0.0
	var sleeve: String = d.setting("arms", "sleeve", "long")
	var outward := -1.0 if side == 0 else 1.0

	var upper := c
	var fore := c
	match sleeve:
		"short", "none":
			upper = skin
			fore = skin
		"rolled":
			fore = skin
	if d.has("arms", "two_tone"):
		fore = c.darkened(0.35)
	var hands := skin
	match d.setting("arms", "hands", "skin"):
		"dark":
			hands = DARK
		"white":
			hands = WHITE
		"colour":
			hands = c
		"metal":
			hands = c.lightened(0.15)
	if metal and d.setting("arms", "hands", "") == "":
		hands = c.lightened(0.15)
	if d.setting("arms", "gauntlet", "") == "white":
		fore = WHITE

	# The arm is one piece made in tools/characters, in three regions: the
	# shoulder (as far as a short sleeve goes), the upper arm and the forearm.
	var shoulder := c if sleeve != "none" else skin
	var piece := "arm_l" if side == 0 else "arm_r"
	rig.add_figure(piece, arm, {"shoulder": shoulder, "upper": upper, "fore": fore}, false, shine)

	# Where the middle of the arm runs: the forearm from the elbow, forward
	# and then in to the end, and the upper arm from the shoulder down.
	var path := CharacterRig.arm_path(side)
	var top := path[0]
	var elbow := path[1]
	# A point `t` along the forearm from the elbow, and the forearm's own
	# space there, with +Y back up the arm toward the elbow.
	var along := func(t: float) -> Vector3:
		var first := path[1].distance_to(path[2])
		if t <= first:
			return path[1] + (path[2] - path[1]).normalized() * t
		return path[2] + (path[3] - path[2]).normalized() * (t - first)
	var basis_at := func(t: float) -> Basis:
		var first := path[1].distance_to(path[2])
		var dir := (path[2] - path[1]).normalized() if t <= first else (path[3] - path[2]).normalized()
		var y := -dir
		var x := (Vector3.RIGHT - y * Vector3.RIGHT.dot(y)).normalized()
		return Basis(x, y, x.cross(y))
	var fore_length := path[1].distance_to(path[2]) + path[2].distance_to(path[3])
	# A point on the upper arm's middle at a height.
	var up_at := func(height: float) -> Vector3:
		var t := clampf((height - top.y) / (elbow.y - top.y), 0.0, 1.0)
		return top.lerp(elbow, t)
	if sleeve == "rolled":
		rig.add(arm, rig.box(Vector3(0.088, 0.03, 0.093), 0.014), c.darkened(0.15), along.call(0.01), basis_at.call(0.01))

	# A band around the arm, `at` along the forearm (or up the upper arm when
	# negative), in a colour. The arm's nearly round, so a band is a short
	# round tube around it.
	var band := func(at: float, colour: Color, thick := 0.014, bulk := 0.006) -> void:
		if at >= 0.0:
			var radius := 0.04 + bulk * 0.5
			rig.add(arm, rig.cylinder(radius, radius, thick, 20), colour, along.call(at), basis_at.call(at), shine)
		else:
			var radius := 0.045 + bulk * 0.5
			rig.add(arm, rig.cylinder(radius, radius, thick, 20), colour, up_at.call(at), Basis.IDENTITY, shine)

	match d.setting("arms", "cuff", ""):
		"colour":
			band.call(fore_length - 0.02, c, 0.03)
		"dark":
			band.call(fore_length - 0.02, DARK, 0.03)
	if d.has("arms", "stripes"):
		for k in 3:
			band.call(-0.035 - k * 0.028, WHITE, 0.012)
			band.call(0.025 + k * 0.035, WHITE, 0.012)
	if d.has("arms", "wraps"):
		for k in 4:
			band.call(0.03 + k * 0.026, WHITE, 0.018, 0.004)
	if d.has("arms", "watch"):
		var watch: Basis = basis_at.call(fore_length - 0.025)
		band.call(fore_length - 0.025, Color("#1b1b1b"), 0.016)
		rig.add(arm, rig.cylinder(0.016, 0.016, 0.01, 14), Color("#c8ccd0"), along.call(fore_length - 0.025) + watch.x * 0.042 * outward, watch * Basis(Vector3.BACK, PI * 0.5), 0.6)
	if d.setting("arms", "bracer", "") == "spikes":
		rig.add(arm, rig.box(Vector3(0.09, 0.075, 0.094), 0.02), Color("#1b1b1b"), along.call(0.06), basis_at.call(0.06))
		for k in 3:
			var b: Basis = basis_at.call(0.035 + k * 0.025)
			var at: Vector3 = along.call(0.035 + k * 0.025) + b.x * 0.045 * outward
			rig.add(arm, rig.cylinder(0.0, 0.013, 0.035, 8), WHITE, at + b.x * 0.015 * outward, CharacterRig.pointing(b.x * outward))
	if d.has("arms", "pads"):
		rig.add(arm, rig.sphere(0.066, 0.07), c.lightened(0.3), top + Vector3(0.0, -0.001, 0.0), Basis.IDENTITY, 0.6)
	if d.has("arms", "puff"):
		rig.add(arm, rig.sphere(0.064, 0.09), c, up_at.call(-0.025))
	if d.has("arms", "fur"):
		var tuft := c.lightened(0.25)
		rig.add(arm, rig.sphere(0.058, 0.05), tuft, top)
		rig.add(arm, rig.sphere(0.05, 0.04), tuft, along.call(fore_length - 0.015), basis_at.call(fore_length - 0.015))
	if d.has("arms", "scales"):
		for k in 3:
			var y := -0.04 - k * 0.035
			rig.add(arm, rig.box(Vector3(0.006, 0.02, 0.03), 0.003), c.lightened(0.3), up_at.call(y) + Vector3(0.046 * outward, 0.0, 0.0))
			var b: Basis = basis_at.call(0.03 + k * 0.03)
			rig.add(arm, rig.box(Vector3(0.006, 0.02, 0.03), 0.003), c.lightened(0.3), along.call(0.03 + k * 0.03) + b.x * 0.041 * outward, b)
	if d.has("arms", "tattoo"):
		# An anchor on the outside of the upper arm.
		var at: Vector3 = up_at.call(-0.07) + Vector3(0.0462 * outward, 0.0, 0.0)
		var turn := Basis(Vector3.UP, -PI * 0.5 * outward)
		rig.print_on(arm, Vector2(0.006, 0.04), Color("#0d69ab"), at, turn)
		rig.print_on(arm, Vector2(0.03, 0.006), Color("#0d69ab"), at + Vector3(0.0, 0.01, 0.0), turn)
		rig.print_on(arm, Vector2(0.03, 0.006), Color("#0d69ab"), at + Vector3(0.0, -0.018, 0.0), turn)
	if d.setting("arms", "gauntlet", "") == "white":
		band.call(0.005, WHITE, 0.025)

	# The hand, with its wrist, which twists to grip.
	var hand_shine := 0.5 if d.setting("arms", "hands", "") == "metal" or metal else 0.0
	rig.add_figure("hand_l" if side == 0 else "hand_r", hand, {"main": hands}, false, hand_shine)
