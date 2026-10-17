class_name HairLooks
extends RefCounted

## Hair and raised facial hair, made in tools/characters/hair.py and
## beards.py, in their own colours on the head. Under a hat that covers the
## top of the head, hair has a cut version that only comes up to the hat's
## rim. The rest of the facial hair is printed on the face (see FacePrint).


static func build(rig: CharacterRig, covered: bool) -> void:
	var style := rig.design.style_of("hair")
	if style != "none" and not rig.add_style("hair", "cut" if covered else ""):
		push_warning("No hair made for %s" % style)


## Raised facial hair, like a full beard or sideburns. Printed facial hair
## isn't made in tools/characters, so there's nothing to add for it.
static func build_beard(rig: CharacterRig) -> void:
	if not CharacterMesh.style("facial_hair", rig.design.style_of("facial_hair")).is_empty():
		rig.add_style("facial_hair")
