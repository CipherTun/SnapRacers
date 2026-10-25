class_name CourseOutlineView
extends Control

## A course's layout drawn from above, fitted into the space it's given, for the
## cup and course cards. Higher road is drawn over lower road, so a bridge
## crosses over what's under it. There's a tick for the start line and a ring
## where there's a loop or a corkscrew.
##
## An outline that has to be worked out is left for a later frame, and only
## one is worked out each frame, so a screen full of them never stalls.
##
## Antialiased lines are slow on phone GPUs, and a screen of cards has dozens,
## so each outline is drawn once into a picture at the screen's pixel size and
## kept. It's drawn as lines only until its picture is ready.

const EDGE := Color(0.0, 0.0, 0.0, 0.5)
const ROAD := Color(1.0, 1.0, 1.0, 0.9)
## How much higher one stretch of road has to be to be drawn on top.
const LEVEL := 2.0
## Most pictures kept before they're all dropped.
const MOST_PICTURES := 300

var path := ""
## The colour for the start line and the loops.
var colour := MenuStyle.ACCENT
## How thick the road is drawn, in pixels.
var thickness := 3.0

var _outline := {}
static var _worked_out_on := -1
## Pictures of outlines by _picture_key(), and the ones being made.
static var _pictures := {}
static var _making := {}
## The pictures were drawn over clear black, so their colours are already
## multiplied by their alpha.
static var _premultiplied: CanvasItemMaterial


func _init(course := "", tint := MenuStyle.ACCENT) -> void:
	path = course
	colour = tint
	mouse_filter = MOUSE_FILTER_IGNORE


func _ready() -> void:
	resized.connect(queue_redraw)
	texture_filter = TEXTURE_FILTER_NEAREST
	if path != "" and CourseOutline.is_ready(path):
		_outline = CourseOutline.of(path)
		set_process(false)
	else:
		set_process(true)


func _process(_delta: float) -> void:
	if path == "":
		set_process(false)
		return
	if _outline.is_empty():
		var frame := Engine.get_process_frames()
		if not CourseOutline.is_ready(path):
			if _worked_out_on == frame:
				return
			_worked_out_on = frame
		_outline = CourseOutline.of(path)
		queue_redraw()
		return
	# Waiting for this outline's picture.
	if _pictures.has(_picture_key()):
		set_process(false)
		queue_redraw()


## How many screen pixels there are to one of this control's.
func _scale() -> float:
	var to_screen := get_viewport().get_final_transform() * get_global_transform_with_canvas()
	return maxf(to_screen.get_scale().x, 0.01)


func _pixels() -> Vector2i:
	return Vector2i((size * _scale()).round())


func _picture_key() -> String:
	var pixels := _pixels()
	return "%s %d %d %s %s" % [CourseOutline._key(path), pixels.x, pixels.y, colour.to_html(), thickness]


func _draw() -> void:
	if _outline.is_empty():
		return
	var pixels := _pixels()
	if pixels.x < 1 or pixels.y < 1:
		return
	var key := _picture_key()
	var picture: Texture2D = _pictures.get(key)
	if picture != null:
		if _premultiplied == null:
			_premultiplied = CanvasItemMaterial.new()
			_premultiplied.blend_mode = CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA
		if material != _premultiplied:
			material = _premultiplied
		draw_texture_rect(picture, Rect2(Vector2.ZERO, Vector2(pixels) / _scale()), false)
		return
	if material != null:
		material = null
	_paint(self, _outline, size, 1.0, thickness, colour)
	# The headless tests have no GPU to draw pictures with.
	if not _making.has(key) and DisplayServer.get_name() != "headless":
		_making[key] = true
		_make_picture.call_deferred(key, _outline, size, _scale(), thickness, colour, get_tree().root)
	set_process(true)


## Draws the outline once in a viewport of its own, keeps what it drew and lets
## the viewport go.
static func _make_picture(key: String, outline: Dictionary, area: Vector2, scale: float, width: float, tint: Color, root: Node) -> void:
	var viewport := PictureMaker.new()
	viewport.key = key
	viewport.size = Vector2i((area * scale).round())
	var painter := Node2D.new()
	painter.draw.connect(func() -> void: _paint(painter, outline, area, scale, width, tint))
	viewport.add_child(painter)
	root.add_child(viewport)


static func _keep(key: String, image: Image) -> void:
	_making.erase(key)
	if image == null or image.is_empty():
		return
	if _pictures.size() >= MOST_PICTURES:
		_pictures.clear()
	_pictures[key] = ImageTexture.create_from_image(image)


## Draws the outline into `area` on `item`, `scale` times as big.
static func _paint(item: CanvasItem, outline: Dictionary, area: Vector2, scale: float, width: float, tint: Color) -> void:
	item.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * scale)
	var to_view := CourseOutline.fit(outline, Rect2(Vector2.ZERO, area), width * 2.0 + 2.0)
	var line: PackedVector2Array = to_view * (outline.line as PackedVector2Array)
	var heights: PackedFloat32Array = outline.heights
	# The road in stretches at each level, drawn from the lowest up.
	var levels := {}
	var low := INF
	for h in heights:
		low = minf(low, h)
	var run := PackedVector2Array()
	var run_level := -1
	for i in line.size() - 1:
		var level := floori((maxf(heights[i], heights[i + 1]) - low) / LEVEL)
		if level != run_level and run.size() > 0:
			levels.get_or_add(run_level, []).append(run)
			run = PackedVector2Array([line[i]])
		elif run.is_empty():
			run.append(line[i])
		run_level = level
		run.append(line[i + 1])
	if run.size() > 1:
		levels.get_or_add(run_level, []).append(run)
	var order := levels.keys()
	order.sort()
	for level in order:
		for stretch in levels[level]:
			item.draw_polyline(stretch, EDGE, width * 2.2, true)
		for stretch in levels[level]:
			item.draw_polyline(stretch, ROAD, width, true)
	for at in outline.loops:
		item.draw_arc(to_view * at, width * 2.4, 0.0, TAU, 20, tint, width * 0.8, true)
	var start: Vector2 = to_view * (outline.start as Vector2)
	var across: Vector2 = outline.across * width * 2.6
	item.draw_line(start - across, start + across, tint, width * 1.2, true)
	item.draw_set_transform(Vector2.ZERO)


## A viewport that draws once, hands what it drew to _keep() a couple of
## frames later, since the frame it's added in may already have been drawn,
## and then frees itself.
class PictureMaker extends SubViewport:
	var key := ""
	var _frames := 0

	func _init() -> void:
		transparent_bg = true
		disable_3d = true
		render_target_update_mode = UPDATE_ONCE

	func _process(_delta: float) -> void:
		_frames += 1
		if _frames < 2:
			return
		CourseOutlineView._keep(key, get_texture().get_image())
		set_process(false)
		queue_free()
