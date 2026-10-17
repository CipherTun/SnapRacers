class_name ArmLooks
extends RefCounted

## An arm, one piece from the rounded shoulder down to the fixed bend at the
## elbow and on to the wrist, then the C shaped hand, in the arms piece's
## colour. Each style is made for each side in tools/characters/arms.py, from
## its settings in pieces.json, like how long the sleeves are and what's on
## the hands.


static func build(rig: CharacterRig, arm: Node3D, hand: Node3D, side: int) -> void:
	if rig.add_style("arms", "" if side == 0 else "arm_r"):
		rig.add_style("arms", "hand_l" if side == 0 else "hand_r")
		return
	push_warning("No arms made for %s" % rig.design.style_of("arms"))
	var c := rig.design.color_of("arms")
	rig.add_figure("arm_l" if side == 0 else "arm_r", arm, {"shoulder": c, "upper": c, "fore": c})
	rig.add_figure("hand_l" if side == 0 else "hand_r", hand, {"main": rig.design.skin()})
