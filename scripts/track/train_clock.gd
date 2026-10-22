class_name TrainClock
extends RefCounted

## The trains' clock (see LevelCrossing). It keeps time with the race clock,
## except online, where a client's is pulled towards the host's so every
## device has the trains in the same place. Lap times never use it.

## How quickly a client's clock catches up with the host's, per second, and
## how far apart they can be before it just jumps.
const PULL := 4.0
const JUMP := 2.0

## Race seconds from GO.
var now := 0.0
## How far the host's clock was ahead of ours when it last said, less what's
## been made up since.
var _behind := 0.0


func _init(start := 0.0) -> void:
	now = start


func run(delta: float) -> void:
	now += delta
	if absf(_behind) > JUMP:
		now += _behind
		_behind = 0.0
	elif _behind != 0.0:
		var step := _behind * minf(1.0, delta * PULL)
		now += step
		_behind -= step


## The host's clock, from an update it sent `lag` seconds ago.
func from_host(at: float, lag := 0.0) -> void:
	_behind = at + lag - now
