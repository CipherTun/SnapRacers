class_name Controllers
extends Node

## Which controller belongs to which player. A controller that's plugged in
## goes to the first player without one, preferring a player whose
## controller was this kind last time, so it comes back to the same player.
## The settings let you swap them round.
##
## With one player on their own, any controller drives (see
## LocalPlayerInput), so this matters for split screen and the menus.

signal changed
## A player's controller has come unplugged.
signal unplugged(person: int)

const PLAYERS := 2

## Where A, B, X and Y are. The game goes by where a button sits, A at the
## bottom, and a Switch controller has B there, so with the Switch layout A
## and B swap, and X and Y, to go by what's printed on them. Auto picks it
## from the controller's name.
const LAYOUTS := ["auto", "xbox", "switch"]
const LAYOUT_NAMES := {"auto": "Auto", "xbox": "Xbox", "switch": "Switch"}
const SWAPS := {JOY_BUTTON_A: JOY_BUTTON_B, JOY_BUTTON_B: JOY_BUTTON_A, JOY_BUTTON_X: JOY_BUTTON_Y, JOY_BUTTON_Y: JOY_BUTTON_X}
const NINTENDO := ["nintendo", "switch", "pro controller", "joy-con", "joycon"]

## Valve's vendor id, with the Deck's own controller and Steam's virtual
## pad, which repeats a controller's presses while Steam Input is on.
const VALVE := 0x28de
const DECK_PAD := 0x1205
const STEAM_PAD := 0x11ff

## Device ids of the controllers with their buttons swapped.
static var swapped := {}
## Device ids of controllers left out, so a press doesn't count twice (see
## ignored_pads).
static var ignored := {}

## Device id to player, 0 for player 1.
var owners := {}
var settings: ConfigFile


func _ready() -> void:
	Input.joy_connection_changed.connect(_on_connection)
	_find_ignored()
	for device in usable_joypads():
		_give(device)
	_find_swaps()
	# Swaps the buttons on each press before anything else in the game sees it.
	get_tree().root.window_input.connect(_swap_event)


## The button the game means for one Godot reports, or the other way round,
## since a swap goes both ways.
static func button(device: int, index: int) -> int:
	return SWAPS.get(index, index) if swapped.has(device) else index


## Whether a controller's called something that sounds like a Switch one.
static func sounds_like_switch(device_name: String) -> bool:
	var lower := device_name.to_lower()
	return NINTENDO.any(func(word: String) -> bool: return lower.contains(word))


func layout() -> String:
	return settings.get_value("controllers", "layout", "auto") if settings != null else "auto"


func set_layout(to: String) -> void:
	if settings != null:
		settings.set_value("controllers", "layout", to)
	_find_swaps()
	changed.emit()


## Whether this controller goes by the Switch layout, or with none, whether
## a controller would.
func is_switch(device: int) -> bool:
	if device == -1:
		return layout() == "switch"
	return swapped.has(device)


func _find_swaps() -> void:
	swapped.clear()
	for device in Input.get_connected_joypads():
		var kind := layout()
		if kind == "switch" or (kind == "auto" and sounds_like_switch(Input.get_joy_name(device))):
			swapped[device] = true


func _swap_event(event: InputEvent) -> void:
	# A left out controller's presses and pushes still come through, so
	# they're turned into nothing anything listens for.
	if (event is InputEventJoypadButton or event is InputEventJoypadMotion) and ignored.has(event.device):
		if event is InputEventJoypadButton:
			event.pressed = false
			event.button_index = JOY_BUTTON_INVALID
		else:
			event.axis_value = 0.0
		return
	var press := event as InputEventJoypadButton
	if press != null:
		press.button_index = button(press.device, press.button_index) as JoyButton


## Which of these controllers to leave out, given as dictionaries with
## "device", "name", "vendor_id" and "product_id". With Steam Input on, Steam
## can make a second copy of the Deck's own controls, which may carry the
## Deck's ids and name too. With more than one pad that looks like the Deck's,
## one is kept: the real one if there is one, then the lowest device id. Any
## other controller, Steam's virtual copy of it or not, is always kept.
static func ignored_pads(pads: Array) -> Array:
	var decks := pads.filter(_looks_like_deck)
	if decks.size() < 2:
		return []
	var keep: Dictionary = decks[0]
	for pad: Dictionary in decks:
		var better := _virtual(keep) and not _virtual(pad)
		var same := _virtual(keep) == _virtual(pad)
		if better or (same and int(pad.device) < int(keep.device)):
			keep = pad
	var out := []
	for pad: Dictionary in decks:
		if pad.device != keep.device:
			out.append(pad.device)
	out.sort()
	return out


## Whether a pad's ids or name say it's the Deck's own controls.
static func _looks_like_deck(pad: Dictionary) -> bool:
	return (int(pad.get("vendor_id", 0)) == VALVE and int(pad.get("product_id", 0)) == DECK_PAD) or str(pad.get("name", "")).to_lower().contains("steam deck")


## Whether a pad's Steam's virtual one, by its ids or name.
static func _virtual(pad: Dictionary) -> bool:
	return (int(pad.get("vendor_id", 0)) == VALVE and int(pad.get("product_id", 0)) == STEAM_PAD) or str(pad.get("name", "")).to_lower().contains("virtual")


## The controllers plugged in that the game listens to.
static func usable_joypads() -> Array[int]:
	var out: Array[int] = []
	for device in Input.get_connected_joypads():
		if not ignored.has(device):
			out.append(device)
	return out


func _find_ignored(gone := -1) -> void:
	var pads := []
	for device in Input.get_connected_joypads():
		var info := Input.get_joy_info(device)
		pads.append({"device": device, "name": Input.get_joy_name(device), "vendor_id": info.get("vendor_id", 0), "product_id": info.get("product_id", 0)})
	var now := {}
	for device in ignored_pads(pads):
		now[device] = true
	set_ignored(now, gone)


## Leaves out these controllers. One newly left out goes the same way as
## coming unplugged, and one that's usable again is handed out like one just
## plugged in. `gone` is a controller that's just been unplugged, so it isn't
## handed out.
func set_ignored(now: Dictionary, gone := -1) -> void:
	var was := ignored.duplicate()
	ignored.clear()
	ignored.merge(now)
	for device in ignored:
		if not was.has(device):
			_drop(device)
	for device in was:
		if not ignored.has(device) and device != gone:
			_give(device)


## The controller player `person` has, or -1.
func device_of(person: int) -> int:
	for device in owners:
		if owners[device] == person:
			return device
	return -1


## Whose a controller is, or -1.
func owner_of(device: int) -> int:
	return owners.get(device, -1)


## Gives a controller to a player. The one they had goes to whoever had this
## one, so it's a swap.
func give(device: int, person: int) -> void:
	var had := device_of(person)
	var was: int = owners.get(device, -1)
	owners[device] = person
	if had != -1 and had != device:
		if was == -1:
			owners.erase(had)
		else:
			owners[had] = was
	_remember()
	changed.emit()


## What kind of controller it is, the same for every one of that kind.
static func _guid(device: int) -> String:
	return Input.get_joy_guid(device) if Input.get_connected_joypads().has(device) else ""


## What a controller is called, like "Xbox Wireless Controller".
static func name_of(device: int) -> String:
	var name := Input.get_joy_name(device) if Input.get_connected_joypads().has(device) else ""
	return name if name != "" else "Controller %d" % (device + 1)


func _on_connection(device: int, connected: bool) -> void:
	_find_swaps()
	_find_ignored(-1 if connected else device)
	if connected:
		_give(device)
	else:
		_drop(device)
	changed.emit()


## Takes a controller off its player, who's told it came unplugged.
func _drop(device: int) -> void:
	var person: int = owners.get(device, -1)
	owners.erase(device)
	if person != -1:
		unplugged.emit(person)


func _give(device: int) -> void:
	if owners.has(device) or ignored.has(device):
		return
	var guid := _guid(device)
	var free := []
	for person in PLAYERS:
		if device_of(person) == -1:
			free.append(person)
	if free.is_empty():
		return
	var person: int = free[0]
	for wants in free:
		if settings != null and settings.get_value("controllers", "player_%d" % (wants + 1), "") == guid:
			person = wants
			break
	owners[device] = person
	_remember()


func _remember() -> void:
	if settings == null:
		return
	for person in PLAYERS:
		var device := device_of(person)
		if device != -1:
			settings.set_value("controllers", "player_%d" % (person + 1), _guid(device))
