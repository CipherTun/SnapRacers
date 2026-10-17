class_name HairLooks
extends RefCounted

## Hair and raised facial hair, made in tools/characters/hair.py and
## beards.py, in their own colours on the head. Under a hat that covers the
## top of the head, hair has a cut version that only comes up to the hat's
## rim. The rest of the facial hair is printed on the face (see FacePrint).


## How far out from the middle of the head the hair (or the head) is at this
## height, for putting something like a crown or a band around it. Both are
## in the head's own space, before it's scaled up.
static func radius_at(style: String, height: float) -> float:
	var R := CharacterRig
	var head := R.HEAD_RADIUS
	if height > R.HEAD_HEIGHT * 0.5 - 0.035:
		var over := height - (R.HEAD_HEIGHT * 0.5 - 0.035)
		head = R.HEAD_RADIUS - 0.035 + sqrt(maxf(0.035 * 0.035 - over * over, 0.0))
	var steps: Array = CharacterMesh.style("hair", style).get("radius_at", [])
	if steps.is_empty() or height < steps[0][0] or height > steps[-1][0]:
		return head
	for i in steps.size() - 1:
		var a: Array = steps[i]
		var b: Array = steps[i + 1]
		if height <= b[0]:
			var t := inverse_lerp(float(a[0]), float(b[0]), height)
			return maxf(head, lerpf(float(a[1]), float(b[1]), t))
	return maxf(head, float(steps[-1][1]))


## How high the top of the hair is, above the middle of the head.
static func top_of(style: String) -> float:
	var entry := CharacterMesh.style("hair", style)
	if entry.is_empty():
		return CharacterRig.HEAD_HEIGHT * 0.5 + 0.04
	return float(entry.top)


static func build(rig: CharacterRig, covered: bool) -> void:
	var style := rig.design.style_of("hair")
	if style != "none" and not rig.add_style("hair", "cut" if covered else ""):
		push_warning("No hair made for %s" % style)


## Raised facial hair, like a full beard or sideburns. Printed facial hair
## isn't made in tools/characters, so there's nothing to add for it.
static func build_beard(rig: CharacterRig) -> void:
	if not CharacterMesh.style("facial_hair", rig.design.style_of("facial_hair")).is_empty():
		rig.add_style("facial_hair")
