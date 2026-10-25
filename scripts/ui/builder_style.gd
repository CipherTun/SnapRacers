class_name BuilderStyle
extends RefCounted

## The look shared by the garage, the driver screen and the track editor.
## Whatever you're building fills the screen and every panel floats over it on
## its own dark, see-through slanted backing, light enough to see the build
## through.

# The colours, from UiKit: red for danger and for things that are wrong, blue
# for numbers.
const DANGER := UiKit.DANGER
const DATA := UiKit.BLUE
## The see-through dark behind a panel.
const SCRIM := Color(0.02, 0.02, 0.05, 0.6)
## The dark ink on the accent coloured buttons.
const ON_ACCENT := UiKit.ON_ACCENT
const TILE := Vector2(104, 104)
## Behind the thing being built.
const BACKGROUND := Color("#2b3440")
## How far a panel's top edge sits to the right of its bottom edge, in pixels,
## whatever its height, so a tall drawer leans no more than a short chip.
const PANEL_SLANT := 10.0
## The lean of the round-ish buttons: the tool buttons, swatches and arrows.
const BUTTON_LEAN := 0.25


## The see-through panel behind a drawer, card or row of controls, padded
## `across` and `down` inside its lean.
static func scrim(across := 8.0, down := 6.0, alpha := SCRIM.a) -> SlantBox:
	var box := UiKit.slant(Color(SCRIM, alpha), UiKit.PANEL_LEAN, UiKit.EDGE, 1, false)
	return UiKit.pad(box, across, down, UiKit.PANEL_LEAN, PANEL_SLANT / UiKit.PANEL_LEAN) as SlantBox


## A word button, bold capitals in a colour with no box. One that `scrolls`
## sits in a scrolling list (see ScrollButton.let_scroll).
static func word(text: String, colour: Color, action: Callable, scrolls := false) -> Button:
	var button := Button.new()
	button.text = text.to_upper()
	button.flat = true
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(0, 48)
	button.add_theme_font_size_override("font_size", UiKit.CHIP)
	button.add_theme_stylebox_override("focus", UiKit.focus_ring(UiKit.LEAN, 0.0))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, colour)
	button.add_theme_color_override("font_disabled_color", Color(colour, 0.35))
	if scrolls:
		ScrollButton.let_scroll(button, action)
	else:
		button.pressed.connect(action)
	return button


## Dresses a button as a small tinted chip, for the smaller controls.
static func chip(button: Button, text: String) -> void:
	button.text = text.to_upper()
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(96, 48)
	button.add_theme_font_size_override("font_size", UiKit.CHIP)
	for state in UiKit.STATES:
		button.add_theme_stylebox_override(state, UiKit.chip(state))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, UiKit.ACCENT)
	button.add_theme_color_override("font_disabled_color", UiKit.FADED)


## A slanted button with a coloured fill. A low one, under 48 high, has
## smaller type. One that `scrolls` sits in a scrolling list, so a drag that
## starts on it scrolls the list (see ScrollButton).
static func pill(text: String, fill: Color, ink: Color, action: Callable, height := 56.0, scrolls := false) -> Button:
	var button: Button = ScrollButton.new() if scrolls else Button.new()
	button.text = text.to_upper()
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(0, height)
	button.add_theme_font_size_override("font_size", UiKit.BODY if height >= 48.0 else UiKit.SMALL)
	for state in UiKit.STATES:
		button.add_theme_stylebox_override(state, UiKit.solid(state, fill, UiKit.LEAN, height))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, ink)
	button.add_theme_color_override("font_disabled_color", UiKit.FADED)
	if scrolls:
		(button as ScrollButton).tapped.connect(action)
	else:
		button.pressed.connect(action)
	return button


## The big accent button, and the dark one that sits beside it.
static func main_pill(text: String, action: Callable, scrolls := false) -> Button:
	return pill(text, Color(UiKit.ACCENT, 0.9), ON_ACCENT, action, 56.0, scrolls)


static func dark_pill(text: String, action: Callable) -> Button:
	return pill(text, Color(SCRIM, 0.7), UiKit.WHITE, action)


## Slides a row centred along the bottom sideways so it's clear of the
## panels beside it: left of any in `right_panels` it's level with, and not
## past any in `left_panels`. It never slides right. It moves the row's
## anchors, so SafeArea, which only sets offsets, doesn't undo it.
static func slide_clear(row: Control, left_panels: Array, right_panels: Array) -> void:
	var width := row.get_parent_area_size().x
	if width <= 0.0:
		return
	var shift := (row.anchor_left - 0.5) * width
	var rect := row.get_global_rect()
	rect.position.x -= shift
	var want := 0.0
	for panel: Control in right_panels:
		var r := panel.get_global_rect()
		if panel.is_visible_in_tree() and r.position.y < rect.end.y and r.end.y > rect.position.y:
			want = minf(want, r.position.x - UiKit.GAP_S - rect.end.x)
	for panel: Control in left_panels:
		var r := panel.get_global_rect()
		if panel.is_visible_in_tree() and r.position.y < rect.end.y and r.end.y > rect.position.y:
			want = maxf(want, minf(r.end.x + UiKit.GAP_S - rect.position.x, 0.0))
	if absf(want - shift) > 0.5:
		row.set_anchor(SIDE_LEFT, 0.5 + want / width, true, false)
		row.set_anchor(SIDE_RIGHT, 0.5 + want / width, true, false)


## The stats chip in the top right: one line of numbers on a small panel,
## which opens into the whole card.
static func stats_chip() -> Button:
	var button := Button.new()
	button.focus_mode = Control.FOCUS_ALL
	button.theme_type_variation = "StatsChipButton"
	return button


## The chip under the toolbar with the part in hand on it, tinted with the
## accent.
static func held_box() -> SlantBox:
	var box := UiKit.slant(Color(UiKit.ACCENT, 0.22), UiKit.PANEL_LEAN, Color(UiKit.ACCENT, 0.5), 1, false)
	UiKit.pad(box, 8, 0, UiKit.PANEL_LEAN, 48.0)
	return box


## Colours a slanted swatch, edged in the accent when it's the one picked, or
## in white on a colour too close to the accent to show it.
static func show_swatch(swatch: Button, colour: Color, picked: bool, lean := BUTTON_LEAN) -> void:
	var height := maxf(swatch.custom_minimum_size.y, 1.0)
	var key := "%s %s %d %.2f" % [colour.to_html(), picked, roundi(height), lean]
	if not _swatches.has(key):
		var box := UiKit.slant(colour, lean, Color.TRANSPARENT, 0, false)
		if picked:
			var near_accent := colour.is_equal_approx(UiKit.ACCENT) or (absf(colour.h - UiKit.ACCENT.h) < 0.05 and colour.s > 0.5 and colour.v > 0.8)
			box.edge = UiKit.WHITE if near_accent else UiKit.ACCENT
			box.edge_width = 4
		_swatches[key] = UiKit.pad(box, 8, 0, lean, height)
	for state in ["normal", "hover", "pressed"]:
		swatch.add_theme_stylebox_override(state, _swatches[key])
	# Godot draws the focus box over the others, so it's only an edge.
	var ring := UiKit.slant(Color.TRANSPARENT, lean, UiKit.WHITE, 4, false)
	swatch.add_theme_stylebox_override("focus", UiKit.pad(ring, 8, 0, lean, height))


static var _swatches := {}


## A pop up list of choices on a dark backing.
static func menu(items: Array) -> PopupMenu:
	var list := PopupMenu.new()
	list.theme = MenuStyle.theme()
	list.add_theme_font_size_override("font_size", UiKit.LEAD)
	list.add_theme_constant_override("v_separation", UiKit.GAP_L)
	list.add_theme_stylebox_override("panel", UiKit.popup())
	for i in items.size():
		list.add_item(items[i], i)
	return list


## The handle left at the edge of the screen when a drawer is put away.
static func drawer_handle(action: Callable) -> Button:
	var handle := Button.new()
	handle.focus_mode = Control.FOCUS_ALL
	handle.custom_minimum_size = Vector2(30, 80)
	handle.theme_type_variation = "DrawerHandleButton"
	handle.text = "›"
	handle.pressed.connect(action)
	return handle


## The backing of a tile in a drawer, lit up when it's the one picked.
static func tile_box(state: String, picked := false) -> StyleBox:
	var box: SlantBox
	match state:
		"pressed":
			box = UiKit.slant(Color(UiKit.ACCENT, 0.3), UiKit.CARD_LEAN, Color.TRANSPARENT, 0, false)
		"hover":
			box = UiKit.slant(Color(1, 1, 1, 0.12), UiKit.CARD_LEAN, Color.TRANSPARENT, 0, false)
		_:
			box = UiKit.slant(Color(1, 1, 1, 0.07), UiKit.CARD_LEAN, Color.TRANSPARENT, 0, false)
	if picked:
		box.fill = Color(UiKit.ACCENT, 0.22 if state != "pressed" else 0.34)
		box.edge = UiKit.ACCENT
		box.edge_width = 2
	# Godot draws the focus box over the tile's usual one, so it's only a
	# white edge and the hover or pressed fill shows through.
	if state == "focus":
		box.fill = Color.TRANSPARENT
		box.edge = UiKit.WHITE
		box.edge_width = 3
	box.lean_height = TILE.y
	box.content_margin_left = 2
	box.content_margin_right = 2
	box.content_margin_top = 4
	box.content_margin_bottom = 4
	return box


## A tile's backings for each state, for a button in a drawer.
static func dress_tile(tile: Button, picked := false) -> void:
	tile.theme_type_variation = "TileButton"
	if picked:
		for state in ["normal", "hover", "pressed", "focus"]:
			tile.add_theme_stylebox_override(state, tile_box(state, picked))
		for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			tile.add_theme_color_override(state, UiKit.ACCENT)


## The editors' kinds of label and button, added to UiKit's theme.
static func add_to(t: Theme) -> void:
	for kind in [
		# A drawer's heading and the small headings on a card.
		["ShelfLabel", "heading", UiKit.NOTE, UiKit.SOFT],
		# Numbers on a card, and what's wrong.
		["StatsLabel", "body", UiKit.NOTE, DATA],
		["ProblemLabel", "body", UiKit.NOTE, DANGER],
		# The line of news over the race button.
		["StatusLabel", "body", UiKit.NOTE, UiKit.SOFT],
		# A part's name under its picture, drawn by hand on a tile.
		["TileLabel", "body", UiKit.TINY, UiKit.WHITE],
	]:
		t.set_type_variation(kind[0], "Label")
		t.set_font("font", kind[0], UiKit.font(kind[1]))
		t.set_font_size("font_size", kind[0], kind[2])
		t.set_color("font_color", kind[0], kind[3])

	t.set_type_variation("TileButton", "Button")
	t.set_font("font", "TileButton", UiKit.font("body"))
	t.set_font_size("font_size", "TileButton", UiKit.TINY)
	for state in UiKit.STATES:
		t.set_stylebox(state, "TileButton", tile_box(state))
	for colour_name in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		t.set_color(colour_name, "TileButton", UiKit.WHITE)

	# The stats chip, blue numbers on a small panel.
	t.set_type_variation("StatsChipButton", "Button")
	t.set_font("font", "StatsChipButton", UiKit.font("body"))
	t.set_font_size("font_size", "StatsChipButton", UiKit.CHIP)
	var chip_box := scrim(10, 6)
	for state in ["normal", "hover", "pressed", "disabled"]:
		t.set_stylebox(state, "StatsChipButton", chip_box)
	var chip_hover := scrim(10, 6, 0.72)
	chip_hover.edge = Color(UiKit.ACCENT, 0.5)
	t.set_stylebox("hover", "StatsChipButton", chip_hover)
	var chip_ring := scrim(10, 6)
	chip_ring.fill = Color.TRANSPARENT
	chip_ring.edge = UiKit.WHITE
	chip_ring.edge_width = 3
	t.set_stylebox("focus", "StatsChipButton", chip_ring)
	for colour_name in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		t.set_color(colour_name, "StatsChipButton", DATA)

	# The drawer's handle, a slanted tab at the edge of the screen.
	t.set_type_variation("DrawerHandleButton", "Button")
	t.set_font_size("font_size", "DrawerHandleButton", UiKit.HEADING)
	var tab := UiKit.slant(SCRIM, 0.12, UiKit.EDGE, 1, false)
	tab.content_margin_left = 6
	tab.content_margin_right = 6
	var tab_lit := UiKit.slant(Color(SCRIM, 0.75), 0.12, Color(UiKit.ACCENT, 0.5), 1, false)
	tab_lit.content_margin_left = 6
	tab_lit.content_margin_right = 6
	for state in ["normal", "pressed", "disabled"]:
		t.set_stylebox(state, "DrawerHandleButton", tab)
	t.set_stylebox("hover", "DrawerHandleButton", tab_lit)
	var tab_ring := UiKit.slant(Color.TRANSPARENT, 0.12, UiKit.WHITE, 3, false)
	tab_ring.content_margin_left = 6
	tab_ring.content_margin_right = 6
	t.set_stylebox("focus", "DrawerHandleButton", tab_ring)

	# A small pill to pick one of a set, like a surface or the weather.
	t.set_type_variation("ChoiceButton", "Button")
	t.set_font_size("font_size", "ChoiceButton", UiKit.SMALL)
	for state in UiKit.STATES:
		t.set_stylebox(state, "ChoiceButton", choice_box(state))


## The backing of a ChoiceButton, padded less than a full size button.
static func choice_box(state: String) -> SlantBox:
	return UiKit.pad(UiKit.pill(state, UiKit.LEAN, 40.0), 12, 4, UiKit.LEAN, 40.0) as SlantBox


## The see-through backing of a round-ish tool button: dark, solid accent
## when it's on.
static func icon_box(state: String, on: bool, height: float) -> StyleBox:
	var key := "%s %s %d" % [state, on, roundi(height)]
	if not _icon_boxes.has(key):
		_icon_boxes[key] = _make_icon_box(state, on, height)
	return _icon_boxes[key]


static var _icon_boxes := {}


static func _make_icon_box(state: String, on: bool, height: float) -> StyleBox:
	var box: SlantBox
	match state:
		"focus":
			# Drawn over its usual box, so it's only an edge.
			box = UiKit.slant(Color.TRANSPARENT, BUTTON_LEAN, UiKit.WHITE, 3, false)
		"hover":
			box = UiKit.slant(UiKit.ACCENT.lightened(0.15) if on else Color(SCRIM, 0.75), BUTTON_LEAN, Color(UiKit.ACCENT, 0.6), 1, false)
		"pressed":
			box = UiKit.slant(UiKit.ACCENT.lightened(0.3) if on else Color(UiKit.ACCENT, 0.35), BUTTON_LEAN, UiKit.ACCENT, 2, false)
		"disabled":
			box = UiKit.slant(Color(SCRIM, 0.3), BUTTON_LEAN, Color(1, 1, 1, 0.06), 1, false)
		_:
			box = UiKit.slant(UiKit.ACCENT if on else Color(SCRIM, 0.55), BUTTON_LEAN, Color.TRANSPARENT if on else UiKit.EDGE, 1, false)
	box.lean_height = height
	return box
