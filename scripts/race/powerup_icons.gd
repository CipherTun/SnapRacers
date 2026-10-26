class_name PowerupIcons
extends RefCounted

## A picture for each power-up (see Powerups.ALL), drawn with shapes so it
## needs no image files. Chunky toy shapes with a dark outline, so they read
## small on a phone.

const OUTLINE := Color(0.08, 0.06, 0.12)
const RED := Color("#d8312f")
const YELLOW := Color("#f2cd37")
const ORANGE := Color("#fe8a18")
const BLUE := Color("#1e7fd8")
const GREEN := Color("#4bb24b")
const GREY := Color("#a0a5a9")
const DARK := Color("#4a4f55")
const WHITE := Color("#f4f4f4")
const BROWN := Color("#a0703a")
const CYAN := Color("#5fd8f0")


## Draws the picture for `kind` on `item`, centred on `at`, `size` across.
static func draw(item: CanvasItem, kind: String, at: Vector2, size: float) -> void:
	var s := size * 0.5
	var w := maxf(1.5, size * 0.045)
	match kind:
		"turbo":
			_chevron(item, at + Vector2(0, s * 0.15), s * 0.75, ORANGE, w)
		"big_turbo":
			_flame(item, at + Vector2(0, s * 0.42), s * 0.55, w)
			_chevron(item, at + Vector2(0, -s * 0.05), s * 0.9, RED, w)
		"triple_turbo":
			for i in 3:
				_chevron(item, at + Vector2(0, s * (0.5 - i * 0.42)), s * 0.55, [YELLOW, ORANGE, RED][i], w)
		"tow":
			_tow(item, at, s, w)
		"wall":
			_wall(item, at, s, w)
		"shockwave":
			for i in 3:
				var r := s * (0.3 + i * 0.27)
				item.draw_arc(at, r, 0.0, TAU, 40, OUTLINE, s * 0.2)
				item.draw_arc(at, r, 0.0, TAU, 40, CYAN.lerp(WHITE, i * 0.25), s * 0.12)
			_shape(item, _circle(at, s * 0.16, 16), WHITE, w)
		"spikes":
			_spikes(item, at, s, w)
		"dropper":
			_brick(item, at + Vector2(0, -s * 0.2), Vector2(s * 1.3, s * 0.65), YELLOW, w)
			_shape(item, PackedVector2Array([at + Vector2(-s * 0.35, s * 0.4), at + Vector2(s * 0.35, s * 0.4), at + Vector2(0, s * 0.85)]), WHITE, w)
		"marbles":
			_marble(item, at + Vector2(-s * 0.38, s * 0.3), s * 0.36, BLUE, w)
			_marble(item, at + Vector2(s * 0.38, s * 0.3), s * 0.36, GREEN, w)
			_marble(item, at + Vector2(0, -s * 0.32), s * 0.36, RED, w)
		"cannon":
			_cannon(item, at, s, w)
		"homing":
			item.draw_arc(at, s * 0.82, 0.0, TAU, 40, OUTLINE, s * 0.22)
			item.draw_arc(at, s * 0.82, 0.0, TAU, 40, RED, s * 0.12)
			for a in 4:
				var d := Vector2.from_angle(a * PI * 0.5)
				item.draw_line(at + d * s * 0.62, at + d * s * 1.0, OUTLINE, s * 0.22)
				item.draw_line(at + d * s * 0.66, at + d * s * 0.96, RED, s * 0.12)
			_brick(item, at + Vector2(0, s * 0.08), Vector2(s * 0.9, s * 0.45), RED, w)
		"shield":
			var pts := PackedVector2Array([
				at + Vector2(-s * 0.75, -s * 0.7), at + Vector2(0, -s * 0.9), at + Vector2(s * 0.75, -s * 0.7),
				at + Vector2(s * 0.7, s * 0.05), at + Vector2(s * 0.4, s * 0.55), at + Vector2(0, s * 0.9),
				at + Vector2(-s * 0.4, s * 0.55), at + Vector2(-s * 0.7, s * 0.05)])
			_shape(item, pts, BLUE, w)
			var inner := PackedVector2Array()
			for p in pts:
				inner.append(at + (p - at) * 0.6 + Vector2(0, -s * 0.04))
			item.draw_colored_polygon(inner, BLUE.lightened(0.35))
		"repair":
			item.draw_arc(at + Vector2(0, -s * 0.45), s * 0.3, PI, TAU, 16, OUTLINE, s * 0.28)
			item.draw_arc(at + Vector2(0, -s * 0.45), s * 0.3, PI, TAU, 16, DARK, s * 0.14)
			_shape(item, _box(at + Vector2(0, s * 0.12), Vector2(s * 1.6, s * 1.2)), GREEN, w)
			item.draw_rect(Rect2(at + Vector2(-s * 0.5, s * 0.02), Vector2(s * 1.0, s * 0.22)), WHITE)
			item.draw_rect(Rect2(at + Vector2(-s * 0.11, s * -0.37), Vector2(s * 0.22, s * 1.0)), WHITE)
		"ghost":
			_ghost(item, at, s, w)
		"lightning":
			_shape(item, PackedVector2Array([
				at + Vector2(s * 0.2, -s * 0.95), at + Vector2(-s * 0.55, s * 0.1), at + Vector2(-s * 0.05, s * 0.1),
				at + Vector2(-s * 0.3, s * 0.95), at + Vector2(s * 0.6, -s * 0.2), at + Vector2(s * 0.08, -s * 0.2),
				at + Vector2(s * 0.4, -s * 0.95)]), YELLOW, w)
		_:
			_shape(item, _circle(at, s * 0.6, 20), GREY, w)


## A filled shape with a dark outline round it.
static func _shape(item: CanvasItem, pts: PackedVector2Array, colour: Color, w: float) -> void:
	if colour.a > 0.0:
		item.draw_colored_polygon(pts, colour)
	if w > 0.0:
		var loop := pts.duplicate()
		loop.append(pts[0])
		item.draw_polyline(loop, OUTLINE, w, true)


static func _box(centre: Vector2, size: Vector2) -> PackedVector2Array:
	var h := size * 0.5
	return PackedVector2Array([centre - h, centre + Vector2(h.x, -h.y), centre + h, centre + Vector2(-h.x, h.y)])


static func _circle(centre: Vector2, r: float, points: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in points:
		pts.append(centre + Vector2.from_angle(TAU * i / points) * r)
	return pts


## A thick arrow head pointing up, for a turbo.
static func _chevron(item: CanvasItem, at: Vector2, s: float, colour: Color, w: float) -> void:
	var t := s * 0.72
	_shape(item, PackedVector2Array([
		at + Vector2(0, -s), at + Vector2(s, 0), at + Vector2(s, t), at + Vector2(0, t - s),
		at + Vector2(-s, t), at + Vector2(-s, 0)]), colour, w)


static func _flame(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	var pts := PackedVector2Array([
		at + Vector2(-s, -s * 0.4), at + Vector2(s, -s * 0.4), at + Vector2(s * 0.6, s * 0.3),
		at + Vector2(s * 0.3, s * 0.0), at + Vector2(0, s * 0.9), at + Vector2(-s * 0.3, s * 0.0), at + Vector2(-s * 0.6, s * 0.3)])
	_shape(item, pts, YELLOW, w)


## A toy brick seen from the side, with studs on top.
static func _brick(item: CanvasItem, at: Vector2, size: Vector2, colour: Color, w: float) -> void:
	var studs := 2 if size.x < size.y * 2.5 else 3
	var stud := Vector2(size.x / (studs * 1.8 + 0.2), size.y * 0.38)
	for i in studs:
		var x := at.x - size.x * 0.5 + size.x * (i + 0.5) / studs
		_shape(item, _box(Vector2(x, at.y - size.y * 0.5 - stud.y * 0.5 + w * 0.5), stud), colour.darkened(0.1), w)
	_shape(item, _box(at, size), colour, w)
	item.draw_rect(Rect2(at - size * 0.5 + Vector2(w, w), Vector2(size.x - w * 2.0, size.y * 0.22)), colour.lightened(0.3))


static func _wall(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	var bw := s * 0.62
	var bh := s * 0.42
	for row in 4:
		var y := at.y - s * 0.84 + row * bh + bh * 0.5
		var shift := 0.0 if row % 2 == 0 else bw * 0.5
		var x := at.x - s * 0.93 - shift
		while x < at.x + s * 0.93:
			var left := maxf(x, at.x - s * 0.93)
			var right := minf(x + bw, at.x + s * 0.93)
			if right - left > w:
				_shape(item, _box(Vector2((left + right) * 0.5, y), Vector2(right - left, bh)), RED if (row + int(x)) % 3 else RED.darkened(0.12), w)
			x += bw


static func _spikes(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	_shape(item, _box(at + Vector2(0, s * 0.62), Vector2(s * 1.8, s * 0.4)), DARK, w)
	for i in 4:
		var x := at.x - s * 0.9 + s * 0.45 * (i + 0.5)
		_shape(item, PackedVector2Array([Vector2(x - s * 0.22, at.y + s * 0.42), Vector2(x, at.y - s * 0.75), Vector2(x + s * 0.22, at.y + s * 0.42)]), GREY.lightened(0.2), w)


static func _marble(item: CanvasItem, at: Vector2, r: float, colour: Color, w: float) -> void:
	_shape(item, _circle(at, r, 20), colour, w)
	item.draw_circle(at + Vector2(-r * 0.35, -r * 0.35), r * 0.28, Color(1, 1, 1, 0.85))


static func _cannon(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	# A squat barrel tipped up to the right on a wedge, the ball just out of it.
	var dir := Vector2.from_angle(deg_to_rad(-30.0))
	var up := dir.orthogonal()
	_shape(item, PackedVector2Array([
		at + Vector2(-s * 0.95, s * 0.92), at + Vector2(s * 0.3, s * 0.92),
		at + Vector2(s * 0.05, s * 0.32), at + Vector2(-s * 0.7, s * 0.6)]), BROWN, w)
	var back := at + Vector2(-s * 0.72, s * 0.3)
	var flare := back + dir * s * 0.6
	var mouth := back + dir * s * 0.85
	_shape(item, PackedVector2Array([
		back + up * s * 0.36, flare + up * s * 0.36, mouth + up * s * 0.5,
		mouth - up * s * 0.5, flare - up * s * 0.36, back - up * s * 0.36]), GREY, w)
	var ball := mouth + dir * s * 0.5
	_shape(item, _circle(ball, s * 0.34, 18), DARK, w)
	item.draw_circle(ball + Vector2(-s * 0.11, -s * 0.11), s * 0.09, Color(1, 1, 1, 0.8))


static func _tow(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	# A rope coming in from the left to a big hook.
	var eye := at + Vector2(s * 0.38, -s * 0.62)
	var rope := PackedVector2Array()
	for i in 13:
		var t := i / 12.0
		var from := at + Vector2(-s * 0.95, s * 0.1)
		rope.append(from.lerp(eye, t) + Vector2(0, -sin(t * PI) * s * 0.35))
	item.draw_polyline(rope, OUTLINE, s * 0.36, true)
	item.draw_polyline(rope, BROWN.lightened(0.2), s * 0.22, true)
	item.draw_arc(eye, s * 0.17, 0.0, TAU, 16, OUTLINE, s * 0.26)
	item.draw_arc(eye, s * 0.17, 0.0, TAU, 16, GREY.lightened(0.2), s * 0.14)
	var hook := at + Vector2(s * 0.0, s * 0.35)
	var shank_end := hook + Vector2(s * 0.38, 0)
	item.draw_line(eye + Vector2(0, s * 0.15), shank_end, OUTLINE, s * 0.34)
	item.draw_line(eye + Vector2(0, s * 0.15), shank_end, GREY.lightened(0.2), s * 0.2)
	item.draw_arc(hook, s * 0.38, 0.0, PI * 1.05, 20, OUTLINE, s * 0.34)
	item.draw_arc(hook, s * 0.38, 0.0, PI * 1.05, 20, GREY.lightened(0.2), s * 0.2)
	_shape(item, PackedVector2Array([hook + Vector2(-s * 0.55, s * 0.02), hook + Vector2(-s * 0.2, s * 0.02), hook + Vector2(-s * 0.38, -s * 0.3)]), GREY.lightened(0.2), w)


static func _ghost(item: CanvasItem, at: Vector2, s: float, w: float) -> void:
	var pts := PackedVector2Array()
	for i in 13:
		pts.append(at + Vector2(0, -s * 0.2) + Vector2.from_angle(PI + PI * i / 12.0) * s * 0.65)
	var bottom := at.y + s * 0.85
	var waves := 3
	for i in waves * 2 + 1:
		var x := at.x + s * 0.65 - s * 1.3 * i / (waves * 2.0)
		pts.append(Vector2(x, bottom - (s * 0.22 if i % 2 else 0.0)))
	_shape(item, pts, WHITE, w)
	for side in [-1.0, 1.0]:
		item.draw_circle(at + Vector2(side * s * 0.24, -s * 0.18), s * 0.14, OUTLINE)
		item.draw_circle(at + Vector2(side * s * 0.24 - s * 0.04, -s * 0.23), s * 0.05, WHITE)
