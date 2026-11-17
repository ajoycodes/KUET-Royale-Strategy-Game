class_name ThinkingPanel
extends Control
## One side of the match, beside the arena: who it is, its score, its tower,
## its four cards on a wooden tray, and what its brain was thinking when it
## chose its last card. The cards themselves are placed by the match screen.

signal look(thinking: Dictionary)

const AREA := Vector2(448, 624)
const ROWS := 3
const TRAY := Rect2(8, 122, 432, 244)
const COIN_ROW := 38.0
const COIN_BAR := Rect2(50, 376, 250, 16)

var side := "left"
var coins_mode := false      # power mode: a coin bar under the cards, and everything below it moved down
var damage_note := "over both legs"

var _color := Color.WHITE
var _active := false
var _thinking := false
var _time := 0.0
var _tower := 20
var _tower_full := 20
var _tower_shown := 20.0

var _tower_text: Label
var _damage: Label
var _heading: Label
var _note: Label
var _busy: Label
var _rows: Array = []        # each: {"mark", "name", "lane", "value", "back"}
var _look: Button
var _last := {}
var _shift := 0.0
var _coins_most := 10
var _coins_shown := 0.0
var _coin_text: Label
var _next_text: Label


func _init() -> void:
	size = AREA
	custom_minimum_size = AREA
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Where card number `place` of this side's hand goes, inside the panel.
func card_spot(place: int) -> Vector2:
	return TRAY.position + Vector2(6 + (place % 2) * 212, 8 + (place / 2) * 118)


func setup(info: Dictionary, side_name: String, side_color: Color) -> void:
	side = side_name
	_color = side_color
	_shift = COIN_ROW if coins_mode else 0.0
	_tower_full = int(info["tower"])
	_tower = _tower_full
	_tower_shown = float(_tower)

	var icon := UI.emoji(str(info["emoji"]), 46)
	icon.position = Vector2(12, 10)
	icon.size = Vector2(66, 66)
	add_child(icon)
	var short := UI.title(str(info["short"]), 38, UI.WHITE, 10)
	short.position = Vector2(86, 2)
	short.size = Vector2(190, 48)
	add_child(short)
	var brain := "played by you" if str(info["brain"]) == "human" else "thinks with " + str(info["brain_name"])
	add_child(UI.fitted("%s side, %s" % [str(UI.SEAT_WORD[side_name]), brain], Vector2(88, 48), 250, 13, UI.WHITE, 800))
	add_child(UI.fitted(str(info["name"]), Vector2(88, 66), 250, 12, UI.WHITE))

	_damage = UI.title("0", 44, UI.GOLD, 10)
	_damage.position = Vector2(340, 0)
	_damage.size = Vector2(94, 54)
	_damage.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_damage.pivot_offset = Vector2(70, 27)
	add_child(_damage)
	add_child(UI.fitted("damage done", Vector2(330, 52), 104, 12, UI.WHITE, 800, HORIZONTAL_ALIGNMENT_RIGHT))
	add_child(UI.fitted(damage_note, Vector2(330, 67), 104, 11, UI.WHITE, 400, HORIZONTAL_ALIGNMENT_RIGHT))

	add_child(UI.fitted("Tower", Vector2(14, 93), 50, 13, UI.MUTED))
	_tower_text = UI.fitted("", Vector2(360, 93), 74, 13, UI.WHITE, 800, HORIZONTAL_ALIGNMENT_RIGHT)
	add_child(_tower_text)

	if coins_mode:
		_coin_text = UI.label("", 15, UI.INK, 800)
		_coin_text.position = Vector2(16, 372)
		_coin_text.size = Vector2(28, 24)
		_coin_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_coin_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		add_child(_coin_text)
		_next_text = UI.fitted("", Vector2(308, 374), 130, 12, UI.WHITE, 400, HORIZONTAL_ALIGNMENT_RIGHT)
		add_child(_next_text)

	_heading = UI.fitted("", Vector2(16, 374 + _shift), 290, 13, UI.MUTED)
	add_child(_heading)
	_look = UI.small_button("Show the search", 130, UI.GOLD, UI.INK)
	_look.position = Vector2(AREA.x - 146, 366 + _shift)
	_look.visible = false
	_look.mouse_filter = Control.MOUSE_FILTER_STOP
	_look.pressed.connect(func() -> void: look.emit(_last))
	add_child(_look)

	for place in ROWS:
		var y := 398.0 + _shift + place * 44.0
		var back := UI.panel(Color(1, 1, 1, 0.0), 10)
		back.position = Vector2(10, y)
		back.size = Vector2(AREA.x - 20, 40)
		add_child(back)
		var mark := UI.label("", 14, UI.GOLD, 800)
		mark.position = Vector2(18, y + 9)
		mark.size = Vector2(16, 20)
		add_child(mark)
		var title := UI.fitted("", Vector2(40, y + 2), 230, 14)
		add_child(title)
		var lane := UI.fitted("", Vector2(40, y + 21), 230, 11, UI.MUTED)
		add_child(lane)
		var value := UI.fitted("", Vector2(270, y + 9), 160, 14, UI.WHITE, 800, HORIZONTAL_ALIGNMENT_RIGHT)
		add_child(value)
		_rows.append({"mark": mark, "name": title, "lane": lane, "value": value, "back": back})

	_note = UI.wrapped(str(info["brain_blurb"]), AREA.x - 32, 12, UI.MUTED, 400)
	_note.position = Vector2(16, 536 + _shift)
	add_child(_note)

	_busy = UI.title("Thinking", 18, UI.GOLD, 6)
	_busy.position = Vector2(16, 372 + _shift)
	_busy.size = Vector2(AREA.x - 32, 24)
	_busy.visible = false
	add_child(_busy)

	set_tower(_tower)
	show_idle(str(info["brain_blurb"]))


func set_tower(health: int) -> void:
	_tower = health
	_tower_text.text = "%d of %d" % [health, _tower_full]
	var tween := create_tween()
	tween.tween_method(func(value: float) -> void:
		_tower_shown = value
		queue_redraw()
	, _tower_shown, float(health), 0.3)


## Power mode: how many coins this side has (a part of a coin shows the next one on its way) and the next card.
func set_coins(value: float, most: int, upcoming: String) -> void:
	_coins_most = most
	_coin_text.text = str(int(value))
	_next_text.text = "Next: " + upcoming
	var tween := create_tween()
	tween.tween_method(func(now: float) -> void:
		_coins_shown = now
		queue_redraw()
	, _coins_shown, value, 0.25)


func set_damage(total: int) -> void:
	if _damage.text != str(total):
		_damage.text = str(total)
		UI.bounce(_damage, 1.4, 0.35)


func set_active(now: bool) -> void:
	_active = now
	queue_redraw()


func set_thinking(now: bool) -> void:
	_thinking = now
	_busy.visible = now
	_heading.visible = not now
	if now:
		_look.visible = false
	if now:
		_clear_rows()
		_note.text = ""


func _clear_rows() -> void:
	for row in _rows:
		_clear_row(row)


func _clear_row(row: Dictionary) -> void:
	for part in ["mark", "name", "lane", "value"]:
		row[part].text = ""
	row["back"].add_theme_stylebox_override("panel", UI.box(Color(1, 1, 1, 0.0), 10))


func show_idle(words: String) -> void:
	_heading.text = "How it thinks"
	_look.visible = false
	_clear_rows()
	_note.position.y = 402 + _shift
	_note.text = words


## Show what the brain looked at when it chose its card.
func show_thinking(thinking: Dictionary) -> void:
	set_thinking(false)
	var algorithm := str(thinking["algorithm"])
	var choices: Array = thinking["choices"]
	if algorithm == "human":
		show_idle("You chose this card yourself.")
		return
	_last = thinking
	_look.visible = true
	_look.text = "Show the search" if algorithm == "alphabeta" else "Show the tree"
	_note.position.y = 536 + _shift
	if thinking.has("note"):
		_heading.text = str(thinking["heading"])
		_note.text = str(thinking["note"])
	elif algorithm == "alphabeta":
		_heading.text = "Alpha-beta: final score each card can reach"
		var skipped := int(thinking["pruned"])
		_note.text = "Looked at %s positions and skipped %s %s. Plain minimax would need up to %s." % [
			UI.number(float(thinking["searched"])), UI.number(float(skipped)), "move" if skipped == 1 else "moves",
			UI.number(float(thinking["plain_minimax"]))]
	else:
		_heading.text = "MCTS: random legs each card won"
		_note.text = "Played %s random legs to the end and backed the card that won most often. C = %d." % [
			UI.number(float(thinking["repeats"])), int(thinking["exploration"])]
	for place in ROWS:
		var row: Dictionary = _rows[place]
		if place >= choices.size():
			_clear_row(row)
			continue
		var choice: Dictionary = choices[place]
		var chosen := bool(choice["chosen"])
		row["mark"].text = "▶" if chosen else ""
		row["name"].text = str(choice["card"])
		row["name"].add_theme_font_override("font", UI.font(800 if chosen else 400))
		row["lane"].text = UI.lane_words(str(choice["where"]))
		row["back"].add_theme_stylebox_override("panel", UI.box(Color(1, 1, 1, 0.20) if chosen else Color(1, 1, 1, 0.07), 10))
		if algorithm == "alphabeta":
			# Scores are shown from this side's own point of view: above 0 is good for it.
			var score := int(choice["score"]) * (1 if side == "left" else -1)
			var text := ("+%d" % score) if score > 0 else str(score)
			row["value"].text = text if bool(choice["exact"]) else "at best " + text
		else:
			row["value"].text = "%d%% of %d" % [int(round(float(choice["average"]) * 100.0)), int(choice["visits"])]
		row["value"].add_theme_color_override("font_color", UI.WHITE if chosen else UI.MUTED)


func _process(delta: float) -> void:
	if _thinking or _active:
		_time += delta
		if _thinking:
			_busy.text = "Thinking" + ".".repeat(1 + int(_time * 3.0) % 3)
		queue_redraw()


func _draw() -> void:
	var area := Rect2(Vector2.ZERO, AREA)
	var edge := Color("0d2238")
	var width := 4
	if _active:
		edge = Color(UI.GOLD, 0.75 + 0.25 * sin(_time * 4.0))
		width = 5
	draw_style_box(UI.box(Color(0, 0, 0, 0.25), 20), Rect2(Vector2(3, 5), AREA))
	draw_style_box(UI.box(UI.PANEL, 20, edge, width), area)
	# The header, in the department's colour.
	draw_style_box(UI.box(_color.darkened(0.30), 16), Rect2(Vector2(6, 6), Vector2(AREA.x - 12, 80)))
	draw_style_box(UI.box(Color(1, 1, 1, 0.10), 16), Rect2(Vector2(6, 6), Vector2(AREA.x - 12, 38)))
	# Tower health.
	var bar := Rect2(Vector2(66, 96), Vector2(286, 12))
	draw_style_box(UI.box(Color("0d2238"), 6), bar.grow(2.5))
	draw_style_box(UI.box(Color("3a4658"), 5), bar)
	var part := clampf(_tower_shown / float(_tower_full), 0.0, 1.0)
	if part > 0.0:
		draw_style_box(UI.box(_color, 5), Rect2(bar.position, Vector2(maxf(8.0, bar.size.x * part), bar.size.y)))
	# The wooden tray the cards lie on.
	draw_style_box(UI.box(UI.WOOD_DARK, 16), TRAY.grow(3.0))
	draw_style_box(UI.box(UI.WOOD, 14), TRAY)
	for plank in range(1, 4):
		var y := TRAY.position.y + plank * TRAY.size.y / 4.0
		draw_line(Vector2(TRAY.position.x + 8, y), Vector2(TRAY.end.x - 8, y), Color(UI.WOOD_DARK, 0.45), 2.0)
	if coins_mode:
		_draw_coins()


func _draw_coins() -> void:
	draw_circle(Vector2(30, 384), 14.0, Color("0d2238"))
	draw_circle(Vector2(30, 384), 12.0, UI.GOLD)
	draw_style_box(UI.box(Color("0d2238"), 8), COIN_BAR.grow(2.5))
	var width := COIN_BAR.size.x / float(_coins_most)
	for place in _coins_most:
		var cell := Rect2(COIN_BAR.position + Vector2(place * width + 1.0, 1.0), Vector2(width - 2.0, COIN_BAR.size.y - 2.0))
		draw_style_box(UI.box(Color("3a4658"), 3), cell)
		var part := clampf(_coins_shown - place, 0.0, 1.0)
		if part > 0.0:
			draw_style_box(UI.box(UI.GOLD if part >= 1.0 else Color(UI.GOLD, 0.55), 3), Rect2(cell.position, Vector2(cell.size.x * part, cell.size.y)))
