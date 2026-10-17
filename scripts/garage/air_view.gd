class_name AirView
extends Node3D

## The garage's picture of the wind on the kart. Every square the wind hits
## is tinted by how much drag it adds, blue for a little up to red for a lot,
## and a few lines of wind stream past from the front and fade out behind.
##
## It only uses the drag KartStats already worked out, and is made again only
## when the kart changes. The wind lines move in their shader, so nothing is
## done each frame. Everything here is in the garage's space, where a grid
## cell is Grid.UNIT across.

## A flat face, as a share of the most a square can catch, sits about here
## on the colours.
const LEAST := 0.3
const MOST := 1.6
const SQUARE_ALPHA := 0.9
const INSET := 0.006 # metres left between squares
const LINE_RADIUS := 0.016 # metres
## How far the wind lines start in front of the kart and go on behind it, in
## studs.
const AHEAD := 6.0
const BEHIND := 10.0
const LINE_STEP := 0.5 # studs between points along a wind line
## How steeply the wind climbs ahead of something in the way and settles
## behind it, in plates a stud for lines over the top and studs a stud for
## lines round the sides.
const CLIMB := 1.6
const SETTLE := 0.4
const SPREAD := 0.8
const CLOSE := 0.15

var _squares: MeshInstance3D
var _lines: MeshInstance3D
var _colours := Gradient.new()
var _wash: ShaderMaterial
var _washed: Array[Node3D] = []


func _ready() -> void:
	_colours.offsets = PackedFloat32Array([0.0, 0.35, 0.6, 0.8, 1.0])
	_colours.colors = PackedColorArray([Color("#3a7bff"), Color("#38d6c8"), Color("#ffd23a"), Color("#ff8a26"), Color("#e8302a")])
	_squares = MeshInstance3D.new()
	_squares.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_squares.material_override = _material("""
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
void vertex() {
	// Pulled a little toward the camera so it isn't lost in the face under it.
	vec4 view = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	view.z += 0.01;
	POSITION = PROJECTION_MATRIX * view;
}
void fragment() {
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a;
}
""")
	add_child(_squares)
	_lines = MeshInstance3D.new()
	_lines.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# UV.x goes from 0 at the start of a line to 1 at its end, and UV.y is
	# the distance along it in metres.
	_lines.material_override = _material("""
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
void fragment() {
	float a = fract(UV.y * 1.4 - TIME * 1.1);
	float streak = smoothstep(0.0, 0.7, a) * (1.0 - smoothstep(0.9, 1.0, a));
	float fade = smoothstep(0.0, 0.1, UV.x) * (1.0 - smoothstep(0.45, 1.0, UV.x));
	ALBEDO = vec3(0.9, 0.97, 1.0);
	ALPHA = fade * (0.25 + 0.65 * streak);
}
""")
	add_child(_lines)
	# Laid over the kart's own colours so the squares' colours stand out.
	_wash = _material("""
shader_type spatial;
render_mode unshaded, depth_draw_never;
void fragment() {
	ALBEDO = vec3(0.55, 0.57, 0.62);
	ALPHA = 0.85;
}
""")


func _material(code: String) -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = code
	var material := ShaderMaterial.new()
	material.shader = shader
	return material


func clear() -> void:
	_squares.mesh = null
	_lines.mesh = null
	for shape in _washed:
		if is_instance_valid(shape):
			_set_wash(shape, null)
	_washed.clear()


func _set_wash(node: Node, wash: Material) -> void:
	if node is GeometryInstance3D:
		node.material_overlay = wash
	for child in node.get_children():
		_set_wash(child, wash)


## Draws it for these stats, laying the squares on the models in `shapes`
## (the parts and the driver).
func show_for(stats: KartStats, shapes: Array[Node3D]) -> void:
	clear()
	for shape in shapes:
		_set_wash(shape, _wash)
	_washed = shapes.duplicate()
	if stats.drag_squares.is_empty():
		return
	_squares.mesh = _square_mesh(stats, _targets(shapes))
	_lines.mesh = _line_mesh(stats.drag_squares)


# The squares.

## Every mesh in the models, as [world to mesh, mesh to world, world box,
## triangles, whether it's the driver].
func _targets(shapes: Array[Node3D]) -> Array:
	var found := []
	for shape in shapes:
		var stack: Array[Node] = [shape]
		while not stack.is_empty():
			var node: Node = stack.pop_back()
			if not is_instance_valid(node) or node.is_queued_for_deletion():
				continue
			stack.append_array(node.get_children())
			if node is MeshInstance3D and node.mesh != null and node.is_visible_in_tree():
				var place: Transform3D = node.global_transform
				var faces: TriangleMesh = node.mesh.generate_triangle_mesh()
				if faces != null:
					found.append([place.affine_inverse(), place, place * node.mesh.get_aabb(), faces, shape is CharacterRig])
	return found


func _square_mesh(stats: KartStats, targets: Array) -> ArrayMesh:
	var full := Grid.STUD * Grid.PLATE * KartStats.BODY_DRAG
	var points := PackedVector3Array()
	var colours := PackedColorArray()
	for entry in stats.drag_squares:
		var key: Vector2i = entry[0]
		var x0 := key.x * Grid.STUD
		var y0 := key.y * Grid.PLATE
		var front: float = entry[1] * Grid.STUD
		var back: float = entry[2] * Grid.STUD
		var middle := Vector2(x0 + Grid.STUD * 0.5, y0 + Grid.PLATE * 0.5)
		# Where the wind meets it, and which way that face leans.
		# Squares where the wind meets no model, like through the gaps in a
		# frame or past a rider's elbows, are left out.
		# The driver's squares go on the driver wherever they are, since a rider
		# leans out past the seat over the tank.
		var driver: bool = entry[4] == "driver"
		var hit_z := INF
		var normal := Vector3.FORWARD
		var start := Vector3(middle.x, middle.y, front - (3.0 if driver else 0.5))
		for target in targets:
			if target[4] != driver:
				continue
			var box: AABB = target[2]
			if middle.x < box.position.x or middle.x > box.end.x or middle.y < box.position.y or middle.y > box.end.y:
				continue
			var to_mesh: Transform3D = target[0]
			var hit: Dictionary = (target[3] as TriangleMesh).intersect_ray(to_mesh * start, to_mesh.basis * Vector3.BACK)
			if hit.is_empty():
				continue
			var at: Vector3 = (target[1] as Transform3D) * (hit.position as Vector3)
			if at.z < hit_z and (driver or (at.z >= front - 0.02 and at.z <= back + 0.02)):
				hit_z = at.z
				normal = ((target[1] as Transform3D).basis * (hit.normal as Vector3)).normalized()
		if hit_z == INF:
			continue
		if normal.z > 0.0:
			normal = -normal
		if normal.z > -0.3:
			normal = Vector3(normal.x, normal.y, -0.3).normalized()
		var ratio: float = entry[3] / full
		var colour := _colours.sample(clampf((ratio - LEAST) / (MOST - LEAST), 0.0, 1.0))
		colour.a = SQUARE_ALPHA
		var corners: Array[Vector3] = []
		for corner in [Vector2(INSET, INSET), Vector2(Grid.STUD - INSET, INSET), Vector2(Grid.STUD - INSET, Grid.PLATE - INSET), Vector2(INSET, Grid.PLATE - INSET)]:
			var p: Vector2 = Vector2(x0, y0) + corner
			# Along the face's slope, but never more than a stud off.
			var dz: float = -(normal.x * (p.x - middle.x) + normal.y * (p.y - middle.y)) / normal.z
			corners.append(Vector3(p.x, p.y, hit_z + clampf(dz, -Grid.STUD, Grid.STUD) - 0.004))
		for i in [0, 1, 2, 0, 2, 3]:
			points.append(corners[i])
			colours.append(colour)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = points
	arrays[Mesh.ARRAY_COLOR] = colours
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


# The wind lines.

func _line_mesh(squares: Array) -> ArrayMesh:
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	for entry in squares:
		var key: Vector2i = entry[0]
		lo = lo.min(Vector3(key.x, key.y, entry[1]))
		hi = hi.max(Vector3(key.x + 1, key.y + 1, entry[2]))
	var steps: Array[float] = []
	var z := lo.z - AHEAD
	while z <= hi.z + BEHIND:
		steps.append(z)
		z += LINE_STEP
	var middle := (lo.x + hi.x) * 0.5
	var width := hi.x - lo.x
	var height := hi.y - lo.y
	var paths: Array[PackedVector3Array] = []
	# Over the top, across the kart.
	for across in [-0.3, 0.0, 0.3]:
		var x: float = middle + across * width
		var near := squares.filter(func(entry: Array) -> bool: return entry[0].x + 1 > x - 1.0 and entry[0].x < x + 1.0)
		var tops: Array[float] = []
		for step in steps:
			tops.append(_highest(near, step))
		var ys := _hull(tops, CLIMB, SETTLE, lo.y + height * (0.5 + absf(across)), 1.5)
		var path := PackedVector3Array()
		for i in steps.size():
			path.append(Vector3(x, ys[i], steps[i]))
		paths.append(path)
	# Round each side, low and high.
	for side in [-1.0, 1.0]:
		for up in [0.3, 0.7]:
			var y: float = lo.y + height * up
			var near := squares.filter(func(entry: Array) -> bool: return entry[0].y + 1 > y - 2.0 and entry[0].y < y + 2.0)
			var outs: Array[float] = []
			for step in steps:
				outs.append(_widest(near, middle, side, step))
			var xs := _hull(outs, SPREAD, CLOSE, width * 0.25, 0.6)
			var path := PackedVector3Array()
			for i in steps.size():
				path.append(Vector3(middle + side * xs[i], y, steps[i]))
			paths.append(path)

	var points := PackedVector3Array()
	var uvs := PackedVector2Array()
	for path in paths:
		_add_tube(path, points, uvs)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = points
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


## The top of these squares at this z, in plates, or -INF if there's nothing
## there.
func _highest(squares: Array, z: float) -> float:
	var top := -INF
	for entry in squares:
		var key: Vector2i = entry[0]
		if z >= entry[1] and z <= entry[2]:
			top = maxf(top, key.y + 1)
	return top


## How far out from the middle these squares reach on one side at this z,
## in studs, or -INF if there's nothing there.
func _widest(squares: Array, middle: float, side: float, z: float) -> float:
	var out := -INF
	for entry in squares:
		var key: Vector2i = entry[0]
		if z >= entry[1] and z <= entry[2]:
			out = maxf(out, (key.x + 1 - middle) if side > 0.0 else (middle - key.x))
	return out


## A smooth path that keeps `gap` clear of `shape`, climbing at `climb` a
## step before it and settling at `settle` after, and never below `least`.
func _hull(shape: Array[float], climb: float, settle: float, least: float, gap: float) -> Array[float]:
	var raw: Array[float] = []
	for i in shape.size():
		var best := least
		for j in shape.size():
			if shape[j] == -INF:
				continue
			var d := (j - i) * LINE_STEP
			best = maxf(best, shape[j] + gap - (climb * d if d > 0.0 else -settle * d))
		raw.append(best)
	# Smoothed out a little, a few times over.
	for pass_count in 3:
		var smooth: Array[float] = []
		for i in raw.size():
			var total := 0.0
			for k in range(-3, 4):
				total += raw[clampi(i + k, 0, raw.size() - 1)]
			smooth.append(total / 7.0)
		raw = smooth
	return raw


## A thin square tube along a path given in grid cells.
func _add_tube(path: PackedVector3Array, points: PackedVector3Array, uvs: PackedVector2Array) -> void:
	var at := PackedVector3Array()
	for p in path:
		at.append(p * Grid.UNIT)
	var rings := []
	var along := 0.0
	for i in at.size():
		if i > 0:
			along += at[i].distance_to(at[i - 1])
		var ahead := (at[mini(i + 1, at.size() - 1)] - at[maxi(i - 1, 0)]).normalized()
		var side := ahead.cross(Vector3.UP).normalized()
		var up := side.cross(ahead).normalized()
		var ring := []
		for k in 4:
			var angle := k * TAU / 4.0
			ring.append(at[i] + (side * cos(angle) + up * sin(angle)) * LINE_RADIUS)
		rings.append([ring, Vector2(float(i) / (at.size() - 1), along)])
	for i in rings.size() - 1:
		var a: Array = rings[i][0]
		var b: Array = rings[i + 1][0]
		var uv_a: Vector2 = rings[i][1]
		var uv_b: Vector2 = rings[i + 1][1]
		for k in 4:
			var n := (k + 1) % 4
			for corner in [[a[k], uv_a], [b[k], uv_b], [b[n], uv_b], [a[k], uv_a], [b[n], uv_b], [a[n], uv_a]]:
				points.append(corner[0])
				uvs.append(corner[1])
