class_name BoardView
extends Control
## The arena. It stands upright: the engine's left side is at the top of the
## screen and its right side at the bottom, so an engine tile (x, y) is drawn
## in column y, row x. It draws grass, roads, the river, castles and units, and
## it can light tiles up to show a path search at work. It knows nothing about
## the rules: the match screen tells it what to show.

signal tile_chosen(spot: int)

const TILE := 48.0
const EDGE := Color("0d2238")

var speed := 1.0

var _rows: Array = []
var _across := 0             # tiles from side to side on screen (the engine's height)
var _down := 0               # tiles from top to bottom on screen (the engine's width)
var _colors := {}
var _sides := {}
var _pieces := {}            # unit number -> UnitPiece
var _towers := {}            # side -> {"tile", "health", "shown", "full", "shake", "face", "count", "aim", "kick"}
var _glow := {}              # Vector2i (engine tile) -> Color, whose alpha fades away
var _lines: Array = []       # {"points", "color", "life", "full", "width"}
var _sparks: Array = []      # {"at", "color", "life", "full"}: a burst where a blow lands
var _shots: Array = []       # {"from", "to", "life", "full"}: a tower's cannonball on its way
var _ghosts := {}            # Vector2i (engine tile) -> Color: a drop on its way, in power mode
var _pick_tiles := {}        # Vector2i (engine tile) -> spot, while a side is choosing where to drop
var _pick_hover := Vector2i(-1, -1)
var _pick_hint := Vector2i(-1, -1)
var _time := 0.0


func setup(view: Dictionary, colors: Dictionary) -> void:
	_rows = view["map"]["rows"]
	_across = int(view["map"]["height"])
	_down = int(view["map"]["width"])
	_colors = colors
	_sides = view["sides"]
	size = Vector2(_across * TILE, _down * TILE)
	custom_minimum_size = size
	mouse_filter = Control.MOUSE_FILTER_PASS
	for side in ["left", "right"]:
		var tile: Array = view["sides"][side]["tower_tile"]
		var face := UI.emoji(str(view["sides"][side]["emoji"]), 22)
		face.size = Vector2(40, 34)
		add_child(face)
		var count := UI.title("", 13, UI.WHITE, 5)
		count.size = Vector2(64, 18)
		count.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		count.z_index = 5
		add_child(count)
		_towers[side] = {"tile": Vector2i(int(tile[0]), int(tile[1])), "health": int(view["sides"][side]["tower"]),
			"shown": float(view["sides"][side]["tower"]), "full": int(view["rules"]["tower_health"]), "shake": 0.0,
			"face": face, "count": count, "aim": Vector2(0, 1 if side == "left" else -1), "kick": 0.0}
	_place_towers()
	queue_redraw()


## The middle of an engine tile, on screen.
func tile_centre(tile: Variant) -> Vector2:
	return Vector2((float(tile[1]) + 0.5) * TILE, (float(tile[0]) + 0.5) * TILE)


func _tile_rect(x: int, y: int) -> Rect2:
	return Rect2(Vector2(y * TILE, x * TILE), Vector2(TILE, TILE))


## The castle stands a little inside the arena, away from the rim.
func tower_centre(side: String) -> Vector2:
	var tile: Vector2i = _towers[side]["tile"]
	return tile_centre([tile.x, tile.y]) + Vector2(0, 4.0 if side == "left" else -6.0)


func piece(number: int) -> UnitPiece:
	return _pieces.get(number)


func _place_towers() -> void:
	for side in _towers:
		var tower: Dictionary = _towers[side]
		var middle := tower_centre(side) + Vector2(sin(_time * 70.0) * 4.0 * float(tower["shake"]), 0)
		tower["face"].position = middle + Vector2(-20, -30)
		tower["count"].position = middle + Vector2(-32, 9)
		tower["count"].text = str(int(tower["health"]))


# ----------------------------------------------------------------- units

func add_unit(info: Dictionary) -> UnitPiece:
	var made := UnitPiece.new()
	made.setup(info, _colors[str(info["side"])])
	made.place(tile_centre(info["tile"]))
	made.z_index = 2
	add_child(made)
	_pieces[int(info["unit"])] = made
	UI.pop_in(made, 0.25)
	return made


## Make the board match a snapshot exactly: positions, health, and who is gone.
func sync_units(units: Array, animate: bool = false) -> void:
	var seen := {}
	for info in units:
		var number := int(info["unit"])
		seen[number] = true
		var made: UnitPiece = _pieces.get(number)
		if made == null:
			made = add_unit(info)
		if made.health != int(info["health"]):
			made.set_health(int(info["health"]))
	for number in _pieces.keys():
		if not seen.has(number):
			var gone: UnitPiece = _pieces[number]
			_pieces.erase(number)
			gone.leave()
	_settle(units, animate)


## Units sharing a tile stand side by side instead of on top of each other.
func _settle(units: Array, animate: bool) -> void:
	var by_tile := {}
	for info in units:
		var key := Vector2i(int(info["tile"][0]), int(info["tile"][1]))
		if not by_tile.has(key):
			by_tile[key] = []
		by_tile[key].append(int(info["unit"]))
	for key in by_tile:
		var here: Array = by_tile[key]
		for place in here.size():
			var made: UnitPiece = _pieces.get(here[place])
			if made == null:
				continue
			var offset := Vector2((place - (here.size() - 1) / 2.0) * 15.0, (place % 2) * 6.0 - (3.0 if here.size() > 1 else 0.0))
			var target := tile_centre([key.x, key.y]) + offset - UnitPiece.ANCHOR
			made.z_index = 2 + key.x            # whoever stands lower on the screen is drawn in front
			if animate:
				made.create_tween().tween_property(made, "position", target, 0.12 / speed)
			else:
				made.position = target


func clear_units() -> void:
	for number in _pieces.keys():
		_pieces[number].queue_free()
	_pieces.clear()


## Walk a piece along a list of tiles. Returns how long it takes.
func walk(number: int, path: Array, per_tile: float) -> float:
	var made: UnitPiece = _pieces.get(number)
	if made == null or path.size() < 2:
		return 0.0
	made.walking = true
	var tween := made.create_tween()
	for place in range(1, path.size()):
		tween.tween_property(made, "position", tile_centre(path[place]) - UnitPiece.ANCHOR, per_tile)
	tween.tween_callback(func() -> void: made.walking = false)
	return per_tile * (path.size() - 1)


# ---------------------------------------------------------------- effects

## Light a tile in a colour. The light fades by itself.
func glow(tile: Variant, color: Color, strength: float = 0.85) -> void:
	_glow[Vector2i(int(tile[0]), int(tile[1]))] = Color(color, strength)
	queue_redraw()


## A line that fades away: a route, a blow or a shot.
func line(points: PackedVector2Array, color: Color, life: float, width: float = 4.0) -> void:
	_lines.append({"points": points, "color": color, "life": life, "full": life, "width": width})
	queue_redraw()


## A burst of light where a blow lands.
func spark(at: Vector2, color: Color) -> void:
	_sparks.append({"at": at, "color": color, "life": 0.4, "full": 0.4})


## Where a tower's cannon ends, for a shot and its flash.
func _muzzle(side: String) -> Vector2:
	var tower: Dictionary = _towers[side]
	var aim: Vector2 = tower["aim"]
	return _cannon_base(side) + aim * (24.0 - 6.0 * float(tower["kick"]))


func _cannon_base(side: String) -> Vector2:
	return tower_centre(side) + Vector2(0, 22.0 if side == "left" else -30.0)


## A tower fires: the cannon turns, kicks back, and a ball flies to the target.
func fire(side: String, to: Vector2, life: float) -> void:
	var tower: Dictionary = _towers[side]
	tower["aim"] = (to - _cannon_base(side)).normalized()
	tower["kick"] = 1.0
	var from := _muzzle(side)
	spark(from, UI.GOLD)
	_shots.append({"from": from, "to": to, "life": life, "full": life})


func route_line(route: Array, color: Color, life: float) -> void:
	var points := PackedVector2Array()
	for tile in route:
		points.append(tile_centre(tile))
	if points.size() >= 2:
		line(points, color, life, 6.0)


## A number that floats up from a point and fades: damage, or a fuzzy priority.
func float_text(at: Vector2, text: String, color: Color, text_size: int = 19, rise: float = 26.0, life: float = 0.8) -> void:
	var made := UI.title(text, text_size, color, 6)
	made.size = Vector2(200, 24)
	made.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	made.position = at - Vector2(100, 12)
	made.z_index = 20
	add_child(made)
	var tween := made.create_tween().set_parallel(true)
	tween.tween_property(made, "position:y", made.position.y - rise, life)
	tween.tween_property(made, "modulate:a", 0.0, life).set_ease(Tween.EASE_IN)
	tween.chain().tween_callback(made.queue_free)


func set_tower(side: String, health: int) -> void:
	var tower: Dictionary = _towers[side]
	if health <= 0 and int(tower["health"]) > 0:
		tower["shake"] = 2.5
		float_text(tower_centre(side) + Vector2(0, -44), "Castle down!", UI.GOLD, 24, 30.0, 1.6)
	if health < int(tower["health"]):
		tower["shake"] = maxf(float(tower["shake"]), 1.0)
		float_text(tower_centre(side) + Vector2(42, -8), "-%d" % (int(tower["health"]) - health), UI.RED, 22)
	tower["health"] = health
	var tween := create_tween()
	tween.tween_method(func(value: float) -> void:
		tower["shown"] = value
		queue_redraw()
	, float(tower["shown"]), float(health), 0.3)
	_place_towers()


func reset_towers(view: Dictionary) -> void:
	for side in ["left", "right"]:
		_towers[side]["health"] = int(view["sides"][side]["tower"])
		_towers[side]["shown"] = float(view["sides"][side]["tower"])
	_place_towers()
	queue_redraw()


# ----------------------------------------------------- choosing where to drop

## Light up every tile of a side's half. A click on one of them says which spot it is.
func start_tile_pick(drops: Array, hint_spot: int = -1) -> void:
	_pick_tiles.clear()
	for spot in drops.size():
		_pick_tiles[Vector2i(int(drops[spot][0]), int(drops[spot][1]))] = spot
	_pick_hint = Vector2i(-1, -1)
	if hint_spot >= 0:
		_pick_hint = Vector2i(int(drops[hint_spot][0]), int(drops[hint_spot][1]))
	_pick_hover = Vector2i(-1, -1)
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	queue_redraw()


func stop_tile_pick() -> void:
	_pick_tiles.clear()
	_pick_hint = Vector2i(-1, -1)
	_pick_hover = Vector2i(-1, -1)
	mouse_default_cursor_shape = Control.CURSOR_ARROW
	queue_redraw()


func _tile_at(at: Vector2) -> Vector2i:
	return Vector2i(int(floor(at.y / TILE)), int(floor(at.x / TILE)))


func _gui_input(event: InputEvent) -> void:
	if _pick_tiles.is_empty():
		return
	if event is InputEventMouseMotion:
		var over := _tile_at(event.position)
		if over != _pick_hover:
			_pick_hover = over
			queue_redraw()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var tile := _tile_at(event.position)
		if _pick_tiles.has(tile):
			Sfx.play("tap")
			tile_chosen.emit(int(_pick_tiles[tile]))


## A ring on the tile where a person's drop will land, until the drop arrives.
func add_ghost(tile: Variant, color: Color) -> void:
	_ghosts[Vector2i(int(tile[0]), int(tile[1]))] = color


func clear_ghost(tile: Variant) -> void:
	_ghosts.erase(Vector2i(int(tile[0]), int(tile[1])))


# ---------------------------------------------------------------- drawing

func _process(delta: float) -> void:
	_time += delta
	for key in _glow.keys():
		var color: Color = _glow[key]
		color.a -= delta * 1.1 * maxf(1.0, speed * 0.7)
		if color.a <= 0.0:
			_glow.erase(key)
		else:
			_glow[key] = color
	for place in range(_lines.size() - 1, -1, -1):
		_lines[place]["life"] -= delta
		if _lines[place]["life"] <= 0.0:
			_lines.remove_at(place)
	for place in range(_sparks.size() - 1, -1, -1):
		_sparks[place]["life"] -= delta
		if _sparks[place]["life"] <= 0.0:
			_sparks.remove_at(place)
	for place in range(_shots.size() - 1, -1, -1):
		_shots[place]["life"] -= delta
		if _shots[place]["life"] <= 0.0:
			spark(_shots[place]["to"], UI.WHITE)
			_shots.remove_at(place)
	for side in _towers:
		_towers[side]["kick"] = maxf(0.0, float(_towers[side]["kick"]) - delta * 5.0)
		if _towers[side]["shake"] > 0.0:
			_towers[side]["shake"] = maxf(0.0, _towers[side]["shake"] - delta * 3.0)
			_place_towers()
	queue_redraw()                       # the river never stands still


func _mark(x: int, y: int) -> String:
	return str(_rows[y])[x]


func _is_road(x: int, y: int) -> bool:
	if x < 0 or y < 0 or x >= _down or y >= _across:
		return false
	return _mark(x, y) in ["=", "S", "B"]


func _draw() -> void:
	# The rim, like a hedge round the arena.
	draw_style_box(UI.box(EDGE, 22), Rect2(Vector2(-16, -16), size + Vector2(32, 32)))
	draw_style_box(UI.box(UI.GRASS_RIM, 18), Rect2(Vector2(-12, -12), size + Vector2(24, 24)))

	# Grass everywhere first, in a checkerboard.
	for x in _down:
		for y in _across:
			draw_rect(_tile_rect(x, y), UI.GRASS if (x + y) % 2 == 0 else UI.GRASS_ALT)

	# Roads, mud and the river on top of the grass.
	for x in _down:
		for y in _across:
			var mark := _mark(x, y)
			var area := _tile_rect(x, y)
			if mark == "=" or mark == "S":
				draw_rect(area.grow(-3.0), UI.ROAD_EDGE)
				draw_rect(area.grow(-6.0), UI.ROAD)
				# Join this road tile to its road neighbours, so lanes read as one path.
				for step in [Vector2i(1, 0), Vector2i(0, 1)]:
					if _is_road(x + step.x, y + step.y):
						var other := _tile_rect(x + step.x, y + step.y)
						draw_rect(area.grow(-6.0).merge(other.grow(-6.0)), UI.ROAD)
			elif mark == "m":
				draw_style_box(UI.box(UI.MUD_DARK, 14), area.grow(-3.0))
				draw_style_box(UI.box(UI.MUD, 12), area.grow(-6.0))
				draw_circle(area.position + Vector2(17, 18), 5.0, UI.MUD_DARK)
				draw_circle(area.position + Vector2(31, 31), 6.0, UI.MUD_DARK)
				draw_circle(area.position + Vector2(33, 15), 3.0, UI.MUD_DARK)
			elif mark == "~" or mark == "B":
				draw_rect(Rect2(area.position + Vector2(0, 5), Vector2(TILE, TILE - 10)), UI.RIVER)
				var wave := sin(_time * 1.8 + y * 1.1) * 4.0
				draw_line(area.position + Vector2(6 + wave, 17), area.position + Vector2(26 + wave, 17), UI.RIVER_LIGHT, 2.5)
				draw_line(area.position + Vector2(22 - wave, 31), area.position + Vector2(42 - wave, 31), UI.RIVER_LIGHT, 2.5)
				draw_rect(Rect2(area.position + Vector2(0, 3), Vector2(TILE, 3)), UI.GRASS_RIM)
				draw_rect(Rect2(area.position + Vector2(0, TILE - 6), Vector2(TILE, 3)), UI.GRASS_RIM)
	for x in _down:
		for y in _across:
			var area := _tile_rect(x, y)
			if _mark(x, y) == "B":
				# A wooden bridge across the river, planks from side to side.
				var deck := Rect2(area.position + Vector2(5, -3), Vector2(TILE - 10, TILE + 6))
				draw_rect(deck.grow(2.0), UI.BRIDGE_DARK)
				draw_rect(deck, UI.BRIDGE)
				for plank in range(1, 6):
					var at := deck.position.y + plank * deck.size.y / 6.0
					draw_line(Vector2(deck.position.x, at), Vector2(deck.end.x, at), UI.BRIDGE_DARK, 1.5)
			elif _mark(x, y) == "S":
				draw_arc(area.get_center(), 13.0, 0.0, TAU, 28, Color(1, 1, 1, 0.75), 2.5, true)

	# Tiles lit by a search.
	for key in _glow:
		var lit: Color = _glow[key]
		var area := _tile_rect(key.x, key.y).grow(-2.0)
		draw_style_box(UI.box(Color(lit, lit.a * 0.5), 8, Color(lit, minf(1.0, lit.a * 1.4)), 3), area)

	# Tiles a person may drop on.
	var beat := 0.5 + 0.5 * sin(_time * 5.0)
	for tile in _pick_tiles:
		var area := _tile_rect(tile.x, tile.y).grow(-3.0)
		var strong: bool = tile == _pick_hover
		draw_style_box(UI.box(Color(1, 1, 1, 0.65 if strong else 0.14 + 0.1 * beat), 8, Color(UI.WHITE, 1.0 if strong else 0.55), 3 if strong else 2), area)
		if tile == _pick_hint:
			draw_style_box(UI.box(Color(0, 0, 0, 0), 10, Color(UI.GOLD, 0.6 + 0.4 * beat), 4), area.grow(1.0))
	for tile in _ghosts:
		var area := _tile_rect(tile.x, tile.y)
		draw_arc(area.get_center(), 14.0 + 4.0 * beat, 0.0, TAU, 28, EDGE, 6.0, true)
		draw_arc(area.get_center(), 14.0 + 4.0 * beat, 0.0, TAU, 28, _ghosts[tile], 4.0, true)

	# The castles.
	for side in _towers:
		var tower: Dictionary = _towers[side]
		var middle := tower_centre(side) + Vector2(sin(_time * 70.0) * 4.0 * float(tower["shake"]), 0)
		_draw_castle(middle, _colors[side], float(tower["shown"]) / float(tower["full"]))
		if float(tower["shown"]) > 0.0:
			_draw_cannon(side)

	# Bursts where blows land.
	for burst in _sparks:
		var part: float = clampf(float(burst["life"]) / float(burst["full"]), 0.0, 1.0)
		var reach := 6.0 + 16.0 * (1.0 - part)
		var middle: Vector2 = burst["at"]
		draw_circle(middle, 7.0 * part, Color(1, 1, 1, 0.8 * part))
		for ray in 8:
			var way := Vector2(1, 0).rotated(ray * TAU / 8.0 + 0.3)
			draw_line(middle + way * reach, middle + way * (reach + 7.0), Color(burst["color"], part), 3.0, true)

	# Cannonballs.
	for shot in _shots:
		var part: float = 1.0 - clampf(float(shot["life"]) / float(shot["full"]), 0.0, 1.0)
		var ball: Vector2 = (shot["from"] as Vector2).lerp(shot["to"], part)
		var behind: Vector2 = (shot["from"] as Vector2).lerp(shot["to"], maxf(0.0, part - 0.3))
		draw_line(behind, ball, Color(UI.GOLD, 0.8), 5.0, true)
		draw_circle(ball, 7.5, EDGE)
		draw_circle(ball, 5.5, UI.GOLD)

	# Routes, blows and shots.
	for entry in _lines:
		var part: float = clampf(float(entry["life"]) / float(entry["full"]), 0.0, 1.0)
		var points: PackedVector2Array = entry["points"]
		draw_polyline(points, Color(EDGE, part * 0.8), float(entry["width"]) + 3.0, true)
		draw_polyline(points, Color(entry["color"], part), float(entry["width"]), true)
		draw_circle(points[points.size() - 1], float(entry["width"]) + 2.0, Color(entry["color"], part))


func _draw_castle(middle: Vector2, color: Color, health_part: float) -> void:
	if health_part <= 0.0:
		_draw_ruin(middle, color)
		return
	# Shadow, stone keep with battlements, a roof in the department's colour, and a health bar.
	draw_set_transform(middle + Vector2(0, 24), 0.0, Vector2(1.0, 0.3))
	draw_circle(Vector2.ZERO, 40.0, Color(0, 0, 0, 0.28))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var keep := Rect2(middle + Vector2(-34, -20), Vector2(68, 44))
	draw_style_box(UI.box(EDGE, 8), keep.grow(3.0))
	draw_style_box(UI.box(UI.STONE, 6), keep)
	draw_rect(Rect2(keep.position + Vector2(0, 30), Vector2(keep.size.x, 14)), UI.STONE_DARK)
	for tooth in 4:
		var block := Rect2(keep.position + Vector2(2 + tooth * 17.3, -9), Vector2(12, 11))
		draw_rect(block.grow(2.5), EDGE)
		draw_rect(block, UI.STONE)
	# The banner where the department's emblem sits.
	var banner := Rect2(middle + Vector2(-17, -27), Vector2(34, 30))
	draw_style_box(UI.box(EDGE, 9), banner.grow(3.0))
	draw_style_box(UI.box(color, 7), banner)
	# Health.
	var bar := Rect2(middle + Vector2(-30, 11), Vector2(60, 12))
	draw_style_box(UI.box(EDGE, 6), bar.grow(2.5))
	draw_style_box(UI.box(Color("3a4658"), 5), bar)
	var part := clampf(health_part, 0.0, 1.0)
	if part > 0.0:
		draw_style_box(UI.box(color, 5), Rect2(bar.position, Vector2(maxf(8.0, bar.size.x * part), bar.size.y)))


## The cannon on a castle's wall, which turns to whatever it shot at last.
func _draw_cannon(side: String) -> void:
	var base := _cannon_base(side)
	var muzzle := _muzzle(side)
	draw_line(base, muzzle, EDGE, 15.0, true)
	draw_line(base, muzzle, UI.STONE_DARK.darkened(0.25), 10.0, true)
	draw_circle(base, 10.0, EDGE)
	draw_circle(base, 7.5, UI.STONE_DARK)


## A castle at zero: a broken keep, fallen stones and smoke.
func _draw_ruin(middle: Vector2, color: Color) -> void:
	draw_set_transform(middle + Vector2(0, 24), 0.0, Vector2(1.0, 0.3))
	draw_circle(Vector2.ZERO, 40.0, Color(0, 0, 0, 0.28))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var keep := PackedVector2Array([middle + Vector2(-34, 24), middle + Vector2(-34, -6), middle + Vector2(-20, -14),
		middle + Vector2(-8, -2), middle + Vector2(6, -16), middle + Vector2(18, -4), middle + Vector2(34, -10), middle + Vector2(34, 24)])
	draw_colored_polygon(keep, UI.STONE_DARK)
	keep.append(keep[0])
	draw_polyline(keep, EDGE, 3.0, true)
	draw_line(middle + Vector2(-12, 0), middle + Vector2(-4, 16), EDGE, 2.0)
	draw_line(middle + Vector2(10, -6), middle + Vector2(14, 12), EDGE, 2.0)
	for stone in [Vector2(-40, 20), Vector2(38, 18), Vector2(-26, 26), Vector2(28, 27)]:
		draw_circle(middle + stone, 5.0, EDGE)
		draw_circle(middle + stone, 3.6, UI.STONE)
	draw_style_box(UI.box(color.darkened(0.4), 4), Rect2(middle + Vector2(-12, 6), Vector2(24, 12)))
	for puff in 3:
		var rise := fmod(_time * 0.6 + puff / 3.0, 1.0)
		draw_circle(middle + Vector2(-8 + puff * 8 + sin(_time + puff) * 4.0, -16 - rise * 34.0), 6.0 + rise * 8.0, Color(0.55, 0.58, 0.62, 0.55 * (1.0 - rise)))
