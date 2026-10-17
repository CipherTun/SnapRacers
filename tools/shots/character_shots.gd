extends SceneTree

## Pictures of the drivers for checking the pieces made in tools/characters:
## a sheet of the figure standing, sitting and astride from all round, a sheet
## of a few looks, and a close-up lit the way the driver screen lights it, to
## judge the shine. Like the other shots it needs a screen, and saves in
## build/shots/characters.
##   DISPLAY=:0 tools/godot/Godot_v4.7.2-stable_linux.x86_64 --path . -s tools/shots/character_shots.gd
## Add --out=/some/folder to save them there as well.

const OUT := "res://build/shots/characters"
const TILE := Vector2i(480, 560)
const COLUMNS := 4

var _out_too := ""
var _view: SubViewport
var _camera: Camera3D
var _stand: Node3D
var _label: Label
var _env: Environment


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			_out_too = arg.substr(6)
	DisplayServer.window_set_size(TILE)
	_view = SubViewport.new()
	_view.size = TILE
	_view.own_world_3d = true
	_view.msaa_3d = Viewport.MSAA_4X
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_view)
	SkyAndSun.add_to(_view, 20.0, BuilderStyle.BACKGROUND)
	# Lit like the driver screen.
	for child in _view.get_children():
		if child is WorldEnvironment:
			_env = child.environment
			_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
			_env.ambient_light_color = Color("#e8e8e8")
			_env.ambient_light_energy = 0.38
			_env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
		elif child is DirectionalLight3D:
			child.light_energy = 0.75
			child.shadow_opacity = 0.55
			child.shadow_blur = 2.5
			child.shadow_bias = 0.08
			child.shadow_normal_bias = 2.5
	CharacterRig.add_toy_lights(_view)
	_camera = Camera3D.new()
	_camera.fov = 28.0
	_view.add_child(_camera)
	_stand = Node3D.new()
	_view.add_child(_stand)
	_label = Label.new()
	_label.add_theme_font_size_override("font_size", 22)
	_label.position = Vector2(10, 6)
	_view.add_child(_label)
	_run.call_deferred()


## The bare figure: no hair, hat or anything else on, one colour all over.
func bare() -> CharacterDesign:
	return CharacterDesign.from_dict({
		"name": "Bare",
		"head": {"style": "smile", "color": "#f2cd37"},
		"hair": {"style": "none", "color": "#6b4430"},
		"headgear": {"style": "none", "color": "#f4f4f4"},
		"torso": {"style": "tee", "color": "#0d69ab"},
		"arms": {"style": "long_sleeves", "color": "#0d69ab"},
		"legs": {"style": "trousers", "color": "#0d69ab"},
	})


func clear() -> void:
	for child in _stand.get_children():
		child.free()


func snap(text: String, at: Vector3, look: Vector3) -> Image:
	_label.text = text
	_camera.position = at
	_camera.look_at(look, Vector3.UP)
	for frame in 4:
		await process_frame
	await RenderingServer.frame_post_draw
	return _view.get_texture().get_image()


func sheet(images: Array, columns: int, size: Vector2i) -> Image:
	var rows := ceili(images.size() / float(columns))
	var out := Image.create(size.x * columns, size.y * rows, false, Image.FORMAT_RGBA8)
	out.fill(BuilderStyle.BACKGROUND)
	for i in images.size():
		var image: Image = images[i]
		image.convert(Image.FORMAT_RGBA8)
		out.blit_rect(image, Rect2i(Vector2i.ZERO, image.get_size()), Vector2i(i % columns * size.x, i / columns * size.y))
	return out


func save(image: Image, file: String) -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	image.save_png(OUT + "/" + file)
	if _out_too != "":
		DirAccess.make_dir_recursive_absolute(_out_too)
		image.save_png(_out_too.path_join(file))
	print("saved ", file)


func rig(design: CharacterDesign, sitting: bool, astride := false) -> CharacterRig:
	clear()
	var r := CharacterRig.new(design, sitting)
	r.astride = astride
	if not sitting:
		r.position = Vector3(0.0, CharacterRig.FEET_BELOW, 0.0)
	_stand.add_child(r)
	return r


func _run() -> void:
	var views := {"front": Vector3(0, 0.15, -1), "side": Vector3(-1, 0.1, 0), "three quarter": Vector3(-0.8, 0.35, -1), "back": Vector3(0.3, 0.25, 1)}
	var shots := []
	rig(bare(), false)
	var middle := Vector3(0.0, 0.52, 0.0)
	for v in views:
		shots.append(await snap("standing " + v, middle + views[v].normalized() * 3.0, middle))
	rig(bare(), true)
	middle = Vector3(0.0, 0.3, -0.05)
	for v in ["front", "side", "three quarter"]:
		shots.append(await snap("sitting " + v, middle + views[v].normalized() * 2.6, middle))
	var astride := rig(bare(), true, true)
	astride.grip(Vector3(-0.3, 0.42, -0.35), Vector3(0.3, 0.42, -0.35), Vector3.LEFT, Vector3.RIGHT)
	shots.append(await snap("astride side", middle + views["side"].normalized() * 2.6, middle))
	# In a kart and on a bike, holding on.
	for kart in ["classic", "superbike"]:
		clear()
		var model := KartModel.make(KartDesign.load_file("res://data/karts/stock/%s.json" % kart), bare())
		_stand.add_child(model)
		await process_frame
		var seat := Vector3(0.0, 0.6, 0.0)
		var found := model.find_children("*", "CharacterRig", true, false)
		if not found.is_empty():
			seat = (found[0] as Node3D).global_position + Vector3(0.0, 0.3, 0.0)
		shots.append(await snap("on the %s" % kart, seat + Vector3(-0.9, 0.35, -1.0).normalized() * 4.4, seat))
	save(sheet(shots, COLUMNS, TILE), "figure.png")

	# A few looks, to check the colour bands and the old pieces on the figure.
	shots = []
	var looks := [
		["short sleeves, shorts", {"arms": "short_sleeves", "legs": "shorts", "torso": "racing_suit"}],
		["boots, rolled sleeves", {"arms": "rolled", "legs": "boots", "torso": "jacket"}],
		["socks, wristbands", {"arms": "wristbands", "legs": "socks", "torso": "jersey"}],
		["robot", {"arms": "mechanical", "legs": "robot_legs", "torso": "robot"}],
		["gown, long gloves", {"arms": "long_gloves", "legs": "gown", "torso": "gown"}],
		["dino feet, scaly", {"arms": "scaly", "legs": "dino_feet", "torso": "dino_belly"}],
		["armoured", {"arms": "armoured", "legs": "armoured", "torso": "armour"}],
		["helmet and hair", {"headgear": "open_helmet", "hair": "short", "torso": "racing_suit"}],
	]
	for look in looks:
		var design := bare()
		for slot in look[1]:
			design.set_piece(slot, look[1][slot])
		design.set_piece("headgear", look[1].get("headgear", "none"), Color("#f4f4f4"))
		rig(design, false)
		middle = Vector3(0.0, 0.52, 0.0)
		shots.append(await snap(look[0], middle + views["three quarter"].normalized() * 3.0, middle))
	save(sheet(shots, COLUMNS, TILE), "looks.png")

	# Close up, lit like the driver screen, to judge the shine.
	_view.size = Vector2i(900, 900)
	DisplayServer.window_set_size(_view.size)
	_label.text = ""
	shots = []
	var r := rig(bare(), false)
	r.rotation.y = PI * 0.8
	shots.append(await snap("", Vector3(0.0, 1.0, 2.0), Vector3(0.0, 0.72, 0.0)))
	r.rotation.y = PI
	shots.append(await snap("", Vector3(0.0, 0.62, 1.6), Vector3(0.0, 0.42, 0.0)))
	save(sheet(shots, 2, _view.size), "closeup.png")
	quit()
