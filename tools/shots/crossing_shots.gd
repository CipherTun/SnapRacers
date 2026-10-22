extends Node

## Takes pictures of a level crossing: a course from data/tracks with its
## first straight tile swapped for a crossing, the train going over with the
## barriers down and karts waiting, the lights, a tunnel and the course from
## above. It needs a screen, and saves in build/shots.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/crossing_shots.tscn -- peach_pit [night]

const OUT := "res://build/shots"

var _course := ""
var _camera: Camera3D


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/crossing_%s_%s.png" % [OUT, _course, name])
	print("saved ", name)


func look(from: Vector3, at: Vector3) -> void:
	_camera.global_position = from
	_camera.look_at(at, Vector3.UP)


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var args := OS.get_cmdline_user_args()
	_course = args[0] if args.size() > 0 else "peach_pit"
	var night := args.has("night")
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/tracks/%s.json" % _course))
	# The first straight past the start with room for the railway.
	var plain: Array = data.pieces.duplicate(true)
	var track: TrackPath
	for i in plain.size():
		var spec: Dictionary = plain[i]
		if i < 3 or spec.get("type", "straight") != "straight" or spec.has("surface"):
			continue
		var pieces: Array = plain.duplicate(true)
		var rest := int(spec.get("length", 1)) - 1
		pieces[i] = {"type": "crossing"}
		if rest > 0:
			pieces.insert(i + 1, {"type": "straight", "length": rest})
		data.pieces = pieces
		track = TrackPath.from_dict(data)
		if not LevelCrossing.cramped(track, track.crossing_offsets()[0]):
			break
	var conditions := Conditions.resolve(track.theme, "clear", "night" if night else "day", 7)
	var builder := TrackBuilder.new(track, conditions)
	add_child(builder)
	await frames(2)
	var crossing: LevelCrossing = builder.crossings[0]
	crossing.own_clock = false
	_camera = Camera3D.new()
	_camera.far = 900.0
	add_child(_camera)
	_camera.make_current()
	var tag := "_night" if night else ""

	# Three karts waiting at the barriers.
	var design := KartDesign.load_file("res://tests/data/legacy/starter.json")
	for n in 3:
		var kart := Kart.new()
		kart.build(design)
		var where := track.place_at(crossing.offset - LevelCrossing.STOP_BACK - 1.0 - (n / 2) * 6.0, 0.6)
		where.origin += where.basis.x * (-2.5 if n % 2 == 0 else 2.5)
		kart.transform = where
		add_child(kart)
	var w := crossing.timetable.road_window(0)
	var way := float(crossing.timetable.direction(0))
	var m := crossing.middle
	var f := crossing.along
	var r := crossing.across

	# Lights on, barriers coming down, train not there yet.
	crossing.time = w.x - TrainTimetable.BARRIERS_BEFORE + 1.0
	await frames(8)
	look(m - f * 24.0 + Vector3.UP * 3.0 + r * 3.0, m + Vector3.UP * 2.0)
	await shot("barriers" + tag)

	# The train going over.
	crossing.time = (w.x + w.y) * 0.5 - 0.3
	await frames(8)
	look(m - f * 30.0 + Vector3.UP * 5.0 - r * 6.0, m + Vector3.UP * 2.0)
	await shot("train" + tag)
	look(m - f * 12.0 + Vector3.UP * 2.0 - r * way * 20.0, m + Vector3.UP * 2.5)
	await shot("train_close" + tag)
	look(m + Vector3.UP * 45.0 - f * 50.0, m)
	await shot("above" + tag)

	# The train coming out of a tunnel.
	var k := 0
	var side := -way
	var far: float = crossing.reach[0 if side < 0.0 else 1]
	crossing.time = crossing.timetable.arrival(k) - (far - 14.0) / TrainTimetable.SPEED
	await frames(8)
	var mouth := crossing.rail_point(side * far)
	look(mouth - r * side * 26.0 + f * 16.0 + Vector3.UP * 6.0, mouth + Vector3.UP * 3.0)
	await shot("tunnel" + tag)

	# Engine side on.
	crossing.time = crossing.timetable.arrival(k) + 0.2
	await frames(4)
	var head := crossing.rail_point(way * 0.0)
	look(head - f * 14.0 + Vector3.UP * 2.5 + r * way * -4.0, head + Vector3.UP * 2.0 - r * way * 4.0)
	await shot("engine" + tag)

	# A kart's broken through an arm, with the bits on the road.
	crossing.time = w.x - TrainTimetable.BARRIERS_BEFORE + TrainTimetable.BARRIER_SWING + 0.5
	await frames(4)
	crossing.break_arm(crossing.arms_in()[0], f * 20.0 + Vector3.UP * 2.0)
	await frames(90)
	look(m - f * 16.0 + Vector3.UP * 3.0 + r * 4.0, m - f * 7.0 + Vector3.UP * 0.8)
	await shot("broken" + tag)
	look(m - f * 3.0 + Vector3.UP * 10.0 - r * 10.0, m - f * 8.0)
	await shot("broken_above" + tag)
	get_tree().quit()
