extends SceneTree

## A piece's edges: "walls" hold a kart in, even down on the grass, and an
## open edge up in the air lets it fall, far enough that the race puts it
## back, and it lands back on the road. "auto" walls in road up in the air.
## It builds a raised run of straights, one for each kind of edge, and slides
## the Starter across each one to the left and to the right.
##
## Run it with:
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/edges_test.gd

## How far below the road a kart has to be for the race to put it back (see
## Race.FALLEN, which this test can't load).
const FALLEN := 4.0

var failures := 0
var world: Node3D
var track: TrackPath
## Each piece's first and last offset along the track.
var spans := {}


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func _initialize() -> void:
	_run.call_deferred()


func frames(n: int) -> void:
	for i in n:
		await physics_frame


func _run() -> void:
	world = Node3D.new()
	root.add_child(world)
	track = TrackPath.from_dict({"theme": "orchard", "pieces": [
		{"type": "straight", "length": 3, "edges": "walls"},
		{"type": "ramp", "length": 2, "rise": 2},
		{"type": "straight", "length": 3, "edges": "walls"},
		{"type": "straight", "length": 3, "edges": "open"},
		{"type": "straight", "length": 3, "edges": "left_open"},
		{"type": "straight", "length": 3, "edges": "right_open"},
		{"type": "straight", "length": 3},
		{"type": "ramp", "length": 2, "rise": -2},
		{"type": "straight", "length": 1},
	]})
	for k in track.points.size():
		var piece := track.piece_of[k]
		var was: Array = spans.get(piece, [INF, -INF])
		spans[piece] = [minf(was[0], track.distances[k]), maxf(was[1], track.distances[k])]
	var builder := TrackBuilder.new(track)
	builder.scenery = "none"
	builder.sky = false
	world.add_child(builder)
	await frames(2)
	var high := track.point_at(_middle(2)).y
	check(high > FALLEN + 1.0, "the run of straights is up in the air (%.1f m)" % high)

	# [piece, its edges, held in on the left, held in on the right]
	for case in [[0, "walls down on the grass", true, true], [2, "walls", true, true], [3, "open", false, false], [4, "left_open", false, true], [5, "right_open", true, false], [6, "auto up in the air", true, true]]:
		for side: float in [-1.0, 1.0]:
			var held: bool = case[2] if side < 0.0 else case[3]
			var way := "left" if side < 0.0 else "right"
			var result := await slide_across(case[0], side)
			if held:
				check(result.on_road, "%s holds a kart in on the %s (%.1f m out at most)" % [case[1], way, result.out])
			else:
				check(result.fell, "%s lets a kart off the %s, and it falls (%.1f m out, %.1f m below the road)" % [case[1], way, result.out, -result.below])
				check(result.back, "and it's put back on the road (%.1f m from the middle, up.y %.2f)" % [result.back_out, result.up])

	print("All edge checks passed." if failures == 0 else "%d edge checks failed." % failures)
	quit(1 if failures > 0 else 0)


## Halfway along a piece.
func _middle(piece: int) -> float:
	return (spans[piece][0] + spans[piece][1]) * 0.5


## Puts the Starter on a piece, a bit before its middle, driving across it
## towards one side, and says where it ends up. One that falls is put back the
## way the race does it, at the road's middle.
func slide_across(piece: int, side: float) -> Dictionary:
	var at := _middle(piece) - 15.0
	var frame := track.frame_at(at)
	var kart := Kart.new()
	kart.build(KartDesign.load_file("res://tests/data/legacy/starter.json"))
	# Turned 30 degrees towards that side, with the gas held.
	var heading := frame.basis.rotated(frame.basis.y, -side * deg_to_rad(30.0))
	kart.transform = Transform3D(heading, frame.origin + frame.basis.y * 0.35)
	kart.reset_to = func(where: Vector3) -> Transform3D:
		var f := track.frame_at(track.offset_of(where))
		return Transform3D(f.basis, f.origin + f.basis.y * Kart.RESET_LIFT)
	world.add_child(kart)
	kart.linear_velocity = -heading.z * 14.0
	kart.controls.throttle = 1.0
	var lowest := 0.0
	var furthest := 0.0
	var fell := false
	for i in 150:
		await physics_frame
		var below := _below(kart)
		lowest = minf(lowest, below)
		furthest = maxf(furthest, absf(_across(kart)))
		if below < -FALLEN:
			fell = true
			break
	# A kart held in has run up to the wall, past the road's edge line, and
	# stayed this side of it, on its wheels.
	var wall := track.width * 0.5 + TrackPath.KERB
	var held := not fell and furthest > track.width * 0.5 - 1.0 and furthest < wall and lowest > -1.0 and kart.global_basis.y.y > 0.8
	var result := {"fell": fell, "below": lowest, "out": furthest, "on_road": held, "back": false, "back_out": 0.0, "up": 0.0}
	if fell:
		kart.controls.throttle = 0.0
		kart.request_reset()
		await frames(90)
		result.back_out = absf(_across(kart))
		result.up = kart.global_basis.y.dot(track.up_at(track.offset_of(kart.global_position)))
		result.back = result.back_out < track.width * 0.5 and absf(_below(kart)) < 1.5 and result.up > 0.9
	kart.queue_free()
	await frames(2)
	return result


## How far above (or below, negative) the road's nearest point the kart is.
func _below(kart: Kart) -> float:
	var offset := track.offset_of(kart.global_position)
	return (kart.global_position - track.point_at(offset)).dot(track.up_at(offset))


## How far right (or left, negative) of the road's middle the kart is.
func _across(kart: Kart) -> float:
	var offset := track.offset_of(kart.global_position)
	return (kart.global_position - track.point_at(offset)).dot(track.right_at(offset))
