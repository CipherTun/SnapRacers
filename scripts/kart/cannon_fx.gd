class_name CannonFx
extends MeshInstance3D

## A puff of fire or smoke for the cannon: a ball that grows, drifts and fades
## out. A muzzle flash, the trail behind a cannonball and the bang when it hits
## are all made of these.

## How many looks a puff goes through as it fades. Puffs share them, so a
## cannonball's dozens of puffs only make a few materials.
const STEPS := 8

static var _ball: SphereMesh
static var _looks: Dictionary = {}

var time := 0.4
var grow := 2.0
var drift := Vector3.ZERO
var _age := 0.0
var _from: Color
var _to: Color
var _step := -1
var _light: OmniLight3D


## One puff at `at`, `size` metres across, going from `from` to `to` as it
## fades.
static func puff(at: Vector3, size: float, from: Color, to: Color, time_ := 0.4, grow_ := 2.0, drift_ := Vector3.ZERO) -> CannonFx:
	var fx := CannonFx.new()
	fx.position = at
	fx.scale = Vector3.ONE * size
	fx.time = time_
	fx.grow = grow_
	fx.drift = drift_
	fx._from = from
	fx._to = to
	fx._show(0)
	return fx


## The flash and smoke out of the front of a kart firing, going `forward`.
static func muzzle(parent: Node, at: Vector3, forward: Vector3) -> void:
	var flash := puff(at, 1.6, Color(1.0, 0.6, 0.12, 0.95), Color(0.9, 0.2, 0.0, 0.0), 0.18, 3.0, forward * 5.0)
	parent.add_child(flash)
	parent.add_child(puff(at, 0.8, Color(1.0, 0.95, 0.6), Color(1.0, 0.55, 0.1, 0.0), 0.1, 2.0, forward * 6.0))
	for i in 5:
		var side := Vector3(sin(i * 2.4), cos(i * 1.9) * 0.5 + 0.5, sin(i * 4.1)) * 1.6
		parent.add_child(puff(at + forward * 0.4, 0.7, Color(0.42, 0.4, 0.38, 0.85), Color(0.6, 0.6, 0.6, 0.0), 0.8 + i * 0.07, 2.2, forward * 5.0 + side))


## A fireball and smoke where a cannonball hits.
static func bang(parent: Node, at: Vector3) -> void:
	var fire := puff(at, 2.0, Color(1.0, 0.55, 0.1, 0.95), Color(0.8, 0.15, 0.0, 0.0), 0.4, 3.0, Vector3.ZERO)
	fire.add_light(Color("#ff8a3d"), 14.0)
	parent.add_child(fire)
	parent.add_child(puff(at, 1.0, Color(1.0, 0.92, 0.55), Color(1.0, 0.5, 0.1, 0.0), 0.18, 3.0, Vector3.ZERO))
	for i in 6:
		var out := Vector3(sin(i * 1.05), 0.6 + 0.4 * cos(i * 2.3), cos(i * 0.63)) * 3.5
		parent.add_child(puff(at, 0.8, Color(0.35, 0.33, 0.31, 0.85), Color(0.55, 0.55, 0.55, 0.0), 0.8 + 0.06 * i, 2.0, out))
	for i in 6:
		var out := Vector3(sin(i * 1.05 + 0.4), 0.8 + 0.5 * sin(i * 1.7), cos(i * 1.05 + 0.4)) * 9.0
		parent.add_child(puff(at, 0.25, Color(1.0, 0.8, 0.3), Color(1.0, 0.3, 0.0, 0.0), 0.4, -1.0, out))


func _init() -> void:
	if _ball == null:
		_ball = SphereMesh.new()
		_ball.radius = 0.5
		_ball.height = 1.0
		_ball.radial_segments = 12
		_ball.rings = 6
	mesh = _ball
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	top_level = true


## The puff's look `step` of STEPS along from its start colour to its end.
func _show(step: int) -> void:
	if step == _step:
		return
	_step = step
	var colour := _from.lerp(_to, float(step) / (STEPS - 1))
	var key := colour.to_html()
	if not _looks.has(key):
		var look := StandardMaterial3D.new()
		look.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		look.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		look.albedo_color = colour
		_looks[key] = look
	material_override = _looks[key]


## A quick light that fades with the puff, `reach` metres. It's kept out of
## the puff's growing scale.
func add_light(colour: Color, reach: float) -> void:
	_light = OmniLight3D.new()
	_light.top_level = true
	_light.light_color = colour
	_light.light_energy = 3.0
	_light.omni_range = reach
	_light.position = position
	add_child(_light)


func _process(delta: float) -> void:
	_age += delta
	var t := clampf(_age / time, 0.0, 1.0)
	if t >= 1.0:
		queue_free()
		return
	position += drift * delta
	drift *= 1.0 - minf(delta * 3.0, 1.0)
	scale *= 1.0 + grow * delta
	_show(mini(int(t * STEPS), STEPS - 1))
	if _light != null:
		_light.global_position = global_position
		_light.light_energy = 3.0 * (1.0 - t)
