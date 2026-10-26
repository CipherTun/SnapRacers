class_name Podium
extends Node3D

## The podium at the end of a Grand Prix, put up on the cup's last course
## once the karts are cleared away (see Race.show_podium()).
##
## Three stepped blocks in the cup's colour with 1, 2 and 3 on their fronts,
## built from the same bricks as the rest of the scenery. The top three stand
## on them with their karts parked behind, and everyone else stands in a row
## either side. The camera sweeps in and then holds still. Once it's held
## for a while, or on a tap or a key, `finished` is sent.
##
## It's laid out in its own space with the front facing +Z, and turned a
## whole number of quarter turns, like every prop, so the brick patterns
## line up with the world's.

signal finished

## How wide and deep each step is, and how tall, first, second and third.
const STEP_WIDTH := 1.5
const STEP_DEPTH := 1.3
const HEIGHTS := [0.8, 0.56, 0.38]
## Across from the middle, in the steps' widths, first, second and third.
const ACROSS := [0.0, -1.0, 1.0]
## The size of a square of the numbers on the fronts, which are 3 by 5.
const PIXEL := 0.06
## How far behind the steps the karts are parked, and how far each is
## turned out from straight ahead, in degrees.
const PARKED := 0.6
const TURNED := [0.0, -18.0, 18.0]
## How thick the plate under it all is, and its colour.
const BASE := 0.12
const BASE_COLOUR := Color("#a3a2a4")
## The gap between the people standing in the rows either side.
const SPACING := 0.6
## How much room it needs around its middle, and how far from the middle its
## camera ends up at most.
const ROOM := 6.0
const CAMERA_OUT := 9.0
## The lamp over it after dark.
const LAMP_ENERGY := 3.0
const LAMP_RANGE := 10.0
## The camera's sweep in, then how long it holds still before `finished`.
const SWEEP := 4.0
const HOLD := 4.0
## How tall a number is, row by row from the top, for 1, 2 and 3.
const DIGITS := {
	1: ["010", "110", "010", "010", "111"],
	2: ["111", "001", "111", "100", "111"],
	3: ["111", "001", "011", "001", "111"],
}
const DARK := Color("#1b2a34")

## Everyone, winner first, each [name, KartDesign, CharacterDesign].
var order: Array = []
var colour := Color("#c4281c")
## Where it stands: the middle of the ground under the steps, and how many
## quarter turns its front is turned from +Z.
var middle := Vector3.ZERO
var facing := 0
## How high the ground is anywhere (TrackBuilder.ground_at()), or null for
## level with `middle` all round, as on the road.
var ground: Variant = null
## Each place's driver and kart, first place first, then the rest.
var drivers: Array[CharacterRig] = []
var karts: Array[Node3D] = []
var camera: Camera3D
## After dark it has a lamp over it. Set it before it goes into the scene.
var lit := false
var _time := 0.0
var _from: Transform3D
var _to: Transform3D
var _done := false
## How far out to the sides everything reaches.
var _reach := 0.0


func _init(everyone: Array, cup_colour: Color, spot: Array, ground_at: Variant = null) -> void:
	name = "Podium"
	order = everyone
	colour = cup_colour
	middle = spot[0]
	facing = spot[1]
	ground = ground_at if spot.size() < 3 or spot[2] else null


## The cup's colour, from its entry in the cups file, or red for one that
## hasn't got one.
static func colour_of(cup: Dictionary) -> Color:
	return Color(str(cup.get("colour", "#c4281c")))


## Where the podium goes, as [middle, quarter turns, whether it's on the
## ground]: on clear, flat ground beside the road near the start line, facing
## the road, with small things there cleared away. Failing that, on the start
## straight just past the line.
static func find_spot(track: TrackPath, builder: TrackBuilder) -> Array:
	var scenery: Scenery = null
	for child in builder.get_children():
		if child is Scenery:
			scenery = child
	if scenery != null:
		var best := []
		var best_score := -INF
		for step in range(-10, 11):
			var along := step * 6.0
			var frame := track.frame_at(fposmod(along, track.length))
			for side in [1.0, -1.0]:
				var out: Vector3 = frame.basis.x * side
				out.y = 0.0
				out = out.normalized()
				for extra in range(0, 30, 3):
					var at := frame.origin + out * (track.width * 0.5 + ROOM + 8.0 + extra)
					at.y = builder.ground_at(at.x, at.z)
					var clutter := scenery.clutter_at(at, ROOM)
					if clutter < 0:
						continue
					var turns := _turns_toward(-out)
					var front := _turned(Vector3.BACK, turns)
					var view := scenery.clutter_at(at + front * CAMERA_OUT, 2.0, false)
					if view < 0:
						continue
					var spread := _bumpiness(at, builder.ground_at)
					if spread > 1.2:
						continue
					var score := -clutter * 1.5 - view - absf(along) * 0.12 - extra * 0.25 - spread * 4.0
					if score > best_score:
						best_score = score
						best = [at, turns, true]
		if not best.is_empty():
			for damage in builder.get_tree().get_nodes_in_group("world_damage"):
				damage.clear_around(best[0], ROOM + 1.0)
				damage.clear_around(best[0] + _turned(Vector3.BACK, best[1]) * CAMERA_OUT, 2.5)
			return best
	# On the road, facing back along it toward the line.
	var frame := track.frame_at(minf(30.0, track.length * 0.25))
	return [frame.origin, _turns_toward(frame.basis.z), false]


## The quarter turn whose front (+Z at none) points most along `dir`.
static func _turns_toward(dir: Vector3) -> int:
	if absf(dir.x) > absf(dir.z):
		return 1 if dir.x > 0.0 else 3
	return 0 if dir.z > 0.0 else 2


static func _turned(v: Vector3, turns: int) -> Vector3:
	return v.rotated(Vector3.UP, turns * PI * 0.5)


## How far up and down the ground goes across the podium's footprint.
static func _bumpiness(at: Vector3, ground_at: Callable) -> float:
	var low := INF
	var high := -INF
	for x in [-1.0, 0.0, 1.0]:
		for z in [-1.0, 0.0, 1.0]:
			var h: float = ground_at.call(at.x + x * ROOM * 0.7, at.z + z * ROOM * 0.7)
			low = minf(low, h)
			high = maxf(high, h)
	return high - low


func _ready() -> void:
	var kit := SceneryKit.new()
	# The steps sit as high as the ground is on average under them and reach
	# down into it, so none float on a slope.
	var top := 0.0
	var bottom := INF
	for x in [-1.5, 0.0, 1.5]:
		for z in [-0.5, 0.5]:
			var h := _ground_at(Vector3(x * STEP_WIDTH, 0.0, z * STEP_DEPTH))
			top += h / 6.0
			bottom = minf(bottom, h)
	bottom -= 0.3
	# A light grey plate under it all, so it stands out from the ground.
	# A pale cup's steps stand on a dark one instead, and get dark numbers.
	var pale := colour.get_luminance() > 0.6
	_box(kit, Vector3(0.0, bottom, 0.0), Vector3(STEP_WIDTH * 3.0 + 0.6, top - bottom + BASE, STEP_DEPTH + 0.6), DARK if pale else BASE_COLOUR, SceneryKit.BRICK)
	top += BASE
	var ink := DARK if pale else Color.WHITE
	for place in 3:
		var x: float = ACROSS[place] * STEP_WIDTH
		var height: float = top + HEIGHTS[place]
		_box(kit, Vector3(x, bottom, 0.0), Vector3(STEP_WIDTH, height - bottom, STEP_DEPTH), colour, SceneryKit.BRICK)
		_number(kit, place + 1, Vector3(x, height - HEIGHTS[place] * 0.5, STEP_DEPTH * 0.5), ink)
	kit.build(self)

	# The karts are parked behind, far enough apart that the biggest fit.
	var gap := STEP_WIDTH * 1.2
	for place in mini(3, order.size()):
		gap = maxf(gap, KartModel.bounds(order[place][1]).size.x + 0.5)
	_reach = STEP_WIDTH * 1.5 + 0.6
	for place in order.size():
		var entry: Array = order[place]
		var rig := CharacterRig.new(entry[2], false)
		rig.lively = true
		rig.name = "Driver%d" % (place + 1)
		var feet := Vector3.ZERO
		if place < 3:
			feet = Vector3(ACROSS[place] * STEP_WIDTH, top + HEIGHTS[place], 0.0)
		else:
			feet = _in_row(place - 3)
			feet.y = _ground_at(feet)
			_reach = maxf(_reach, absf(feet.x) + 0.4)
		rig.transform = _placed(feet + Vector3.UP * CharacterRig.FEET_BELOW, 0.0)
		add_child(rig)
		drivers.append(rig)
		if place < 3:
			var kart := KartModel.make(entry[1], entry[2], false)
			kart.name = "Kart%d" % (place + 1)
			var box := KartModel.bounds(entry[1])
			var middle_at := Vector3(ACROSS[place] * gap, 0.0, -(STEP_DEPTH * 0.5 + PARKED + box.size.z * 0.5))
			var where := _placed(middle_at, deg_to_rad(TURNED[place]))
			# The box's middle over the spot, and its bottom on the ground.
			var centre := box.get_center()
			where.origin -= where.basis * Vector3(centre.x, 0.0, centre.z)
			where.origin.y = _ground_at(middle_at) - box.position.y
			kart.transform = where
			add_child(kart)
			karts.append(kart)
			_reach = maxf(_reach, absf(middle_at.x) + box.size.x * 0.5 + 0.3)

	if lit:
		var lamp := OmniLight3D.new()
		lamp.light_color = CourseLamps.COLOUR
		lamp.light_energy = LAMP_ENERGY
		lamp.omni_range = LAMP_RANGE
		lamp.shadow_enabled = false
		lamp.transform = _placed(Vector3(0.0, top + 3.5, 2.5), 0.0)
		add_child(lamp)

	camera = Camera3D.new()
	camera.fov = 45.0
	camera.near = 0.05
	add_child(camera)
	var look := Vector3(0.0, top + 0.7, -0.4)
	var out := _camera_distance()
	_to = _looking(Vector3(0.0, top + 2.1, out), look)
	var start := Vector3(0.0, top + 7.0, out * 1.8).rotated(Vector3.UP, deg_to_rad(50.0))
	_from = _looking(start, look)
	camera.global_transform = _from
	camera.make_current()


## Where the `n`th of the rest of the field stands, by turns either side of
## the steps, the nearest first.
func _in_row(n: int) -> Vector3:
	var side := -1.0 if n % 2 == 0 else 1.0
	return Vector3(side * (STEP_WIDTH * 1.5 + 0.5 + (n / 2) * SPACING), 0.0, STEP_DEPTH * 0.5 - 0.1)


## How far out the camera stops, so everyone fits across the screen.
func _camera_distance() -> float:
	var size := get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(16.0, 9.0)
	var aspect := size.x / maxf(size.y, 1.0)
	var across := atan(tan(deg_to_rad(camera.fov) * 0.5) * aspect)
	return minf(_reach / tan(across) * 1.1 + STEP_DEPTH, CAMERA_OUT)


## The ground's height at a point in the podium's own space, in the world.
func _ground_at(local: Vector3) -> float:
	if ground == null:
		return middle.y
	var at := middle + _turned(local, facing)
	return (ground as Callable).call(at.x, at.z)


## A transform in the world for a point in the podium's own space, facing
## its front, turned `yaw` more.
func _placed(local: Vector3, yaw: float) -> Transform3D:
	var at := middle + _turned(Vector3(local.x, 0.0, local.z), facing)
	at.y = local.y
	# Drivers and karts face -Z, so they're turned around to face the front.
	return Transform3D(Basis(Vector3.UP, PI + facing * PI * 0.5 + yaw), at)


func _looking(local: Vector3, at: Vector3) -> Transform3D:
	var from := middle + _turned(Vector3(local.x, 0.0, local.z), facing)
	from.y = local.y
	var to := middle + _turned(Vector3(at.x, 0.0, at.z), facing)
	to.y = at.y
	return Transform3D.IDENTITY.translated(from).looking_at(to, Vector3.UP)


## A box in the podium's own space standing on `bottom`.
func _box(kit: SceneryKit, bottom: Vector3, size: Vector3, tint: Color, surface: int) -> void:
	var at := middle + _turned(Vector3(bottom.x, 0.0, bottom.z), facing)
	at.y = bottom.y
	var turned := size if facing % 2 == 0 else Vector3(size.z, size.y, size.x)
	kit.box(at, turned, tint, surface, false)


## A number on a step's front, its middle at `at`, in squares standing a
## little proud of it.
func _number(kit: SceneryKit, n: int, at: Vector3, ink: Color) -> void:
	var rows: Array = DIGITS[n]
	for row in rows.size():
		for column in 3:
			if rows[row][column] != "1":
				continue
			var square := at + Vector3((column - 1) * PIXEL, (2 - row) * PIXEL - PIXEL * 0.5, 0.01)
			_box(kit, square, Vector3(PIXEL, PIXEL, 0.04), ink, SceneryKit.PLAIN)


func _process(delta: float) -> void:
	_time += delta
	var t := clampf(_time / SWEEP, 0.0, 1.0)
	var eased := 1.0 - pow(1.0 - t, 3.0)
	var from := _from.origin.lerp(_to.origin, eased)
	var turn := _from.basis.get_rotation_quaternion().slerp(_to.basis.get_rotation_quaternion(), eased)
	camera.global_transform = Transform3D(Basis(turn), from)
	if _time >= SWEEP + HOLD:
		finish()


## Skips to the end.
func finish() -> void:
	if _done:
		return
	_done = true
	finished.emit()


func _unhandled_input(event: InputEvent) -> void:
	var tapped: bool = event is InputEventScreenTouch and event.pressed
	var clicked: bool = event is InputEventMouseButton and event.pressed
	var key: bool = (event is InputEventKey or event is InputEventJoypadButton) and event.pressed and not event.is_echo()
	if tapped or clicked or key:
		get_viewport().set_input_as_handled()
		finish()
