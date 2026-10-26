class_name TowRope
extends MeshInstance3D

## A tow rope from one kart to the kart ahead of it. For a few seconds the kart
## on the end is pulled along towards a spot just behind the one it's caught
## onto, in its slipstream, a bit faster than it's going, and then it lets go
## with a short burst. The rope is drawn as a thin bar between them.

const TIME := 3.0
## How far behind the kart ahead it pulls towards, how much faster than it,
## and how hard.
const BEHIND := 4.0
const FASTER := 1.15
const PULL := 2200.0
## How far ahead a kart has to be for the rope to reach it.
const REACH := 60.0
## How far ahead along the road a kart has to be before the rope can catch it,
## about two and a half kart lengths.
const NEAREST := 6.0
## How far off straight ahead it can be, as the cosine of the angle (50 degrees).
const CONE := 0.64
const BURST := 1.0

var from: Kart
var to: Kart
var left := TIME


## A rope from this kart to the one ahead of it, or null if nobody's in reach.
static func throw(kart: Kart, ahead: Kart) -> TowRope:
	if ahead == null or not is_instance_valid(ahead) or ahead.global_position.distance_to(kart.global_position) > REACH:
		return null
	var rope := TowRope.new()
	rope.from = kart
	rope.to = ahead
	return rope


## The kart a rope from this one would catch, or null. It's the nearest one
## NEAREST to REACH ahead along the road, in front of this kart and going the
## same way, so not one beside it, behind it or across a hairpin. It only reads
## the race's karts and their offsets along the track.
static func target(kart: Kart) -> Kart:
	# The race is asked without naming it, since Race needs the Game autoload
	# and the -s tests load karts without one.
	var race = kart.get_parent()
	if race == null or not ("racers" in race) or not ("track" in race) or race.track == null:
		return null
	var from_offset := -1.0
	var others := []
	for racer in race.racers:
		if racer.kart == kart:
			from_offset = racer.offset
		elif is_instance_valid(racer.kart):
			others.append({"kart": racer.kart, "offset": racer.offset})
	if from_offset < 0.0:
		return null
	return pick(kart, from_offset, others, race.track.length) as Kart


## The nearest of these, each {"kart", "offset"}, that a rope from this kart at
## this offset can catch on a track this long. Offsets wrap at the line, so a
## kart just over it counts as just ahead, whatever lap either is on. Ties go
## to the first in the list.
static func pick(kart: Node3D, from_offset: float, others: Array, track_length: float) -> Node3D:
	var facing := -kart.global_basis.z
	var best: Node3D = null
	var best_gap := INF
	for other in others:
		var ahead: Node3D = other.kart
		var gap := fposmod(float(other.offset) - from_offset, track_length)
		if gap < NEAREST or gap > REACH or gap >= best_gap:
			continue
		var toward := ahead.global_position - kart.global_position
		if toward.length() < 0.1 or toward.length() > REACH or facing.dot(toward.normalized()) < CONE:
			continue
		if facing.dot(-ahead.global_basis.z) < 0.0:
			continue
		best = ahead
		best_gap = gap
	return best


func _init() -> void:
	var bar := BoxMesh.new()
	bar.size = Vector3(0.16, 0.16, 1.0)
	mesh = bar
	material_override = PartVisuals.material(Color("#f2cd37"))
	top_level = true


func _ready() -> void:
	if from != null:
		from.tow = self


## The push the kart on the end gets this step.
func pull_on(kart: Kart) -> Vector3:
	if not is_instance_valid(to) or kart != from:
		return Vector3.ZERO
	var spot := to.global_position + to.global_basis.z * BEHIND
	var toward := spot - kart.global_position
	toward.y = 0.0
	if toward.length() < 1.0:
		return Vector3.ZERO
	var ahead_speed := maxf(to.linear_velocity.length(), 5.0)
	if kart.linear_velocity.dot(toward.normalized()) > ahead_speed * FASTER:
		return Vector3.ZERO
	return toward.normalized() * PULL


## Timed in physics steps, so the rope lets go and the burst starts on the
## same step on every machine.
func _physics_process(delta: float) -> void:
	left -= delta
	if left <= 0.0 or not is_instance_valid(from) or not is_instance_valid(to):
		if is_instance_valid(from):
			if from.tow == self:
				from.tow = null
				if not from.remote:
					from.start_boost(maxf(from.boost_left, BURST), 1)
		set_physics_process(false)
		set_process(false)
		queue_free()


func _process(_delta: float) -> void:
	if not is_instance_valid(from) or not is_instance_valid(to):
		return
	var a := from.global_position + Vector3.UP * 0.6
	var b := to.global_position + Vector3.UP * 0.6
	var length := a.distance_to(b)
	if length < 0.1:
		visible = false
		return
	visible = true
	global_transform = Transform3D(Basis.looking_at(b - a, Vector3.UP).scaled_local(Vector3(1.0, 1.0, length)), (a + b) * 0.5)
