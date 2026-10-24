class_name UiKit
extends RefCounted

## The arcade racer look every screen shares: colours, type, spacing, the
## slanted boxes and the one Theme built from them. MenuStyle and BuilderStyle
## call into this.

# Colours.
const INK := Color("#0b0b12")
## The bottom of the backdrop.
const INK_LOW := Color("#22101c")
const YELLOW := Color("#ffd60a")
const RED := Color("#ff2d3d")
const GREEN := Color("#3ddc5a")
const BLUE := Color("#7fd8ff")
const WHITE := Color.WHITE
## The dark, nearly solid fill behind a panel or button.
const PANEL := Color(0.02, 0.02, 0.05, 0.85)
const PANEL_HOVER := Color(0.09, 0.09, 0.15, 0.9)
## The thin light line round a panel.
const EDGE := Color(1, 1, 1, 0.15)
const MUTED := Color(1, 1, 1, 0.6)
const FADED := Color(1, 1, 1, 0.35)
## The accent: focus, the chosen one, you.
const ACCENT := YELLOW
## Text on an accent or yellow fill.
const ON_ACCENT := INK
const DANGER := Color("#ff6b6b")
const MEDALS := { 1: Color("#f2b632"), 2: Color("#cdd3db"), 3: Color("#c47a45") }

# Type sizes, in UI pixels. SMALL is the smallest anything gets, so it stays
# readable on a phone.
const TITLE := 64
const HEADING := 30
const BODY := 22
const SMALL := 16
const DIGITS := 34

# Spacing steps.
const GAP_XS := 4
const GAP_S := 8
const GAP_M := 12
const GAP_L := 18
const GAP_XL := 24
const GAP_XXL := 40

# Slant, as how far the top moves right per pixel of height. Buttons and
# chips lean like the type, cards less so they don't look squashed.
const LEAN := 0.35
const CARD_LEAN := 0.12
const PANEL_LEAN := 0.3
## The hard drop shadow under panels and buttons.
const SHADOW := Vector2(6, 6)
const SHADOW_COLOUR := Color(0, 0, 0, 0.5)
## The stripes on cards and panels.
const STRIPE_WIDTH := 10.0
const UNDERLINE := 6.0

const BUTTON_HEIGHT := 60.0
const STATES := ["normal", "hover", "pressed", "focus", "disabled"]

const _FONTS := "res://art/fonts/chakra_petch/"

static var _theme: Theme
static var _fonts := {}


# ------------------------------------------------------------------ type

## Chakra Petch for each step of the type scale: "title", "heading", "body"
## or "digits" (even-width digits, so a ticking clock doesn't jiggle).
static func font(kind := "body") -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var f := FontVariation.new()
	match kind:
		"title":
			f.base_font = load(_FONTS + "ChakraPetch-BoldItalic.ttf")
			f.variation_transform = Transform2D(Vector2(1, 0), Vector2(-0.12, 1), Vector2.ZERO)
			f.set_spacing(TextServer.SPACING_GLYPH, 1)
		"heading":
			f.base_font = load(_FONTS + "ChakraPetch-BoldItalic.ttf")
			f.set_spacing(TextServer.SPACING_GLYPH, 1)
		"digits":
			# Made by tools/fonts/even_digits.py, as the font has no tnum.
			f.base_font = load(_FONTS + "ChakraPetch-BoldItalic-EvenDigits.ttf")
		_:
			f.base_font = load(_FONTS + "ChakraPetch-Bold.ttf")
	_fonts[kind] = f
	return f


# ----------------------------------------------------------------- boxes

## A slanted box. Every other box here is one of these.
static func slant(fill: Color, lean := LEAN, edge := Color.TRANSPARENT, edge_width := 0, shadow := true) -> SlantBox:
	var box := SlantBox.new()
	box.fill = fill
	box.lean = lean
	box.edge = edge
	box.edge_width = edge_width
	if shadow:
		box.shadow = SHADOW
		box.shadow_colour = SHADOW_COLOUR
	return box


## Padding inside a box, with room for its lean at a given height.
static func pad(box: StyleBox, across: float, down: float, lean := 0.0, height := BUTTON_HEIGHT) -> StyleBox:
	var extra := height * lean * 0.5
	box.content_margin_left = across + extra
	box.content_margin_right = across + extra
	box.content_margin_top = down
	box.content_margin_bottom = down
	return box


## The white ring round whatever a controller or the keys have picked out.
## It's white so it can't be mixed up with the yellow on a chosen one.
static func focus_ring(lean := LEAN, gap := 5.0) -> SlantBox:
	var box := slant(Color.TRANSPARENT, lean, WHITE, 4, false)
	box.grow = gap
	return box


## A button: dark with a light edge, lit up when hovered, yellow edged when
## held.
static func pill(state: String, lean := LEAN, height := BUTTON_HEIGHT) -> StyleBox:
	var box: SlantBox
	match state:
		"hover":
			box = slant(PANEL_HOVER, lean, Color(YELLOW, 0.5), 1)
		"pressed":
			box = slant(Color(0.2, 0.17, 0.02, 0.92), lean, YELLOW, 3)
		"focus":
			box = focus_ring(lean)
		"disabled":
			box = slant(Color(1, 1, 1, 0.05), lean, Color(1, 1, 1, 0.08), 1, false)
		_:
			box = slant(PANEL, lean, EDGE, 1)
	return pad(box, 24, 10, lean, height)


## A filled button, like the big yellow one at the end of a row.
static func solid(state: String, colour: Color, lean := LEAN, height := 56.0) -> StyleBox:
	var box: SlantBox
	match state:
		"hover":
			box = slant(colour.lightened(0.1), lean)
		"pressed":
			box = slant(colour.lightened(0.25), lean)
		"focus":
			box = focus_ring(lean)
		"disabled":
			box = slant(Color(1, 1, 1, 0.05), lean, Color.TRANSPARENT, 0, false)
		_:
			box = slant(colour, lean)
	return pad(box, 28, 8, lean, height)


## A small tinted button for the smaller controls.
static func chip(state: String, lean := LEAN, height := 48.0) -> StyleBox:
	var box: SlantBox
	match state:
		"hover":
			box = slant(Color(YELLOW, 0.26), lean, Color.TRANSPARENT, 0, false)
		"pressed":
			box = slant(Color(YELLOW, 0.4), lean, Color.TRANSPARENT, 0, false)
		"focus":
			box = focus_ring(lean, 4.0)
		"disabled":
			box = slant(Color(1, 1, 1, 0.05), lean, Color.TRANSPARENT, 0, false)
		_:
			box = slant(Color(YELLOW, 0.16), lean, Color.TRANSPARENT, 0, false)
	return pad(box, 16, 4, lean, height)


## A card in a grid, like a cup or a course, with a stripe of its colour down
## the left side. A focused one has a thick yellow edge.
static func card(state: String, colour := Color.TRANSPARENT) -> StyleBox:
	var box: SlantBox
	match state:
		"hover":
			box = slant(PANEL_HOVER, CARD_LEAN, Color(1, 1, 1, 0.3), 1)
		"pressed":
			box = slant(PANEL_HOVER, CARD_LEAN, YELLOW, 3)
		"focus":
			box = slant(Color.TRANSPARENT, CARD_LEAN, YELLOW, 3, false)
		"disabled":
			box = slant(Color(PANEL, 0.4), CARD_LEAN, Color(1, 1, 1, 0.06), 1, false)
		_:
			box = slant(Color(PANEL, 0.88), CARD_LEAN, Color(1, 1, 1, 0.14), 1)
	if colour.a > 0.0 and state != "focus":
		box.stripe = colour
		box.stripe_width = STRIPE_WIDTH
	return pad(box, 14, 10, CARD_LEAN, 200.0)


## A dark panel for the HUD and other floating bits, with a red line along
## the bottom when `underline` is set.
static func panel(lean := PANEL_LEAN, underline := false) -> SlantBox:
	var box := slant(Color(0.02, 0.02, 0.05, 0.8), lean, EDGE, 1)
	if underline:
		box.underline = RED
		box.underline_height = UNDERLINE
	pad(box, 14, 8, lean, 80.0)
	return box


## The backing of a popup or dialog: square, nearly solid, with a red stripe
## down the left.
static func popup() -> SlantBox:
	var box := slant(Color(INK, 0.97), 0.0, Color(1, 1, 1, 0.18), 1)
	box.stripe = RED
	box.stripe_width = 6.0
	pad(box, 24, 18)
	box.content_margin_left = 34
	return box


## A text field.
static func field(focused := false) -> StyleBox:
	var box := slant(Color(1, 1, 1, 0.05), 0.15, YELLOW if focused else Color(1, 1, 1, 0.45), 2, false)
	return pad(box, 16, 10, 0.15, 50.0)


# ----------------------------------------------------------------- theme

## The one theme for every screen, the HUD and the editors.
static func theme() -> Theme:
	if _theme != null:
		return _theme
	var t := Theme.new()
	_theme = t
	t.default_font = font("body")
	t.default_font_size = BODY

	for type in ["Button", "OptionButton", "MenuButton", "CheckBox", "CheckButton"]:
		for state in STATES:
			t.set_stylebox(state, type, pill(state))
		t.set_font("font", type, font("heading"))
		for colour_name in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
			t.set_color(colour_name, type, WHITE)
		t.set_color("font_disabled_color", type, FADED)
		t.set_constant("h_separation", type, GAP_M)
	# A switch or tick box is a line of text with its picture, so no box
	# round it until it's focused.
	for type in ["CheckBox", "CheckButton"]:
		var plain := StyleBoxEmpty.new()
		pad(plain, 12, 6)
		for state in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
			t.set_stylebox(state, type, plain)
		t.set_color("font_hover_color", type, YELLOW)

	t.set_color("font_color", "Label", WHITE)
	t.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0))
	# Kinds of label for the type scale, picked with theme_type_variation.
	for kind in [["TitleLabel", "title", TITLE], ["HeadingLabel", "heading", HEADING], ["SmallLabel", "body", SMALL], ["DigitsLabel", "digits", DIGITS]]:
		t.set_type_variation(kind[0], "Label")
		t.set_font("font", kind[0], font(kind[1]))
		t.set_font_size("font_size", kind[0], kind[2])
	t.set_color("font_color", "SmallLabel", MUTED)

	for type in ["LineEdit", "SpinBox"]:
		t.set_stylebox("normal", type, field())
		t.set_stylebox("focus", type, field(true))
		t.set_stylebox("read_only", type, field())
	t.set_color("font_color", "LineEdit", WHITE)
	t.set_color("font_placeholder_color", "LineEdit", FADED)
	t.set_color("caret_color", "LineEdit", YELLOW)
	t.set_color("selection_color", "LineEdit", Color(YELLOW, 0.35))

	t.set_stylebox("panel", "PanelContainer", pad(slant(PANEL, 0.0, EDGE, 1, false), 12, 10))
	t.set_stylebox("panel", "Panel", slant(PANEL, 0.0, EDGE, 1, false))
	for type in ["PopupPanel", "PopupMenu", "AcceptDialog", "ConfirmationDialog", "FileDialog"]:
		t.set_stylebox("panel", type, popup())
	t.set_stylebox("embedded_border", "Window", popup())
	t.set_stylebox("embedded_unfocused_border", "Window", popup())
	t.set_font("title_font", "Window", font("heading"))
	t.set_color("title_color", "Window", WHITE)
	t.set_font_size("title_font_size", "Window", BODY)

	var hover := slant(Color(YELLOW, 0.22), 0.0, Color.TRANSPARENT, 0, false)
	t.set_stylebox("hover", "PopupMenu", hover)
	t.set_font("font", "PopupMenu", font("heading"))
	t.set_color("font_color", "PopupMenu", WHITE)
	t.set_color("font_hover_color", "PopupMenu", YELLOW)
	t.set_color("font_disabled_color", "PopupMenu", FADED)
	t.set_constant("v_separation", "PopupMenu", GAP_L)
	t.set_stylebox("separator", "PopupMenu", _line(Color(1, 1, 1, 0.15)))

	var track := StyleBoxFlat.new()
	track.bg_color = Color(1, 1, 1, 0.12)
	track.content_margin_top = 4.0
	track.content_margin_bottom = 4.0
	t.set_stylebox("background", "ProgressBar", track)
	var done := StyleBoxFlat.new()
	done.bg_color = YELLOW
	t.set_stylebox("fill", "ProgressBar", done)
	t.set_color("font_color", "ProgressBar", WHITE)

	_add_sliders(t)
	_add_scroll_bars(t)
	add_pictures(t)
	return t


static func _line(colour: Color) -> StyleBoxLine:
	var line := StyleBoxLine.new()
	line.color = colour
	line.thickness = 2
	return line


static func _add_sliders(t: Theme) -> void:
	var track := StyleBoxFlat.new()
	track.bg_color = Color(1, 1, 1, 0.15)
	track.content_margin_top = 5.0
	track.content_margin_bottom = 5.0
	track.skew = Vector2(LEAN, 0)
	var filled := track.duplicate() as StyleBoxFlat
	filled.bg_color = YELLOW
	t.set_stylebox("slider", "HSlider", track)
	t.set_stylebox("grabber_area", "HSlider", filled)
	t.set_stylebox("grabber_area_highlight", "HSlider", filled)
	var knob := grabber(WHITE)
	t.set_icon("grabber", "HSlider", knob)
	t.set_icon("grabber_highlight", "HSlider", grabber(YELLOW))
	t.set_icon("grabber_disabled", "HSlider", grabber(FADED))
	t.set_stylebox("focus", "HSlider", focus_ring(0.0, 4.0))


static func _add_scroll_bars(t: Theme) -> void:
	var states := {
		"scroll": Color(1, 1, 1, 0.06),
		"scroll_focus": Color(1, 1, 1, 0.1),
		"grabber": Color(YELLOW, 0.55),
		"grabber_highlight": Color(YELLOW, 0.8),
		"grabber_pressed": YELLOW,
	}
	var none := ImageTexture.create_from_image(Image.create_empty(1, 1, false, Image.FORMAT_RGBA8))
	for type in ["VScrollBar", "HScrollBar"]:
		for state in states:
			var box := StyleBoxFlat.new()
			box.bg_color = states[state]
			if type == "VScrollBar":
				box.content_margin_left = 5.0
				box.content_margin_right = 5.0
			else:
				box.content_margin_top = 5.0
				box.content_margin_bottom = 5.0
			t.set_stylebox(state, type, box)
		for icon in ["increment", "increment_highlight", "increment_pressed", "decrement", "decrement_highlight", "decrement_pressed"]:
			t.set_icon(icon, type, none)


# -------------------------------------------------------------- pictures
# The engine draws its own icons from SVG, which our cut down engine leaves
# out, so on a phone or the web they'd be blank. These are drawn here.

## Pictures for switches, tick boxes, the OptionButton arrow and SpinBox.
static func add_pictures(to: Theme) -> void:
	var on := switch_picture(true, 1.0)
	var off := switch_picture(false, 1.0)
	var on_dim := switch_picture(true, 0.4)
	var off_dim := switch_picture(false, 0.4)
	for side in ["", "_mirrored"]:
		to.set_icon("checked" + side, "CheckButton", on)
		to.set_icon("unchecked" + side, "CheckButton", off)
		to.set_icon("checked_disabled" + side, "CheckButton", on_dim)
		to.set_icon("unchecked_disabled" + side, "CheckButton", off_dim)

	var ticked := tick_picture(true, 1.0)
	var empty := tick_picture(false, 1.0)
	for type in ["CheckBox", "PopupMenu"]:
		to.set_icon("checked", type, ticked)
		to.set_icon("unchecked", type, empty)
		to.set_icon("radio_checked", type, ticked)
		to.set_icon("radio_unchecked", type, empty)
	for name in ["checked_disabled", "radio_checked_disabled"]:
		to.set_icon(name, "CheckBox", tick_picture(true, 0.4))
	for name in ["unchecked_disabled", "radio_unchecked_disabled"]:
		to.set_icon(name, "CheckBox", tick_picture(false, 0.4))

	var down := arrow_picture(Vector2.DOWN, WHITE)
	to.set_icon("arrow", "OptionButton", down)
	to.set_icon("submenu", "PopupMenu", arrow_picture(Vector2.RIGHT, WHITE))
	to.set_icon("submenu_mirrored", "PopupMenu", arrow_picture(Vector2.LEFT, WHITE))

	to.set_icon("updown", "SpinBox", updown_picture())
	for state in ["", "_hover", "_pressed", "_disabled"]:
		var ink := YELLOW if state == "_hover" or state == "_pressed" else WHITE
		if state == "_disabled":
			ink = FADED
		to.set_icon("up" + state, "SpinBox", arrow_picture(Vector2.UP, ink))
		to.set_icon("down" + state, "SpinBox", arrow_picture(Vector2.DOWN, ink))


## How much of the pixel at `p` is inside a parallelogram over `rect`
## leaning by `lean`, for soft edges.
static func _inside(p: Vector2, rect: Rect2, lean: float) -> float:
	var shift := rect.size.y * lean * 0.5
	var left := rect.position.x + shift - lean * (p.y - rect.position.y)
	var right := left + rect.size.x - shift * 2.0
	var across := minf(p.x - left, right - p.x) / sqrt(1.0 + lean * lean)
	var down := minf(p.y - rect.position.y, rect.end.y - p.y)
	return clampf(minf(across, down) + 0.5, 0.0, 1.0)


## Paints a leaning shape onto a picture, over what's there.
static func _paint(image: Image, rect: Rect2, lean: float, colour: Color) -> void:
	for y in image.get_height():
		for x in image.get_width():
			var cover := _inside(Vector2(x + 0.5, y + 0.5), rect, lean)
			if cover > 0.0:
				image.set_pixel(x, y, image.get_pixel(x, y).blend(Color(colour, colour.a * cover)))


static func _blank(width: int, height: int) -> Image:
	return Image.create_empty(width, height, false, Image.FORMAT_RGBA8)


## A switch: a slanted track with a block at one end, yellow when it's on.
static func switch_picture(on: bool, alpha: float) -> ImageTexture:
	var image := _blank(66, 32)
	var whole := Rect2(1, 2, 64, 28)
	_paint(image, whole, LEAN, Color(YELLOW, alpha) if on else Color(1, 1, 1, 0.22 * alpha))
	var block := Rect2(whole.end.x - 30, 6, 26, 20) if on else Rect2(whole.position.x + 4, 6, 26, 20)
	_paint(image, block, LEAN, Color(INK, alpha) if on else Color(1, 1, 1, alpha))
	return ImageTexture.create_from_image(image)


## A slanted tick box, yellow with a dark tick when it's ticked.
static func tick_picture(ticked: bool, alpha: float) -> ImageTexture:
	var image := _blank(34, 30)
	var whole := Rect2(1, 1, 32, 28)
	if ticked:
		_paint(image, whole, LEAN * 0.6, Color(YELLOW, alpha))
		_line_on(image, [Vector2(9, 15), Vector2(15, 21), Vector2(25, 8)], 3.5, Color(INK, alpha))
	else:
		_paint(image, whole, LEAN * 0.6, Color(1, 1, 1, 0.6 * alpha))
		_paint(image, whole.grow(-3.0), LEAN * 0.6, Color(INK, 0.92))
	return ImageTexture.create_from_image(image)


## A chevron pointing `towards`.
static func arrow_picture(towards: Vector2, ink: Color) -> ImageTexture:
	var image := _blank(20, 20)
	var c := Vector2(10, 10)
	var side := Vector2(-towards.y, towards.x)
	_line_on(image, [c - towards * 3.5 + side * 6.0, c + towards * 3.5, c - towards * 3.5 - side * 6.0], 3.0, ink)
	return ImageTexture.create_from_image(image)


## The SpinBox's up and down arrows, one over the other.
static func updown_picture() -> ImageTexture:
	var image := _blank(20, 32)
	_line_on(image, [Vector2(4, 13), Vector2(10, 7), Vector2(16, 13)], 3.0, WHITE)
	_line_on(image, [Vector2(4, 19), Vector2(10, 25), Vector2(16, 19)], 3.0, WHITE)
	return ImageTexture.create_from_image(image)


## A slider's handle: a slanted white block.
static func grabber(colour: Color) -> ImageTexture:
	var image := _blank(26, 32)
	_paint(image, Rect2(1, 1, 24, 30), LEAN, Color(0, 0, 0, 0.5))
	_paint(image, Rect2(1, 1, 22, 28), LEAN, colour)
	return ImageTexture.create_from_image(image)


## Draws a thick line through `points` onto a picture, with soft edges.
static func _line_on(image: Image, points: Array, width: float, ink: Color) -> void:
	for y in image.get_height():
		for x in image.get_width():
			var p := Vector2(x + 0.5, y + 0.5)
			var near := INF
			for i in points.size() - 1:
				var closest := Geometry2D.get_closest_point_to_segment(p, points[i], points[i + 1])
				near = minf(near, p.distance_to(closest))
			var cover := clampf(width * 0.5 - near + 0.5, 0.0, 1.0)
			if cover > 0.0:
				image.set_pixel(x, y, image.get_pixel(x, y).blend(Color(ink, ink.a * cover)))


# -------------------------------------------------------------- backdrop

## The dark backdrop with faint speed stripes leaning with the type, now and
## then a red one. `tint` colours the stripes.
class Backdrop extends Control:
	var tint := Color.WHITE
	var red := true

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED:
			queue_redraw()

	func _draw() -> void:
		var w := size.x
		var h := size.y
		draw_polygon(PackedVector2Array([Vector2.ZERO, Vector2(w, 0), Vector2(w, h), Vector2(0, h)]),
			PackedColorArray([UiKit.INK, UiKit.INK, UiKit.INK_LOW, UiKit.INK_LOW]))
		var lean := UiKit.LEAN
		var rng := RandomNumberGenerator.new()
		rng.seed = 7
		var x := -h * lean
		while x < w + 40.0:
			var wide := rng.randf_range(2.0, 22.0)
			var alpha := rng.randf_range(0.015, 0.05)
			var colour := Color(tint, alpha)
			if red and rng.randf() < 0.12:
				colour = Color(UiKit.RED, alpha * 1.6)
			draw_colored_polygon(PackedVector2Array([Vector2(x + h * lean, 0), Vector2(x + h * lean + wide, 0), Vector2(x + wide, h), Vector2(x, h)]), colour)
			x += wide + rng.randf_range(10.0, 60.0)


static func backdrop() -> Control:
	return Backdrop.new()
