class_name SlantBox
extends StyleBox

## A box leaning like the type, for the arcade look. The whole shape stays
## inside the control's rect, so a slanted button never hangs over the edge
## of a list. It can have a hard drop shadow, an edge line, a stripe down the
## left side and one along the bottom, and `grow` draws it bigger than the
## rect, for a focus ring. Made of skewed StyleBoxFlats, so it's smooth in
## the Compatibility renderer too.

## How far the top leans right for each pixel of height.
@export var lean := 0.3:
	set(value):
		lean = value
		_dirty()
@export var fill := Color.BLACK:
	set(value):
		fill = value
		_dirty()
@export var edge := Color.TRANSPARENT:
	set(value):
		edge = value
		_dirty()
@export var edge_width := 0:
	set(value):
		edge_width = value
		_dirty()
## Where the hard shadow sits, in pixels. Zero for none.
@export var shadow := Vector2.ZERO:
	set(value):
		shadow = value
		_dirty()
@export var shadow_colour := Color(0, 0, 0, 0.5):
	set(value):
		shadow_colour = value
		_dirty()
## A stripe down the left side, as wide as `stripe_width`.
@export var stripe := Color.TRANSPARENT:
	set(value):
		stripe = value
		_dirty()
@export var stripe_width := 0.0:
	set(value):
		stripe_width = value
		_dirty()
## A stripe along the bottom, as high as `underline_height`.
@export var underline := Color.TRANSPARENT:
	set(value):
		underline = value
		_dirty()
@export var underline_height := 0.0:
	set(value):
		underline_height = value
		_dirty()
## Past this height the box leans less, so its edge moves across no more than
## it would at this height and stays clear of the padding (see UiKit.pad()).
## Zero leans by `lean` at any height.
@export var lean_height := 0.0:
	set(value):
		lean_height = value
		_dirty()
## Pixels drawn outside the rect all round.
@export var grow := 0.0:
	set(value):
		grow = value
		_dirty()

var _face: StyleBoxFlat
var _shade: StyleBoxFlat
var _stripe: StyleBoxFlat
var _under: StyleBoxFlat


func _dirty() -> void:
	_face = null
	emit_changed()


func _build() -> void:
	_face = _flat(fill)
	_face.draw_center = fill.a > 0.0
	if edge_width > 0 and edge.a > 0.0:
		_face.border_color = edge
		_face.set_border_width_all(edge_width)
	_shade = _flat(shadow_colour) if shadow != Vector2.ZERO and shadow_colour.a > 0.0 else null
	_stripe = _flat(stripe) if stripe_width > 0.0 and stripe.a > 0.0 else null
	_under = _flat(underline) if underline_height > 0.0 and underline.a > 0.0 else null


func _flat(colour: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = colour
	box.anti_aliasing = true
	return box


func _draw(to_canvas_item: RID, rect: Rect2) -> void:
	if _face == null:
		_build()
	rect = rect.grow(grow)
	var tilt := lean
	if lean_height > 0.0 and rect.size.y > lean_height + grow * 2.0:
		tilt = lean * (lean_height + grow * 2.0) / rect.size.y
	for box in [_face, _shade, _stripe, _under]:
		if box != null:
			box.skew = Vector2(tilt, 0.0)
	# A skewed StyleBoxFlat hangs half its lean over each side, so it's drawn
	# that much narrower.
	var shift := rect.size.y * tilt * 0.5
	var inner := rect.grow_individual(-shift, 0.0, -shift, 0.0)
	if _shade != null:
		_shade.draw(to_canvas_item, Rect2(inner.position + shadow, inner.size))
	_face.draw(to_canvas_item, inner)
	var inset := float(edge_width)
	if _stripe != null:
		_stripe.draw(to_canvas_item, _part(inner, tilt, inset + 2.0, inset + 2.0 + stripe_width, inset + 2.0, inner.size.y - inset - 2.0))
	if _under != null:
		_under.draw(to_canvas_item, _part(inner, tilt, 0.0, inner.size.x, inner.size.y - underline_height, inner.size.y))


## The rect for a skewed piece of the face, from `x0` to `x1` across it and
## `y0` to `y1` down, both measured as if it didn't lean.
func _part(inner: Rect2, tilt: float, x0: float, x1: float, y0: float, y1: float) -> Rect2:
	var middle := inner.size.y * 0.5 - (y0 + y1) * 0.5
	return Rect2(inner.position.x + x0 + middle * tilt, inner.position.y + y0, x1 - x0, y1 - y0)
