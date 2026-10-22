class_name TrainTimetable
extends RefCounted

## When the train comes through one level crossing, worked out from the race
## clock and the race's seed alone. Every device in an online race has the
## same seed and clock, so they all see the train in the same place without
## sending it.
##
## Times are race seconds from GO. Distances are along the railway from the
## middle of the road, in the way that train's going, so the front of the
## train reaches the middle of the road at its arrival time. Trains take
## turns coming from each side at random.

## How fast the train goes, in m/s.
const SPEED := 22.0
## The engine and three carriages, front to back, in metres.
const LENGTH := 36.0
## The first train reaches the road this long after GO, somewhere between.
const FIRST_SOONEST := 6.0
const FIRST_LATEST := 20.0
## Then one comes along about this often, picked once for the race.
const EVERY_LEAST := 40.0
const EVERY_MOST := 55.0
## And each one is up to this much early or late. With rails at most
## LevelCrossing.MOST_REACH long each side, a train is gone well before the
## next one's due.
const WOBBLE := 4.0
## The lights start flashing this long before the train gets to the road.
const LIGHTS_BEFORE := 8.0
## The barriers start coming down this long before, and take BARRIER_SWING
## to get there.
const BARRIERS_BEFORE := 5.0
const BARRIER_SWING := 2.0
## After the back of the train is off the road, the barriers wait this long
## before going up.
const OPEN_AFTER := 1.0

## The first train's arrival, and the time between trains.
var first := 0.0
var every := 0.0
## How far the road reaches either side of the railway, in metres along it
## (curbs and a little more), for when the road's blocked.
var road_half := 9.0
## How far the rails run out each side before going into a tunnel, in metres:
## [left of the road, right of the road] as you drive along it.
var reach := [100.0, 100.0]
var _seed := 0
## Each train's arrival and direction once worked out, by train number, so
## asking every frame doesn't make anything new.
var _arrivals := {}
var _directions := {}


## `chance_seed` is the race's seed and `index` which crossing on the course
## this is, so two crossings don't share trains.
func _init(chance_seed := 0, index := 0, road := 9.0, reach_left := 100.0, reach_right := 100.0) -> void:
	_seed = chance_seed * 7919 + index * 104729 + 17
	road_half = road
	reach = [reach_left, reach_right]
	var rng := _rng_for(-1)
	first = lerpf(FIRST_SOONEST, FIRST_LATEST, rng.randf())
	every = lerpf(EVERY_LEAST, EVERY_MOST, rng.randf())


func _rng_for(train: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed * 31 + train
	return rng


## When the front of train `k` (0 for the first) reaches the middle of the road.
func arrival(k: int) -> float:
	if not _arrivals.has(k):
		_work_out(k)
	return _arrivals[k]


func _work_out(k: int) -> void:
	var rng := _rng_for(k)
	_arrivals[k] = first + k * every + (rng.randf() * 2.0 - 1.0) * WOBBLE
	_directions[k] = 1 if rng.randf() < 0.5 else -1


## Which way train `k` goes: 1 from the left of the road to the right, as you
## drive along it, and -1 the other way.
func direction(k: int) -> int:
	if not _directions.has(k):
		_work_out(k)
	return _directions[k]


## How far along the railway the front of train `k` is at time `t`, past the
## middle of the road in the way it's going.
func head(k: int, t: float) -> float:
	return (t - arrival(k)) * SPEED


## How far the rails reach on the side train `k` comes from, and the side it
## goes to.
func reach_in(k: int) -> float:
	return reach[0] if direction(k) > 0 else reach[1]


func reach_out(k: int) -> float:
	return reach[1] if direction(k) > 0 else reach[0]


## The train out on the rails at time `t`, or -1 if they're empty. It's out
## from when its front leaves one tunnel until its back's in the other.
func train_at(t: float) -> int:
	var near := _nearest(t)
	for k in range(maxi(near - 1, 0), near + 2):
		var front := head(k, t)
		if front >= -reach_in(k) and front - LENGTH <= reach_out(k):
			return k
	return -1


## From when the front of train `k` gets to the road until its back's off it,
## as Vector2(from, until).
func road_window(k: int) -> Vector2:
	var at := arrival(k)
	return Vector2(at - road_half / SPEED, at + (road_half + LENGTH) / SPEED)


## The next train to be on the road at or after time `t`, or the one on it
## now, as Vector2(from, until), with its number in z.
func next_window(t: float) -> Vector3:
	var near := _nearest(t)
	for k in range(maxi(near - 1, 0), near + 3):
		var w := road_window(k)
		if w.y >= t:
			return Vector3(w.x, w.y, k)
	var w := road_window(near + 3)
	return Vector3(w.x, w.y, near + 3)


## Whether the train's on the road now, or will be within `soon` seconds.
func blocked(t: float, soon := 0.0) -> bool:
	var w := next_window(t)
	return w.x <= t + soon


## Whether the lights are flashing.
func lights_on(t: float) -> bool:
	var w := next_window(t - OPEN_AFTER - BARRIER_SWING)
	return t >= w.x - LIGHTS_BEFORE and t <= w.y + OPEN_AFTER + BARRIER_SWING


## How far down the barriers are, from 0 (up) to 1 (across the road).
func barriers(t: float) -> float:
	var w := next_window(t - OPEN_AFTER - BARRIER_SWING)
	var down := clampf((t - (w.x - BARRIERS_BEFORE)) / BARRIER_SWING, 0.0, 1.0)
	var up := clampf((t - (w.y + OPEN_AFTER)) / BARRIER_SWING, 0.0, 1.0)
	return minf(down, 1.0 - up)


## The train due nearest before time `t`, or 0 before the first. The ones
## worth looking at are this one and its neighbours.
func _nearest(t: float) -> int:
	return maxi(floori((t - first) / every), 0)
