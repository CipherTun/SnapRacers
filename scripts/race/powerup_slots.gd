class_name PowerupSlots
extends Control

## The two power-ups a kart holds, as two boxes side by side at the bottom of
## the HUD, in the same order as the gadget buttons. An empty box is only a
## faint outline, and a held one shows its picture (see PowerupIcons), with
## how many goes are left when there's more than one. A box pops a little when
## it fills.

## Each box's size and the gap between them, in the UI's own units.
const BOX := 64.0
const GAP := 12.0
const EMPTY_FILL := Color(1.0, 1.0, 1.0, 0.05)
const EMPTY_EDGE := Color(1.0, 1.0, 1.0, 0.18)
const HELD_FILL := Color(0.04, 0.04, 0.1, 0.6)
const HELD_EDGE := Color(1.0, 1.0, 1.0, 0.75)
## How big a box starts when it fills, and how long it takes to settle.
const POP := 1.3
const POP_TIME := 0.2

var kinds: Array[String] = []
var uses: Array[int] = []
var _pop: Array[float] = []


func _init() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(BOX * Powerups.HOLD + GAP * (Powerups.HOLD - 1), BOX)
	for slot in Powerups.HOLD:
		kinds.append("")
		uses.append(0)
		_pop.append(1.0)


## Shows what's held, popping any box that has just filled or changed.
func show_held(held: Array, held_uses: Array) -> void:
	var changed := false
	for slot in Powerups.HOLD:
		var kind: String = held[slot] if slot < held.size() else ""
		var left: int = held_uses[slot] if slot < held_uses.size() else 0
		if kind != kinds[slot]:
			if kind != "":
				_pop[slot] = POP
			kinds[slot] = kind
			changed = true
		if left != uses[slot]:
			uses[slot] = left
			changed = true
	if changed:
		queue_redraw()


func _process(delta: float) -> void:
	for slot in Powerups.HOLD:
		if _pop[slot] > 1.0:
			_pop[slot] = maxf(1.0, _pop[slot] - (POP - 1.0) * delta / POP_TIME)
			queue_redraw()


func _draw() -> void:
	var font := get_theme_default_font()
	for slot in Powerups.HOLD:
		var centre := Vector2(BOX * 0.5 + slot * (BOX + GAP), BOX * 0.5)
		var scale := _pop[slot]
		draw_set_transform(centre, 0.0, Vector2.ONE * scale)
		var box := StyleBoxFlat.new()
		box.set_corner_radius_all(12)
		box.set_border_width_all(2)
		var held := kinds[slot] != ""
		box.bg_color = HELD_FILL if held else EMPTY_FILL
		box.border_color = HELD_EDGE if held else EMPTY_EDGE
		var rect := Rect2(Vector2.ONE * -BOX * 0.5, Vector2.ONE * BOX)
		draw_style_box(box, rect)
		if held:
			PowerupIcons.draw(self, kinds[slot], Vector2.ZERO, BOX * 0.72)
			if uses[slot] > 1:
				var text := "x%d" % uses[slot]
				var at := Vector2(BOX * 0.5 - 4.0, BOX * 0.5 - 6.0)
				var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20).x
				draw_string_outline(font, at - Vector2(width, 0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, 5, Color(0, 0, 0, 0.9))
				draw_string(font, at - Vector2(width, 0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color("#f2cd37"))
	draw_set_transform(Vector2.ZERO)
