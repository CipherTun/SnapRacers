extends Node

## Every screen with only a controller. From the button picked out first,
## the d-pad has to reach every button, slider and typing box on the screen,
## going by the same focus neighbours Godot moves along. Also the pure parts
## of the Steam Deck support: which controllers to listen to, and how the
## Deck and Game Mode are told apart.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . res://tests/pad_tour_test.tscn

var failures := 0
var host: Node


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func screen() -> Node:
	for i in range(host.get_child_count() - 1, -1, -1):
		var child := host.get_child(i)
		if not child.is_queued_for_deletion():
			return child
	return null


## The controls on a screen a controller should be able to reach.
static func reachable_kinds(root: Node) -> Array[Control]:
	var found: Array[Control] = []
	for node in root.find_children("*", "Control", true, false):
		var control := node as Control
		if control.focus_mode != Control.FOCUS_ALL or not control.is_visible_in_tree():
			continue
		if not (control is BaseButton or control is Slider or control is LineEdit):
			continue
		# Hidden behind a clipped scroll area still counts: focus scrolls to it.
		found.append(control)
	return found


## Everything the d-pad reaches from `start`.
static func walk(start: Control) -> Dictionary:
	var seen := {start: true}
	var todo: Array[Control] = [start]
	while not todo.is_empty():
		var at: Control = todo.pop_back()
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			# A slider takes left and right. A typing box doesn't, as the
			# d-pad isn't the arrow keys.
			if at is HSlider and side in [SIDE_LEFT, SIDE_RIGHT]:
				continue
			var next := at.find_valid_focus_neighbor(side)
			if next != null and not seen.has(next):
				seen[next] = true
				todo.append(next)
	return seen


func tour(what: String, show: Callable) -> void:
	show.call()
	await frames(4)
	var root := screen()
	if root == null:
		check(false, what + ": no screen")
		return
	if root.has_method("own_controls") and root.own_controls():
		check(true, what + ": has its own controller controls")
		return
	var first := PadFocus.first_button(root)
	check(first != null, what + ": something's picked out first")
	if first == null:
		return
	var seen := walk(first)
	var missed := reachable_kinds(root).filter(func(c: Control) -> bool: return not seen.has(c))
	var names := missed.map(func(c: Control) -> String:
		return "%s '%s' at %s" % [c.get_class(), c.text if "text" in c else "", c.get_global_rect().position])
	check(missed.is_empty(), "%s: the d-pad reaches all %d controls%s" % [what, seen.size(), "" if missed.is_empty() else ", missed " + ", ".join(names)])


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_pure()
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	PadFocus.using_pad = true
	await tour("main menu", Game.show_menu)
	await tour("editors", Game.show_editors)
	await tour("single player", Game.show_single_player)
	await tour("multiplayer", Game.show_multiplayer)
	await tour("cups", Game.show_cups)
	await tour("cups for two", Game.show_cups.bind(true))
	await tour("your cups", Game.show_your_cups)
	await tour("cup builder", Game.show_cup_builder)
	await tour("course grid", Game.show_course_grid.bind(Game.MODE_RACE, true, "baseplate"))
	await tour("kart picker", Game.show_kart_picker.bind(func(): pass, Game.show_menu, true))
	await tour("online", Game.show_online)
	await tour("driver builder", Game.show_driver)
	await tour("about", Game.show_about)
	Game.net.host(OfflineMultiplayerPeer.new())
	await tour("lobby", Game.show_lobby)
	var lobby: Lobby = screen()
	lobby._pick()
	await frames(3)
	_walk_all("lobby's course picker", lobby._picker)
	var picked := lobby._picker.gui_get_focus_owner()
	check(picked != null and lobby._picker_list.is_ancestor_of(picked), "the picker has a course picked out when it opens")
	await pad(JOY_BUTTON_B)
	check(not lobby._picker.visible and screen() is Lobby, "B closes it, and stays in the lobby")
	Game.net.leave()
	await _popups()
	await _touch_controls()
	await _other_keyboard()
	await _left_out()
	await _race_menu()
	Game.show_settings()
	await frames(4)
	var settings: SettingsScreen = screen()
	for tab in SettingsScreen.TABS.size():
		settings._show_tab(tab)
		await frames(3)
		var first := PadFocus.first_button(settings)
		var seen := walk(first)
		var missed := reachable_kinds(settings).filter(func(c: Control) -> bool: return not seen.has(c))
		var names := missed.map(func(c: Control) -> String: return "%s '%s'" % [c.get_class(), c.text if "text" in c else ""])
		check(missed.is_empty(), "settings %s: the d-pad reaches all %d controls%s" % [SettingsScreen.TABS[tab], seen.size(), "" if missed.is_empty() else ", missed " + ", ".join(names)])
	print("All pad tour checks passed." if failures == 0 else "%d pad tour checks failed." % failures)
	get_tree().quit(1 if failures > 0 else 0)


## Walks a part of a screen, like a popup, from its first button.
func _walk_all(what: String, root: Node) -> void:
	var first := PadFocus.first_button(root)
	if first == null:
		check(false, what + ": nothing to pick out")
		return
	var seen := walk(first)
	var missed := reachable_kinds(root).filter(func(c: Control) -> bool: return not seen.has(c))
	var names := missed.map(func(c: Control) -> String: return "%s '%s'" % [c.get_class(), c.text if "text" in c else ""])
	check(missed.is_empty(), "%s: the d-pad reaches all %d controls%s" % [what, seen.size(), "" if missed.is_empty() else ", missed " + ", ".join(names)])


## The race's own menu, opened with Start.
func _race_menu() -> void:
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.start_race(Game.TRACKS + "/peach_pit.json")
	var race: Race = null
	while race == null:
		await frames(1)
		race = screen() as Race
	while not race.started:
		await frames(10)
	race.open_menu(race.player)
	await frames(3)
	_walk_all("race menu", race._menus[race.player])
	race.leave()
	await frames(3)


func pad(button: JoyButton) -> void:
	for down in [true, false]:
		var event := InputEventJoypadButton.new()
		event.device = 0
		event.button_index = button
		event.pressed = down
		Input.parse_input_event(event)
		await frames(3)


## B closes the windows over a screen, and only them.
func _popups() -> void:
	Game.show_cups()
	await frames(4)
	var adding := AddWindow.open(screen(), "Add a cup")
	await frames(3)
	check(adding.gui_get_focus_owner() != null, "the add window has something picked out")
	await pad(JOY_BUTTON_B)
	check(not is_instance_valid(adding) or not adding.visible, "B closes the add window")
	check(screen() is CupGrid, "and stays on the cups")
	var sharing := ShareWindow.open({"name": "Test"}, screen())
	await frames(3)
	await pad(JOY_BUTTON_B)
	check(not is_instance_valid(sharing) or not sharing.visible, "B closes the share window")
	check(screen() is CupGrid, "and stays on the cups too")
	Game.show_cup_builder()
	await frames(4)
	var builder: CupBuilder = screen()
	builder._delete_dialog.popup_centered()
	await frames(3)
	await pad(JOY_BUTTON_B)
	check(not builder._delete_dialog.visible and screen() is CupBuilder, "B closes a dialog like Cancel")


## On a computer the touch controls wait for a touch, and step aside again
## for a controller, a stick or the keys. A click doesn't bring them back.
func _touch_controls() -> void:
	var touch := TouchControls.new()
	touch.size = Vector2(1280, 720)
	add_child(touch)
	touch.visible = TouchControls.shown_at_start()
	check(not touch.visible, "touch controls start hidden on a computer")
	var click := InputEventScreenTouch.new()
	click.device = InputEvent.DEVICE_ID_EMULATION
	click.pressed = true
	touch._input(click)
	check(not touch.visible, "a click doesn't bring them up")
	var finger := InputEventScreenTouch.new()
	finger.position = Vector2(5, 5)
	finger.pressed = true
	touch._input(finger)
	check(touch.visible, "a touch does")
	var stick := InputEventJoypadMotion.new()
	stick.axis = JOY_AXIS_TRIGGER_RIGHT
	stick.axis_value = 1.0
	touch._input(stick)
	check(not touch.visible, "and a trigger pushed hides them again")
	touch._input(finger)
	var key := InputEventKey.new()
	key.keycode = KEY_W
	key.pressed = true
	touch._input(key)
	check(not touch.visible, "and so does a key")
	touch.free()


## With the keyboard on the screen up, real keys still type, so Steam's own
## keyboard works as well.
func _other_keyboard() -> void:
	var was: String = Game.settings.get_value("player", "name", "")
	Game.show_settings()
	await frames(4)
	var box: LineEdit = screen().find_children("*", "LineEdit", true, false)[0]
	box.text = "Ab"
	box.grab_focus()
	await pad(JOY_BUTTON_A)
	var keys := get_tree().root.find_children("*", "PadKeyboard", true, false)
	check(not keys.is_empty(), "A on the name brings up the keyboard on the screen")
	for code in [KEY_Z, KEY_BACKSPACE, KEY_C]:
		for down in [true, false]:
			var key := InputEventKey.new()
			key.keycode = code
			key.unicode = 0 if code == KEY_BACKSPACE else String(OS.get_keycode_string(code)).to_lower().unicode_at(0)
			key.pressed = down
			Input.parse_input_event(key)
			await frames(2)
	check(box.text == "Abc", "and real keys type into the box while it's up (%s)" % box.text)
	for down in [true, false]:
		var enter := InputEventKey.new()
		enter.keycode = KEY_ENTER
		enter.pressed = down
		Input.parse_input_event(enter)
		await frames(2)
	keys = get_tree().root.find_children("*", "PadKeyboard", true, false).filter(func(k): return not k.is_queued_for_deletion())
	check(keys.is_empty() and screen() is SettingsScreen, "Enter is done")
	Game.set_setting("player", "name", was)


## A controller left out (Steam's copy of the Deck's) does nothing.
func _left_out() -> void:
	Controllers.ignored[5] = true
	var seen := []
	var listen := func(event: InputEvent) -> void:
		if event is InputEventJoypadButton and event.pressed:
			seen.append(event.device)
	get_tree().root.window_input.connect(listen)
	for device in [5, 0]:
		var event := InputEventJoypadButton.new()
		event.device = device
		event.button_index = JOY_BUTTON_A
		event.pressed = true
		Input.parse_input_event(event)
		await frames(2)
		event = event.duplicate()
		event.pressed = false
		Input.parse_input_event(event)
		await frames(2)
	get_tree().root.window_input.disconnect(listen)
	Controllers.ignored.clear()
	check(seen == [0], "a press on a left out controller comes through as nothing (%s)" % [seen])


func _pure() -> void:
	var deck := {"device": 0, "name": "Steam Deck", "vendor_id": 0x28de, "product_id": 0x1205}
	var steam := {"device": 1, "name": "Steam Virtual Gamepad", "vendor_id": 0x28de, "product_id": 0x11ff}
	var xbox := {"device": 2, "name": "Xbox Wireless Controller", "vendor_id": 0x045e, "product_id": 0x0b13}
	check(Controllers.ignored_pads([deck, steam]) == [1], "with the Deck's own pad and Steam's copy of it, Steam's is left out")
	check(Controllers.ignored_pads([steam, deck]) == [1], "whichever order they come in")
	check(Controllers.ignored_pads([steam]).is_empty(), "Steam's pad on its own is used")
	check(Controllers.ignored_pads([deck]).is_empty(), "and the Deck's on its own")
	check(Controllers.ignored_pads([steam, xbox]).is_empty(), "Steam's copy of another controller is used")
	var unnamed := {"device": 3, "name": "Steam Virtual Gamepad", "vendor_id": 0, "product_id": 0}
	check(Controllers.ignored_pads([deck, unnamed]) == [3], "Steam's pad goes by its name too")
	check(SteamDeck.deck_from("Valve", "Jupiter") and SteamDeck.deck_from("Valve\n", "Galileo\n"), "a Deck, LCD or OLED, by its firmware names")
	check(not SteamDeck.deck_from("Valve", "Index") and not SteamDeck.deck_from("ASUS", "Jupiter"), "and nothing else")
	check(SteamDeck.game_mode_from({"XDG_CURRENT_DESKTOP": "gamescope"}), "Game Mode by gamescope")
	check(SteamDeck.game_mode_from({"SteamGamepadUI": "1"}) and SteamDeck.game_mode_from({"SteamDeck": "1"}), "or Steam's own markers")
	check(not SteamDeck.game_mode_from({"XDG_CURRENT_DESKTOP": "KDE"}), "and not on a desktop")
	check(InputBindings.pad(ConfigFile.new(), 0, "gadget_1").has([InputBindings.BUTTON, JOY_BUTTON_PADDLE1, 1]), "R4 uses power-up 1")
	check(InputBindings.pad(ConfigFile.new(), 0, "gadget_2").has([InputBindings.BUTTON, JOY_BUTTON_PADDLE2, 1]), "and L4 power-up 2")
	var remapped := ConfigFile.new()
	InputBindings.set_pad(remapped, 0, "look_back", 0, [InputBindings.BUTTON, JOY_BUTTON_PADDLE1, 1])
	check(not InputBindings.pad(remapped, 0, "gadget_1").has([InputBindings.BUTTON, JOY_BUTTON_PADDLE1, 1]), "R4 given to something else leaves power-up 1")
	check(InputBindings.pad(remapped, 0, "gadget_1").has([InputBindings.BUTTON, JOY_BUTTON_RIGHT_SHOULDER, 1]), "which keeps RB")
