class_name HeadlightPool
extends MeshInstance3D

## The light a kart's headlights throw ahead of it. A real light would mean
## drawing the road and everything near it again for every kart, too slow for a
## phone, so this is a box around the beam that reads the depth of whatever's
## already drawn inside it and adds light to the surfaces that fall in the beam.
## Only solid things are in the depth, so see-through ones don't catch it.

## How far the beam reaches and how wide the box is, in metres, and how bright.
const LENGTH := 10.0
const WIDTH := 6.0
## How far the box goes below and above where the wheels touch, in metres, to
## take in ground going down or up and karts or walls ahead.
const BELOW := 2.5
const ABOVE := 3.0
## How high the lamps are above where the wheels touch, in metres.
const LAMP_HEIGHT := 0.4
const BRIGHTNESS := 0.6

const SHADER := """
shader_type spatial;
// Drawn on the box's inside faces with no depth test, so it still works with
// the camera inside it (bumper view) or something in front of it.
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_front, shadows_disabled, fog_disabled;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float bright = 0.6;
uniform float reach = 10.0;
// The lamps, in the box's own space.
uniform vec3 lamp = vec3(0.0);
uniform float floor_below = 2.5;

// The lamps and the beam's directions in view space, the same at every corner.
varying vec3 v_lamp;
varying vec3 v_ahead;
varying vec3 v_side;
varying vec3 v_up;

void vertex() {
	v_lamp = (MODELVIEW_MATRIX * vec4(lamp, 1.0)).xyz;
	mat3 turn = mat3(MODELVIEW_MATRIX);
	v_ahead = normalize(turn * vec3(0.0, 0.0, -1.0));
	v_side = normalize(turn * vec3(1.0, 0.0, 0.0));
	v_up = normalize(turn * vec3(0.0, 1.0, 0.0));
}

void fragment() {
	// The surface already drawn behind this pixel, in view space, from
	// OpenGL's depth (-1 to 1 once scaled). The sky reads as 0 or 1 depending
	// on the device and gets no light. No discard, since the dFdx below needs
	// every pixel.
	float depth = texture(depth_tex, SCREEN_UV).r;
	float solid = step(0.000001, depth) * step(depth, 0.999999);
	vec4 view = INV_PROJECTION_MATRIX * vec4(vec3(SCREEN_UV, depth) * 2.0 - 1.0, 1.0);
	vec3 p = view.xyz / view.w;

	vec3 d = p - v_lamp;
	float ahead = dot(d, v_ahead);
	float side = abs(dot(d, v_side));
	float up = dot(d, v_up);
	float dist = length(d);

	// Brightest down the middle, widening and fading out with distance, and
	// nothing behind the lamps.
	float half_width = 0.5 + 0.17 * ahead;
	float fan = 1.0 - smoothstep(0.3 * half_width, half_width, side);
	float fade = smoothstep(0.0, 1.2, ahead) * (1.0 - smoothstep(0.6 * reach, reach, dist));
	// Less light close to the lamps, so a kart just ahead doesn't go white.
	fade *= mix(0.45, 1.0, smoothstep(1.0, 3.0, dist));
	// Not too far above the beam, and fading out before the bottom of the box.
	float high = 1.0 - smoothstep(0.3 + 0.1 * ahead, 0.8 + 0.25 * ahead, up);
	float low = smoothstep(-floor_below, -floor_below + 0.6, up);

	// Faces turned towards the lamps get more light and faces turned away get
	// none. The normal comes from 2x2 pixel blocks, so it's off along creases
	// and at depth jumps (the edge of a kart); a wide ramp and a little less
	// light there keep that from showing. Upright faces get at most 0.2 against
	// the road's 0.7 to 0.9, since the light adds up where several beams fall on
	// one kart, and more than that turns it white.
	vec3 normal = normalize(cross(dFdx(p), dFdy(p)));
	normal *= sign(dot(normal, -p));
	float facing = smoothstep(-0.35, 0.25, dot(normal, -d / max(dist, 0.001)));
	facing *= mix(0.2, 1.0, max(dot(normal, v_up), 0.0));
	float jump = fwidth(p.z) / max(-p.z, 0.1);
	facing *= mix(1.0, 0.6, smoothstep(0.02, 0.06, jump));

	ALBEDO = vec3(1.0, 0.92, 0.75) * bright * fan * fade * high * low * facing * solid;
}
"""

static var _shader: Shader


## A beam in front of a kart whose front is `front` and whose wheels touch the
## ground at `ground` (both along and up, in the kart's own space).
func _init(front: float, ground: float) -> void:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = SHADER
	var box := BoxMesh.new()
	box.size = Vector3(WIDTH, BELOW + ABOVE, LENGTH)
	mesh = box
	var middle := (ABOVE - BELOW) * 0.5
	var material := ShaderMaterial.new()
	material.shader = _shader
	material.set_shader_parameter("bright", BRIGHTNESS)
	material.set_shader_parameter("reach", LENGTH)
	material.set_shader_parameter("lamp", Vector3(0.0, LAMP_HEIGHT - middle, LENGTH * 0.5))
	material.set_shader_parameter("floor_below", BELOW + LAMP_HEIGHT)
	material_override = material
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	position = Vector3(0.0, ground + middle, front - LENGTH * 0.5)
