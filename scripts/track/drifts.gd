class_name Drifts
extends Puddles

## Snow drifts on the road. They pile up over the race the same way puddles
## do (see Puddles.grow()): low and few at the start and deep by the end,
## mostly along the road's edges. A drift drags, more the deeper it is, and
## throws up powder as you push through.
##
## factor_at() is how deep the snow is at a point, from 0 to 1 of DEEP.

const DRIFT_PER_100M := [3.0, 6.0]
const DRIFT_SIZE := [3.0, 7.0]
## How high a full one is in the middle, in metres.
const DEEP := 0.5
## How many lie along an edge, out of every one, and how far they can lap
## over the edge.
const AT_EDGE := 0.6
const OVER_EDGE := 0.5
const SNOW := Color("#eef3f8")
## For the AI: one at least this deep is worth going round.
const AVOID_DEPTH := 0.45

## Powder thrown up: at most this many puffs at once, only for karts this
## close to a race camera (metres), and only above this speed in m/s.
const PUFFS := 48
const POWDER_RANGE := 35.0
const POWDER_SPEED := 4.0
## Puffs a second from a kart at 20 m/s in a full drift, and how long each lasts.
const PUFF_RATE := 30.0
const PUFF_LIFE := 0.7

const POWDER_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled, blend_mix, skip_vertex_transform;
varying vec2 shape;

void vertex() {
	// Each puff faces the camera, from its middle and size in INSTANCE_CUSTOM.
	vec3 middle = INSTANCE_CUSTOM.xyz;
	vec3 world = middle + (INV_VIEW_MATRIX[0].xyz * VERTEX.x + INV_VIEW_MATRIX[1].xyz * VERTEX.y) * INSTANCE_CUSTOM.w;
	VERTEX = (VIEW_MATRIX * vec4(world, 1.0)).xyz;
	shape = UV * 2.0 - 1.0;
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a * (1.0 - smoothstep(0.3, 1.0, length(shape)));
}
"""

static var _dome: ArrayMesh
static var _powder_shader: Shader

## The karts in the race, for the powder.
var karts: Array = []
var _powder: MultiMesh
## Each puff as [middle, velocity, age].
var _puffs: Array = []
var _owed := {}
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 1
	_make_powder()


func _seed_key(chance_seed: int, track: TrackPath) -> Array:
	return [chance_seed, track.name, "snow"]


func _per_100m() -> Array:
	return DRIFT_PER_100M


func _sizes() -> Array:
	return DRIFT_SIZE


func _spacing() -> float:
	return 0.6


func _across(rng: RandomNumberGenerator, radius: float, track: TrackPath) -> float:
	var half := track.width * 0.5
	if rng.randf() < AT_EDGE:
		return (1.0 if rng.randf() < 0.5 else -1.0) * maxf(half + OVER_EDGE - radius, 0.0)
	return rng.randf_range(-1.0, 1.0) * maxf(half - EDGE - radius, 0.0)


## How deep it is, 0 to 1, over a dome as high as the drift's grown.
func _profile(i: int, d: float, radius: float) -> float:
	if d >= radius:
		return 0.0
	return growth(i) * cos(d / radius * PI * 0.5)


func _worth_avoiding(i: int) -> bool:
	return growth(i) >= AVOID_DEPTH


func _mesh() -> Mesh:
	if _dome == null:
		# A low dome one across and one high, a little lumpy at the rim.
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		var sides := 12
		var rings := 4
		var point := func(ring: int, side: int) -> Vector3:
			var t := float(ring) / rings
			var r := 0.5 * sin((1.0 - t) * PI * 0.5)
			var a := TAU * side / sides
			return Vector3(cos(a) * r, sin(t * PI * 0.5), sin(a) * r)
		for ring in rings:
			for side in sides:
				var a: Vector3 = point.call(ring, side)
				var b: Vector3 = point.call(ring, side + 1)
				var c: Vector3 = point.call(ring + 1, side + 1)
				var d: Vector3 = point.call(ring + 1, side)
				tool.add_vertex(a)
				tool.add_vertex(b)
				tool.add_vertex(c)
				if ring < rings - 1:
					tool.add_vertex(a)
					tool.add_vertex(c)
					tool.add_vertex(d)
		tool.generate_normals()
		_dome = tool.commit()
	return _dome


func _colour() -> Color:
	return SNOW


func _surface() -> int:
	return SceneryKit.PLAIN


func _shape(i: int, flat: Basis, radius: float) -> Basis:
	return flat * Basis.from_scale(Vector3(radius * 2.0, maxf(DEEP * growth(i), 0.01), radius * 2.0))


func _make_powder() -> void:
	if spots.is_empty():
		set_process(false)
		return
	if _powder_shader == null:
		_powder_shader = Shader.new()
		_powder_shader.code = POWDER_SHADER
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	_powder = MultiMesh.new()
	_powder.transform_format = MultiMesh.TRANSFORM_3D
	_powder.use_colors = true
	_powder.use_custom_data = true
	_powder.mesh = quad
	_powder.instance_count = PUFFS
	_powder.visible_instance_count = 0
	_powder.custom_aabb = _multi.custom_aabb.grow(4.0) if _multi != null else AABB()
	var look := ShaderMaterial.new()
	look.shader = _powder_shader
	var draw := MultiMeshInstance3D.new()
	draw.multimesh = _powder
	draw.material_override = look
	draw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(draw)


## Throws up powder behind karts pushing through a drift near a camera, and
## moves the puffs along. It's only for looks, so it's not the same on
## every device.
func _process(delta: float) -> void:
	if _powder == null:
		return
	var cams := get_tree().get_nodes_in_group("race_cameras")
	for kart in karts:
		if not is_instance_valid(kart):
			continue
		var speed: float = kart.linear_velocity.length()
		var depth := factor_at(kart.global_position) if speed > POWDER_SPEED else 0.0
		if depth <= 0.05 or not _near(kart, cams):
			_owed.erase(kart)
			continue
		var owed: float = _owed.get(kart, 0.0) + PUFF_RATE * depth * speed / 20.0 * delta
		while owed >= 1.0 and _puffs.size() < PUFFS:
			owed -= 1.0
			var back: Vector3 = kart.global_basis.z
			var side: Vector3 = kart.global_basis.x * _rng.randf_range(-0.9, 0.9)
			var throw: Vector3 = kart.linear_velocity * 0.25 + Vector3.UP * _rng.randf_range(1.5, 3.0) + side * 1.5
			_puffs.append([kart.global_position + back * 0.6 + side + Vector3.UP * 0.2, throw, 0.0])
		_owed[kart] = minf(owed, 1.0)
	if _puffs.is_empty() and _powder.visible_instance_count == 0:
		return
	var i := 0
	while i < _puffs.size():
		var puff: Array = _puffs[i]
		puff[2] += delta
		if puff[2] >= PUFF_LIFE:
			_puffs.remove_at(i)
			continue
		puff[1] += Vector3.DOWN * 4.0 * delta
		puff[1] *= 1.0 - minf(2.0 * delta, 1.0)
		puff[0] += puff[1] * delta
		i += 1
	for n in _puffs.size():
		var puff: Array = _puffs[n]
		var t: float = puff[2] / PUFF_LIFE
		_powder.set_instance_custom_data(n, Color(puff[0].x, puff[0].y, puff[0].z, lerpf(0.4, 1.3, t)))
		_powder.set_instance_color(n, Color(1.0, 1.0, 1.0, 0.8 * (1.0 - t)))
	_powder.visible_instance_count = _puffs.size()


func _near(kart: Node3D, cams: Array) -> bool:
	if cams.is_empty():
		return false
	for cam in cams:
		if cam.target == kart or kart.global_position.distance_squared_to(cam.global_position) < POWDER_RANGE * POWDER_RANGE:
			return true
	return false
