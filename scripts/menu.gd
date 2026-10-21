class_name MenuScreen
extends Control
## The first screen: pick two departments, give each a brain, start.

signal start(config: Dictionary)

const HOW := [
	["A* search", "The route of a careful unit: the cheapest way across road, grass and mud.", "Lab 03"],
	["Best-first search", "The route of a reckless unit: straight at the goal, mud or not.", "Lab 03"],
	["Breadth-first search", "The route of a hover unit (every tile costs the same) and the area of a splash.", "Course"],
	["Uniform-cost search", "Which enemy is cheapest to reach, when there are several to choose from.", "Course"],
	["Fuzzy inference", "Which enemy to hit when several are in range. Three rules.", "Lab 05"],
	["Alpha-beta search", "One brain: looks at every way the leg can go, to the very end.", "Theory, on Lab 04"],
	["Monte Carlo Tree Search", "The other brain: plays random legs and backs what wins.", "Lab 08"],
	["CSP backtracking", "Builds each deck of four cards under the cost and role limits.", "Lab 06"],
]

var departments: Array = []
var brains := {}
var problem := ""
var open_how := false

var _pick := {"left": 0, "right": 1}
var _brain := {"left": "alphabeta", "right": "mcts"}
var _boxes := {}
var _how: Control


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN
	for place in departments.size():
		if str(departments[place]["id"]) == "cse":
			_pick["left"] = place
		elif str(departments[place]["id"]) == "me":
			_pick["right"] = place
	_pick["right"] = mini(int(_pick["right"]), departments.size() - 1)

	var title := UI.title("KUET Royale", 62, UI.GOLD, 14)
	title.position = Vector2(0, 44)
	title.size = Vector2(UI.SCREEN.x, 70)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	var under := UI.label("Department wars. Two brains, eight algorithms, one campus.", 18, UI.MUTED, 400)
	under.position = Vector2(0, 116)
	under.size = Vector2(UI.SCREEN.x, 26)
	under.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(under)

	if problem != "":
		var sheet := UI.panel(UI.PANEL, 16, UI.RED, 2)
		sheet.position = Vector2(240, 250)
		sheet.size = Vector2(800, 150)
		add_child(sheet)
		var words := UI.wrapped(problem, 740, 16, UI.WHITE)
		words.position = Vector2(270, 280)
		add_child(words)
		return

	for side in ["left", "right"]:
		_build_side(side)
	var versus := UI.label("against", 20, UI.MUTED, 400)
	versus.position = Vector2(590, 300)
	versus.size = Vector2(100, 30)
	versus.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(versus)

	var go := UI.button("Start the match", UI.GOLD, UI.INK, 20, 800)
	go.position = Vector2(480, 548)
	go.size = Vector2(320, 58)
	go.pressed.connect(func() -> void:
		start.emit({"left": departments[_pick["left"]]["id"], "right": departments[_pick["right"]]["id"],
			"left_brain": _brain["left"], "right_brain": _brain["right"]})
	)
	add_child(go)
	var how := UI.button("How the AI works", UI.PANEL_LIGHT, UI.WHITE, 15)
	how.position = Vector2(540, 618)
	how.size = Vector2(200, 40)
	how.pressed.connect(_show_how)
	add_child(how)
	var note := UI.label("Every match has two legs. The side that plays second can always answer, so each side starts once.", 13, UI.DIM, 400)
	note.position = Vector2(0, 676)
	note.size = Vector2(UI.SCREEN.x, 20)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(note)
	_refresh()
	if open_how:
		_show_how()


func _build_side(side: String) -> void:
	var x := 130.0 if side == "left" else 730.0
	var sheet := UI.panel(UI.PANEL, 20, UI.PANEL_LINE, 2)
	sheet.position = Vector2(x, 180)
	sheet.size = Vector2(420, 330)
	add_child(sheet)

	var seat := UI.label("Top of the arena. Plays first in leg 1." if side == "left" else "Bottom of the arena. Plays first in leg 2.", 13, UI.MUTED, 400)
	seat.position = Vector2(x + 24, 196)
	add_child(seat)

	var icon := UI.emoji("", 54)
	icon.position = Vector2(x + 24, 226)
	icon.size = Vector2(80, 80)
	add_child(icon)
	var short := UI.label("", 44, UI.WHITE, 800)
	short.position = Vector2(x + 116, 222)
	short.size = Vector2(190, 56)
	add_child(short)
	var full := UI.label("", 14, UI.MUTED, 400)
	full.position = Vector2(x + 118, 276)
	full.size = Vector2(280, 20)
	add_child(full)
	var motto := UI.label("", 15, UI.WHITE, 400)
	motto.position = Vector2(x + 24, 318)
	motto.size = Vector2(372, 22)
	add_child(motto)

	var change := UI.button("Change", UI.PANEL_LIGHT, UI.WHITE, 13)
	change.position = Vector2(x + 316, 236)
	change.size = Vector2(82, 34)
	change.pressed.connect(func() -> void:
		_pick[side] = (int(_pick[side]) + 1) % departments.size()
		_refresh()
	)
	change.visible = departments.size() > 1
	add_child(change)

	var who := UI.label("Who picks the cards?", 13, UI.MUTED, 400)
	who.position = Vector2(x + 24, 362)
	add_child(who)
	var buttons := {}
	var at := x + 24.0
	for brain in ["alphabeta", "mcts", "human"]:
		var made := UI.button(str(brains[brain]["name"]), UI.PANEL_LIGHT, UI.WHITE, 14)
		made.position = Vector2(at, 388)
		made.size = Vector2(120, 40)
		made.pressed.connect(func() -> void:
			_brain[side] = brain
			_refresh()
		)
		add_child(made)
		buttons[brain] = made
		at += 126.0
	var blurb := UI.wrapped("", 372, 13, UI.MUTED)
	blurb.position = Vector2(x + 24, 444)
	add_child(blurb)
	_boxes[side] = {"icon": icon, "short": short, "full": full, "motto": motto, "buttons": buttons, "blurb": blurb}


func _refresh() -> void:
	for side in ["left", "right"]:
		var info: Dictionary = departments[_pick[side]]
		var color := Color(str(info["color"]))
		var box: Dictionary = _boxes[side]
		box["icon"].text = str(info["emoji"])
		box["short"].text = str(info["short"])
		box["short"].add_theme_color_override("font_color", color)
		box["full"].text = str(info["name"])
		box["motto"].text = str(info["motto"])
		for brain in box["buttons"]:
			UI.choice_style(box["buttons"][brain], brain == _brain[side], color)
		box["blurb"].text = str(brains[_brain[side]]["blurb"])


func _show_how() -> void:
	if _how != null:
		return
	_how = Control.new()
	_how.size = UI.SCREEN
	var dim := ColorRect.new()
	dim.color = Color(0.03, 0.05, 0.07, 0.8)
	dim.size = UI.SCREEN
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_how.add_child(dim)
	var sheet := UI.panel(UI.PANEL, 20, UI.PANEL_LINE, 2)
	sheet.position = Vector2(110, 40)
	sheet.size = Vector2(1060, 640)
	sheet.mouse_filter = Control.MOUSE_FILTER_STOP
	_how.add_child(sheet)

	var title := UI.label("Eight algorithms, eight jobs", 28, UI.WHITE, 800)
	title.position = Vector2(40, 24)
	sheet.add_child(title)
	var lead := UI.wrapped("Every one was taught in the course and is used the way it was taught. The game has turns, nothing is hidden and nothing is random, so each algorithm fits exactly.", 980, 14, UI.MUTED)
	lead.position = Vector2(40, 66)
	sheet.add_child(lead)

	for place in HOW.size():
		var y := 122.0 + place * 46.0
		var row := UI.panel(UI.PANEL_LIGHT if place % 2 == 0 else Color(1, 1, 1, 0.0), 10)
		row.position = Vector2(30, y)
		row.size = Vector2(1000, 42)
		sheet.add_child(row)
		var algorithm := UI.label(str(HOW[place][0]), 15, UI.GOLD, 800)
		algorithm.position = Vector2(46, y + 10)
		sheet.add_child(algorithm)
		sheet.add_child(UI.fitted(str(HOW[place][1]), Vector2(262, y + 10), 610, 14))
		var taught := UI.label(str(HOW[place][2]), 13, UI.MUTED, 400)
		taught.position = Vector2(872, y + 12)
		taught.size = Vector2(150, 20)
		taught.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		sheet.add_child(taught)

	var rules := UI.wrapped("The whole fuzzy rule base:   IF distance is near OR health is low THEN priority is high.   IF distance is medium OR health is medium THEN priority is medium.   IF distance is far OR health is full THEN priority is low.", 980, 13, UI.MUTED)
	rules.position = Vector2(40, 502)
	sheet.add_child(rules)

	var back := UI.button("Back", UI.GOLD, UI.INK, 16)
	back.position = Vector2(455, 572)
	back.size = Vector2(150, 44)
	back.pressed.connect(func() -> void:
		_how.queue_free()
		_how = null
	)
	sheet.add_child(back)
	add_child(_how)
