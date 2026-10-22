extends SceneTree

## The edges of the road, with bumpy curbs on the corners that throw you into
## the air at speed, grass that slows you down without stopping you dead, no
## sliding off the road, and soft tire stacks you bounce off. It builds a
## little course of hairpins and straights and drives the Starter over each.
##
## Run it with:
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/runoff_test.gd

var failures := 0
var world: Node3D
var builder: TrackBuilder
var track: TrackPath


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func _initialize() -> void:
	_run.call_deferred()


func frames(n: int) -> void:
	for i in n:
		await physics_frame


func road_pad(at: Vector3, size: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = Kart.LAYER_WORLD
	body.set_meta("grip", 1.0)
	body.set_meta("drag", 1.0)
	var shape := CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	shape.shape.size = size
	body.add_child(shape)
	body.position = at
	world.add_child(body)
	return body


func kart_at(where: Transform3D, speed: float) -> Kart:
	var kart := Kart.new()
	kart.build(KartDesign.load_file("res://tests/data/legacy/starter.json"))
	kart.transform = where
	world.add_child(kart)
	kart.linear_velocity = -where.basis.z * speed
	return kart


func _run() -> void:
	world = Node3D.new()
	root.add_child(world)
	# A long rectangle: two straights joined by hairpins at each end.
	track = TrackPath.from_dict({"theme": "orchard", "pieces": [
		{"type": "straight", "length": 3},
		{"type": "curve", "turn": "right", "size": 1},
		{"type": "curve", "turn": "right", "size": 1},
		{"type": "straight", "length": 3},
		{"type": "curve", "turn": "right", "size": 1},
		{"type": "curve", "turn": "right", "size": 1},
	]})
	check(track.closes, "the test course closes")
	builder = TrackBuilder.new(track)
	builder.scenery = "none"
	builder.sky = false
	world.add_child(builder)
	await frames(2)

	var walls := 0
	var kerbs: Array[StaticBody3D] = []
	for child in builder.get_children():
		if child is StaticBody3D and child.get_meta("kerb", false):
			kerbs.append(child)
	check(kerbs.size() >= 4, "the hairpins have curbs, inside and out (%d)" % kerbs.size())
	# Nothing sticks up beside the road at ground level: a ray just above the
	# road, out across the edge, hits nothing.
	var space := world.get_world_3d().direct_space_state
	for offset: float in [20.0, 60.0]:
		var frame := track.frame_at(offset)
		for side: float in [-1.0, 1.0]:
			var from: Vector3 = frame.origin + frame.basis.y * 0.4 + frame.basis.x * side * (track.width * 0.5 - 1.0)
			var query := PhysicsRayQueryParameters3D.create(from, from + frame.basis.x * side * 6.0)
			if not space.intersect_ray(query).is_empty():
				walls += 1
	check(walls == 0, "there are no walls beside the road at ground level (%d)" % walls)

	# Riding a curb, fast and then slowly. It's a long straight one on a strip
	# of road, with the kart's right hand wheels on it and nothing steering.
	road_pad(Vector3(-82.0, 0.04, -50.0), Vector3(8.0, 0.08, 400.0))
	var strip := StaticBody3D.new()
	strip.collision_layer = Kart.LAYER_WORLD
	strip.set_meta("kerb", true)
	strip.set_meta("grip", TrackBuilder.KERB_GRIP)
	var box := CollisionShape3D.new()
	box.shape = BoxShape3D.new()
	box.shape.size = Vector3(1.5, TrackBuilder.KERB_HEIGHT * 2.0, 400.0)
	strip.add_child(box)
	strip.position = Vector3(-80.0, 0.0, -50.0)
	world.add_child(strip)
	for speed: float in [22.0, 3.0]:
		var airborne := await ride_kerb(Vector3(-80.75, 0.35, 60.0), speed)
		if speed > 10.0:
			check(airborne > 0.1, "riding a curb at %d m/s throws the wheels into the air (%.2f of the time)" % [speed, airborne])
		else:
			check(airborne < 0.03, "at %d m/s a curb only rumbles (%.2f of the time in the air)" % [speed, airborne])

	# Running wide onto the grass at speed, and coasting.
	var off := track.frame_at(40.0)
	off.origin += off.basis.x * (track.width * 0.5 + 6.0) + Vector3.UP * 0.3
	var kart := kart_at(off, 24.0)
	await frames(30)
	var after_half := kart.forward_speed
	check(after_half > 24.0 * 0.6, "running onto the grass doesn't stop you dead (%.1f m/s after half a second)" % after_half)
	check(kart.off_road > 0.5, "the wheels know they're off the road (%.2f)" % kart.off_road)
	await frames(180)
	check(kart.forward_speed < 24.0 * 0.55, "but coasting on it slows you right down (%.1f m/s after 3.5 s)" % kart.forward_speed)
	check(kart.global_basis.y.y > 0.8, "and you stay on your wheels (up.y %.2f)" % kart.global_basis.y.y)
	kart.queue_free()

	# Even on the gas, grass is slower than the road, and you can't slide there.
	var road := StaticBody3D.new()
	road.collision_layer = Kart.LAYER_WORLD
	road.set_meta("grip", 1.0)
	road.set_meta("drag", 1.0)
	var road_box := CollisionShape3D.new()
	road_box.shape = BoxShape3D.new()
	road_box.shape.size = Vector3(8.0, 0.08, 400.0)
	road.add_child(road_box)
	road.position = Vector3(-100.0, 0.04, -50.0)
	world.add_child(road)
	var on_road := kart_at(Transform3D(Basis.IDENTITY, Vector3(-100.0, 0.35, 60.0)), 22.0)
	on_road.controls.throttle = 1.0
	var on_grass := kart_at(off, 22.0)
	on_grass.controls.throttle = 1.0
	await frames(120)
	check(on_grass.forward_speed < on_road.forward_speed * 0.85, "on the gas, grass is slower than the road (%.1f against %.1f m/s)" % [on_grass.forward_speed, on_road.forward_speed])
	check(on_grass.forward_speed > 6.0, "without stopping you dead (%.1f m/s)" % on_grass.forward_speed)
	on_grass.controls.brake = 1.0
	on_grass.controls.steer = 1.0
	await frames(12)
	check(not on_grass.sliding, "you can't start a slide on the grass")
	on_grass.sliding = true
	on_grass.slide_way = 1.0
	on_grass.slide_amount = 1.0
	await frames(4)
	check(not on_grass.sliding, "and a slide already going ends as soon as you're off the road")
	on_road.queue_free()
	on_grass.queue_free()
	road.queue_free()

	var sand: Array = TrackPath.OFFROAD["sand"]
	var grass: Array = TrackPath.OFFROAD["grass"]
	var snow: Array = TrackPath.OFFROAD["snow"]
	check(sand[0] < grass[0] and grass[0] < TrackPath.SURFACES["asphalt"][0], "sand off the road grips less than grass, and both less than the road (sand %.2f, grass %.2f)" % [sand[0], grass[0]])
	check(sand[1] > grass[1] and grass[1] > TrackPath.SURFACES["asphalt"][1], "and both drag more, sand the most (sand %.1f, grass %.1f)" % [sand[1], grass[1]])
	check(snow[0] < grass[0] and snow[1] > 1.0, "snow off the road is slipperier than grass and still slow")

	# A line of tire stacks, out on the grass, and a kart driving into it on a
	# short strip of road so the grass doesn't eat its speed first.
	var kit := SceneryKit.new()
	var line_at := Vector3(-60.0, 0.0, 70.0)
	for i in 20:
		Props.barrier_stack(kit, line_at + Vector3(-8.0 + i * 0.8, 0.0, 0.0), Props.RED)
	var holder := Node3D.new()
	world.add_child(holder)
	kit.build(holder)
	road_pad(Vector3(-60.0, 0.04, 80.0), Vector3(8.0, 0.08, 24.0))
	kart = kart_at(Transform3D(Basis.IDENTITY, line_at + Vector3(0.0, 0.3, 20.0)), 15.0)
	await frames(120)
	check(kart.global_position.z > line_at.z + 0.5, "a kart doesn't go through the tire stacks (%.1f m in front)" % (kart.global_position.z - line_at.z))
	check(kart.linear_velocity.z > 0.5, "it bounces back off them (%.1f m/s)" % kart.linear_velocity.z)
	check(kart.global_basis.y.y > 0.7, "and it's still upright (up.y %.2f)" % kart.global_basis.y.y)

	await mud_checks()

	print("All runoff checks passed." if failures == 0 else "%d runoff checks failed." % failures)
	quit(1 if failures > 0 else 0)


## Puts a kart at `at` going at `speed` with its throttle held (so it keeps
## going), for two seconds, and says how much of the time its wheels were off
## the ground.
func ride_kerb(at: Vector3, speed: float) -> float:
	var kart := kart_at(Transform3D(Basis.IDENTITY, at), speed)
	kart.controls.throttle = 1.0 if speed > 10.0 else 0.15
	await frames(20)
	var off := 0
	var total := 0
	for i in 120:
		await physics_frame
		for w in kart.wheels:
			total += 1
			if not w.grounded:
				off += 1
	kart.queue_free()
	await frames(2)
	return float(off) / maxf(total, 1)


## Mud as a road piece grips and drags between dirt and grass, so on the gas
## it's slower than dirt and quicker than grass. A built mud piece carries its
## grip and drag, and the ground beside the road can be mud too.
func mud_checks() -> void:
	var mud: Array = TrackPath.SURFACES["mud"]
	var dirt: Array = TrackPath.SURFACES["dirt"]
	var grass: Array = TrackPath.SURFACES["grass"]
	check(mud[0] < dirt[0] and mud[0] > grass[0], "mud grips between dirt and grass (%.2f)" % mud[0])
	check(mud[1] > dirt[1] and mud[1] < grass[1], "and drags between them (%.1f)" % mud[1])
	var off_mud: Array = TrackPath.OFFROAD["mud"]
	check(off_mud[0] <= TrackPath.OFFROAD["dirt"][0] and off_mud[0] >= TrackPath.OFFROAD["grass"][0] and off_mud[1] >= TrackPath.OFFROAD["dirt"][1] and off_mud[1] <= TrackPath.OFFROAD["grass"][1], "mud beside the road is between dirt and grass too")
	check(TrackBuilder.COLOURS.has("mud"), "mud has its own colour")

	var muddy := TrackPath.from_dict({"theme": "orchard", "pieces": [
		{"type": "straight", "length": 2, "surface": "mud"},
		{"type": "straight", "length": 2},
	]})
	var built := TrackBuilder.new(muddy)
	built.scenery = "none"
	built.sky = false
	built.position = Vector3(400.0, 0.0, 0.0)
	world.add_child(built)
	await frames(2)
	var found := false
	for child in built.get_children():
		if child is StaticBody3D and child.get_meta("piece", -1) == 0:
			found = is_equal_approx(child.get_meta("grip", 0.0), mud[0]) and is_equal_approx(child.get_meta("drag", 0.0), mud[1])
	check(found, "a mud piece's road has mud's grip and drag")
	built.queue_free()

	# Three strips side by side, far from everything else, each a surface,
	# and the same kart on the gas down each.
	var speeds := {}
	var karts := {}
	var x := 200.0
	for surface in ["dirt", "mud", "grass"]:
		var feel: Array = TrackPath.SURFACES[surface]
		var strip := road_pad(Vector3(x, 0.04, -50.0), Vector3(8.0, 0.08, 400.0))
		strip.set_meta("grip", feel[0])
		strip.set_meta("drag", feel[1])
		var k := kart_at(Transform3D(Basis.IDENTITY, Vector3(x, 0.35, 120.0)), 18.0)
		k.controls.throttle = 1.0
		karts[surface] = k
		x += 20.0
	await frames(180)
	for surface in karts:
		speeds[surface] = karts[surface].forward_speed
		karts[surface].queue_free()
	check(speeds.mud < speeds.dirt and speeds.mud > speeds.grass, "on the gas, mud is slower than dirt and quicker than grass (dirt %.1f, mud %.1f, grass %.1f m/s)" % [speeds.dirt, speeds.mud, speeds.grass])
	await frames(2)
