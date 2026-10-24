class_name RaceWindow
extends Control

## The slanted window onto a race beside the main menu's buttons, with the
## course's name on a red ribbon. It's a still taken once by
## tools/shots/menu_still.gd, so the menu costs no more to draw than a picture.
## It sits on the right of the screen and keeps clear of `beside`.

const PICTURE := preload("res://art/ui/menu_race.jpg")
## The course the still was taken on.
const COURSE := "windsurf_way"
## How far it runs off the right edge.
const OFF_EDGE := 60.0

## What it keeps to the right of, like the column of buttons.
var beside: Control

var _name := ""


func _init() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	anchor_left = 0.5
	anchor_right = 1.0
	anchor_top = 0.2
	anchor_bottom = 0.88
	offset_right = OFF_EDGE


func _ready() -> void:
	var file := FileAccess.open(Tracks.path_of(COURSE), FileAccess.READ)
	if file != null:
		var data: Variant = JSON.parse_string(file.get_as_text())
		if data is Dictionary:
			_name = str(data.get("name", "")).to_upper()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _process(_delta: float) -> void:
	# Clear of the buttons, wherever a camera hole has pushed them.
	var left := 0.0
	if beside != null and is_instance_valid(beside):
		var row := beside.get_global_rect()
		left = maxf(0.0, row.end.x + 30.0 - get_parent_area_size().x * anchor_left)
	if not is_equal_approx(offset_left, left):
		offset_left = left


func _draw() -> void:
	var window := Rect2(Vector2.ZERO, Vector2(size.x, size.y - 16.0))
	if window.size.x < 100.0 or window.size.y < 100.0:
		return
	var corners := UiKit.slant_points(window)
	var shadow := PackedVector2Array()
	for at in corners:
		shadow.append(at + Vector2(10, 10))
	draw_colored_polygon(shadow, UiKit.SHADOW_COLOUR)
	# The picture fills the window, cut down at the sides or top and bottom
	# to keep its shape, with the kart a little under the middle.
	var shape := window.size.x / window.size.y
	var picture := Vector2(PICTURE.get_size()).aspect()
	var part := Rect2(0, 0, 1, 1)
	if shape > picture:
		part.size.y = picture / shape
		part.position.y = (1.0 - part.size.y) * 0.6
	else:
		part.size.x = shape / picture
		part.position.x = (1.0 - part.size.x) * 0.5
	var uvs := PackedVector2Array()
	for at in corners:
		uvs.append(part.position + part.size * (at / window.size))
	draw_polygon(corners, PackedColorArray([Color.WHITE]), uvs, PICTURE)
	var edge := corners.duplicate()
	edge.append(corners[0])
	draw_polyline(edge, UiKit.YELLOW, 5.0, true)
	if _name != "":
		var font := UiKit.font("heading")
		var wide := font.get_string_size(_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 26).x + 60.0
		var ribbon := Rect2(window.size.y * UiKit.LEAN * 0.25 + 30.0, size.y - 46.0, wide, 46.0)
		UiKit.draw_slant(self, Rect2(ribbon.position + UiKit.SHADOW, ribbon.size), UiKit.SHADOW_COLOUR)
		UiKit.draw_slant(self, ribbon, UiKit.RED)
		var base := ribbon.get_center().y + (font.get_ascent(26) - font.get_descent(26)) * 0.5
		draw_string(font, Vector2(ribbon.position.x + 28.0, base), _name, HORIZONTAL_ALIGNMENT_LEFT, -1, 26, UiKit.WHITE)
