class_name Puddles
extends Node3D

## Puddles on the road in the rain. Driving through one there's even less
## grip than on the wet road, and the water drags. They're the same for the
## same seed, so everyone online has the same ones.
##
## They build up over the race: every spot is placed at the start, and each
## one starts growing at its own point in the race and is full size
## GROW later (see grow()). The race passes in how far the leader's got, so
## a device only needs that one number to have the same puddles as the rest.
##
## They're not bodies a wheel can touch: a kart asks how far into a puddle a
## point is (see factor_at()), so the road under them stays the road, sticky
## and all.

## How many for every 100 m of road, from a light rain to a storm, and how
## big across when full, in metres.
const PER_100M := [3.0, 6.0]
const SIZE := [3.0, 9.0]
## They keep this far in from the road's edges.
const EDGE := 1.5
## Never where the road climbs, rolls or leaves the ground.
const NOT_ON := ["ramp", "jump", "loop", "corkscrew", "wallride", "bank"]
## For looking them up quickly, a grid of squares this big.
const CELL := 4.0
const WATER := Color("#0d1116")
## Where in the race (0 at the start, 1 at the end) each one starts to grow,
## and how much of the race it takes to get to full size. A few have started
## before GO, so there's a little water from the start, and all are full by
## the end.
const STARTS := [-0.2, 0.65]
const GROW := 0.35
## Just started, one is this much of its full size.
const SMALLEST := 0.3
## The build-up goes in steps this big, so every device steps together and
## nothing's redrawn more often than that.
const STEP := 0.01
## A puddle's drawn again once its size is this far off what's drawn, in
## metres.
const REDRAW := 0.1
## For the AI: one this big across or more is worth going round.
const AVOID_SIZE := 4.0

## Each one as [middle, full radius, where it starts growing].
var spots: Array = []
## How far the build-up's got, from 0 to 1. It only ever goes up.
var level := 0.0
## Each one's radius now, 0 until it's started.
var radius_now: PackedFloat32Array = []
var _cells := {}
var _drawn: PackedFloat32Array = []
var _multi: MultiMesh
var _track: TrackPath
## Which way is up at each one, worked out once.
var _ups: Array[Vector3] = []


func _init(track: TrackPath = null, chance_seed := 0, amount := 0.0) -> void:
	if track == null:
		return
	_track = track
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(_seed_key(chance_seed, track))
	var sizes := _sizes()
	var count := roundi(track.length / 100.0 * lerpf(_per_100m()[0], _per_100m()[1], amount))
	var placed: Array = []
	# Where each placed one's middle is on the grid, for the spacing check.
	var near := {}
	var reach: float = sizes[1] * 0.5
	var tries := 0
	while placed.size() < count and tries < count * 20:
		tries += 1
		var offset := rng.randf() * track.length
		var type := track.piece_type_at(offset)
		if NOT_ON.has(type) or track.up_at(offset).y < 0.97 or track.pieces[track.piece_of[track._index_before(offset)]].sticky:
			continue
		var radius := rng.randf_range(sizes[0], sizes[1]) * 0.5
		var across := _across(rng, radius, track)
		var start := rng.randf_range(STARTS[0], STARTS[1])
		var middle := track.point_at(offset) + track.right_at(offset) * across
		if _crowded(near, placed, middle, radius, reach):
			continue
		var key := _cell(middle)
		if not near.has(key):
			near[key] = []
		near[key].append(placed.size())
		placed.append([middle, radius, start])
	# In the order they start, so the ones drawn are always the first few.
	placed.sort_custom(func(a: Array, b: Array) -> bool: return a[2] < b[2])
	for s in placed:
		add(s[0], s[1], s[2])
	_level_sizes()
	_draw()


## Whether one this big here would be too close to one already placed. `near`
## has where their middles are on the grid, and none is bigger than `reach`.
func _crowded(near: Dictionary, placed: Array, middle: Vector3, radius: float, reach: float) -> bool:
	var low := _cell(middle - Vector3.ONE * (radius + reach))
	var high := _cell(middle + Vector3.ONE * (radius + reach))
	for x in range(low.x, high.x + 1):
		for z in range(low.y, high.y + 1):
			for j in near.get(Vector2i(x, z), []):
				if placed[j][0].distance_to(middle) < (placed[j][1] + radius) * _spacing():
					return true
	return false


## Puts one here, this big when full, starting to grow at `start`. Tests
## make their own this way, already full size.
func add(middle: Vector3, radius: float, start := -1.0) -> void:
	spots.append([middle, radius, start])
	radius_now.append(_size_now(spots.size() - 1))
	_drawn.append(0.0)
	var low := _cell(middle - Vector3(radius, 0.0, radius))
	var high := _cell(middle + Vector3(radius, 0.0, radius))
	for x in range(low.x, high.x + 1):
		for z in range(low.y, high.y + 1):
			var key := Vector2i(x, z)
			if not _cells.has(key):
				_cells[key] = []
			_cells[key].append(spots.size() - 1)


## Builds up to this far through the race, from 0 to 1. It never goes back,
## and goes in STEPs, so any device given the same progress has exactly the
## same puddles.
func grow(progress: float) -> void:
	var now := stepped(progress)
	if now <= level:
		return
	level = now
	_level_sizes()
	if _multi == null:
		return
	var shown := 0
	var redraw := false
	for i in spots.size():
		if radius_now[i] > 0.0:
			shown = i + 1
		if absf(radius_now[i] - _drawn[i]) > REDRAW or (_drawn[i] == 0.0) != (radius_now[i] == 0.0):
			redraw = true
	if redraw:
		for i in shown:
			_place(i)
		_multi.visible_instance_count = shown


## Progress rounded down to a STEP. Online it goes as a whole number of
## STEPs (see steps_of()), and comes back exactly the same.
static func stepped(progress: float) -> float:
	return from_steps(steps_of(progress))


static func steps_of(progress: float) -> int:
	return floori(clampf(progress, 0.0, 1.0) / STEP + 0.0001)


static func from_steps(steps: int) -> float:
	return steps * STEP


## How grown this one is now, from 0 (not started) to 1 (full size).
func growth(i: int) -> float:
	return clampf((level - spots[i][2]) / GROW, 0.0, 1.0)


## How far into a puddle this point is: 0 outside, 1 in the middle, and in
## between near its edge.
func factor_at(point: Vector3) -> float:
	var most := 0.0
	for i in _cells.get(_cell(point), []):
		var radius := radius_now[i]
		if radius <= 0.0:
			continue
		var middle: Vector3 = spots[i][0]
		var d := Vector2(point.x - middle.x, point.z - middle.z).length()
		if absf(point.y - middle.y) < 2.0:
			most = maxf(most, _profile(i, d, radius))
	return most


## Whether one big enough to go round is within `margin` of this point.
func in_the_way(point: Vector3, margin: float) -> bool:
	var low := _cell(point - Vector3.ONE * margin)
	var high := _cell(point + Vector3.ONE * margin)
	for x in range(low.x, high.x + 1):
		for z in range(low.y, high.y + 1):
			for i in _cells.get(Vector2i(x, z), []):
				if not _worth_avoiding(i):
					continue
				var middle: Vector3 = spots[i][0]
				if Vector2(point.x - middle.x, point.z - middle.z).length() < radius_now[i] + margin and absf(point.y - middle.y) < 2.0:
					return true
	return false


func _profile(_i: int, d: float, radius: float) -> float:
	return 1.0 - smoothstep(radius * 0.7, radius, d)


func _worth_avoiding(i: int) -> bool:
	return radius_now[i] * 2.0 >= AVOID_SIZE


func _seed_key(chance_seed: int, track: TrackPath) -> Array:
	return [chance_seed, track.name]


func _per_100m() -> Array:
	return PER_100M


func _sizes() -> Array:
	return SIZE


## How close two can be, as a share of their radii added up. Under 1 they
## run into each other when full, which spreads the water.
func _spacing() -> float:
	return 0.7


## How far across the road one goes, right positive.
func _across(rng: RandomNumberGenerator, radius: float, track: TrackPath) -> float:
	return rng.randf_range(-1.0, 1.0) * maxf(track.width * 0.5 - EDGE - radius, 0.0)


func _level_sizes() -> void:
	for i in spots.size():
		radius_now[i] = _size_now(i)


## This one's radius now: SMALLEST of its full size as it starts,
## and 0 before.
func _size_now(i: int) -> float:
	var g := growth(i)
	return spots[i][1] * lerpf(SMALLEST, 1.0, g) if g > 0.0 else 0.0


static func _cell(point: Vector3) -> Vector2i:
	return Vector2i(floori(point.x / CELL), floori(point.z / CELL))


## Flat water lying on the road, drawn all at once.
func _draw() -> void:
	if spots.is_empty():
		return
	_multi = MultiMesh.new()
	_multi.transform_format = MultiMesh.TRANSFORM_3D
	_multi.use_colors = true
	_multi.use_custom_data = true
	_multi.mesh = _mesh()
	_multi.instance_count = spots.size()
	var shown := 0
	for i in spots.size():
		_ups.append(_track.up_at(_track.offset_of(spots[i][0])))
		_multi.set_instance_color(i, _colour())
		_multi.set_instance_custom_data(i, Color(float(_surface()), 0.0, 0.0, 0.0))
		_place(i)
		if radius_now[i] > 0.0:
			shown = i + 1
	_multi.visible_instance_count = shown
	# Sized to the whole lot full grown, since they grow while it's drawn.
	var box := AABB(spots[0][0], Vector3.ZERO)
	for s in spots:
		box = box.expand(s[0] + Vector3(s[1], 2.0, s[1])).expand(s[0] - Vector3(s[1], 0.5, s[1]))
	_multi.custom_aabb = box
	var draw := MultiMeshInstance3D.new()
	draw.multimesh = _multi
	draw.material_override = SceneryKit.material()
	draw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(draw)


func _mesh() -> Mesh:
	return SceneryKit.mesh_for("cylinder")


func _colour() -> Color:
	return WATER


func _surface() -> int:
	return SceneryKit.PUDDLE


## Puts one where it is at the size it is now.
func _place(i: int) -> void:
	var middle: Vector3 = spots[i][0]
	var radius := maxf(radius_now[i], 0.01)
	var up := _ups[i]
	var flat := Basis.looking_at(up.cross(Vector3.RIGHT).normalized() if absf(up.x) < 0.9 else Vector3.FORWARD, up)
	_multi.set_instance_transform(i, Transform3D(_shape(i, flat, radius), middle + up * 0.02))
	_drawn[i] = radius_now[i]


func _shape(_i: int, flat: Basis, radius: float) -> Basis:
	return flat * Basis.from_scale(Vector3(radius * 2.0, 0.02, radius * 2.0))
