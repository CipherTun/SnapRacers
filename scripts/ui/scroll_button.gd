class_name ScrollButton
extends Button

## A button that can sit in a scrolling list. A drag that starts on it goes
## through to the list, so you can scroll by dragging anywhere, and the
## button only does its thing if the finger didn't move and the list didn't
## scroll. A touch that stops the list coasting doesn't count as a tap either.

signal tapped

const DRAG := 20.0
## A touch this soon after the list last moved is taken as stopping it, in
## milliseconds.
const STILL_FOR := 150

var _press := Vector2.ZERO
var _moved := false
var _list: ScrollContainer
var _scroll_at := Vector2.ZERO


func _init() -> void:
	mouse_filter = MOUSE_FILTER_PASS
	pressed.connect(func() -> void:
		if not _moved and not scrolled():
			tapped.emit())


func _ready() -> void:
	var up := get_parent()
	while up != null and not up is ScrollContainer:
		up = up.get_parent()
	_list = up
	if _list != null and not _list.has_meta("scrolled_at"):
		_list.set_meta("scrolled_at", 0)
		var mark := func(_value: float) -> void: _list.set_meta("scrolled_at", Time.get_ticks_msec())
		_list.get_v_scroll_bar().value_changed.connect(mark)
		_list.get_h_scroll_bar().value_changed.connect(mark)


## Whether the list has scrolled since the finger went down.
func scrolled() -> bool:
	if _list == null:
		return false
	return Vector2(_list.scroll_horizontal, _list.scroll_vertical).distance_to(_scroll_at) > 4.0


func _gui_input(event: InputEvent) -> void:
	var down: bool = (event is InputEventScreenTouch or event is InputEventMouseButton) and event.pressed
	if down:
		_press = event.position
		_moved = false
		if _list != null:
			_scroll_at = Vector2(_list.scroll_horizontal, _list.scroll_vertical)
			if Time.get_ticks_msec() - int(_list.get_meta("scrolled_at", 0)) < STILL_FOR:
				_moved = true
	elif event is InputEventScreenDrag and event.position.distance_to(_press) > DRAG:
		_moved = true
