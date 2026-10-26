extends Node

## Pictures of the snow drifts on a snowy course at a few points in their
## build-up, from above at two spots along the road where most of them lie
## and from low down on the road where the most tongues lie just ahead. It
## needs a screen, and saves in build/shots, or in OUT_DIR if that's set.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/drift_shots.tscn -- frostbite_forest [name] [build-up ...]

const OUT := "res://build/shots"
const BUILD_UPS := [0.3, 0.6, 1.0]


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var course: String = args[0] if args.size() > 0 else "frostbite_forest"
	var name: String = args[1] if args.size() > 1 else course
	var steps: Array = BUILD_UPS if args.size() <= 2 else Array(args.slice(2)).map(func(value): return float(value))
	var out: String = OS.get_environment("OUT_DIR") if OS.has_environment("OUT_DIR") else OUT
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	seed(1)
	var host := Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "weather", "snow")
	Game.settings.set_value("race", "time", "day")
	Game.racing_alone = true
	Game.show_race(Game.TRACKS + "/" + course + ".json")
	var race: Race = null
	while race == null:
		await get_tree().process_frame
		for child in host.get_children():
			if child is Race:
				race = child
	for i in 10:
		await get_tree().process_frame
	var track := race.track
	var drifts: Puddles = race.builder.drifts
	var spots := _spots(track, drifts)
	var low := _low_spot(track, drifts)
	var cam := Camera3D.new()
	cam.fov = 60.0
	race.add_child(cam)
	DirAccess.make_dir_recursive_absolute(out)
	for step in steps:
		race.build_up = maxf(race.build_up, step)
		for i in 5:
			await get_tree().physics_frame
		var shown: int = drifts._multi.visible_instance_count
		print("at %.2f: %d lumps, %d triangles" % [step, shown, shown * drifts._mesh().get_faces().size() / 3])
		# From above at each spot, then low down on the road at the low spot,
		# looking along it, with the player's kart parked on the crest of a
		# tongue there so its shadow shows on the snow.
		_park(race.player.kart, track, drifts, low)
		for n in spots.size() + 1:
			var at: float = spots[mini(n, spots.size() - 1)] if n < spots.size() else low
			var from := track.point_at(at) + track.up_at(at) * 7.0 - track.forward_at(at) * 4.0
			var look := track.point_at(at + 22.0)
			if n == spots.size():
				from = track.point_at(at - 4.0) + track.up_at(at) * 2.0
				look = track.point_at(at + 18.0)
			cam.look_at_from_position(from, look, Vector3.UP)
			cam.current = true
			for i in 3:
				await get_tree().process_frame
			RenderingServer.force_draw.call_deferred()
			await RenderingServer.frame_post_draw
			var picture := get_viewport().get_texture().get_image()
			if picture.get_size() != Vector2i(1280, 720):
				picture.resize(1280, 720, Image.INTERPOLATE_LANCZOS)
			picture.save_png("%s/drifts_%s_%d_%03d.png" % [out, name, n + 1, roundi(step * 100.0)])
	print("saved drifts_%s" % name)
	get_tree().quit()


## Two places along the road, well apart, with the most tongues just ahead.
func _spots(track: TrackPath, drifts: Puddles) -> Array:
	var scores: Array = []
	var o := 0.0
	while o < track.length:
		var ahead := track.point_at(o + 22.0)
		var count := 0
		for i in drifts.spots.size():
			if not drifts._only_looks[i] and drifts.spots[i][0].distance_to(ahead) < 22.0:
				count += 1
		scores.append([count, o])
		o += 10.0
	scores.sort_custom(func(a: Array, b: Array) -> bool: return a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]))
	var picked: Array = []
	for s in scores:
		var far := true
		for p in picked:
			var gap := absf(s[1] - p)
			far = far and minf(gap, track.length - gap) > 150.0
		if far:
			picked.append(s[1])
		if picked.size() == 2:
			break
	return picked


## Where on the road, looking along it from low down, the most snow lies
## in tongues 8 to 26 m ahead on a fairly straight stretch of plain road.
func _low_spot(track: TrackPath, drifts: Puddles) -> float:
	var best := 0.0
	var most := -1
	var o := 0.0
	while o < track.length:
		var count := 0
		for i in drifts.spots.size():
			if drifts._only_looks[i]:
				continue
			var ahead := fposmod(drifts._laid[i] - o, track.length)
			if ahead > 8.0 and ahead < 26.0:
				count += roundi(drifts._long[i] * drifts._wide[i])
		# Only where the road runs fairly straight, so they're in the picture,
		# and isn't ice, which they hardly show on.
		var plain: bool = track.pieces[track.piece_of[track._index_before(o + 16.0)]].surface != "ice"
		if count > most and plain and track.forward_at(o).dot(track.forward_at(o + 26.0)) > 0.95:
			most = count
			best = o
		o += 5.0
	print("low view at %.0f m with %d m² of tongues ahead" % [best, most])
	return best


## Holds the kart still on the crest of the biggest tongue grown so far
## from 6 to 20 m past `at`.
func _park(kart: RigidBody3D, track: TrackPath, drifts: Puddles, at: float) -> void:
	var best := -1
	for i in drifts.spots.size():
		var ahead := fposmod(drifts._laid[i] - at, track.length)
		if not drifts._only_looks[i] and drifts.radius_now[i] > 0.0 and ahead > 6.0 and ahead < 20.0 and (best < 0 or drifts._wide[i] * drifts._long[i] > drifts._wide[best] * drifts._long[best]):
			best = i
	if best < 0:
		return
	var grown: float = drifts.radius_now[best] / float(drifts.spots[best][1])
	var crest: Vector3 = drifts._root[best] + drifts._dir[best] * drifts._long[best] * grown * Drifts.CREST
	kart.freeze = true
	kart.global_transform = Transform3D(Basis.looking_at(track.forward_at(track.offset_of(crest, at + 12.0, 30.0))), crest + Vector3.UP * 0.45)
