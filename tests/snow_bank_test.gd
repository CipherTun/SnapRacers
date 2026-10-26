extends SceneTree

## Snow drifts: the same seed and build-up step give exactly the same depth
## everywhere, and the snow lies on the road in tongues blown in from the
## edge the wind comes from, in bunches with clear road between, and they
## stay on the road and lie on it however it curves or climbs. Karts at
## full throttle down a straight lose a noticeable bit of speed crossing a
## full drift at its crest, almost nothing crossing a dusting or a tip, and
## more along a long deep one, but keep going.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/snow_bank_test.gd

## Where the drifts lie along the straight, and where the timing starts and
## stops, in metres.
const DRIFT := 170.0
const FROM := 150.0
const TO := 230.0
## Each kart has its own copy of the straight, this far over from the last,
## so they can't bump each other.
const LANES := {"clear": 0.0, "dusting": 600.0, "deep": 1200.0, "tip": 1800.0, "long": 2400.0}

var failures := 0


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func _initialize() -> void:
	var forest := TrackPath.load_file("res://data/tracks/frostbite_forest.json")
	var a := Drifts.new(forest, 7, 1.0)
	var b := Drifts.new(forest, 7, 1.0)
	a.grow(0.6)
	for step in 80:
		b.grow(step * 0.0077)
	b.grow(0.6)
	var same := a.level == b.level
	var deep_points := 0
	var at := 0.0
	while at < forest.length:
		for across: float in [-7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0]:
			var point := forest.point_at(at) + forest.right_at(at) * across
			same = same and a.snow_at(point) == b.snow_at(point)
			if a.factor_at(point) > 0.3:
				deep_points += 1
		at += 1.5
	check(same and deep_points > 20, "two lots of drifts with the same seed and step are exactly as deep everywhere, however they got there (%d deep points)" % deep_points)
	var c := Drifts.new(forest, 8, 1.0)
	c.grow(0.6)
	check(str(c.spots) != str(a.spots), "another seed lays them somewhere else")
	a.free()
	b.free()
	c.free()
	# Over a few races: tongues start at the edge the wind comes from and
	# run into the road, most snow is on the road, and there's clear road
	# between the bunches.
	var tongues := 0
	var windward := 0
	var into_road := 0
	var on_road := 0.0
	var off_road := 0.0
	var clear_stretches := 0
	for race_seed in 6:
		var d := Drifts.new(forest, race_seed, 1.0)
		d.grow(1.0)
		for i in d.spots.size():
			if d._only_looks[i]:
				continue
			tongues += 1
			var o: float = d._laid[i]
			var right := forest.right_at(o)
			var side := signf((d._root[i] - forest.point_at(o)).dot(right))
			if side == signf(right.dot(d.wind)) or absf(right.dot(d.wind)) <= 0.05:
				windward += 1
			if d._dir[i].dot(-right * side) > 0.3:
				into_road += 1
		var bare := 0.0
		at = 0.0
		while at < forest.length:
			var any := false
			for across: float in [-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0]:
				var depth := d.factor_at(forest.point_at(at) + forest.right_at(at) * across)
				on_road += depth
				any = any or depth > 0.02
			for across: float in [-11.0, -9.0, 9.0, 11.0]:
				off_road += d.factor_at(forest.point_at(at) + forest.right_at(at) * across)
			bare = 0.0 if any else bare + 1.0
			if bare == 20.0:
				clear_stretches += 1
			at += 1.0
		d.free()
	check(windward == tongues and into_road == tongues and tongues > 100, "every tongue starts at the edge the wind comes from and runs into the road (%d of them)" % tongues)
	check(on_road > off_road * 10.0, "the snow lies on the road, not beside it (%.0f on, %.0f off)" % [on_road, off_road])
	check(clear_stretches > 20, "with clear road between the bunches (%d stretches of 20 m)" % clear_stretches)
	# On courses with curves, hills and open sky, every tongue and wisp lies
	# on the road from where it first gets onto it to its tip, and hugs it.
	var lumps := 0
	var strays: Array = []
	for course in ["frostbite_forest", "slalom_slopes", "cumulus_curl", "zeppelin_zigzag", "serpent_summit", "rattlesnake_ridge"]:
		var path := TrackPath.load_file("res://data/tracks/%s.json" % course)
		var e := Drifts.new(path, 3, 1.0)
		e.grow(1.0)
		for i in e.spots.size():
			lumps += 1
			var up := path.up_at(e._laid[i])
			var flat := (e._dir[i] - up * e._dir[i].dot(up)).normalized()
			var hint: float = e._laid[i]
			var on := false
			var s := 0.0
			while s <= e._long[i]:
				var point := e._root[i] + flat * s
				var o := path.offset_of(point, hint, 20.0)
				hint = o
				var middle := path.point_at(o)
				var across := (point - middle).dot(path.right_at(o))
				var inside := absf(across) < path.width * 0.5
				on = on or inside
				var off_by := absf((middle + path.right_at(o) * across - point).dot(up))
				if (on and not inside) or off_by > Drifts.HUG + 0.02:
					strays.append("%s %.0f m" % [course, o])
					break
				s += 0.5
		e.free()
	check(lumps > 500 and strays.is_empty(), "tongues and wisps stay on the road and hug it on curves, hills and over the sky (%d, off at %s)" % [lumps, str(strays.slice(0, 5))])
	root.add_child(Runner.new(self))


class Runner:
	extends Node

	var test: SceneTree
	var track: TrackPath
	var karts := {}
	var offsets := {}
	var before := {}
	var slowest := {}
	var started := {}
	var took := {}
	var time := 0.0

	func _init(for_test: SceneTree) -> void:
		test = for_test

	func _ready() -> void:
		track = TrackPath.from_dict({ "pieces": [{ "type": "straight", "length": 14 }] })
		for which in LANES:
			var road := TrackBuilder.new(track)
			road.position = track.place_at(0.0, 0.0).basis.x * float(LANES[which])
			add_child(road)
			var kart := Kart.new()
			kart.build(KartDesign.load_file("res://tests/data/legacy/starter.json"))
			var place := track.place_at(2.0, 0.05)
			place.origin += place.basis.x * LANES[which]
			kart.transform = place
			kart.weather_grip = Conditions.GRIP.snow
			kart.weather_drag = Conditions.DRAG.snow
			if which != "clear":
				kart.drifts = Drifts.new()
				var lane := track.place_at(DRIFT, 0.0)
				var across := lane.basis.x
				if which == "long":
					# A long deep one down the lane, its crest 30 m in.
					var from := track.place_at(FROM, 0.0)
					kart.drifts.add_tongue_at(from.origin + from.basis.x * float(LANES[which]), -from.basis.z, 5.0, 120.0, 1.0)
				else:
					# One 5 m wide and 12 m long running across the road,
					# crossed at its crest or near its tip, full or just
					# started.
					var share: float = 0.9 if which == "tip" else Drifts.CREST
					var at: Vector3 = lane.origin + across * float(LANES[which])
					kart.drifts.add_tongue_at(at - across * share * 12.0, across, 5.0, 12.0, 1.0, -Puddles.GROW * 0.15 if which == "dusting" else -1.0)
				add_child(kart.drifts)
			add_child(kart)
			karts[which] = kart
			offsets[which] = 2.0
			slowest[which] = INF

	func _physics_process(delta: float) -> void:
		time += delta
		for which in karts:
			var kart: Kart = karts[which]
			kart.controls.throttle = 1.0
			var shift := track.place_at(0.0, 0.0).basis.x * float(LANES[which])
			offsets[which] = track.offset_of(kart.global_position - shift, offsets[which], 30.0)
			var o: float = offsets[which]
			var speed := kart.linear_velocity.length()
			if o >= FROM and not started.has(which):
				started[which] = time
				before[which] = speed
			if o >= FROM and o < TO:
				slowest[which] = minf(slowest[which], speed)
			if o >= TO and not took.has(which):
				took[which] = time - started[which]
		if took.size() == karts.size():
			var lost := {}
			for which in karts:
				lost[which] = before[which] - slowest[which]
			print("  speeds: %s" % ", ".join(karts.keys().map(func(w): return "%s %.1f -> %.1f m/s, %.2f s for %.0f m" % [w, before[w], slowest[w], took[w], TO - FROM])))
			test.check(lost.deep > before.deep * 0.12 and lost.deep < before.deep * 0.25, "crossing a full drift at its crest costs a noticeable bit of speed (%.1f of %.1f m/s)" % [lost.deep, before.deep])
			test.check(lost.dusting < 0.5 and lost.tip < 0.5, "a dusting or a tip is barely felt (%.2f and %.2f m/s lost)" % [lost.dusting, lost.tip])
			test.check(lost.long > lost.deep and slowest.long > 8.0, "a long deep one slows more, but the kart keeps going (%.1f m/s at its slowest)" % slowest.long)
			finish()
		elif time > 40.0:
			test.check(false, "every kart gets down the straight in 40 s (%s)" % str(offsets))
			finish()

	func finish() -> void:
		print("All snow bank checks passed." if test.failures == 0 else "%d snow bank checks failed." % test.failures)
		test.quit(1 if test.failures > 0 else 0)
