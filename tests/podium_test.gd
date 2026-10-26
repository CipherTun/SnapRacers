extends Node

## The podium after a cup's last race, on every cup's last course: the top
## three jumping up onto the right steps in order with their own drivers, the
## rest of the field below on the ground clapping or sulking, the winner
## holding the cup's trophy, the karts cleared away, no errors, and the
## standings over it after, with the camera still, until Back frees the race.
## The first cup's show is watched all the way through; the others are
## skipped partway, which jumps to how it ends.
##
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --fixed-fps 60 --path . res://tests/podium_test.tscn

var failures := 0
var host: Node
var errors := Errors.new()


## Counts the errors logged, so a cup that logs any fails.
class Errors extends Logger:
	var count := 0
	var last := ""

	func _log_error(_function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, _error_type: int, _script_backtraces: Array[ScriptBacktrace]) -> void:
		count += 1
		last = "%s (%s:%d)" % [rationale if rationale != "" else code, file, line]


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func screen() -> Node:
	for i in range(host.get_child_count() - 1, -1, -1):
		var child := host.get_child(i)
		if not child.is_queued_for_deletion():
			return child
	return null


func _ready() -> void:
	OS.add_logger(errors)
	host = Node.new()
	add_child(host)
	Game.start(host, false)
	Game.settings.set_value("race", "split", Game.SOLO)
	Game.settings.set_value("race", "difficulty", Difficulty.DEFAULT)
	for cup in GrandPrix.cups():
		await _cup(cup.id)
	OS.remove_logger(errors)
	print("All podium checks passed." if failures == 0 else "%d podium checks failed." % failures)
	get_tree().quit(1 if failures > 0 else 0)


func _cup(id: String) -> void:
	var before := errors.count
	Game.start_grand_prix(id)
	var gp := Game.grand_prix
	# Straight to the last race, before the first one's loaded.
	gp.round = gp.track_ids().size() - 1
	Game.track_path = gp.track_path()
	var race: Race = null
	for i in 300:
		await frames(1)
		if screen() is Race:
			race = screen()
			break
	if race == null:
		check(false, "%s: the last race starts" % id)
		return
	print("-- %s, on %s" % [id, race.track.name])
	await frames(12)
	var who := {}
	for r in race.racers:
		who[r.name] = r.kart.driver
	var order: Array = race.racers.map(func(r): return r.name)
	order.reverse()
	Game.finish_grand_prix_race(order)
	await frames(3)
	var podium := race.podium
	check(podium != null and screen() == race, "the podium goes up on the course")
	if podium == null:
		return
	check(race.racers.is_empty() and race.find_children("*", "Kart", true, false).is_empty(), "and the karts are cleared away")
	var names := gp.standings().map(func(s): return s[0])
	check(podium.order.map(func(e): return e[0]) == names, "everyone's there in the standings' order")
	check(podium.drivers.size() == names.size() and podium.karts.size() == 3, "%d drivers and 3 karts" % podium.drivers.size())
	check(range(names.size()).all(func(i): return podium.drivers[i].design == who[names[i]]), "each in the driver they raced as")
	check(errors.count == before, "with no errors (%d%s)" % [errors.count - before, ", the last " + errors.last if errors.count > before else ""])
	# Taps right after it goes up are ignored.
	var tap := InputEventScreenTouch.new()
	tap.pressed = true
	var skipped := [false]
	podium.finished.connect(func(): skipped[0] = true)
	podium._unhandled_input(tap)
	check(not skipped[0], "a tap right after it goes up doesn't skip it")
	race.go_back()
	check(not skipped[0] and race.cup_standings == null, "and an early Back doesn't skip it either")
	if id == GrandPrix.cups()[0].id:
		await _watch(podium)
	else:
		# Partway, with third up and second in the air.
		podium._time = Podium.LEAPS[1] + 0.2
		await frames(3)
	# A narrow screen pulls the camera back to fit the rows.
	var wide := await _distance_in(podium, Vector2i(1280, 720))
	var narrow := await _distance_in(podium, Vector2i(768, 1024))
	check(narrow > wide and narrow <= Podium.CAMERA_FAR, "the camera pulls back on a portrait screen (%.1f m, %.1f m wide)" % [narrow, wide])
	race.go_back()
	await frames(3)
	check(skipped[0], "Back skips to the end")
	var feet := []
	var across := []
	for rig in podium.drivers:
		var local: Vector3 = (rig.global_position - podium.middle).rotated(Vector3.UP, -podium.facing * PI * 0.5)
		feet.append(rig.global_position.y - CharacterRig.FEET_BELOW)
		across.append(local.x)
	check(feet[0] > feet[1] and feet[1] > feet[2], "first stands highest, then second, then third")
	check(absf(across[0]) < 0.01 and across[1] < -1.0 and across[2] > 1.0, "first in the middle, second on the left, third on the right")
	var ground: float = race.builder.ground_at(podium.middle.x, podium.middle.z)
	check(feet[2] > ground + 0.2, "on top of the steps")
	var below := true
	for i in range(3, podium.drivers.size()):
		var at := podium.drivers[i].global_position
		var floor_at: float = race.builder.ground_at(at.x, at.z) if podium.ground != null else podium.middle.y
		below = below and absf(feet[i] - floor_at) < 0.05 and feet[i] < feet[2]
	check(below, "and the rest of the field stand on the ground below")
	var winner := podium.drivers[0]
	var trophy := podium.trophy
	var cup: Dictionary = GrandPrix.cups().filter(func(c): return c.id == id)[0]
	var pieces := TrophyModel.pieces(cup.get("trophy", {}), Podium.colour_of(cup), "gold").size()
	check(trophy != null and winner.held() == trophy and trophy.get_parent() == winner.upper() and podium.trophy_spec == cup.get("trophy", {}) and trophy.get_child_count() == pieces + 1,
			"the winner holds the cup's trophy (%s)" % cup.get("trophy", {}).get("top", "cup"))
	if trophy != null:
		var hand := winner.hand_position(1)
		var top := winner.to_local(_box_of(trophy).end).y
		check(top > CharacterRig.HEAD_Y, "up high, its top past the middle of the head (%.2f m up)" % top)
		# In the head's own space, where its box fits it closely, whether any
		# corner of the trophy's bricks is inside it.
		var head := winner.head()
		var head_box := AABB()
		var first := true
		for shown in head.find_children("*", "MeshInstance3D", true, false):
			var b: AABB = head.global_transform.affine_inverse() * shown.global_transform * shown.get_aabb()
			head_box = b if first else head_box.merge(b)
			first = false
		var into := trophy.find_children("*", "MeshInstance3D", true, false).filter(func(m):
			var to_head: Transform3D = head.global_transform.affine_inverse() * m.global_transform
			for v in m.mesh.get_faces():
				if head_box.has_point(to_head * v):
					return true
			return false)
		check(into.is_empty(), "clear of their head (%d of its bricks in it)" % into.size())
		check(winner.to_global(hand).distance_to(trophy.global_transform * podium.trophy_grip) < 0.01, "and in their hand")
	var clapping := range(1, podium.drivers.size()).filter(func(i): return podium.drivers[i]._clap_left > 0.0)
	var sulking := range(3, podium.drivers.size()).filter(func(i): return podium.drivers[i]._sulk_left > 0.0)
	check(clapping.size() == podium.drivers.size() - 1 - Podium.SULKING and sulking == range(podium.drivers.size() - Podium.SULKING, podium.drivers.size()),
			"second and third and the field clap, and the last %d sulk" % Podium.SULKING)
	check(podium.confetti.emitting, "and the confetti's coming down")
	var off := race.track.point_at(race.track.offset_of(podium.middle)).distance_to(podium.middle)
	print("  podium %.0f m from the middle of the road%s" % [off, ", on the start straight" if off < race.track.width else ""])
	if not Scenery.theme_named(race.track.theme).get("void", false):
		check(off > race.track.width, "beside the road, off it")
	check(errors.count == before, "and still no errors (%d%s)" % [errors.count - before, ", the last " + errors.last if errors.count > before else ""])
	var standings := race.cup_standings
	check(screen() == race and standings != null and standings.is_visible_in_tree(), "then the standings come up over the podium")
	if standings == null:
		return
	check(standings.find_children("*", "Label", true, false).any(func(l): return l.text.contains("trophy")), "with the trophy")
	check(not standings.find_children("*", "Control", true, false).any(func(c): return c is UiKit.Backdrop), "and no backdrop over it")
	check(not standings.accepting(), "presses on the standings are ignored at first")
	var press := InputEventKey.new()
	press.pressed = true
	press.keycode = KEY_ENTER
	standings._input(press)
	check(get_viewport().is_input_handled(), "and swallowed")
	get_viewport().set_input_as_handled()
	var first := PadFocus.pick(standings)
	check(PadFocus._race_part(race) == standings and first != null and standings.is_ancestor_of(first), "a controller picks out their buttons (%s)" % (first.text if first is Button else "none"))
	race._open_any()
	race._notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(race._menus.is_empty() and not get_tree().paused, "and the pause menu doesn't open over them")
	for i in ceili(Podium.SETTLE * 60.0) + 5:
		await frames(1)
	var held := podium.camera.global_transform
	await frames(10)
	check(podium.still() and podium.camera.global_transform.is_equal_approx(held), "the camera holds still behind them")
	check(standings.accepting(), "then they count")
	var laid := [0]
	standings.laid_out.connect(func(): laid[0] += 1)
	var was_shift := podium.camera.h_offset
	var was_window := get_window().size
	get_window().size = Vector2i(900, 1100)
	await frames(4)
	check(laid[0] == 1 and not is_equal_approx(podium.camera.h_offset, was_shift), "a resize lays the panel and camera out again")
	get_window().size = was_window
	await frames(3)
	race.go_back()
	await frames(2)
	check(not is_instance_valid(race) or race.is_queued_for_deletion(), "Back leaves, and the race goes with it")
	check(screen() is CupGrid, "back to the cups")
	await frames(2)


## Watches the show up to the trophy being in the winner's hand: the top
## three jump up third, second then first, and the trophy comes down to them.
func _watch(podium: Podium) -> void:
	var up_at := [INF, INF, INF]
	var tops := []
	var was := INF
	var falling := true
	for place in 3:
		tops.append(podium._on_step[place].y)
	while podium._time < Podium.TROPHY_IN + 0.3:
		await frames(1)
		for place in 3:
			if up_at[place] == INF and absf(podium.drivers[place].position.y - tops[place]) < 0.005:
				up_at[place] = podium._time
		if podium.trophy != null and not podium._landed:
			falling = falling and podium.trophy.global_position.y <= was + 0.0001
			was = podium.trophy.global_position.y
	check(up_at[2] < up_at[1] and up_at[1] < up_at[0] and up_at[0] < Podium.TROPHY_IN, "third, second then first jump up onto their steps (%.1f, %.1f, %.1f s)" % [up_at[2], up_at[1], up_at[0]])
	check(was < INF and falling, "the trophy comes down from above")
	check(podium.drivers[0].held() == podium.trophy, "into the winner's hand")
	check(podium.confetti.emitting, "with confetti")


## The box round everything drawn under `node`, in the world.
func _box_of(node: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for shown in node.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = shown.global_transform * shown.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box


## How far out a copy of `podium` puts its camera in a viewport of `size`.
func _distance_in(podium: Podium, size: Vector2i) -> float:
	var port := SubViewport.new()
	port.size = size
	add_child(port)
	var copy := Podium.new(podium.order, podium.colour, [podium.middle, podium.facing, false])
	port.add_child(copy)
	await frames(1)
	var out := copy._camera_distance()
	port.queue_free()
	return out
