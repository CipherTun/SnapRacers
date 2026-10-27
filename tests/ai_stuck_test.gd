extends SceneTree

## An AI driver nose to nose with a kart someone's driving into it, pushing
## it back down the road, then two AI drivers that want the same bit of road
## driving into each other. Each AI should notice it isn't getting anywhere, ease off and
## get clear, and the person's kart must never be reset.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/ai_stuck_test.gd


class Runner:
	extends Node

	## How long each AI gets to get clear and on down the road, in seconds.
	const CLEAR_WITHIN := 12.0
	## How far on down the road counts as clear, in metres.
	const GET_ON := 25.0
	## How much harder than usual the person's kart pushes.
	const PERSON_PUSH := 3.0

	var track: TrackPath
	var design: KartDesign
	var failures := 0
	var phase := "person"
	var tick := 0
	var karts: Array[Kart] = []
	var drivers: Array[AIDriver] = []
	var offsets: Array[float] = []
	var starts: Array[float] = []
	var resets: Array[int] = []
	var person: Kart
	var person_resets := 0
	var most_gap := 0.0

	func _ready() -> void:
		track = TrackPath.from_dict({ "pieces": [{ "type": "straight", "length": 14 }] })
		add_child(TrackBuilder.new(track))
		design = KartDesign.load_file("res://tests/data/legacy/starter.json")
		_start_person()

	func _place(at: float, across: float, turn: float) -> Kart:
		var kart := Kart.new()
		kart.build(design)
		var frame := track.place_at(at)
		frame.origin += frame.basis.x * across
		frame.basis = frame.basis.rotated(frame.basis.y, -turn)
		kart.transform = frame
		add_child(kart)
		karts.append(kart)
		offsets.append(at)
		starts.append(at)
		var count := resets.size()
		resets.append(0)
		kart.was_reset.connect(func() -> void: resets[count] += 1)
		return kart

	func _drive(kart: Kart, line: float) -> AIDriver:
		var ai := AIDriver.new()
		ai.kart = kart
		ai.track = track
		ai.line = line
		ai.skill = 0.95
		kart.controls = ai.controls
		add_child(ai)
		drivers.append(ai)
		return ai

	func _clear() -> void:
		for ai in drivers:
			ai.kart = null
			ai.queue_free()
		for kart in karts:
			kart.queue_free()
		karts.clear()
		drivers.clear()
		offsets.clear()
		starts.clear()
		resets.clear()
		tick = 0

	## The AI with a person's kart nose to nose with it, pushing it back
	## down the road harder than the AI can push forward. The AI keeps
	## moving, backwards, so going by speed alone it never knows it's stuck.
	func _start_person() -> void:
		var ai_kart := _place(100.0, 0.0, 0.0)
		person = _place(102.6, 0.3, PI)
		person.push = PERSON_PUSH
		var ai := _drive(ai_kart, 0.0)
		ai.others = [ai_kart, person]
		person.was_reset.connect(func() -> void: person_resets += 1)

	## Two AIs side by side turned sharply into each other, each wanting the
	## other's side of the road and not told about the other, so they drive
	## into each other.
	func _start_pair() -> void:
		_clear()
		var left := _place(100.0, -1.0, 0.9)
		var right := _place(100.0, 1.0, -0.9)
		_drive(left, 3.0)
		_drive(right, -3.0)
		phase = "pair"

	func check(ok: bool, what: String) -> void:
		print(("  ok    " if ok else "  FAIL  ") + what)
		if not ok:
			failures += 1

	func _physics_process(_delta: float) -> void:
		if karts.is_empty():
			return
		tick += 1
		for i in karts.size():
			offsets[i] = track.offset_of(karts[i].global_position, offsets[i], 30.0)
		for i in drivers.size():
			drivers[i].offset = offsets[i]
		if phase == "person":
			# The person keeps steering into the AI.
			var toward := (karts[0].global_position - person.global_position).dot(person.global_basis.x)
			person.controls.throttle = 1.0
			person.controls.steer = clampf(toward, -1.0, 1.0)
			most_gap = maxf(most_gap, karts[0].global_position.distance_to(person.global_position))
			var on := offsets[0] - starts[0]
			if on > GET_ON or tick > CLEAR_WITHIN * 60.0:
				check(on > GET_ON, "the AI gets clear of the person's kart and on down the road (%.0f m in %.1f s)" % [on, tick / 60.0])
				check(most_gap > 4.0, "it gets away from the person's kart (%.1f m apart at most)" % most_gap)
				check(person_resets == 0, "the person's kart is never reset (%d)" % person_resets)
				check(resets[0] == 0, "the AI gets clear without resetting (%d)" % resets[0])
				_start_pair()
			return
		var both := minf(offsets[0] - starts[0], offsets[1] - starts[1])
		if both > GET_ON or tick > CLEAR_WITHIN * 60.0:
			check(both > GET_ON, "two AIs pressed together both get on down the road (%.0f and %.0f m in %.1f s)" % [offsets[0] - starts[0], offsets[1] - starts[1], tick / 60.0])
			check(resets[0] + resets[1] == 0, "and neither resets (%d)" % (resets[0] + resets[1]))
			print("All AI stuck checks passed." if failures == 0 else "%d AI stuck checks failed." % failures)
			get_tree().quit(1 if failures > 0 else 0)


func _initialize() -> void:
	root.add_child(Runner.new())
