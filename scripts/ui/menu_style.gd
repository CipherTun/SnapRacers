class_name MenuStyle
extends RefCounted

## Builds the menu screens: a dark backdrop with speed stripes, a big title
## and a column of slanted buttons, all from UiKit.

const TOP := UiKit.INK
const BOTTOM := UiKit.INK_LOW
const ACCENT := UiKit.ACCENT
const COLUMN_WIDTH := 460.0
const BUTTON_HEIGHT := UiKit.BUTTON_HEIGHT


## The theme for every screen (see UiKit).
static func theme() -> Theme:
	return UiKit.theme()


## Pictures for the switches and the other controls the engine draws from SVG.
static func add_switches(to: Theme) -> void:
	UiKit.add_pictures(to)


## Fills the whole screen with the backdrop, top to bottom.
static func backdrop() -> Control:
	return UiKit.backdrop()


## A full screen with the backdrop and a centred column to put things in. It
## scrolls only if what's in it is taller than the screen.
static func screen(root: Control) -> VBoxContainer:
	root.theme = theme()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var back := backdrop()
	root.add_child(back)
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var scroll := ScrollContainer.new()
	scroll.follow_focus = true
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var centre := CenterContainer.new()
	centre.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	centre.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.add_child(centre)
	var column := VBoxContainer.new()
	column.custom_minimum_size = Vector2(COLUMN_WIDTH, 0.0)
	column.add_theme_constant_override("separation", 12)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	centre.add_child(column)
	return column


static func title(text := "SnapRacers", subtitle := "") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.theme_type_variation = "TitleLabel"
	box.add_child(label)
	if subtitle != "":
		var sub := Label.new()
		sub.text = subtitle
		sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sub.add_theme_color_override("font_color", ACCENT)
		box.add_child(sub)
	return box


## A pill button. It works in a scrolling list too (see ScrollButton).
static func button(text: String, action: Callable, subtitle := "") -> Button:
	var b := ScrollButton.new()
	b.text = text if subtitle == "" else "%s\n%s" % [text, subtitle]
	b.custom_minimum_size = Vector2(0.0, BUTTON_HEIGHT)
	b.focus_mode = Control.FOCUS_ALL
	if action.is_valid():
		b.tapped.connect(action)
	return b


## Lights up a button as the chosen one of a set, with accent text and an
## outline, or puts it back to plain.
static func mark(b: Button, on: bool) -> void:
	var colour := ACCENT if on else Color.WHITE
	for state in ["font_color", "font_hover_color", "font_focus_color"]:
		b.add_theme_color_override(state, colour)
	for state in ["normal", "hover"]:
		b.remove_theme_stylebox_override(state)
		if on:
			var box := UiKit.pill(state) as SlantBox
			box.edge = ACCENT
			box.edge_width = 3
			b.add_theme_stylebox_override(state, box)


## Back (or Quit) under a menu's buttons.
static func back_at_bottom(column: Container, action: Callable, text := "Back") -> Button:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0.0, 6.0)
	column.add_child(gap)
	var b := link(text, action)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	column.add_child(b)
	return b


## Plain accent coloured text that works like a button, for Back.
static func link(text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.flat = true
	b.focus_mode = Control.FOCUS_ALL
	b.add_theme_color_override("font_color", ACCENT)
	b.add_theme_color_override("font_hover_color", ACCENT.lightened(0.2))
	b.add_theme_color_override("font_pressed_color", ACCENT.darkened(0.2))
	b.add_theme_font_size_override("font_size", 26)
	b.add_theme_stylebox_override("focus", UiKit.focus_ring(UiKit.LEAN, 2.0))
	b.pressed.connect(action)
	return b


## A slider for a setting, big enough for a thumb, with a thick track filled in
## the accent colour up to a slanted handle (see UiKit).
static func slider(value: float, changed: Callable, low := 0.0, high := 1.0, step := 0.1) -> HSlider:
	var s := HSlider.new()
	s.min_value = low
	s.max_value = high
	s.step = step
	s.value = value
	s.focus_mode = Control.FOCUS_ALL
	s.custom_minimum_size = Vector2(320.0, 48.0)
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.value_changed.connect(changed)
	return s


## A heading, with a line of grey explanation under it when there's one.
static func heading(text: String, explanation := "") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 26)
	label.add_theme_font_override("font", UiKit.font("heading"))
	box.add_child(label)
	if explanation != "":
		var more := Label.new()
		more.text = explanation
		more.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		more.add_theme_font_size_override("font_size", 18)
		more.add_theme_color_override("font_color", UiKit.MUTED)
		box.add_child(more)
	return box


## A page with its title in the top left, Back in the top right and a column
## underneath for what's on it. Returns that column.
## With `centred` the margin away from a camera hole grows to match, for a
## column as wide as the room inside the margins (see page_room()).
static func page(root: Control, heading_text: String, back: Callable, width := 760.0, centred := false) -> VBoxContainer:
	root.theme = theme()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := backdrop()
	root.add_child(bg)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 40)
	margin.add_theme_constant_override("margin_right", 40)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 16)
	root.add_child(margin)
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# The title and Back stay clear of a camera hole.
	var safe := SafeArea.new()
	root.add_child(safe)
	safe.pad(margin, centred)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 12)
	margin.add_child(outer)

	var top := HBoxContainer.new()
	outer.add_child(top)
	var label := Label.new()
	label.text = heading_text
	label.add_theme_font_size_override("font_size", 44)
	label.add_theme_font_override("font", UiKit.font("title"))
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(label)
	top.add_child(link("Back", back))

	var scroll := ScrollContainer.new()
	scroll.follow_focus = true
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)
	var centre := CenterContainer.new()
	centre.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(centre)
	var column := VBoxContainer.new()
	column.custom_minimum_size = Vector2(width, 0.0)
	column.add_theme_constant_override("separation", 18)
	centre.add_child(column)
	return column


## The page's margin container, for a column made by page().
static func page_margin(column: Control) -> MarginContainer:
	var node := column.get_parent()
	while node != null and not node is MarginContainer:
		node = node.get_parent()
	return node


## How wide a column made by page() can be inside the page's margins, which
## grow to clear a camera hole.
static func page_room(column: Control) -> float:
	# The margin container's own size grows with what's in it, so this goes
	# by the screen's.
	var margin := page_margin(column)
	return margin.get_viewport_rect().size.x - margin.get_theme_constant("margin_left") - margin.get_theme_constant("margin_right")
