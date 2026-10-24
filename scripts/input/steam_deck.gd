class_name SteamDeck
extends RefCounted

## Tells whether the game's on a Steam Deck, and whether it's in SteamOS's
## Game Mode, and sizes the window to match: full screen in Game Mode, and a
## 1280x800 window, the Deck's own screen size, on the Deck's desktop.
##
## SNAPRACERS_DECK=1 and SNAPRACERS_GAMEMODE=1 pretend on another computer,
## and =0 turns either off.

## The Deck's product names in its firmware: Jupiter for the LCD one,
## Galileo for the OLED one.
const PRODUCTS := ["Jupiter", "Galileo"]
const DECK_SCREEN := Vector2i(1280, 800)


static func is_deck() -> bool:
	var fake := OS.get_environment("SNAPRACERS_DECK")
	if fake != "":
		return fake == "1"
	if OS.get_name() != "Linux":
		return false
	return deck_from(_read("/sys/class/dmi/id/sys_vendor"), _read("/sys/class/dmi/id/product_name"))


static func game_mode() -> bool:
	var fake := OS.get_environment("SNAPRACERS_GAMEMODE")
	if fake != "":
		return fake == "1"
	var env := {}
	for name in ["XDG_CURRENT_DESKTOP", "SteamGamepadUI", "SteamDeck"]:
		env[name] = OS.get_environment(name)
	return game_mode_from(env)


## Whether the firmware's vendor and product names are a Deck's.
static func deck_from(vendor: String, product: String) -> bool:
	return vendor.strip_edges() == "Valve" and PRODUCTS.has(product.strip_edges())


## Whether these environment variables mean Game Mode: gamescope is Game
## Mode's compositor, and Steam sets the other two for what it starts there.
static func game_mode_from(env: Dictionary) -> bool:
	return env.get("XDG_CURRENT_DESKTOP", "") == "gamescope" or env.get("SteamGamepadUI", "") != "" or env.get("SteamDeck", "") != ""


## Full screen in Game Mode, and a window the size of the Deck's screen on
## its desktop. Anywhere else the window's left as it is. Goes through the
## Window, so the game's view follows the new size.
static func fit_window(window: Window) -> void:
	if not OS.has_feature("pc") or DisplayServer.get_name() == "headless":
		return
	if game_mode():
		window.mode = Window.MODE_FULLSCREEN
	elif is_deck():
		window.mode = Window.MODE_WINDOWED
		window.size = DECK_SCREEN
		var screen := DisplayServer.screen_get_usable_rect(window.current_screen)
		window.position = screen.position + ((screen.size - DECK_SCREEN) / 2).max(Vector2i.ZERO)


static func _read(path: String) -> String:
	return FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else ""
