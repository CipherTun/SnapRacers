class_name ViewBlockers
extends RefCounted

## Works out which of a kart's parts get in the way of its driver's view
## ahead in first person, so their own camera can draw those a little
## see-through (see Kart.head_layer and RaceCamera). It's worked out when the
## kart's put together, never while racing.
##
## A part is in the way if any of it shows inside the first person camera's
## view above the line from the eyes down to the road ROAD_AHEAD metres out.
## Everything is in the kart's own space, looking along -z.

## How see-through the parts in the way are drawn, as their opacity.
const OPACITY := 0.8
## Parts that only hide the road closer than this aren't in the way.
const ROAD_AHEAD := 6.0
## The first person camera's field of view (RaceCamera uses 75 degrees up and
## down) and a phone's shape, wide enough for most.
const UP := 0.767 # tan(37.5 degrees)
const ACROSS := UP * 2.2
const NEAR := 0.02

static var _materials := {}


## The layer of the see-through copies of the parts in the way, which only
## that driver's first person camera draws, two after their head's layer.
static func see_through_layer(head_layer: int) -> int:
	return head_layer + 2


## The layer of the solid parts in the way, which that camera leaves out.
static func blocking_layer(head_layer: int) -> int:
	return head_layer + 4


## Which of these looks are in the way, by their place in the list. `boxes`
## are each look's bounds, to skip most of them without looking closer.
static func find(looks: Array[Node3D], boxes: Array[AABB], eye: Vector3, ground_y: float) -> Array[int]:
	var down := maxf(eye.y - ground_y, 0.1) / ROAD_AHEAD
	var rect := Rect2(-ACROSS, -down, ACROSS * 2.0, UP + down)
	var found: Array[int] = []
	for i in looks.size():
		if _box_in_view(boxes[i], eye, rect) and _in_view(looks[i], looks[i].transform, eye, rect):
			found.append(i)
	return found


## The see-through material for one of KartMesh's, shared by every kart.
## Lamps stay as they are.
static func material(solid: Material) -> Material:
	if not solid is BaseMaterial3D:
		return solid
	if not _materials.has(solid):
		var m: BaseMaterial3D = solid.duplicate()
		if m.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
			# The depth pass first, so only the nearest side of the part shows
			# and its insides don't flicker through.
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
		m.albedo_color.a *= OPACITY
		_materials[solid] = m
	return _materials[solid]


static func _box_in_view(box: AABB, eye: Vector3, rect: Rect2) -> bool:
	var c: Array[Vector3] = []
	for k in 8:
		c.append(box.get_endpoint(k))
	# The box's six sides, two triangles each.
	for face in [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]:
		if _triangle_in_view(c[face[0]], c[face[1]], c[face[2]], eye, rect) \
				or _triangle_in_view(c[face[0]], c[face[2]], c[face[3]], eye, rect):
			return true
	return false


static func _in_view(node: Node, where: Transform3D, eye: Vector3, rect: Rect2) -> bool:
	if node is MeshInstance3D and node.mesh != null:
		for i in node.mesh.get_surface_count():
			if _surface_in_view(node.mesh.surface_get_arrays(i), where, eye, rect):
				return true
	elif node is MultiMeshInstance3D and node.multimesh != null and node.multimesh.mesh != null:
		var multi: MultiMesh = node.multimesh
		for k in multi.instance_count:
			for i in multi.mesh.get_surface_count():
				if _surface_in_view(multi.mesh.surface_get_arrays(i), where * multi.get_instance_transform(k), eye, rect):
					return true
	for child in node.get_children():
		if child is Node3D and _in_view(child, where * child.transform, eye, rect):
			return true
	return false


static func _surface_in_view(arrays: Array, where: Transform3D, eye: Vector3, rect: Rect2) -> bool:
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	var points := PackedVector3Array()
	points.resize(verts.size())
	for v in verts.size():
		points[v] = where * verts[v]
	if indices.is_empty():
		for t in range(0, points.size() - 2, 3):
			if _triangle_in_view(points[t], points[t + 1], points[t + 2], eye, rect):
				return true
	else:
		for t in range(0, indices.size() - 2, 3):
			if _triangle_in_view(points[indices[t]], points[indices[t + 1]], points[indices[t + 2]], eye, rect):
				return true
	return false


## Whether any of this triangle shows inside `rect`, where a point ahead of
## the eye at (x, y, -ahead) shows at (x, y) / ahead. Straight lines stay
## straight that way, so the triangle cut off at NEAR is still a flat shape.
static func _triangle_in_view(a: Vector3, b: Vector3, c: Vector3, eye: Vector3, rect: Rect2) -> bool:
	var tri: Array[Vector3] = [a - eye, b - eye, c - eye]
	if tri[0].z > -NEAR and tri[1].z > -NEAR and tri[2].z > -NEAR:
		return false
	# What shows of each corner ahead, and where each side crosses NEAR.
	var shown := PackedVector2Array()
	for k in 3:
		var p := tri[k]
		var q := tri[(k + 1) % 3]
		if p.z <= -NEAR:
			shown.append(Vector2(p.x, p.y) / -p.z)
		if (p.z <= -NEAR) != (q.z <= -NEAR):
			var cut := p.lerp(q, (-NEAR - p.z) / (q.z - p.z))
			shown.append(Vector2(cut.x, cut.y) / NEAR)
	return _overlaps(shown, rect)


## Whether a flat convex shape overlaps a rectangle, by looking for a line
## between them along the rectangle's sides and the shape's.
static func _overlaps(shape: PackedVector2Array, rect: Rect2) -> bool:
	var low := shape[0]
	var high := shape[0]
	for p in shape:
		low = low.min(p)
		high = high.max(p)
	if high.x < rect.position.x or low.x > rect.end.x or high.y < rect.position.y or low.y > rect.end.y:
		return false
	var corners := [rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)]
	for k in shape.size():
		var edge := shape[(k + 1) % shape.size()] - shape[k]
		var normal := Vector2(-edge.y, edge.x)
		if normal.length_squared() < 1e-12:
			continue
		var a_min := INF
		var a_max := -INF
		for p in shape:
			a_min = minf(a_min, normal.dot(p))
			a_max = maxf(a_max, normal.dot(p))
		var b_min := INF
		var b_max := -INF
		for p in corners:
			b_min = minf(b_min, normal.dot(p))
			b_max = maxf(b_max, normal.dot(p))
		if a_max < b_min or b_max < a_min:
			return false
	return true
