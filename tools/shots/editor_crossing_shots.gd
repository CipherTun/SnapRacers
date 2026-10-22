extends Node

## Takes a picture of the track editor with a level crossing on Peach Pit and
## the Straights drawer open, where the crossing tile is. Run it with its own
## XDG_DATA_HOME so the editor's autosave stays out of your profile:
##   XDG_DATA_HOME=/tmp/x xvfb-run -a -s '-screen 0 1600x720x24' tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . --resolution 1600x720 res://tools/shots/editor_crossing_shots.tscn

const OUT := "res://build/shots"
## Peach Pit's straight tile with room for a railway beside it.
const PIECE := 20
var host: Node


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Tracks.path_of("peach_pit")))
	var spot := -1
	for i in range(3, data.pieces.size()):
		var spec: Dictionary = data.pieces[i]
		if spec.get("type", "straight") != "straight" or spec.has("surface"):
			continue
		var pieces: Array = data.pieces.duplicate(true)
		var rest := int(spec.get("length", 1)) - 1
		pieces[i] = {"type": "crossing"}
		if rest > 0:
			pieces.insert(i + 1, {"type": "straight", "length": rest})
		var track := TrackPath.from_dict({"pieces": pieces, "hills": data.get("hills", 0.0), "name": data.name})
		if not LevelCrossing.cramped(track, track.crossing_offsets()[0]):
			data.pieces = pieces
			spot = i
			break
	data.name = "Crossing shot"
	var path := "user://crossing_shot.json"
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data))
	file.close()
	Game.show_track_editor()
	var editor: TrackEditor = null
	while editor == null:
		await get_tree().process_frame
		for child in host.get_children():
			if child is TrackEditor:
				editor = child
	editor.load_course(path)
	for i in 90:
		await get_tree().process_frame
	editor._select(spot)
	for i in 120:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(OUT + "/crossing_editor.png")
	print("saved editor")
	host.queue_free()
	for i in 3:
		await get_tree().process_frame
	get_tree().quit()
