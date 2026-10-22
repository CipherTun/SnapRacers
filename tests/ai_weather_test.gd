extends SceneTree

## An AI driver down a long straight with a big puddle and then a deep snow
## drift in its line. It has to steer round both, and drive straight
## through a drift that's only just started.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/ai_weather_test.gd

## Each one as [along the track, across, radius].
const PUDDLE := [120.0, 0.0, 3.5]
const DEEP := [230.0, 1.0, 3.0]
const SHALLOW := [330.0, 0.0, 3.0]


class Runner:
	extends Node

	var track: TrackPath
	var kart: Kart
	var ai: AIDriver
	var offset := 2.0
	var tick := 0
	var failures := 0
	var most := {"puddle": 0.0, "deep": 0.0, "shallow": 0.0}

	func _ready() -> void:
		track = TrackPath.from_dict({ "pieces": [{ "type": "straight", "length": 14 }] })
		add_child(TrackBuilder.new(track))
		kart = Kart.new()
		kart.build(KartDesign.load_file("res://tests/data/legacy/starter.json"))
		kart.transform = track.place_at(2.0, 0.05)
		kart.weather_grip = Conditions.GRIP.snow
		kart.puddles = Puddles.new()
		kart.puddles.add(_spot(PUDDLE), PUDDLE[2])
		add_child(kart.puddles)
		kart.drifts = Drifts.new()
		kart.drifts.add(_spot(DEEP), DEEP[2])
		# Started a moment ago, so it's still low.
		kart.drifts.add(_spot(SHALLOW), SHALLOW[2], -Puddles.GROW * 0.2)
		add_child(kart.drifts)
		add_child(kart)
		ai = AIDriver.new()
		ai.kart = kart
		ai.track = track
		kart.controls = ai.controls
		add_child(ai)

	func _spot(spot: Array) -> Vector3:
		var place := track.place_at(spot[0], 0.0)
		return place.origin + place.basis.x * spot[1]

	func check(ok: bool, what: String) -> void:
		print(("  ok    " if ok else "  FAIL  ") + what)
		if not ok:
			failures += 1

	func _physics_process(_delta: float) -> void:
		tick += 1
		offset = track.offset_of(kart.global_position, offset, 30.0)
		ai.offset = offset
		var at := kart.global_position
		most.puddle = maxf(most.puddle, kart.puddles.factor_at(at))
		var depth := kart.drifts.factor_at(at)
		if absf(offset - DEEP[0]) < 10.0:
			most.deep = maxf(most.deep, depth)
		if absf(offset - SHALLOW[0]) < 10.0:
			most.shallow = maxf(most.shallow, depth)
		if offset > SHALLOW[0] + 20.0:
			check(most.puddle < 0.05, "it goes round a big puddle in its line (deepest in %.2f)" % most.puddle)
			check(most.deep < 0.05, "and round a deep drift (deepest in %.2f)" % most.deep)
			check(most.shallow > 0.05, "but straight through a drift that's only just started (%.2f deep)" % most.shallow)
			finish()
		if tick == 60 * 40:
			check(false, "it gets down the straight in 40 s (it's at %.0f m)" % offset)
			finish()

	func finish() -> void:
		print("All AI weather checks passed." if failures == 0 else "%d AI weather checks failed." % failures)
		get_tree().quit(1 if failures > 0 else 0)


func _initialize() -> void:
	root.add_child(Runner.new())
