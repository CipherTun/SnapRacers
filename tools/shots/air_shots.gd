extends Node

## Takes pictures of the garage with the wind shown, for a few stock karts
## from the front corner and the side. Like the other shots it needs a screen,
## and saves in build/shots, or the folder after --.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . res://tools/shots/air_shots.tscn -- /some/folder

const KARTS := ["starter", "streamliner", "superbike", "brick_tank"]

var out := "res://build/shots"


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		out = args[0]
	DirAccess.make_dir_recursive_absolute(out)
	var host := Node.new()
	add_child(host)
	Game.start(host, false)
	for key in KARTS:
		Game.design = Game.stock_kart(key)
		Game.show_garage()
		var garage: Garage = null
		while garage == null or not garage.is_node_ready():
			await get_tree().process_frame
			for child in host.get_children():
				if child is Garage and not child.is_queued_for_deletion():
					garage = child
		await get_tree().create_timer(1.0).timeout
		garage.set_air(true)
		for view in ["angle", "side"]:
			garage.show_view(view)
			await _save("%s_%s" % [key, view])
	get_tree().quit()


func _save(name: String) -> void:
	await get_tree().create_timer(0.7).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("%s/air_%s.png" % [out, name])
	print("saved ", name)
