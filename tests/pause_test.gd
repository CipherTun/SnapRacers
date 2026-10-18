extends Node

## The menu in a race. In a single player race it pauses everything, its
## settings work straight away, Resume carries on and Quit leaves. Esc opens
## and closes it. In split screen either player pauses it for both and
## either can carry on.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . res://tests/pause_test.tscn

var failures := 0
var host: Node


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func race_on_screen() -> Race:
	for child in host.get_children():
		if child is Race and not child.is_queued_for_deletion():
			return child
	return null


func start(split: String) -> Race:
	# Set this for the run without saving over what was last picked.
	Game.settings.set_value("race", "split", split)
	Game.settings.set_value("race", "kart", Game.OWN_KART)
	var before := race_on_screen()
	Game.start_race(Game.TRACKS + "/peach_pit.json")
	var race: Race = null
	while race == null or race == before:
		await get_tree().process_frame
		race = race_on_screen()
	while not race.started:
		await frames(10)
	await frames(60)
	return race


## Taps a button through the screen, wherever its half is and however it's
## turned.
func tap(button: Control) -> void:
	var at := button.get_global_transform_with_canvas() * (button.size * 0.5)
	var holder := button.get_viewport().get_parent()
	if holder is SubViewportContainer:
		at = holder.get_global_transform_with_canvas() * (at * holder.stretch_shrink)
	for down in [true, false]:
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = down
		event.position = at
		event.global_position = at
		# In the screen's own units, since a headless window has no size.
		get_viewport().push_input(event, true)
		await frames(1)
	await frames(2)


func pad(device: int, index: JoyButton) -> void:
	for down in [true, false]:
		var event := InputEventJoypadButton.new()
		event.device = device
		event.button_index = index
		event.pressed = down
		Input.parse_input_event(event)
		Input.flush_buffered_events()
		await frames(2)


func _ready() -> void:
	# This keeps going while the race is paused.
	process_mode = Node.PROCESS_MODE_ALWAYS
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	var map_was := Game.map_view(0)
	var camera_was := Game.camera_view(0)
	var split_was := Game.split()

	var race := await start(Game.SOLO)
	var me := race.humans[0]
	var hud: RaceHud = me.hud
	var menu_button: IconButton = hud._menu
	check(menu_button.visible and menu_button.picture == "pause", "there's a menu button at the top")
	menu_button.pressed.emit()
	await frames(2)
	check(race.menu_open(me) and get_tree().paused, "it opens the menu and pauses the race")
	var time := race.time
	var at := me.kart.global_position
	await frames(60)
	check(race.time == time and me.kart.global_position.is_equal_approx(at), "nothing moves while it's paused (%.2f s, %.2f m)" % [race.time - time, me.kart.global_position.distance_to(at)])
	var menu: RaceMenu = race._menus[me]
	check(menu.can_restart and menu.find_children("*", "Button", true, false).any(func(b): return b.text == "QUIT THE RACE"), "with Restart and Quit in it")
	var mode := hud.map.mode
	menu._next_map()
	check(hud.map.mode != mode and Game.map_view(0) == hud.map.mode, "changing the map there changes it straight away")
	var view: String = me.camera.view
	menu._camera_button.pressed.emit()
	check(me.camera.view != view, "and the camera too")
	menu.resume_pressed.emit()
	await frames(30)
	check(not race.menu_open(me) and not get_tree().paused and race.time > time, "Resume carries on")

	race.go_back()
	await frames(2)
	check(race.menu_open(me) and get_tree().paused, "Esc opens it")
	race.go_back()
	await frames(2)
	check(not race.menu_open(me) and not get_tree().paused, "and closes it again")

	# A controller coming unplugged pauses with the menu open.
	Game.controllers._on_connection(21, true)
	Game.controllers.give(21, 0)
	Game.controllers._on_connection(21, false)
	await frames(2)
	check(race.menu_open(me) and get_tree().paused, "unplugging the controller opens the menu and pauses")
	race._menus[me].quit_pressed.emit()
	await frames(5)
	check(race_on_screen() == null and not get_tree().paused, "Quit leaves the race, and nothing's paused after")

	# Split screen pauses for both, from either player.
	for split in [Game.SIDE_BY_SIDE, Game.FACE_TO_FACE]:
		print("-- %s" % split)
		race = await start(split)
		var first := race.humans[0]
		var second := race.humans[1]
		Game.controllers._on_connection(22, true)
		Game.controllers.give(22, 0)
		Game.controllers._on_connection(23, true)
		Game.controllers.give(23, 1)
		await frames(2)
		await tap(second.hud._menu)
		check(race.menu_open(second) and get_tree().paused and not race._shared_map.visible, "player 2's menu button pauses it, and the map between the halves goes")
		race.go_back()
		await frames(5)
		race.open_menu(second)
		await frames(2)
		check(race.menu_open(second) and race.menu_open(first) and get_tree().paused, "player 2 opening the menu pauses the race, with a menu for each")
		var own: RaceMenu = race._menus[second]
		check(own.get_viewport() == second.hud.get_viewport() and own.focus_on_open and not race._menus[first].focus_on_open, "player 2's is in their own half")
		check(own.pauses and own.can_restart, "it says Paused and has Restart in a single race")
		if split == Game.FACE_TO_FACE:
			var holder := own.get_viewport().get_parent() as Control
			check(is_equal_approx(holder.rotation, PI), "face to face it's turned round to player 2")
		time = race.time
		var places := race.racers.map(func(r): return r.kart.global_position)
		await frames(60)
		var still := true
		for i in race.racers.size():
			still = still and race.racers[i].kart.global_position.is_equal_approx(places[i])
		check(race.time == time and still, "the clock and every kart stop")
		check(not first.input.can_process() and not second.input.can_process(), "and neither player's controls drive")
		var ai: Array = race.racers.filter(func(r): return r.ai != null)
		check(not ai.is_empty() and ai.all(func(r): return not r.ai.can_process()) and not first.kart.sound.can_process(), "nor the AI, and kart sounds pause")
		check(not second.camera.can_process() and not first.camera.can_process(), "the cameras pause too")
		# Tapping Resume in player 2's half, turned round or not.
		await tap(own._resume)
		check(not race.menu_open(first) and not race.menu_open(second) and not get_tree().paused and race._shared_map.visible, "tapping Resume in player 2's half carries on for both")
		await frames(30)
		check(race.time > time, "and the clock goes again")

		first.hud._menu.pressed.emit()
		await frames(2)
		check(race.menu_open(first) and race.menu_open(second) and get_tree().paused, "player 1's menu button pauses it too")
		await pad(23, JOY_BUTTON_START)
		check(not race.menu_open(first) and not race.menu_open(second) and not get_tree().paused, "and Start on player 2's controller carries on")
		await frames(10)
		check(not race.menu_open(second) and not get_tree().paused, "without opening it again")
		race.go_back()
		await frames(2)
		check(race.menu_open(first) and get_tree().paused, "Esc pauses it")
		await pad(22, JOY_BUTTON_B)
		check(not get_tree().paused, "and B on player 1's controller carries on")
		for device in [22, 23]:
			Game.controllers._on_connection(device, false)
		await frames(2)
		check(race.menu_open(first) and get_tree().paused, "a controller coming unplugged pauses with that player's menu open")
		race.go_back()
		race.leave()
		await frames(5)

	# The split goes back first, since putting the views back saves.
	Game.settings.set_value("race", "split", split_was)
	Game.set_map_view(0, map_was)
	Game.set_camera_view(0, camera_was)
	print("All pause checks passed." if failures == 0 else "%d pause checks failed." % failures)
	get_tree().quit(1 if failures > 0 else 0)
