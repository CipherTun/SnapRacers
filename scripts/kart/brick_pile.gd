class_name BrickPile
extends RigidBody3D

## One of the loose bricks a brick dropper leaves behind, a handful of
## different sizes that tumble out the back and scatter. Karts hit them like
## anything else, so running into a pile at speed can knock your parts off.
## They clear away after a while.

const LIFETIME := 15.0
const SHRINK_TIME := 0.5
## Phones can't handle too many loose bodies, so past this many the oldest go
## first.
const MOST_AT_ONCE := 48
## Each brick in a drop: its size in studs across and along, whether it's a
## plate, and where it comes out, as (right, up) in metres from behind the
## middle of the kart. The same every time, so every device drops the same pile.
const DROP := [
	[Vector2i(2, 4), false, Vector2(0.0, 0.5)],
	[Vector2i(2, 2), false, Vector2(-0.7, 0.6)],
	[Vector2i(1, 4), false, Vector2(0.75, 0.7)],
	[Vector2i(2, 3), true, Vector2(-0.3, 1.0)],
	[Vector2i(1, 2), false, Vector2(0.4, 1.1)],
	[Vector2i(1, 1), false, Vector2(-0.9, 1.2)],
	[Vector2i(1, 3), false, Vector2(0.95, 1.3)],
	[Vector2i(2, 2), true, Vector2(0.1, 1.5)],
]
const BRICK_HIGH := 0.45
const PLATE_HIGH := 0.18
## Kilograms a cubic metre, so a 2 by 4 brick is about 5 kg.
const DENSITY := 22.0
const COLOURS := [Color("#c4281c"), Color("#f2cd37"), Color("#0d69ab"), Color("#f2f3f2"), Color("#237841"), Color("#da8540")]

static var _alive: Array[BrickPile] = []

var _age := 0.0


static func drop_behind(from: Kart) -> Array[BrickPile]:
	var out: Array[BrickPile] = []
	var back := from.global_basis.z
	var right := from.global_basis.x
	var up := from.global_basis.y
	for i in DROP.size():
		var each: Array = DROP[i]
		var studs: Vector2i = each[0]
		var size := Vector3(studs.x * Grid.STUD, PLATE_HIGH if each[1] else BRICK_HIGH, studs.y * Grid.STUD)
		var brick := BrickPile.new(size, COLOURS[i % COLOURS.size()])
		var spot: Vector2 = each[2]
		var at := from.global_position + back * (2.3 + i * 0.12) + right * spot.x + up * spot.y
		brick.transform = Transform3D(from.global_basis.rotated(up, i * 0.9), at)
		# Thrown back and out a little, spinning, so they spread across the road.
		brick.linear_velocity = from.linear_velocity * 0.3 + right * spot.x * 2.5 + up * (1.0 + spot.y)
		brick.angular_velocity = Vector3(sin(i * 2.1), cos(i * 1.7), sin(i * 3.3)) * 5.0
		out.append(brick)
	return out


func _init(size := Vector3(0.5, BRICK_HIGH, 1.0), colour := Color("#c4281c")) -> void:
	mass = maxf(size.x * size.y * size.z * DENSITY, 0.6)
	collision_layer = Kart.LAYER_HAZARD
	collision_mask = Kart.LAYER_WORLD | Kart.LAYER_KARTS | Kart.LAYER_HAZARD
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	add_child(shape)
	var look := MeshInstance3D.new()
	look.mesh = MeshKit.rounded_box(size - Vector3.ONE * 0.01, 0.02)
	look.material_override = PartVisuals.material(colour)
	add_child(look)
	add_child(PartVisuals.make_studs(size, colour))


func _ready() -> void:
	_alive.append(self)
	while _alive.size() > MOST_AT_ONCE:
		var oldest: BrickPile = _alive.pop_front()
		if is_instance_valid(oldest):
			oldest.queue_free()


func _exit_tree() -> void:
	_alive.erase(self)


func _physics_process(delta: float) -> void:
	_age += delta
	var left := LIFETIME - _age
	if left <= 0.0:
		queue_free()
	elif left < SHRINK_TIME:
		# Shrinking away, it stops getting in anyone's way.
		collision_layer = 0
		collision_mask = Kart.LAYER_WORLD
		var s := maxf(left / SHRINK_TIME, 0.01)
		for child in get_children():
			if child is Node3D and not child is CollisionShape3D:
				child.scale = Vector3.ONE * s
