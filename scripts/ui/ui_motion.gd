class_name UiMotion
extends RefCounted

## Short tweens for the menus: a new screen fades in, buttons pop when
## they're picked out or pressed, and popups grow open. Nothing moves in the
## headless tests or anywhere in a race, and none of it touches race timing.
## Tweens only, so it's the same on the phone and the web.

## Durations in seconds.
const FADE := 0.16
const POP := 0.14
const PRESS := 0.14
const GROW := 0.14
const POP_SCALE := 1.05
const PRESS_SCALE := 0.95
## How big a popup starts, against its full size.
const GROW_FROM := 0.88


## Whether `node` can move: there's a screen, and it isn't in a race (other
## than the standings over the podium).
static func enabled(node: Node) -> bool:
	if DisplayServer.get_name() == "headless" or node == null or not node.is_inside_tree():
		return false
	var up := node
	while up != null:
		# The standings over the podium move like any other menu.
		if up is GrandPrixStandings:
			return true
		if up is Race:
			return false
		up = up.get_parent()
	return true


## Fades a new screen in over `backdrop`, which is shown until it's in.
## Screens that aren't Controls, like the garage, just appear.
static func open_screen(screen: Node, backdrop: CanvasLayer) -> void:
	if not screen is Control or not enabled(screen):
		return
	var control := screen as Control
	control.modulate.a = 0.0
	backdrop.visible = true
	var tween := control.create_tween()
	tween.tween_property(control, "modulate:a", 1.0, FADE).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.finished.connect(func() -> void:
		if is_instance_valid(backdrop):
			backdrop.visible = false)


## A small pop when a button's picked out with a controller or the keys.
static func pop(button: Control) -> void:
	if not PadFocus.using_pad or not enabled(button):
		return
	var tween := _scale_tween(button)
	tween.tween_property(button, "scale", Vector2.ONE * POP_SCALE, POP * 0.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(button, "scale", Vector2.ONE, POP * 0.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


## A small dip when a button's pressed. It comes back by itself, so a press
## that ends somewhere else can't leave it small.
static func press(button: Control) -> void:
	if not enabled(button):
		return
	var tween := _scale_tween(button)
	tween.tween_property(button, "scale", Vector2.ONE * PRESS_SCALE, PRESS * 0.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(button, "scale", Vector2.ONE, PRESS * 0.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


## A scale tween about the button's centre, stopping any it already has.
static func _scale_tween(button: Control) -> Tween:
	var old: Variant = button.get_meta("scale_tween") if button.has_meta("scale_tween") else null
	if old is Tween and old.is_valid():
		old.kill()
	button.pivot_offset = button.size * 0.5
	var tween := button.create_tween()
	button.set_meta("scale_tween", tween)
	return tween


## Has popups and dialogs grow open from now on. Call it with each node
## that's added to the tree.
static func watch(node: Node) -> void:
	if not (node is PopupPanel or node is AcceptDialog) or node.has_meta("grows"):
		return
	node.set_meta("grows", true)
	var window := node as Window
	window.about_to_popup.connect(func() -> void: grow(window))


## Grows a popup open from a little smaller about its middle. An embedded
## window can't be scaled itself, so its canvas is.
static func grow(window: Window) -> void:
	if not enabled(window):
		return
	var old: Variant = window.get_meta("grow_tween") if window.has_meta("grow_tween") else null
	if old is Tween and old.is_valid():
		old.kill()
	var scale_to := func(s: float) -> void:
		window.canvas_transform = Transform2D(0.0, Vector2(s, s), 0.0, Vector2(window.size) * (1.0 - s) * 0.5)
	# Deferred, as about_to_popup comes before the window takes its new size.
	scale_to.call_deferred(GROW_FROM)
	var tween := window.create_tween()
	window.set_meta("grow_tween", tween)
	tween.tween_method(scale_to, GROW_FROM, 1.0, GROW).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.finished.connect(func() -> void: window.canvas_transform = Transform2D.IDENTITY)
