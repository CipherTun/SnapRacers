extends Node

## Pictures of the podium after a cup's last race, in the weather and at the
## time of day asked for: as the camera sweeps in and once it's still. It
## needs a screen.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/podium_shots.tscn -- baseplate rain night [folder]

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
	DisplayServer.window_set_size(Vector2i(1280, 720))
	seed(1)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "weather", weather)
	Game.settings.set_value("race", "time", time)
	Game.start_grand_prix(cup)
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
	for i in AT.size():
		while podium._time < AT[i]:
			await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
		var picture := get_viewport().get_texture().get_image()
		if picture.get_size() != Vector2i(1280, 720):
			picture.resize(1280, 720, Image.INTERPOLATE_LANCZOS)
		picture.save_png("%s/podium_%s_%s_%s_%d.png" % [out, cup, weather, time, i + 1])
	print("saved podium_%s_%s_%s in %d ms" % [cup, weather, time, Time.get_ticks_msec() - start])
	get_tree().quit()
