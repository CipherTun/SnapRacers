extends Node

## Times the frames when a cup's podium goes up, to find shader stalls. It
## starts the game with the splash's warm-up (or without, with "cold"), races
## the cup's last course in the weather and time asked for, ends it and
## prints the longest frame in each part of the show: as the podium goes up,
## the trophy coming down and the confetti. It needs a screen. To see what a
## first launch does, give it an empty data folder and turn off the driver's
## own shader cache:
##   XDG_DATA_HOME=<empty folder> __GL_SHADER_DISK_CACHE=0 DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/perf/podium_perf.tscn -- baseplate storm night [cold]

## The parts of the show, from these times in seconds after it goes up.
const PARTS := [["going up", 0.0], ["jumping", 1.0], ["trophy", Podium.TROPHY_FROM], ["confetti", Podium.TROPHY_IN], ["holding", Podium.TROPHY_IN + 1.0]]

var host: Node


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var cup: String = args[0] if args.size() > 0 else "baseplate"
	var weather: String = args[1] if args.size() > 1 else "storm"
	var time: String = args[2] if args.size() > 2 else "night"
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	host = Node.new()
	add_child(host)
	var warm := not args.has("cold")
	var from := Time.get_ticks_msec()
	Game.start(host, warm)
	while warm and not _showing(MainMenu):
		await get_tree().process_frame
	print("splash took %d ms" % (Time.get_ticks_msec() - from))
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "weather", weather)
	Game.settings.set_value("race", "time", time)
	Game.start_grand_prix(cup)
	Game.grand_prix.round = Game.grand_prix.track_ids().size() - 1
	Game.track_path = Game.grand_prix.track_path()
	while not _showing(Race):
		await get_tree().process_frame
	var race: Race = host.get_children().filter(func(c): return c is Race)[0]
	# Long enough for the race's own first frames to be over.
	for i in 180:
		await get_tree().process_frame
	print("on %s, %s at %s, lamp %s" % [race.track.name, race.conditions.weather, race.conditions.time, race.conditions.beams()])
	var order := race.racers.map(func(r): return r.name)
	var was := Time.get_ticks_usec()
	Game.finish_grand_prix_race(order)
	var podium: Podium = race.podium
	var longest := []
	longest.resize(PARTS.size())
	longest.fill(0.0)
	var all := 0.0
	while is_instance_valid(podium) and podium._time < Podium.LENGTH - 0.5:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		var took := (now - was) / 1000.0
		was = now
		var part := 0
		for i in PARTS.size():
			if podium._time >= PARTS[i][1]:
				part = i
		longest[part] = maxf(longest[part], took)
		all = maxf(all, took)
	for i in PARTS.size():
		print("  %-9s longest frame %6.1f ms" % [PARTS[i][0], longest[i]])
	print("longest frame on the podium %.1f ms" % all)
	get_tree().quit()


func _showing(type: Variant) -> bool:
	return host.get_children().any(func(c): return is_instance_of(c, type))
