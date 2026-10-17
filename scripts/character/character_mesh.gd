class_name CharacterMesh
extends RefCounted

## Bakes each moving part of a driver (a bone: the legs, the upper body, the
## head, each arm and each hand) into one mesh, so a driver is about ten draw
## calls however many pieces they wear. Each piece keeps its colour in the
## mesh's vertex colours, with one surface each for plastic, plastic seen from
## both sides, metal and glass. The face isn't baked, since it's painted.
##
## Also reads data/characters/pieces_made.json, the pieces modelled in
## tools/characters, and keeps the bakes per driver so the same driver is only
## baked once.

const MADE_PATH := "res://data/characters/pieces_made.json"
const FIGURE_PATH := "res://data/characters/figure.json"
## How many drivers' bakes are kept. Trying on pieces makes a new one each
## time, so past this they're all let go.
const MOST_KEPT := 48

static var _made := {}
static var _meshes := {}
static var _baked := {}
static var _materials := {}


static func made() -> Dictionary:
	if _made.is_empty():
		var data = JSON.parse_string(FileAccess.get_file_as_string(MADE_PATH))
		if typeof(data) == TYPE_DICTIONARY:
			_made = data
	return _made


## The figure's numbers as tools/characters/figure.py wrote them.
static func figure() -> Dictionary:
	var data = JSON.parse_string(FileAccess.get_file_as_string(FIGURE_PATH))
	return data if typeof(data) == TYPE_DICTIONARY else {}


## A piece of the bare figure's meshes by region, sitting or standing.
static func figure_regions(piece: String, seated := false) -> Dictionary:
	var entry: Dictionary = made().get("figure", {}).get(piece, {})
	if seated and entry.has("seated"):
		entry = entry.seated
	var out := {}
	for region in entry.get("regions", {}):
		out[region] = mesh(entry.regions[region])
	return out


## A style made in tools/characters, like a neck piece, or an empty one
## when that style isn't made there.
static func style(slot: String, name: String) -> Dictionary:
	return made().get("styles", {}).get(slot, {}).get(name, {})


## The colour and shine of a style's region, for a piece in `colour`. Main is
## the piece's own colour, dark and light are shades of it and the rest are
## fixed, from pieces_made.json.
static func region_colour(entry: Dictionary, region: String, colour: Color) -> Array:
	match region:
		"main":
			return [colour, float(entry.get("metallic", 0.0))]
		"dark":
			return [colour.darkened(0.3), 0.0]
		"light":
			return [colour.lightened(0.4), 0.0]
	var fixed: Array = made().get("colours", {}).get(region, ["#ff00ff", 0.0])
	return [Color(fixed[0]), float(fixed[1])]


static func mesh(path: String) -> Mesh:
	if not _meshes.has(path):
		_meshes[path] = load(path)
	return _meshes[path]


## The bakes kept for a driver, by bone, or an empty one.
static func kept(key: String) -> Dictionary:
	return _baked.get(key, {})


static func keep(key: String, bones: Dictionary) -> void:
	if _baked.size() >= MOST_KEPT:
		_baked.clear()
	_baked[key] = bones


## One mesh of every mesh under `bone` (in its space), except under the nodes
## in `skip` (other bones) and anything marked "unbaked". The meshes baked are
## freed. It's null when there's nothing to bake.
static func bake(bone: Node3D, skip: Array) -> ArrayMesh:
	var surfaces := {}
	var done: Array[Node] = []
	for child in bone.get_children():
		if child is Node3D and not skip.has(child):
			_gather(child, child.transform, surfaces, skip, done)
	for node in done:
		node.free()
	if surfaces.is_empty():
		return null
	var out := ArrayMesh.new()
	for kind in ["plastic", "both", "metal", "glass"]:
		if not surfaces.has(kind):
			continue
		var s: Array = surfaces[kind]
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = s[0]
		arrays[Mesh.ARRAY_NORMAL] = s[1]
		arrays[Mesh.ARRAY_COLOR] = s[2]
		arrays[Mesh.ARRAY_INDEX] = s[3]
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		out.surface_set_material(out.get_surface_count() - 1, material(kind))
	return out


## The toy plastic for one kind of surface, coloured by the mesh.
static func material(kind: String) -> Material:
	if _materials.has(kind):
		return _materials[kind]
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	# The colours are the pieces' own, which are sRGB like any colour picked.
	m.vertex_color_is_srgb = true
	m.roughness = 0.55
	m.metallic_specular = 0.35
	match kind:
		"both":
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
		"metal":
			m.metallic = 0.5
			m.roughness = 0.3
		"glass":
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
	CharacterRig.make_toy(m)
	_materials[kind] = m
	return m


static func _gather(node: Node3D, where: Transform3D, surfaces: Dictionary, skip: Array, done: Array[Node]) -> void:
	if node.has_meta("unbaked"):
		return
	if node is MeshInstance3D and node.mesh != null:
		for i in node.mesh.get_surface_count():
			var mat: Material = node.material_override if node.material_override != null else node.mesh.surface_get_material(i)
			_add(node.mesh.surface_get_arrays(i), where, mat, surfaces)
		done.append(node)
	for child in node.get_children():
		if child is Node3D and not skip.has(child):
			_gather(child, where * child.transform, surfaces, skip, done)


static func _add(arrays: Array, where: Transform3D, mat: Material, surfaces: Dictionary) -> void:
	var colour := Color.WHITE
	var kind := "plastic"
	if mat is StandardMaterial3D:
		colour = mat.albedo_color
		if mat.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
			kind = "glass"
		elif mat.metallic > 0.3:
			kind = "metal"
		elif mat.cull_mode == BaseMaterial3D.CULL_DISABLED:
			kind = "both"
	if not surfaces.has(kind):
		surfaces[kind] = [PackedVector3Array(), PackedVector3Array(), PackedColorArray(), PackedInt32Array()]
	var s: Array = surfaces[kind]
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL] if arrays[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	var start: int = s[0].size()
	s[0].append_array(where * verts)
	if normals.size() == verts.size():
		var turn := Transform3D(where.basis.inverse().transposed(), Vector3.ZERO)
		var moved: PackedVector3Array = turn * normals
		if not turn.basis.is_equal_approx(turn.basis.orthonormalized()):
			for v in moved.size():
				moved[v] = moved[v].normalized()
		s[1].append_array(moved)
	else:
		var up := PackedVector3Array()
		up.resize(verts.size())
		up.fill(Vector3.UP)
		s[1].append_array(up)
	var colours := PackedColorArray()
	colours.resize(verts.size())
	colours.fill(colour)
	s[2].append_array(colours)
	if indices.is_empty():
		indices.resize(verts.size())
		for v in verts.size():
			indices[v] = v
	# A mirror image turns the triangles inside out, so they go the other way.
	var flip := where.basis.determinant() < 0.0
	var shifted := PackedInt32Array()
	shifted.resize(indices.size())
	for i in indices.size():
		shifted[i] = indices[i - i % 3 + 2 - i % 3 if flip else i] + start
	s[3].append_array(shifted)
