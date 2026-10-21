class_name CardView
extends Control
## One card of a deck: icon, name, cost, the four numbers, and one plain
## sentence saying what the unit is good for.

signal picked(index: int)

const AREA := Vector2(208, 112)

var index := -1
var used := false

var _color := Color.WHITE
var _search_color := Color.WHITE
var _pickable := false
var _selected := false
var _hinted := false
var _hover := false
var _time := 0.0
var _played: Label
var _card := ""


func _init() -> void:
	size = AREA
	custom_minimum_size = AREA
	pivot_offset = AREA / 2.0
	mouse_filter = Control.MOUSE_FILTER_STOP


func setup(card: Dictionary, side_color: Color) -> void:
	index = int(card["index"])
	_color = side_color
	var walks := str(card["walks"])
	var search: String = UI.WALK_SEARCH[walks]
	_search_color = UI.SEARCH_COLOR[search]

	_card = str(card["name"])
	var icon := UI.emoji(str(card["icon"]), 28)
	icon.position = Vector2(12, 6)
	icon.size = Vector2(42, 40)
	icon.visible = not Characters.has(_card)
	add_child(icon)

	var title_size := 15
	while title_size > 11 and UI.font(800).get_string_size(str(card["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, title_size).x > 112.0:
		title_size -= 1
	add_child(UI.fitted(str(card["name"]), Vector2(60, 5 + (15 - title_size) / 2.0), 114, title_size, UI.INK, 800))
	var kind := "%s. %s: %s" % [str(card["role"]), str(UI.WALK_NAME[walks]), str(UI.SEARCH_NAME[search]).replace(" search", "")]
	add_child(UI.fitted(kind, Vector2(72, 26), 130, 11, UI.INK_SOFT))

	var cost := UI.label(str(int(card["cost"])), 14, UI.INK, 800)
	cost.position = Vector2(AREA.x - 32, 5)
	cost.size = Vector2(24, 24)
	cost.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cost.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(cost)

	var numbers := [["❤️", card["health"]], ["⚔️", card["damage"]], ["🎯", card["range"]], ["👟", card["speed"]]]
	for place in numbers.size():
		var x := 12.0 + place * 48.0
		var sign := UI.emoji(str(numbers[place][0]), 12)
		sign.position = Vector2(x, 47)
		sign.size = Vector2(20, 20)
		add_child(sign)
		var value := UI.label(str(int(numbers[place][1])), 15, UI.INK, 800)
		value.position = Vector2(x + 21, 46)
		value.size = Vector2(24, 20)
		add_child(value)

	var about := UI.wrapped(str(card["about"]), AREA.x - 22, 11, UI.INK_SOFT)
	about.position = Vector2(12, 70)
	about.add_theme_constant_override("line_spacing", -2)
	add_child(about)

	_played = UI.title("Played", 20, UI.WHITE, 8)
	_played.size = AREA
	_played.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_played.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_played.visible = false
	_played.rotation_degrees = -8
	_played.pivot_offset = AREA / 2.0
	add_child(_played)
	set_used(bool(card["used"]))


func set_used(now: bool) -> void:
	used = now
	_played.visible = now
	if now:
		_selected = false
		_pickable = false
	queue_redraw()


func set_pickable(now: bool) -> void:
	_pickable = now and not used
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if _pickable else Control.CURSOR_ARROW
	if not _pickable:
		_hover = false
	queue_redraw()


func set_selected(now: bool) -> void:
	_selected = now
	create_tween().tween_property(self, "scale", Vector2(1.05, 1.05) if now else Vector2.ONE, 0.1)
	queue_redraw()


func set_hinted(now: bool) -> void:
	_hinted = now
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_ENTER and _pickable:
		_hover = true
		Sfx.play("hover")
		queue_redraw()
	elif what == NOTIFICATION_MOUSE_EXIT:
		_hover = false
		queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if _pickable and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		Sfx.play("tap")
		picked.emit(index)


func _process(delta: float) -> void:
	if _pickable or _hinted:
		_time += delta
		queue_redraw()


func _draw() -> void:
	var area := Rect2(Vector2.ZERO, AREA)
	var edge := Color("0d2238")
	var width := 3
	if _selected:
		edge = UI.WHITE
		width = 5
	elif _hover:
		edge = UI.WHITE
		width = 4
	elif _pickable:
		edge = Color(UI.WHITE, 0.6 + 0.4 * sin(_time * 4.0))
		width = 4
	draw_style_box(UI.box(Color(0, 0, 0, 0.25), 12), Rect2(Vector2(2, 4), AREA))
	draw_style_box(UI.box(UI.PAPER if not used else UI.PAPER_DIM, 12, edge, width), area)
	# A band in the department's colour down the left edge, and the cost in a gold coin.
	draw_style_box(UI.box(_color, 6), Rect2(Vector2(5, 6), Vector2(6, AREA.y - 12)))
	draw_circle(Vector2(AREA.x - 20, 17), 13.5, Color("0d2238"))
	draw_circle(Vector2(AREA.x - 20, 17), 11.5, UI.GOLD)
	# The colour of the search this unit walks by.
	draw_circle(Vector2(65, 35), 4.5, Color("0d2238"))
	draw_circle(Vector2(65, 35), 3.2, _search_color)
	draw_line(Vector2(14, 68), Vector2(AREA.x - 12, 68), UI.PAPER_DIM, 1.5)
	if Characters.has(_card):
		Characters.draw(self, Vector2(34, 45), 0.82, _card, _color, 0.0, false)
	if used:
		draw_style_box(UI.box(Color(0.05, 0.13, 0.22, 0.62), 12), area)
	if _hinted:
		draw_style_box(UI.box(Color(0, 0, 0, 0), 15, Color(UI.GOLD, 0.6 + 0.4 * sin(_time * 5.0)), 5), area.grow(5.0))
