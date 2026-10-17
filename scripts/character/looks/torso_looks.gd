class_name TorsoLooks
extends RefCounted

## The torso, the standard moulded torso with its style printed on as colour
## regions, in the torso's colour. They're all made in
## tools/characters/torsos.py.


static func build(rig: CharacterRig) -> void:
	if not rig.add_style("torso"):
		push_warning("No torso made for %s" % rig.design.style_of("torso"))
		rig.add_figure("torso", rig.upper(), {"main": rig.design.color_of("torso")})
