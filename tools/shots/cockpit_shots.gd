extends Node

## Pictures from the driver's eyes in a stock kart, with the AI driving. With
## "split", player 2's half watches player 1's kart from behind instead, and
## with "lap" it drives a whole lap first and takes one more. It needs a screen.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/cockpit_shots.tscn -- flathead [solo|split|lap] [out folder] [name]

const AT := [3.0, 9.0]

var host: Node


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var kart: String = args[0] if args.size() > 0 else "flathead"
	var split: bool = args.size() > 1 and args[1] == "split"
	var out: String = args[2] if args.size() > 2 else "res://build/shots"
	var name: String = args[3] if args.size() > 3 else kart
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	seed(1)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SIDE_BY_SIDE if split else Game.SOLO)
	Game.settings.set_value("race", "kart", kart)
	Game.settings.set_value("race", "player_two", "flathead")
	Game.settings.set_value("controls", "player_1", "buttons")
	Game.settings.set_value("controls", "player_2", "buttons")
	Game.settings.set_value("camera", "player_1", "driver")
	Game.settings.set_value("camera", "player_2", "chase")
	Game.racing_alone = not split
	Game.mode = Game.MODE_RACE
	Game.show_race(Game.TRACKS + "/peach_pit.json")
	var race: Race = null
	while race == null:
		await get_tree().process_frame
		for child in host.get_children():
			if child is Race:
				race = child
	for human in race.humans:
		var driver := AIDriver.new()
		driver.kart = human.kart
		driver.track = race.track
		race.add_child(driver)
		human.ai = driver
		human.kart.controls = driver.controls
	if split:
		# Player 2's camera follows player 1's kart, still culling as player 2.
		await get_tree().process_frame
		race.humans[1].camera.target = race.humans[0].kart
		race.humans[1].camera.snap()
	DirAccess.make_dir_recursive_absolute(out)
	for i in AT.size():
		while race.time < AT[i]:
			await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/%s_%d.png" % [out, name, i + 1])
	if args.size() > 1 and args[1] == "lap":
		var me: Race.Racer = race.humans[0]
		while me.progress.laps < 1:
			await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/%s_lap.png" % [out, name])
		print("lap done at %.1f s, view %s, %d parts lost" % [race.time, me.camera.view, me.kart.lost.size()])
	print("saved %s" % name)
	get_tree().quit()
