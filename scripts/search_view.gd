class_name SearchView
extends Control
## The picture of one decision: the brain's choices drawn as a tree.
##
## For alpha-beta, every first move is a branch with the final score it can
## force and how many positions were looked at below it; branches the search
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
	if alpha:
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
	root_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(root_label)

	var heading := UI.label("Positions looked at below it" if alpha else "Random legs sent down this branch", 13, UI.MUTED)
	heading.position = Vector2(BAR_X, TOP - 26)
	add_child(heading)
	add_child(UI.fitted("Final score for %s" % short if alpha else "Legs won", Vector2(BOX_X + 150, TOP - 26), 170, 13, UI.MUTED, 400,
		HORIZONTAL_ALIGNMENT_RIGHT))
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
		add_child(UI.fitted("%s, %s lane" % [str(row["card"]), str(UI.LANE_WORD[str(row["lane"])])],
			Vector2(BOX_X + 12, y + (_row_height - 22) / 2.0), 200, 14, name_color, 800 if bool(row["chosen"]) else 400))
		var value := ""
		if alpha:
			var score := int(row["score"]) * (1 if side == "left" else -1)
			var text := ("+%d" % score) if score > 0 else str(score)
			value = text if bool(row["exact"]) else "at best " + text
		else:
			value = "won %d%%" % int(round(float(row["average"]) * 100.0))
		add_child(UI.fitted(value, Vector2(BOX_X + 212, y + (_row_height - 22) / 2.0), 108, 14, name_color, 800, HORIZONTAL_ALIGNMENT_RIGHT))
		var count := UI.number(float(row["positions"] if alpha else row["visits"]))
		if faded:
			count += ", cut short"
		add_child(UI.fitted(count, Vector2(BAR_X + BAR_W + 12, y + (_row_height - 22) / 2.0), 118, 13, name_color))

	if alpha and thinking.has("line"):
		var expects := UI.label("What alpha-beta expects to happen next:", 14, UI.MUTED)
		expects.position = Vector2(20, TOP + ROWS_HEIGHT + 20)
		add_child(expects)
		var x := 20.0
		var line: Array = thinking["line"]
		for place in line.size():
			var move: Dictionary = line[place]
			var who := str(view["sides"][str(move["side"])]["short"])
			var chip := UI.fitted("%s: %s, %s" % [who, str(move["card"]), str(UI.LANE_WORD[str(move["lane"])])],
				Vector2(x + 14, TOP + ROWS_HEIGHT + 52), 280, 14, UI.INK, 800)
			chip.add_theme_color_override("font_color", UI.INK)
			var back := UI.panel(colors[str(move["side"])], 10)
			back.position = Vector2(x, TOP + ROWS_HEIGHT + 46)
			back.size = Vector2(300, 34)
			add_child(back)
			add_child(chip)
			x += 330.0
	queue_redraw()


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
		var box := Rect2(Vector2(BOX_X, y + 3), Vector2(BOX_W, _row_height - 6))
		var into := Vector2(BOX_X, box.get_center().y)
		var bend := Vector2((out.x + into.x) / 2.0, 0)
		var points := PackedVector2Array([out, Vector2(bend.x, out.y), Vector2(bend.x, into.y), into])
		var line_color := UI.GOLD if chosen else (Color(UI.DIM, 0.7) if faded else Color(UI.MUTED, 0.8))
		draw_polyline(points, line_color, 4.0 if chosen else 2.0, true)
		var fill := Color(UI.GOLD, 0.25) if chosen else (Color(1, 1, 1, 0.04) if faded else Color(1, 1, 1, 0.10))
		draw_style_box(UI.box(fill, 10, UI.GOLD if chosen else Color(1, 1, 1, 0.15), 2 if chosen else 1), box)
		var amount := float(row["positions"] if alpha else row["visits"])
		var bar := Rect2(Vector2(BAR_X, y + _row_height / 2.0 - 7), Vector2(BAR_W, 14))
		draw_style_box(UI.box(Color(0, 0, 0, 0.35), 7), bar)
		var part := clampf(amount / _most, 0.0, 1.0)
		if part > 0.0:
			var tint := UI.GOLD if chosen else (UI.DIM if faded else _color)
			draw_style_box(UI.box(tint, 7), Rect2(bar.position, Vector2(maxf(10.0, BAR_W * part), bar.size.y)))
