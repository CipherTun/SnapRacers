extends Node

## Retakes the README's builder and kart-picker screens at 1280 x 720.
## Run with a separate XDG_DATA_HOME so editor autosaves stay in that profile:
##   xvfb-run -a -s '-screen 0 1280x720x24' tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . --fixed-fps 60 --disable-render-loop res://tools/shots/menu_shots.tscn
const OUT := "res://build/shots/readme"
var host: Node


func _ready() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	DirAccess.make_dir_recursive_absolute(OUT)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	Game.design = Game.stock_kart("quarter_mile").duplicate_design()
	Game.character = Game.roster_driver("racer").duplicate_design()
	Game.settings.set_value("race", "kart", "quarter_mile")

	Game.show_garage()
	var garage: Garage = await screen_of(Garage)
	garage.ui._show_category(2)
	await ready_pictures()
	await shot("garage")

	Game.show_kart_picker(Game.show_menu, Game.show_menu, true)
	var picker: KartPicker = await screen_of(KartPicker)
	await ready_pictures()
	var card: Control = picker._cards["night_shift"]
	for node in picker.find_children("*", "ScrollContainer", true, false):
		if node.is_ancestor_of(card):
			node.scroll_vertical = roundi(card.position.y)
	await get_tree().process_frame
	await shot("karts")

	Game.character = Game.roster_driver("brickley").duplicate_design()
	Game.show_driver()
	var driver: DriverBuilder = await screen_of(DriverBuilder)
	await ready_pictures()
	driver._last_touch = 0.0
	driver._turntable.rotation.y = PI + 0.25
	await shot("driver")

	Game.show_track_editor()
	var editor: TrackEditor = await screen_of(TrackEditor)
	editor.load_course(Tracks.path_of("pithead_park"))
	# Wait for the editor's full course build after loading.
	for i in 60:
		await get_tree().process_frame
	await ready_pictures()
	await shot("editor")
	host.queue_free()
	for i in 3:
		await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
	get_tree().quit()


func screen_of(kind: Variant) -> Node:
	for i in 120:
		await get_tree().process_frame
		for child in host.get_children():
			if is_instance_of(child, kind) and not child.is_queued_for_deletion():
				return child
	push_error("Screenshot screen did not open")
	get_tree().quit(1)
	return null


func ready_pictures() -> void:
	# Thumbnails need real render frames before their images reach the UI.
	for i in 180:
		await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
		var busy := false
		for node in get_tree().root.find_children("*", "", true, false):
			if node is PartThumbnails or node is KartThumbnails or node is DriverThumbnails:
				busy = busy or node.is_processing()
		if i >= 4 and not busy:
			return
	push_error("Screenshot thumbnails did not finish")
	get_tree().quit(1)


func shot(which: String) -> void:
	# One frame lays out the UI after the last thumbnail or scroll change.
	for i in 2:
		await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
	var picture := get_viewport().get_texture().get_image()
	if picture.get_size() != Vector2i(1280, 720):
		push_error("Unexpected screenshot dimensions: %s" % picture.get_size())
		get_tree().quit(1)
		return
	picture.save_png("%s/%s.png" % [OUT, which])
	print("saved ", which)
