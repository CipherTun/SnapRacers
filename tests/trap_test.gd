extends SceneTree

## Dropped road patches must miss the dropper's wheels, including long karts.
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/trap_test.gd
class Runner:
	extends Node
	var failures := 0

	func check(ok: bool, what: String) -> void:
		print(("  ok    " if ok else "  FAIL  ") + what)
		if not ok:
			failures += 1

	func frames(count: int) -> void:
		for i in count:
			await get_tree().physics_frame

	func make_kart(key: String, at: Vector3) -> Kart:
		var kart := Kart.new()
		kart.build(KartDesign.load_file("res://tests/data/legacy/%s.json" % key))
		kart.position = at
		add_child(kart)
		return kart

	func _ready() -> void:
		var ground := StaticBody3D.new()
		ground.collision_layer = Kart.LAYER_WORLD
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(160, 2, 160)
		shape.shape = box
		shape.position.y = -1.0
		ground.add_child(shape)
		add_child(ground)
		for key in ["starter", "rocket", "streamliner"]:
			for kind in ["spikes", "marbles"]:
				var dropper := make_kart(key, Vector3(-20, 0.05, 0))
				var control := make_kart(key, Vector3(20, 0.05, 0))
				await frames(60)
				dropper.give(kind)
				check(dropper.use_gadget(0), "%s drops %s" % [key, kind])
				await frames(2)
				var trap: BrickTrap = get_children().filter(func(n): return n is BrickTrap)[0]
				var wheels_clear := true
				for wheel in dropper.wheels:
					var at := dropper.to_global(wheel.rest)
					var query := PhysicsRayQueryParameters3D.create(at + Vector3.UP, at + Vector3.DOWN * 2, Kart.LAYER_WORLD, [dropper.get_rid()])
					var hit := dropper.get_world_3d().direct_space_state.intersect_ray(query)
					wheels_clear = wheels_clear and hit.get("collider") == ground
				check(wheels_clear, "%s's wheels are clear of its dropped %s" % [key, kind])
				for kart in [dropper, control]:
					kart.linear_velocity = Vector3(0, 0, -14)
					kart.controls.throttle = 1.0
				await frames(10)
				check(dropper.lost.is_empty(), "%s does not lose parts to its own %s" % [key, kind])
				check(absf(dropper.forward_speed - control.forward_speed) < 0.1, "%s drives away from %s normally (%.2f against %.2f m/s)" % [key, kind, dropper.forward_speed, control.forward_speed])
				trap.queue_free()
				dropper.queue_free()
				control.queue_free()
				await frames(2)
		print("All trap checks passed." if failures == 0 else "%d trap checks failed." % failures)
		get_tree().quit(1 if failures > 0 else 0)

func _initialize() -> void:
	root.add_child(Runner.new())
