class_name BuilderStyle
extends RefCounted

## The look shared by the garage, the driver screen and the track editor.
## Whatever you're building fills the screen and every panel floats over it on
## its own dark, see-through backing.

# The colours, from UiKit: red for danger and for things that are wrong, blue
# for numbers and the see-through black behind panels.
const DANGER := UiKit.DANGER
const DATA := UiKit.BLUE
const SCRIM := Color(0, 0, 0, 0.65)
## The dark ink on the accent coloured buttons.
const ON_ACCENT := UiKit.ON_ACCENT
const TILE := Vector2(104, 104)
## Behind the thing being built.
const BACKGROUND := Color("#2b3440")


## The see-through black behind a panel.
static func scrim(radius := 12, alpha := 0.65) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0, 0, 0, alpha)
	style.set_corner_radius_all(radius)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


## A word button, bold capitals in a colour with no box.
static func word(text: String, colour: Color, action: Callable) -> Button:
	var button := Button.new()
	button.text = text.to_upper()
	button.flat = true
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(0, 48)
	button.add_theme_font_size_override("font_size", 19)
	button.add_theme_stylebox_override("focus", UiKit.focus_ring(UiKit.LEAN, 0.0))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, colour)
	button.add_theme_color_override("font_disabled_color", Color(colour, 0.35))
	button.pressed.connect(action)
	return button


## Dresses a button as a small tinted chip, for the smaller controls.
static func chip(button: Button, text: String) -> void:
	button.text = text.to_upper()
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(96, 48)
	button.add_theme_font_size_override("font_size", 19)
	for state in UiKit.STATES:
		button.add_theme_stylebox_override(state, UiKit.chip(state))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, MenuStyle.ACCENT)
	button.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.35))


## A slanted button with a coloured fill.
static func pill(text: String, fill: Color, ink: Color, action: Callable, height := 56.0) -> Button:
	var button := Button.new()
	button.text = text.to_upper()
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(0, height)
	button.add_theme_font_size_override("font_size", 22)
	for state in UiKit.STATES:
		button.add_theme_stylebox_override(state, UiKit.solid(state, fill, UiKit.LEAN, height))
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, ink)
	button.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.35))
	button.pressed.connect(action)
	return button


## The big accent button, and the dark one that sits beside it.
static func main_pill(text: String, action: Callable) -> Button:
	return pill(text, Color(MenuStyle.ACCENT, 0.9), ON_ACCENT, action)


static func dark_pill(text: String, action: Callable) -> Button:
	return pill(text, SCRIM, Color.WHITE, action)


## Colours a round swatch, with a white ring around it when it's the one picked.
static func show_swatch(swatch: Button, colour: Color, picked: bool) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = colour
	style.set_corner_radius_all(int(swatch.custom_minimum_size.x * 0.5))
	if picked:
		style.border_color = Color.WHITE
		style.set_border_width_all(4)
	for state in ["normal", "hover", "pressed"]:
		swatch.add_theme_stylebox_override(state, style)


## A pop up list of choices on a dark backing.
static func menu(items: Array) -> PopupMenu:
	var list := PopupMenu.new()
	list.theme = MenuStyle.theme()
	list.add_theme_font_size_override("font_size", 24)
	list.add_theme_constant_override("v_separation", 18)
	list.add_theme_stylebox_override("panel", UiKit.popup())
	for i in items.size():
		list.add_item(items[i], i)
	return list


## The handle left at the edge of the screen when a drawer is put away.
static func drawer_handle(action: Callable) -> Button:
	var handle := Button.new()
	handle.focus_mode = Control.FOCUS_ALL
	handle.custom_minimum_size = Vector2(30, 80)
	var tab_style := StyleBoxFlat.new()
	tab_style.bg_color = SCRIM
	tab_style.corner_radius_top_right = 12
	tab_style.corner_radius_bottom_right = 12
	for state in ["normal", "hover", "pressed"]:
		handle.add_theme_stylebox_override(state, tab_style)
	handle.text = "›"
	handle.add_theme_font_size_override("font_size", 30)
	handle.pressed.connect(action)
	return handle


## The backing of a tile in a drawer, lit up when it's the one picked.
static func tile_box(state: String, picked := false) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = Color(1, 1, 1, 0.06 if state != "pressed" else 0.18)
	box.set_corner_radius_all(6)
	box.content_margin_top = 4
	box.content_margin_bottom = 4
	if picked:
		box.bg_color = Color(MenuStyle.ACCENT, 0.22)
		box.border_color = MenuStyle.ACCENT
		box.set_border_width_all(2)
	return box
