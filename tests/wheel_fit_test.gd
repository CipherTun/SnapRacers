extends SceneTree

## Checks every wheel goes on every axle and pin it should: each wheel tried on
## each free axle or pin of every part that has one, standing on its own, and
## on the axles of the stock vehicles once their own wheel is taken off.
##   tools/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . -s tests/wheel_fit_test.gd

var failures := 0


func check(ok: bool, what: String) -> void:
	print(("  ok    " if ok else "  FAIL  ") + what)
	if not ok:
		failures += 1


## Whether the wheel goes onto any of these spots where it fits and joins,
## with the kart lifted if it has to be.
func fitting(design: KartDesign, wheel: String, spots: Array) -> bool:
	for spot in spots:
		for way in Snap.ways(wheel, spot, Basis.IDENTITY, spot.at):
			if design.fits_lifted(wheel, way.place) and design.attaches_place(wheel, way.place):
				return true
	return false


## The kart's open axles and pins on part `index`, by which connector they're
## on.
func axles_of(design: KartDesign, index: int) -> Dictionary:
	var out := {}
	for spot in Snap.open_spots(design):
		if spot.part == index and spot.type in ["axle", "pin"]:
			if not out.has(spot.index):
				out[spot.index] = []
			out[spot.index].append(spot)
	return out


## Whether wheel `a` is no bigger than wheel `b` every way.
func smaller(a: String, b: String) -> bool:
	var size_a := PartCatalog.fine_size(a)
	var size_b := PartCatalog.fine_size(b)
	return size_a.x <= size_b.x + 0.01 and size_a.y <= size_b.y + 0.01 and size_a.z <= size_b.z + 0.01


## How long a line connector is, in the fine unit.
func room(id: String, index: int) -> float:
	return Connectors.of(id)[index].get("length", 0.0)


func _init() -> void:
	var wheels := []
	var holders := []
	for id in PartCatalog.ids():
		if KartDesign.is_wheel(id):
			wheels.append(id)
		elif Connectors.of(id).any(func(c: Dictionary) -> bool: return c.type in ["axle", "pin"]):
			holders.append(id)
	check(wheels.size() >= 10 and holders.size() >= 20, "there are wheels and parts they go on (%d, %d)" % [wheels.size(), holders.size()])

	# Each part on its own on the floor, facing forward and back, since wheels
	# keep their axles across the kart. An axle you can slide a wheel onto
	# from the end takes any wheel. One held at both ends, like a bike's
	# swingarm or fork, takes at least one, and any wheel no wider and no
	# bigger across than one it takes.
	var missing := []
	for id in holders:
		for rot in [0, 2]:
			var design := KartDesign.new()
			var size := KartDesign.grid_size(id, Grid.yaw(rot))
			var at := Vector3i((KartDesign.BUILD_SIZE.x - size.x) / 2, 0, (KartDesign.BUILD_SIZE.z - size.z) / 2)
			design.parts.append({ "id": id, "at": at, "rot": rot })
			var axles := axles_of(design, 0)
			for index in axles:
				var held: bool = id.begins_with("b_") and room(id, index) < 60.0
				var fit := []
				var unfit := []
				for wheel in wheels:
					(fit if fitting(design, wheel, axles[index]) else unfit).append(wheel)
				if held and fit.is_empty():
					missing.append("no wheel on %s connector %d turned %d" % [id, index, rot])
				for wheel in unfit:
					if not held or fit.any(func(other: String) -> bool: return smaller(wheel, other)):
						missing.append("%s on %s connector %d turned %d" % [wheel, id, index, rot])
	check(missing.is_empty(), "every wheel that should goes on every axle and pin %s" % [missing])

	# The stock vehicles, with each wheel taken off and put back.
	var stock_missing := []
	var outside := []
	for path in DirAccess.get_files_at("res://data/karts/stock"):
		if not path.ends_with(".json"):
			continue
		var design := KartDesign.load_file("res://data/karts/stock/" + path)
		for i in design.parts.size():
			var own: String = design.parts[i].id
			if not KartDesign.is_wheel(own):
				continue
			# A few stick out of the front of the build area, so they can't
			# go back on in the garage either way.
			if not KartDesign.in_area(own, KartDesign.place_of(design.parts[i])):
				outside.append("%s wheel %d" % [path, i])
				continue
			var without := design.duplicate_design()
			without.parts.remove_at(i)
			var spots := Snap.spots_for(without, own).filter(func(s: Dictionary) -> bool: return s.type in ["axle", "pin"])
			var near := spots.filter(func(s: Dictionary) -> bool: return KartDesign.fine_box(own, KartDesign.place_of(design.parts[i])).grow(1.0).has_point(s.at))
			if not fitting(without, own, near):
				stock_missing.append("%s wheel %d (%s)" % [path, i, own])
	check(stock_missing.is_empty(), "every stock vehicle's wheels go back on %s" % [stock_missing])
	if not outside.is_empty():
		print("        not counting ones outside the build area %s" % [outside])

	# The trail bike wheel goes on at every dot along a sports bike frame's
	# back axle, with the frame on the floor, and the garage's snap finds it.
	var bike := KartDesign.new()
	bike.parts.append({ "id": "b_frame_sport", "at": Vector3i(9, 0, 7), "rot": 0 })
	var back: Array = axles_of(bike, 0).values()[0]
	var good := 0
	var snapped := 0
	for spot in back:
		if fitting(bike, "w_moto_trail", [spot]):
			good += 1
		var way := Snap.best(bike, "w_moto_trail", Snap.ways("w_moto_trail", spot, Basis.IDENTITY, spot.at))
		if way.get("fits", false):
			snapped += 1
	check(good == back.size() and snapped == back.size(), "a trail bike wheel goes on at each of the %d dots along a sports bike's back axle (%d, snapped %d)" % [back.size(), good, snapped])
	var way := Snap.best(bike, "w_moto_trail", Snap.ways("w_moto_trail", back[0], Basis.IDENTITY, back[0].at))
	var lift := KartDesign.lift_for("w_moto_trail", way.place)
	check(lift == 4 and bike.headroom() >= lift, "with the kart going up 4 plates to make room under it (%d)" % lift)
	bike.raise(lift)
	way.place.origin.y += lift * Grid.PLATE_FINE
	bike.parts.append(KartDesign.placed_entry("w_moto_trail", way.place))
	check(bike.fits_place("w_moto_trail", way.place, 1) and KartDesign.joined(bike.parts[0], bike.parts[1]), "and once it's up the wheel's on inside the build area")

	print("%d failed" % failures if failures else "all passed")
	quit(1 if failures else 0)
