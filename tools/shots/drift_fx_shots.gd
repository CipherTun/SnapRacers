extends Node

## A short run of pictures of one slide: the tire smoke, the sparks as it
## charges each boost level, then the boost flames once it's let go. The
## kart's put on the course's longest fairly straight stretch of the surface
## asked for, near its left edge, kicked into a gentle slide to the right and
## held there. It needs a screen, and saves in build/shots, or in OUT_DIR if
## that's set.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/drift_fx_shots.tscn -- peach_pit clear asphalt [name]
## SIDE=1 adds a picture from the side with the kart parked and a boost going.

const OUT := "res://build/shots"
## How many physics steps apart the pictures are.
const EVERY := 8


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var course: String = args[0] if args.size() > 0 else "peach_pit"
	var weather: String = args[1] if args.size() > 1 else "clear"
	var surface: String = args[2] if args.size() > 2 else "asphalt"
	var name: String = args[3] if args.size() > 3 else surface
	var out: String = OS.get_environment("OUT_DIR") if OS.has_environment("OUT_DIR") else OUT
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	seed(1)
	var host := Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "weather", weather)
	Game.settings.set_value("race", "time", "day")
	Game.racing_alone = true
	Game.show_race(Game.TRACKS + "/" + course + ".json")
	var race: Race = null
	while race == null:
		await get_tree().process_frame
		for child in host.get_children():
			if child is Race:
				race = child
	while not race.started:
		await get_tree().physics_frame
	race.hud.visible = false
	var track := race.track
	var kart := race.player.kart
	var controls := KartControls.new()
	kart.controls = controls
	var at := _stretch(track, surface)
	var frame := track.frame_at(at)
	print("%s at %.0f m on %s" % [name, at, track.pieces[track.piece_of[track._index_before(at)]].surface])
	# The race puts back a kart that jumps a long way from where it was.
	race.player.offset = at
	kart.freeze = true
	var ahead := track.forward_at(at)
	kart.global_transform = Transform3D(Basis.looking_at(ahead, track.up_at(at)), frame.origin - track.right_at(at) * track.width * 0.42 + track.up_at(at) * 0.5)
	await get_tree().physics_frame
	await get_tree().physics_frame
	kart.freeze = false
	for i in 3:
		await get_tree().physics_frame
		kart.linear_velocity = ahead * 20.0
		kart.angular_velocity = Vector3.ZERO
	controls.throttle = 1.0
	var cam := Camera3D.new()
	cam.fov = 55.0
	race.add_child(cam)
	cam.current = true
	DirAccess.make_dir_recursive_absolute(out)
	var shot := 0
	var let_go := 29 + Kart.slide_steps_of(Kart.SLIDE_LEVELS[-1]) + 20
	var offset := at
	for step in 300:
		if step == 20:
			controls.brake = 1.0
			controls.steer = 1.0
		elif step == 29:
			controls.brake = 0.0
		elif step == let_go:
			controls.steer = 0.0
		offset = track.offset_of(kart.global_position, offset, 30.0)
		var across := (kart.global_position - track.point_at(offset)).dot(track.right_at(offset))
		if step == 29:
			controls.steer = 0.16
		await get_tree().physics_frame
		# From behind and to the outside of the slide, low down.
		var back := kart.global_basis.z
		var side := -kart.global_basis.x
		cam.look_at_from_position(kart.global_position + back * 4.5 + side * 2.5 + Vector3.UP * 1.4, kart.global_position + Vector3.UP * 0.3, Vector3.UP)
		if step >= 24 and step % EVERY == 0 and step < let_go + 50:
			await RenderingServer.frame_post_draw
			var picture := get_viewport().get_texture().get_image()
			if picture.get_size() != Vector2i(1280, 720):
				picture.resize(1280, 720, Image.INTERPOLATE_LANCZOS)
			shot += 1
			picture.save_png("%s/drift_fx_%s_%02d.png" % [out, name, shot])
			print("  %02d: step %d, sliding %s, level %d, boost %.2f (level %d), %.1f m/s, %d wheels on other ground, %d glowing bits, %d puffs, %.1f m across, on %s" % [shot, step, kart.sliding, kart.slide_level, kart.boost_left, kart.boost_level, kart.linear_velocity.length(), kart.wheels.filter(func(w: Kart.Wheel) -> bool: return w.grounded and w.surface != surface).size(), kart.fx._glow.count, kart.fx._smoke.count, across, kart.wheels.map(func(w: Kart.Wheel) -> String: return w.surface if w.grounded else "air")])
	# With SIDE set, a last picture from the side of the kart parked with a
	# boost going.
	if OS.has_environment("SIDE"):
		kart.linear_velocity = Vector3.ZERO
		kart.freeze = true
		kart.linear_velocity = Vector3.ZERO
		kart.start_boost(3.0, 3)
		for i in 20:
			await get_tree().process_frame
			cam.look_at_from_position(kart.global_position - kart.global_basis.x * 4.0 + Vector3.UP * 1.0, kart.global_position, Vector3.UP)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/drift_fx_%s_side.png" % [out, name])
	print("saved drift_fx_%s" % name)
	get_tree().quit()


## The middle of the longest fairly straight stretch of road of `surface`.
func _stretch(track: TrackPath, surface: String) -> float:
	var best := 0.0
	var longest := -1.0
	var start := -1.0
	var o := 0.0
	while o < track.length:
		var here: String = track.pieces[track.piece_of[track._index_before(o)]].surface
		var straight := track.forward_at(o).dot(track.forward_at(o + 10.0)) > 0.97
		if here == surface and straight:
			if start < 0.0:
				start = o
			if o - start > longest:
				longest = o - start
				best = start
		else:
			start = -1.0
		o += 2.0
	return best + 5.0
