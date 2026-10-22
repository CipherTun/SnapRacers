extends SceneTree

## A course up in the sky (tests/data/sky_test.json): there's no ground under
## it, floating islands and clouds go under and around it, a kart that goes
## off an open edge falls until the race puts it back, and the AI drives
## around both its loops.
##
## Run it with:
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . -s tests/sky_test.gd

const COURSE := "res://tests/data/sky_test.json"
## How far below the road a kart has to be for the race to put it back (see
## Race.FALLEN, which this test can't load).
const FALLEN := 4.0

var failures := 0
var world: Node3D
var track: TrackPath
var builder: TrackBuilder


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func _initialize() -> void:
	_run.call_deferred()


func frames(n: int) -> void:
	for i in n:
		await physics_frame


func _run() -> void:
	var course := CourseDesign.load_file(COURSE)
	check(course != null and course.theme == "sky", "the test course is up in the sky")
	check(course.problems().is_empty(), "it's ready to race %s" % [course.problems()])
	check(Sharing.buildable(course), "and it can be shared")
	track = course.track()
	var loops := track.pieces.filter(func(p): return p.type == "loop").size()
	check(loops == 2, "it has two loops (%d)" % loops)
	check(CourseOutline.of_track(track).loops.size() == 2, "the map marks both")
	var summary := CourseOutline.describe(track)
	check(summary.contains("two loops"), "its line says so (%s)" % summary)

	world = Node3D.new()
	root.add_child(world)
	builder = TrackBuilder.new(track)
	builder.sky = false
	world.add_child(builder)
	await frames(2)
	await no_ground()
	islands_and_clouds()
	await fall_off()
	await both_loops()

	print("All sky checks passed." if failures == 0 else "%d sky checks failed." % failures)
	quit(1 if failures > 0 else 0)


## Nothing solid but other road under the road's open edges, where an orchard
## course has its grass.
func no_ground() -> void:
	check(builder.terrain == null, "there's no ground")
	var offroad := builder.find_children("*", "StaticBody3D", true, false).filter(func(b): return b.get_meta("offroad", false))
	check(offroad.is_empty(), "and nothing to drive on off the road (%d)" % offroad.size())
	var space := world.get_world_3d().direct_space_state
	var out := track.width * 0.5 + TrackPath.KERB + 4.0
	var hits := 0
	var tries := 0
	var at := 0.0
	while at < track.length:
		for side: float in [-1.0, 1.0]:
			var from := track.point_at(at) + track.right_at(at) * side * out + Vector3.UP * 2.0
			var ray := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 300.0)
			# Other road, like the far side of a loop, doesn't count.
			var hit := space.intersect_ray(ray)
			if not hit.is_empty() and not hit.collider.has_meta("piece"):
				hits += 1
			tries += 1
		at += 25.0
	check(hits == 0, "looking straight down beside the road finds nothing but road to land on (%d of %d)" % [hits, tries])


## Islands under the road and clouds below them.
func islands_and_clouds() -> void:
	var lowest := INF
	for p in track.points:
		lowest = minf(lowest, p.y)
	var damage: WorldDamage = builder.find_children("*", "WorldDamage", true, false).filter(func(d): return d.get_parent() is Scenery).front()
	var below := 0
	var clouds := 0
	for kind in damage._instances:
		for inst in damage._instances[kind]:
			var y: float = inst[0].origin.y
			if y < lowest - 35.0:
				clouds += 1
			elif y < lowest - 8.0:
				below += 1
	check(below > 200, "floating islands go below the road (%d bricks)" % below)
	check(clouds > 50, "with clouds below them (%d puffs)" % clouds)


## The Starter slides off the side of the start straight, falls with nothing
## to catch it, and is put back on the road.
func fall_off() -> void:
	var at := 20.0
	var frame := track.frame_at(at)
	var kart := _kart()
	var heading := frame.basis.rotated(frame.basis.y, -deg_to_rad(35.0))
	kart.transform = Transform3D(heading, frame.origin + frame.basis.y * 0.35)
	world.add_child(kart)
	kart.linear_velocity = -heading.z * 14.0
	kart.controls.throttle = 1.0
	var fell_at := -1
	for i in 300:
		await physics_frame
		if fell_at < 0 and _below(kart) < -FALLEN:
			fell_at = i
		if fell_at >= 0 and i > fell_at + 90:
			break
	check(fell_at >= 0, "a kart off the open edge falls (%.1f m below the road)" % -_below(kart))
	check(_below(kart) < -20.0, "and keeps on falling with nothing under it (%.1f m below)" % -_below(kart))
	kart.controls.throttle = 0.0
	kart.request_reset()
	await frames(90)
	var across := absf((kart.global_position - track.point_at(track.offset_of(kart.global_position))).dot(track.right_at(track.offset_of(kart.global_position))))
	check(across < track.width * 0.5 and absf(_below(kart)) < 1.5 and kart.global_basis.y.y > 0.9, "it's put back on the road (%.1f m from the middle, %.1f m off it)" % [across, _below(kart)])
	kart.queue_free()
	await frames(2)


## The AI drives from the start line around both loops, upside down at the
## top of each, without falling off.
func both_loops() -> void:
	var spans := []
	for i in track.pieces.size():
		if track.pieces[i].type == "loop":
			var first := INF
			var last := -INF
			for k in track.points.size():
				if track.piece_of[k] == i:
					first = minf(first, track.distances[k])
					last = maxf(last, track.distances[k])
			spans.append([first, last])
	var kart := _kart()
	kart.transform = track.place_at(2.0, 0.05)
	world.add_child(kart)
	var ai := AIDriver.new()
	ai.kart = kart
	ai.track = track
	kart.controls = ai.controls
	world.add_child(ai)
	var offset := 2.0
	var upside_down := [false, false]
	var fell := false
	var goal: float = spans[1][1] + 30.0
	for i in 60 * 120:
		await physics_frame
		offset = track.offset_of(kart.global_position, offset, 30.0)
		ai.offset = offset
		for n in spans.size():
			if offset > spans[n][0] and offset < spans[n][1] and kart.global_basis.y.y < -0.5:
				upside_down[n] = true
		if _below(kart, offset) < -FALLEN:
			fell = true
			break
		if offset > goal:
			break
	check(not fell, "the AI doesn't fall off on the way (%.0f m along)" % offset)
	check(upside_down[0], "it goes over the top of the first loop")
	check(upside_down[1], "and the second")
	check(offset > goal, "and comes out of the second (%.0f m along, it ends at %.0f)" % [offset, spans[1][1]])
	ai.queue_free()
	kart.queue_free()
	await frames(2)


func _kart() -> Kart:
	var kart := Kart.new()
	kart.build(KartDesign.load_file("res://tests/data/legacy/starter.json"))
	kart.reset_to = func(where: Vector3) -> Transform3D:
		var f := track.frame_at(track.offset_of(where))
		return Transform3D(f.basis, f.origin + f.basis.y * Kart.RESET_LIFT)
	return kart


## How far above (or below, negative) the road's nearest point the kart is.
func _below(kart: Kart, offset := -1.0) -> float:
	if offset < 0.0:
		offset = track.offset_of(kart.global_position)
	return (kart.global_position - track.point_at(offset)).dot(track.up_at(offset))
