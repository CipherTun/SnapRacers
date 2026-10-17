class_name NeckLooks
extends RefCounted

## What's around the neck, like scarves, ties, necklaces and collars, in the
## neck piece's colour. They're all made in tools/characters/necks.py.


static func build(rig: CharacterRig) -> void:
	if rig.design.style_of("neck") != "none" and not rig.add_style("neck"):
		push_warning("No neck piece made for %s" % rig.design.style_of("neck"))
