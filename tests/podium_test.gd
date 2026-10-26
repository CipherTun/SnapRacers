extends Node

## The podium after a cup's last race, on every cup's last course: the top
## three on the right steps in order with their own drivers, the rest of the
## field below on the ground, the karts cleared away, no errors, and the
## standings after it.
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
	var off := race.track.point_at(race.track.offset_of(podium.middle)).distance_to(podium.middle)
	print("  podium %.0f m from the middle of the road%s" % [off, ", on the start straight" if off < race.track.width else ""])
	if not Scenery.theme_named(race.track.theme).get("void", false):
		check(off > race.track.width, "beside the road, off it")
	check(errors.count == before, "with no errors (%d%s)" % [errors.count - before, ", the last " + errors.last if errors.count > before else ""])
	podium.finish()
	await frames(3)
	check(screen() is GrandPrixStandings, "then the standings come up")
	Game.grand_prix = null
	await frames(2)
