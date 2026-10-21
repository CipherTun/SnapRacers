class_name ZapFx
extends Node3D

## Lightning on a struck kart: a bolt from the sky, then sparks and a glow
## that stay on for as long as the kart is slowed.

const COLOUR := Color(1.0, 0.92, 0.35, 1.0)
const EMIT := Color(1.0, 0.95, 0.55)
## The sky bolt is only on for this long at the start. Sparks and the glow
## last the whole slowdown.
const BOLT_TIME := 0.55
const SPARK_EVERY := 0.07

var _age := 0.0
var _spark_wait := 0.0
var _bolt: MeshInstance3D
var _column: MeshInstance3D
var _glow: MeshInstance3D
var _disc: MeshInstance3D
var _sparks: Array[MeshInstance3D] = []
var _light: OmniLight3D
var _rng := RandomNumberGenerator.new()

static var _spark_mesh: ArrayMesh


func _init() -> void:
	top_level = true
	_rng.randomize()
	_bolt = _mesh(_sky_bolt(), 1.4)
	add_child(_bolt)
	var pole := CylinderMesh.new()
	pole.top_radius = 0.06
	pole.bottom_radius = 0.2
	pole.height = 16.0
	pole.radial_segments = 8
	pole.cap_top = false
	pole.cap_bottom = false
	_column = _mesh(pole, 1.1)
	_column.position.y = 8.0
	add_child(_column)
	var ball := SphereMesh.new()
	ball.radius = 1.35
	ball.height = 2.7
	ball.radial_segments = 16
	ball.rings = 8
	_glow = _mesh(ball, 0.7)
	_glow.position.y = 0.7
	add_child(_glow)
	var pad := CylinderMesh.new()
	pad.top_radius = 1.0
	pad.bottom_radius = 1.0
	pad.height = 0.1
	pad.radial_segments = 20
	_disc = _mesh(pad, 1.0)
	_disc.position.y = 0.05
	add_child(_disc)
	if _spark_mesh == null:
		_spark_mesh = _ribbon(_jagged(1.0, 0.45, 5), 0.08)
	for i in 5:
		var spark := _mesh(_spark_mesh, 1.2)
		add_child(spark)
		_sparks.append(spark)
	_light = OmniLight3D.new()
	_light.light_color = Color("#fff1a8")
	_light.light_energy = 8.0
	_light.omni_range = 12.0
	_light.shadow_enabled = false
	_light.position.y = 1.4
	add_child(_light)
	_place_sparks()


func _ready() -> void:
	_follow()


## Starts the strike over, if lightning hits a kart that's already zapped.
func restart() -> void:
	_age = 0.0
	_spark_wait = 0.0
	_place_sparks()


func _process(delta: float) -> void:
	if not _follow():
		return
	_age += delta
	var life := Kart.ZAP_TIME
	if _age >= life:
		queue_free()
		return
	var fade := 1.0 if _age < life - 0.4 else (life - _age) / 0.4
	var strike := clampf(1.0 - _age / BOLT_TIME, 0.0, 1.0)
	_bolt.visible = strike > 0.0
	_column.visible = strike > 0.0
	if strike > 0.0:
		_tint(_bolt, strike * 1.4)
		_tint(_column, strike)
		_column.scale = Vector3(1.0 + strike * 0.8, 1.0, 1.0 + strike * 0.8)
	var pulse := 0.55 + 0.45 * sin(_age * 18.0)
	_tint(_glow, fade * (0.22 + 0.2 * pulse))
	_glow.scale = Vector3.ONE * (1.0 + 0.12 * pulse + strike * 0.5)
	_disc.scale = Vector3(lerpf(1.6, 3.2, 1.0 - strike), 1.0, lerpf(1.6, 3.2, 1.0 - strike))
	_tint(_disc, fade * (0.25 + strike * 0.7))
	_spark_wait -= delta
	if _spark_wait <= 0.0:
		_spark_wait = SPARK_EVERY
		_place_sparks()
	for spark in _sparks:
		_tint(spark, fade * (0.7 + 0.3 * pulse))
	if _light != null:
		_light.light_energy = fade * (2.2 + 6.0 * strike + 1.4 * pulse)


func _place_sparks() -> void:
	for spark in _sparks:
		var around := _rng.randf() * TAU
		var reach := _rng.randf_range(0.35, 1.15)
		spark.position = Vector3(cos(around) * reach, _rng.randf_range(0.25, 1.9), sin(around) * reach)
		spark.basis = Basis.from_euler(Vector3(
			_rng.randf_range(-0.8, 0.8),
			_rng.randf_range(0.0, TAU),
			_rng.randf_range(-0.8, 0.8)))
		var size := _rng.randf_range(1.4, 2.6)
		spark.scale = Vector3(size, size, size)


func _follow() -> bool:
	var kart := get_parent() as Node3D
	if kart == null or not is_instance_valid(kart):
		queue_free()
		return false
	global_position = kart.global_position
	global_basis = Basis.IDENTITY
	return true


func _sky_bolt() -> ArrayMesh:
	return _ribbon(PackedVector3Array([
		Vector3(0.15, 16.0, 0.0),
		Vector3(1.35, 13.4, 0.25),
		Vector3(-1.05, 10.8, -0.35),
		Vector3(0.95, 8.1, 0.4),
		Vector3(-0.75, 5.4, -0.2),
		Vector3(0.55, 2.9, 0.18),
		Vector3(-0.12, 1.2, 0.0),
		Vector3(0.0, 0.35, 0.0),
	]), 0.22)


func _jagged(height: float, jag: float, points: int) -> PackedVector3Array:
	var pts := PackedVector3Array()
	for i in points:
		var t := float(i) / float(points - 1)
		var side := 0.0 if i == 0 or i == points - 1 else (1.0 if i % 2 == 0 else -1.0) * jag
		pts.append(Vector3(side, t * height, side * 0.35))
	return pts


func _ribbon(points: PackedVector3Array, width: float) -> ArrayMesh:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in points.size() - 1:
		var a := points[i]
		var b := points[i + 1]
		var along := b - a
		var side := along.cross(Vector3.UP)
		if side.length_squared() < 0.0001:
			side = along.cross(Vector3.FORWARD)
		side = side.normalized() * (width * 0.5)
		var a0 := a - side
		var a1 := a + side
		var b0 := b - side
		var b1 := b + side
		for vertex in [a0, a1, b1, a0, b1, b0]:
			tool.set_normal(Vector3.UP)
			tool.add_vertex(vertex)
	tool.index()
	return tool.commit()


func _mesh(mesh: Mesh, bright: float) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	var look := StandardMaterial3D.new()
	look.albedo_color = COLOUR
	look.emission_enabled = true
	look.emission = EMIT * bright
	look.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	look.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	look.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	look.cull_mode = BaseMaterial3D.CULL_DISABLED
	node.material_override = look
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return node


func _tint(node: MeshInstance3D, alpha: float) -> void:
	var look: StandardMaterial3D = node.material_override
	var a := clampf(alpha, 0.0, 1.0)
	look.albedo_color.a = a
	look.emission = EMIT * a
