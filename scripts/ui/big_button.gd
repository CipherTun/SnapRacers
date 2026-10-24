class_name BigButton
extends ScrollButton

## A big slanted menu button, like the main menu's, with a picture in a block
## at its left end and its words in capitals. It turns yellow with arrows
## pointing on when it's picked out. A second line in `text`, after a line
## break, goes under the first in smaller letters.

## The picture in the block (see UiKit.draw_icon()).
var picture := ""

var _words := ""
var _more := ""


func _init(words := "", what := "", more := "") -> void:
	super()
	text = words if more == "" else "%s\n%s" % [words, more]
	_words = words.to_upper()
	_more = more
	picture = what
	theme_type_variation = "BigButton"
	focus_mode = FOCUS_ALL
	# The words are drawn by hand, so the text only sizes the button by its clipped width.
	clip_text = true


func _notification(what: int) -> void:
	if what == NOTIFICATION_THEME_CHANGED or what == NOTIFICATION_ENTER_TREE:
		_size_up()


func _size_up() -> void:
	var high := UiKit.BUTTON_HEIGHT if _more == "" else 78.0
	# Room for the words, and for the arrows after the first line.
	var wide := _font().get_string_size(_words, HORIZONTAL_ALIGNMENT_LEFT, -1, _size()).x + 90.0
	if _more != "":
		wide = maxf(wide, UiKit.font("body").get_string_size(_more, HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.SMALL).x + 16.0)
	custom_minimum_size = Vector2(maxf(470.0, _text_left(high) + wide + high * UiKit.LEAN * 0.5), high)


func _font() -> Font:
	return UiKit.font("heading")


func _size() -> int:
	return UiKit.HEADING if _more == "" else 28


func _text_left(high: float) -> float:
	return 26.0 + (high - 16.0) * UiKit.LEAN + 62.0


func _lit() -> bool:
	if disabled:
		return false
	return has_focus() or get_draw_mode() != DRAW_NORMAL


func _draw() -> void:
	var lit := _lit()
	var high := size.y
	# The block sits just inside the slanted left end.
	var block := Rect2(Vector2(10.0, 8.0), Vector2(62.0 + (high - 16.0) * UiKit.LEAN, high - 16.0))
	UiKit.draw_slant(self, block, UiKit.INK if lit else UiKit.RED)
	var ink := UiKit.INK if lit else UiKit.WHITE
	if disabled:
		ink = UiKit.FADED
	if picture != "":
		UiKit.draw_icon(self, picture, block.get_center() + Vector2(2, 0), 26.0, UiKit.YELLOW if lit else UiKit.WHITE, 3.0)
	var left := _text_left(high)
	var font := _font()
	var big := _size()
	var middle := high * 0.5 if _more == "" else high * 0.5 - 11.0
	draw_string(font, Vector2(left, middle + (font.get_ascent(big) - font.get_descent(big)) * 0.5), _words, HORIZONTAL_ALIGNMENT_LEFT, -1, big, ink)
	if _more != "":
		var body := UiKit.font("body")
		var y := high * 0.5 + 17.0 + (body.get_ascent(UiKit.SMALL) - body.get_descent(UiKit.SMALL)) * 0.5
		draw_string(body, Vector2(left, y), _more, HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.SMALL, Color(UiKit.INK, 0.75) if lit else UiKit.MUTED)
	if lit:
		# Three arrows pointing on, at the right end.
		for i in 3:
			var a := Vector2(size.x - high * UiKit.LEAN * 0.5 - 70.0 + i * 16.0, high * 0.5)
			draw_colored_polygon(PackedVector2Array([a + Vector2(-6, -12), a + Vector2(2, -12), a + Vector2(10, 0), a + Vector2(2, 12), a + Vector2(-6, 12), a + Vector2(2, 0)]), UiKit.INK)
