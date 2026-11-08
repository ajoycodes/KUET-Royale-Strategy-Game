class_name SearchView
extends Control
## The picture of one decision: the brain's choices drawn as a tree.
##
## For alpha-beta, every first move is a branch with the final score it can
## reach and how many positions were looked at below it; branches the search
## cut short are greyed out, and the line of play it expects is shown underneath.
## For MCTS, every first move is a branch with how many random legs went down
## it and how many of those it won.

const AREA := Vector2(1040, 520)
const ROOT := Rect2(20, 0, 170, 64)
const BOX_X := 240.0
const BOX_W := 330.0
const BAR_X := 600.0
const BAR_W := 300.0
const TOP := 110.0
const ROWS_HEIGHT := 330.0

var _thinking := {}
var _rows: Array = []
var _row_height := 40.0
var _color := Color.WHITE
var _most := 1.0


func _init() -> void:
	size = AREA
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func setup(thinking: Dictionary, view: Dictionary, colors: Dictionary) -> void:
	_thinking = thinking
	var side := str(thinking["side"])
	var other := "right" if side == "left" else "left"
	_color = colors[side]
	_rows = thinking["choices"]
	_row_height = minf(42.0, ROWS_HEIGHT / maxf(1.0, float(_rows.size())))
	var short := str(view["sides"][side]["short"])
	var alpha := str(thinking["algorithm"]) == "alphabeta"

	var title := UI.title("How %s chose its card" % ("alpha-beta" if alpha else "MCTS"), 26, UI.GOLD, 8)
	title.position = Vector2(20, 0)
	add_child(title)
	var lead := ""
	var power := thinking.has("note")      # power mode looks at a short window, and says so itself
	if power:
		lead = str(thinking["note"]) + (" Grey branches were cut short: the search had already seen that they could not beat the best one." if alpha else "")
	elif alpha:
		lead = "It looked at %s positions; plain minimax would need up to %s. Grey branches were cut short: the search had already seen that they could not beat the best one." % [
			UI.number(float(thinking["searched"])), UI.number(float(thinking["plain_minimax"]))]
	else:
		lead = "It played %s random legs to the end. UCB1 = t / n + C × √(ln N / n), with C = %d, sends more legs down the branches that keep winning; it plays the branch that won most often." % [
			UI.number(float(thinking["repeats"])), int(thinking["exploration"])]
	var words := UI.wrapped(lead, AREA.x - 40, 14, UI.MUTED)
	words.position = Vector2(20, 40)
	add_child(words)

	var root_label := UI.title("%s to play" % short, 18, UI.WHITE, 6)
	root_label.position = Vector2(ROOT.position.x, TOP + ROWS_HEIGHT / 2.0 - 16)
	root_label.size = Vector2(ROOT.size.x, 32)
	root_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	root_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(root_label)

	var heading := UI.label("Positions looked at below it" if alpha else ("Random games sent down this branch" if power else "Random legs sent down this branch"), 13, UI.MUTED)
	heading.position = Vector2(BAR_X, TOP - 26)
	add_child(heading)
	add_child(UI.fitted(("Tower swing for %s" if power else "Final score for %s") % short if alpha else ("Games won" if power else "Legs won"), Vector2(BOX_X + 150, TOP - 26), 170, 13, UI.MUTED, 400,
		HORIZONTAL_ALIGNMENT_RIGHT))
	var row_text := 12
	var move_heading := UI.label("First card", 13, UI.MUTED)
	move_heading.position = Vector2(BOX_X + 12, TOP - 26)
	add_child(move_heading)

	_most = 1.0
	for row in _rows:
		_most = maxf(_most, float(row["positions"] if alpha else row["visits"]))
	for place in _rows.size():
		var row: Dictionary = _rows[place]
		var y := TOP + place * _row_height
		var faded: bool = alpha and not bool(row["exact"])
		var name_color := UI.WHITE if not faded else UI.DIM
		_row_label("%s, %s" % [str(row["card"]), UI.lane_words(str(row["where"]))], BOX_X + 12, y, 212, row_text, name_color, 800 if bool(row["chosen"]) else 400)
		var value := ""
		if alpha:
			var score := int(row["score"]) * (1 if side == "left" else -1)
			var text := ("+%d" % score) if score > 0 else str(score)
			value = text if bool(row["exact"]) else "at best " + text
		else:
			value = "won %d%%" % int(round(float(row["average"]) * 100.0))
		_row_label(value, BOX_X + 222, y, 98, row_text, name_color, 800, HORIZONTAL_ALIGNMENT_RIGHT)
		var count := UI.number(float(row["positions"] if alpha else row["visits"]))
		if faded:
			count += ", cut short"
		_row_label(count, BAR_X + BAR_W + 12, y, 118, row_text, name_color)

	if alpha and not power:
		var expects := UI.label("What alpha-beta expects to happen next:", 14, UI.MUTED)
		expects.position = Vector2(20, TOP + ROWS_HEIGHT + 20)
		add_child(expects)
		var x := 20.0
		var line: Array = thinking["line"]
		for place in line.size():
			var move: Dictionary = line[place]
			var who := str(view["sides"][str(move["side"])]["short"])
			var chip := UI.fitted("%s: %s, %s" % [who, str(move["card"]), UI.lane_words(str(move["where"]))],
				Vector2(x + 14, TOP + ROWS_HEIGHT + 46), 280, 14, UI.INK, 800)
			chip.size.y = 34.0
			chip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			chip.add_theme_color_override("font_color", UI.INK)
			var back := UI.panel(colors[str(move["side"])], 10)
			back.position = Vector2(x, TOP + ROWS_HEIGHT + 46)
			back.size = Vector2(300, 34)
			add_child(back)
			add_child(chip)
			x += 330.0
	queue_redraw()


## Words in a row, centred on the row's box from top to bottom.
func _row_label(text: String, x: float, y: float, width: float, text_size: int, color: Color, weight: int = 400,
		align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT) -> void:
	var made := UI.fitted(text, Vector2(x, y), width, text_size, color, weight, align)
	made.size.y = _row_height
	made.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(made)


func _draw() -> void:
	var alpha := str(_thinking.get("algorithm", "")) == "alphabeta"
	var root := Rect2(ROOT.position + Vector2(0, TOP + ROWS_HEIGHT / 2.0 - 32), ROOT.size)
	draw_style_box(UI.box(_color.darkened(0.3), 14, Color("0d2238"), 3), root)
	var out := Vector2(root.end.x, root.get_center().y)
	for place in _rows.size():
		var row: Dictionary = _rows[place]
		var y := TOP + place * _row_height
		var faded: bool = alpha and not bool(row["exact"])
		var chosen := bool(row["chosen"])
		var tall := minf(_row_height - 3.0, 30.0)
		var box := Rect2(Vector2(BOX_X, y + (_row_height - tall) / 2.0), Vector2(BOX_W, tall))
		var into := Vector2(BOX_X, box.get_center().y)
		var bend := Vector2((out.x + into.x) / 2.0, 0)
		var points := PackedVector2Array([out, Vector2(bend.x, out.y), Vector2(bend.x, into.y), into])
		var line_color := UI.GOLD if chosen else (Color(UI.DIM, 0.7) if faded else Color(UI.MUTED, 0.8))
		draw_polyline(points, line_color, 4.0 if chosen else 2.0, true)
		var fill := Color(UI.GOLD, 0.25) if chosen else (Color(1, 1, 1, 0.04) if faded else Color(1, 1, 1, 0.10))
		draw_style_box(UI.box(fill, 10, UI.GOLD if chosen else Color(1, 1, 1, 0.15), 2 if chosen else 1), box)
		var amount := float(row["positions"] if alpha else row["visits"])
		var thick := minf(14.0, _row_height - 7.0)
		var bar := Rect2(Vector2(BAR_X, y + (_row_height - thick) / 2.0), Vector2(BAR_W, thick))
		draw_style_box(UI.box(Color(0, 0, 0, 0.35), 7), bar)
		var part := clampf(amount / _most, 0.0, 1.0)
		if part > 0.0:
			var tint := UI.GOLD if chosen else (UI.DIM if faded else _color)
			draw_style_box(UI.box(tint, 7), Rect2(bar.position, Vector2(maxf(10.0, BAR_W * part), bar.size.y)))
