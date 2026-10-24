class_name PadKeyboard
extends PopupPanel

## A keyboard on the screen, for typing with a controller when there's no
## other way to. Press A on a typing box to bring it up, then pick out keys
## with the d-pad and press them with A. X deletes, Y is a space, and Start
## or B is done. Done hands the box what was typed as if Enter was pressed.
## A real keyboard types too, and its Escape puts the text back how it was.
##
## Each key press changes the box straight away, the same as typing would, so
## whatever listens for the box changing keeps up.

const ROWS := ["1234567890", "QWERTYUIOP", "ASDFGHJKL'", "ZXCVBNM-.!"]
const KEY := Vector2(64, 56)

var box: LineEdit
## Whether the next letter's a capital. It's on at the start of each word, the
## way a phone does it, and Shift turns it on or off.
var _capital := true
var _letters: Array[Button] = []
var _shift: Button
var _shown: Label
## The box's text when the keyboard came up, for Escape.
var _was := ""


## Lets a controller bring up the keyboard on this box.
static func attach(to: LineEdit) -> void:
	to.gui_input.connect(func(event: InputEvent) -> void:
		if event is InputEventJoypadButton and event.pressed and event.button_index == JOY_BUTTON_A:
			to.accept_event()
			open(to))


static func open(to: LineEdit) -> PadKeyboard:
	var keys := PadKeyboard.new()
	keys.box = to
	to.add_child(keys)
	var screen := to.get_viewport().get_visible_rect().size
	keys.reset_size()
	keys.position = Vector2i(roundi((screen.x - keys.size.x) * 0.5), roundi(screen.y - keys.size.y - 16.0))
	keys.popup()
	return keys


func _init() -> void:
	theme = MenuStyle.theme()
	transient = true
	exclusive = true
	# It stays up if another window takes the focus (see ShareWindow).
	popup_window = false


func _ready() -> void:
	# It types on the end, where a name's usually added to or deleted from.
	box.caret_column = box.text.length()
	_was = box.text
	_capital = _word_start()
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	add_child(column)
	_shown = Label.new()
	_shown.theme_type_variation = "LeadLabel"
	_shown.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_shown)
	for row in ROWS:
		var line := HBoxContainer.new()
		line.alignment = BoxContainer.ALIGNMENT_CENTER
		line.add_theme_constant_override("separation", 6)
		column.add_child(line)
		for character in row:
			var key := _key(character, line)
			key.pressed.connect(func() -> void: _type(key.text))
			if character != character.to_lower():
				_letters.append(key)
	var bottom := HBoxContainer.new()
	bottom.alignment = BoxContainer.ALIGNMENT_CENTER
	bottom.add_theme_constant_override("separation", 6)
	column.add_child(bottom)
	_shift = _key("Shift", bottom, 2.0)
	_shift.pressed.connect(func() -> void:
		_capital = not _capital
		_show())
	_key("Space", bottom, 3.0).pressed.connect(_type.bind(" "))
	_key("Delete", bottom, 2.0).pressed.connect(_delete)
	var done := _key("Done", bottom, 2.0)
	done.theme_type_variation = "MainButton"
	done.pressed.connect(_done)
	_show()
	_letters[0].grab_focus.call_deferred()


func _key(label: String, row: HBoxContainer, wide := 1.0) -> Button:
	var key := Button.new()
	key.text = label
	key.focus_mode = Control.FOCUS_ALL
	key.custom_minimum_size = Vector2(KEY.x * wide + 6.0 * (wide - 1.0), KEY.y)
	key.theme_type_variation = "KeyButton"
	row.add_child(key)
	return key


## X, Y, Start and B, so the commonest keys are a button away. Real keys go
## into the box too, so another keyboard on the screen (like Steam's) or a
## keyboard plugged in still types while this one's up. This runs in the
## keyboard's own viewport before its buttons see the event, so handling it
## here stops Space or Enter also pressing the key that's picked out.
func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		_typed(event)
		return
	if not event is InputEventJoypadButton or not event.pressed:
		return
	match event.button_index:
		JOY_BUTTON_X:
			_delete()
		JOY_BUTTON_Y:
			_type(" ")
		JOY_BUTTON_START, JOY_BUTTON_B:
			_done()
		_:
			return
	set_input_as_handled()


## A real key. The arrows and Tab still move between the keys on the screen,
## and everything else, let go or held with Ctrl or Alt, goes no further.
func _typed(key: InputEventKey) -> void:
	if key.keycode in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_TAB]:
		return
	set_input_as_handled()
	if not key.pressed:
		return
	match key.keycode:
		KEY_BACKSPACE:
			_delete()
		KEY_ENTER, KEY_KP_ENTER:
			_done()
		KEY_ESCAPE:
			_cancel()
		_:
			if key.unicode < 32 or key.ctrl_pressed or key.alt_pressed or key.meta_pressed:
				return
			var text := String.chr(key.unicode)
			# Typed as it comes, without this keyboard's own capitals.
			if box.max_length > 0 and box.text.length() + 1 > box.max_length:
				return
			box.insert_text_at_caret(text)
			_capital = text == " "
			_changed()


func _type(text: String) -> void:
	if text.length() == 1 and text != text.to_lower() and not _capital:
		text = text.to_lower()
	if box.max_length > 0 and box.text.length() + text.length() > box.max_length:
		return
	box.insert_text_at_caret(text)
	_capital = text == " "
	_changed()


func _delete() -> void:
	var at := box.caret_column
	if at <= 0:
		return
	box.delete_text(at - 1, at)
	_capital = _word_start()
	_changed()


## Whether the caret's at the start of a word.
func _word_start() -> bool:
	return box.caret_column == 0 or box.text[box.caret_column - 1] == " "


func _changed() -> void:
	box.text_changed.emit(box.text)
	_show()


func _done() -> void:
	hide()
	box.grab_focus()
	box.text_submitted.emit(box.text)
	queue_free()


## Closes without changing the box.
func _cancel() -> void:
	if box.text != _was:
		box.text = _was
		box.caret_column = _was.length()
		box.text_changed.emit(box.text)
	hide()
	box.grab_focus()
	queue_free()


func _show() -> void:
	_shown.text = box.text + "_"
	for key in _letters:
		key.text = key.text.to_upper() if _capital else key.text.to_lower()
	_shift.text = "Shift" if not _capital else "SHIFT"
