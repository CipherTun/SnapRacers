class_name HeadgearLooks
extends RefCounted

## Hats, helmets and the like, made in tools/characters/headgear.py, in the
## headgear's colour on the head. Each says what hair shows under it: hats
## have the cut hair under them, helmets and hoods hide it, and what's worn
## on the hair (a headband, a tiara, a party hat, horns) has the full hair
## and is placed to fit each hairdo.


## What hair shows under this headgear: "cut", "hidden" or "full".
static func hair_under(style: String) -> String:
	var entry := CharacterMesh.style("headgear", style)
	return str(entry.get("hair", "full"))


## Whether this headgear covers the top of the head, hiding the top of the
## hair and the stud.
static func covers_top(style: String) -> bool:
	return hair_under(style) != "full"


## Where headgear worn on the hair goes for this hairdo, in the head's space.
static func fit(style: String, hair: String) -> Transform3D:
	var fits: Dictionary = CharacterMesh.style("headgear", style).get("fit", {})
	var f: Array = fits.get(hair, fits.get("none", [1.0, 1.0, 0.0, 0.0]))
	return Transform3D(Basis.from_scale(Vector3(f[0], f[1], f[0])), Vector3(0.0, f[2], f[3]))


static func build(rig: CharacterRig) -> void:
	var style := rig.design.style_of("headgear")
	if style == "none":
		return
	var hair := rig.design.style_of("hair")
	if not rig.add_style("headgear", "", fit(style, hair)):
		push_warning("No headgear made for %s" % style)
