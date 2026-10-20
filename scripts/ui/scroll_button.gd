class_name ScrollButton
extends Button

## A button that can sit in a scrolling list. A drag that starts on it goes
## through to the list, so you can scroll by dragging anywhere, and a finger
## or mouse click only does its thing if it didn't move and the list didn't
## scroll. A touch that stops the list coasting doesn't count as a tap either.
## A controller or key press always counts, even if the list has scrolled.

signal tapped

const DRAG := 20.0
## A touch this soon after the list last moved is taken as stopping it, in
## milliseconds.
const STILL_FOR := 150

var _press := Vector2.ZERO
var _moved := false
var _pointer := false
var _list: ScrollContainer
var _scroll_at := Vector2.ZERO


func _init() -> void:
	mouse_filter = MOUSE_FILTER_PASS
	pressed.connect(_emit_tapped)


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


func _emit_tapped() -> void:
	var skip := _pointer and (_moved or scrolled())
	_pointer = false
	_moved = false
	if skip:
		return
	tapped.emit()


func _gui_input(event: InputEvent) -> void:
	var down: bool = (event is InputEventScreenTouch and event.pressed) \
			or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT)
	if down:
		_press = event.position
		_moved = false
		_pointer = true
		if _list != null:
			_scroll_at = Vector2(_list.scroll_horizontal, _list.scroll_vertical)
			if Time.get_ticks_msec() - int(_list.get_meta("scrolled_at", 0)) < STILL_FOR:
				_moved = true
	elif event is InputEventScreenDrag and event.position.distance_to(_press) > DRAG:
		_moved = true
	elif event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_LEFT \
			and event.position.distance_to(_press) > DRAG:
		_moved = true
