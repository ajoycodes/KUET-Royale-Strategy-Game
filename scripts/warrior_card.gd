class_name WarriorCard
extends Control
## One warrior with everything about it, for the warriors screen and the troop picker.

signal clicked(card: Dictionary)

const AREA := Vector2(296, 250)
const NUMBERS := [["health", "Health"], ["damage", "Damage"], ["range", "Range"], ["speed", "Speed"]]

var card := {}
var chosen := false

var _color := Color.WHITE
var _search_color := Color.WHITE
var _pickable := false
var _hover := false
var _time := 0.0


func _init() -> void:
	size = AREA
	custom_minimum_size = AREA
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func setup(info: Dictionary, side_color: Color, pickable: bool = false) -> void:
	card = info
	_color = side_color
	_pickable = pickable
	if pickable:
		mouse_filter = Control.MOUSE_FILTER_STOP
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var walks := str(info["walks"])
	var search: String = UI.WALK_SEARCH[walks]
	_search_color = UI.SEARCH_COLOR[search]

	var title_size := 18
	while title_size > 13 and UI.font(800).get_string_size(str(info["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, title_size).x > 146.0:
		title_size -= 1
	add_child(UI.fitted(str(info["name"]), Vector2(98, 10), 150, title_size, UI.INK, 800))
	add_child(UI.fitted(str(info["role"]), Vector2(98, 36), 150, 13, UI.INK_SOFT, 800))
	var walk_label := UI.fitted("%s: %s" % [str(UI.WALK_NAME[walks]), str(UI.SEARCH_NAME[search])], Vector2(112, 56), 178, 11, UI.INK_SOFT)
	walk_label.size.y = 18.0                 # centred on the search colour's dot
	walk_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(walk_label)

	var price := UI.label(str(int(info["cost"])), 19, UI.INK, 800)
	price.position = Vector2(AREA.x - 46, 8)
	price.size = Vector2(36, 36)
	price.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	price.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(price)

	for place in NUMBERS.size():
		var x := 98.0 + place * 47.5
		var value := UI.label(str(int(info[NUMBERS[place][0]])), 18, UI.INK, 800)
		value.position = Vector2(x, 80)
		value.size = Vector2(48, 24)
		value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(value)
		var word := UI.label(str(NUMBERS[place][1]), 10, UI.INK_SOFT)
		word.position = Vector2(x, 104)
		word.size = Vector2(48, 16)
		word.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(word)

	var special: Dictionary = info["special"]
	add_child(UI.fitted(str(special["name"]), Vector2(16, 128), 264, 15, UI.INK, 800))
	var rule := UI.wrapped(str(special["words"]), 266, 12, UI.INK)
	rule.position = Vector2(16, 150)
	rule.add_theme_constant_override("line_spacing", -1)
	add_child(rule)
	var about := UI.wrapped(str(info["about"]), 266, 11, UI.INK_SOFT)
	about.position = Vector2(16, 200)
	about.add_theme_constant_override("line_spacing", -2)
	add_child(about)


func set_chosen(now: bool) -> void:
	chosen = now
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
		clicked.emit(card)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _draw() -> void:
	var area := Rect2(Vector2.ZERO, AREA)
	var edge := Color("0d2238")
	var width := 3
	if chosen:
		edge = UI.GOLD
		width = 6
	elif _hover:
		edge = UI.WHITE
		width = 4
	draw_style_box(UI.box(Color(0, 0, 0, 0.25), 14), Rect2(Vector2(2, 4), AREA))
	draw_style_box(UI.box(UI.PAPER, 14, edge, width), area)
	draw_style_box(UI.box(_color, 6), Rect2(Vector2(6, 8), Vector2(7, 106)))
	# The cost in a gold coin.
	draw_circle(Vector2(AREA.x - 28, 26), 18.0, Color("0d2238"))
	draw_circle(Vector2(AREA.x - 28, 26), 15.5, UI.GOLD)
	# The colour of the search this warrior walks by.
	draw_circle(Vector2(104, 65), 4.5, Color("0d2238"))
	draw_circle(Vector2(104, 65), 3.2, _search_color)
	# Four numbers on a darker strip, and a line above the special.
	draw_style_box(UI.box(UI.PAPER_DIM, 8), Rect2(Vector2(98, 78), Vector2(190, 44)))
	draw_line(Vector2(16, 126), Vector2(AREA.x - 14, 126), UI.PAPER_DIM, 1.5)
	if Characters.has(str(card.get("name", ""))):
		Characters.draw(self, Vector2(54, 100), 1.45, str(card["name"]), _color, _time, false)
	if chosen:
		# The tick sits on the corner, where it covers no words.
		draw_circle(Vector2(26, 26), 15.0, Color("0d2238"))
		draw_circle(Vector2(26, 26), 12.5, UI.GOLD)
		draw_polyline(PackedVector2Array([Vector2(20, 26), Vector2(24, 31), Vector2(32, 21)]), UI.INK, 3.0, true)
