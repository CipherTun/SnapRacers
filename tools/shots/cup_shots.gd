extends Node

## Captures the current cup picker, including trophy thumbnails.
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/cup_shots.tscn
func _ready() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	var host := Node.new()
	add_child(host)
	Game.start(host, false)
	Records.use_file("user://screenshot_records.cfg")
	Game.show_cups()
	# Give each batch of trophy thumbnails time to render and reach the cards.
	for i in 90:
		await get_tree().process_frame
		RenderingServer.force_draw.call_deferred()
		await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute("res://build/shots")
	get_viewport().get_texture().get_image().save_png("res://build/shots/cups.png")
	print("saved cups")
	get_tree().quit()
