extends Node

## Pictures of the podium after a cup's last race, in the weather and at the
## time of day asked for: as the camera sweeps in, once it's still, and with
## the standings over it. "two" at the end is a cup for two. It needs a screen.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/podium_shots.tscn -- baseplate rain night [folder] [WIDTHxHEIGHT] [two]

const OUT := "res://build/shots"
## When to take them, in seconds after the podium goes up.
const AT := [0.8, 2.5, 5.0]

var host: Node


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var cup: String = args[0] if args.size() > 0 else "baseplate"
	var weather: String = args[1] if args.size() > 1 else "clear"
	var time: String = args[2] if args.size() > 2 else "day"
	var out: String = args[3] if args.size() > 3 else OUT
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	var size := Vector2i(1280, 720)
	if args.size() > 4:
		size = Vector2i(int(args[4].get_slice("x", 0)), int(args[4].get_slice("x", 1)))
	DisplayServer.window_set_size(size)
	seed(1)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "weather", weather)
	Game.settings.set_value("race", "time", time)
	var two := args.size() > 5 and args[5] == "two"
	Game.start_grand_prix(cup, two)
	# Straight to the last race, before the first one's loaded.
	Game.grand_prix.round = Game.grand_prix.track_ids().size() - 1
	Game.track_path = Game.grand_prix.track_path()
	var race: Race = null
	while race == null:
		await get_tree().process_frame
		for child in host.get_children():
			if child is Race:
				race = child
	print("on ", race.track.name)
	for i in 20:
		await get_tree().process_frame
	var order := race.racers.map(func(r): return r.name)
	order.shuffle()
	Game.finish_grand_prix_race(order)
	var podium: Podium = race.podium
	DirAccess.make_dir_recursive_absolute(out)
	var start := Time.get_ticks_msec()
	var named := "%s_%s_%s%s_%dx%d" % [cup, weather, time, "_two" if two else "", size.x, size.y]
	for i in AT.size():
		while podium._time < AT[i]:
			await get_tree().process_frame
		await _save("%s/podium_%s_%d.png" % [out, named, i + 1], size)
	podium.finish()
	while not podium.still():
		await get_tree().process_frame
	for i in 10:
		await get_tree().process_frame
	await _save("%s/standings_%s.png" % [out, named], size)
	print("saved podium_%s_%s_%s in %d ms" % [cup, weather, time, Time.get_ticks_msec() - start])
	get_tree().quit()


func _save(path: String, size: Vector2i) -> void:
	RenderingServer.force_draw.call_deferred()
	await RenderingServer.frame_post_draw
	var picture := get_viewport().get_texture().get_image()
	if picture.get_size() != size:
		picture.resize(size.x, size.y, Image.INTERPOLATE_LANCZOS)
	picture.save_png(path)
