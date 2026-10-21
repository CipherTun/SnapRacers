extends SceneTree

## An AI driver down a long empty straight, then a faster one stuck behind a
## slower one. The first should keep the stick still once it's up to speed,
## and the second should get past instead of sitting on the leader's bumper.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/ai_drive_test.gd


class Runner:
	extends Node

	var track: TrackPath
	var tick := 0
	var failures := 0
	var phase := "wiggle"
	var design: KartDesign
	var kart: Kart
	var ai: AIDriver
	var offset := 2.0
	var max_steer := 0.0
	var flips := 0
	var last_steer := 0.0
	var sampled := false
	var leader: Kart
	var chaser: Kart
	var leader_ai: AIDriver
	var chaser_ai: AIDriver
	var leader_off := 40.0
	var chaser_off := 8.0
	var passed_at := -1

	func _ready() -> void:
		track = TrackPath.from_dict({ "pieces": [{ "type": "straight", "length": 14 }] })
		add_child(TrackBuilder.new(track))
		design = KartDesign.load_file("res://tests/data/legacy/starter.json")
		_spawn_one(2.0, 0.0)

	func _spawn_one(at: float, across: float) -> void:
		kart = Kart.new()
		kart.build(design)
		kart.transform = track.place_at(at, across)
		add_child(kart)
		ai = AIDriver.new()
		ai.kart = kart
		ai.track = track
		ai.line = 0.0
		ai.skill = 0.95
		kart.controls = ai.controls
		add_child(ai)
		offset = at

	func _spawn_pass() -> void:
		ai.kart = null
		kart.queue_free()
		ai.queue_free()
		kart = null
		ai = null
		leader = Kart.new()
		leader.build(design)
		leader.transform = track.place_at(40.0, 0.0)
		add_child(leader)
		chaser = Kart.new()
		chaser.build(design)
		chaser.transform = track.place_at(8.0, 0.0)
		add_child(chaser)
		leader_ai = AIDriver.new()
		leader_ai.kart = leader
		leader_ai.track = track
		leader_ai.line = 0.0
		leader_ai.skill = 0.9
		leader_ai.pace = 0.55
		leader.controls = leader_ai.controls
		add_child(leader_ai)
		chaser_ai = AIDriver.new()
		chaser_ai.kart = chaser
		chaser_ai.track = track
		chaser_ai.line = 0.0
		chaser_ai.skill = 0.95
		chaser_ai.pace = 1.0
		chaser.controls = chaser_ai.controls
		add_child(chaser_ai)
		var karts: Array[Kart] = [leader, chaser]
		leader_ai.others = karts
		chaser_ai.others = karts
		leader_off = 40.0
		chaser_off = 8.0
		phase = "pass"

	func check(ok: bool, what: String) -> void:
		print(("  ok    " if ok else "  FAIL  ") + what)
		if not ok:
			failures += 1

	func _physics_process(_delta: float) -> void:
		tick += 1
		if phase == "wiggle":
			offset = track.offset_of(kart.global_position, offset, 30.0)
			ai.offset = offset
			if tick >= 480 and tick <= 720:
				sampled = true
				var s := kart.controls.steer
				max_steer = maxf(max_steer, absf(s))
				if last_steer != 0.0 and signf(s) != signf(last_steer) and absf(s) > 0.05:
					flips += 1
				last_steer = s
			if tick == 720:
				check(kart.linear_velocity.length() > 12.0, "it gets up to speed on the straight (%.1f m/s)" % kart.linear_velocity.length())
				check(max_steer < 0.28, "once it's up to speed the stick stays still (max %.2f)" % max_steer)
				check(flips <= 4, "and it doesn't flip the wheel back and forth (%d times)" % flips)
				_spawn_pass()
			return
		leader_off = track.offset_of(leader.global_position, leader_off, 30.0)
		chaser_off = track.offset_of(chaser.global_position, chaser_off, 30.0)
		leader_ai.offset = leader_off
		chaser_ai.offset = chaser_off
		if passed_at < 0 and chaser_off > leader_off + 3.0:
			passed_at = tick
			check(true, "the faster driver gets past (at %.1f s, %.0f m ahead)" % [(tick - 720) / 60.0, chaser_off - leader_off])
			finish()
			return
		if tick == 720 + 60 * 22:
			check(false, "the faster driver gets past within 22 s (it's %.0f m, leader %.0f m)" % [chaser_off, leader_off])
			finish()

	func finish() -> void:
		print("All AI drive checks passed." if failures == 0 else "%d AI drive checks failed." % failures)
		get_tree().quit(1 if failures > 0 else 0)


func _initialize() -> void:
	root.add_child(Runner.new())
