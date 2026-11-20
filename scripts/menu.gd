class_name MenuScreen
extends Control
## The first screen: pick two departments, give each a brain, start.

signal start(config: Dictionary)

const HOW := [
	["A* search", "The route of a careful unit: the cheapest way across road, grass and mud."],
	["Best-first search", "The route of a reckless unit: straight at the goal, mud or not."],
	["Breadth-first search", "The route of a hover unit (every tile costs the same) and the area of a splash."],
	["Uniform-cost search", "Which enemy is cheapest to reach, when there are several to choose from."],
	["Fuzzy inference", "Which enemy to hit when several are in range. Three rules."],
	["Alpha-beta search", "One brain: tries every card on the lane spots, to the very end of the leg."],
	["Monte Carlo Tree Search", "The other brain: plays random legs and backs what wins."],
	["CSP backtracking", "Builds a brain's deck of four cards under the cost and role limits."],
]
const NOTES := {
	"classic": "Every match has two legs, and each side starts once. A person picks their own four warriors.",
	"power": "One minute, no turns. All eight warriors come round. Drop them when you can pay. A fallen tower ends it at once.",
}

var departments: Array = []
var brains := {}
var power_blurbs := {}
var rules := {}
var problem := ""
var open_how := false

var _pick := {"left": 0, "right": 1}
var _brain := {"left": "alphabeta", "right": "mcts"}
var _boxes := {}
var _how: Control
var _mode := "classic"
var _mode_buttons := {}
var _note: Label


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN
	for place in departments.size():
		if str(departments[place]["id"]) == "cse":
			_pick["left"] = place
		elif str(departments[place]["id"]) == "me":
			_pick["right"] = place
	_pick["right"] = mini(int(_pick["right"]), departments.size() - 1)

	add_child(UI.logo("logo_menu.png", Vector2(UI.SCREEN.x / 2.0, 48), Vector2(598, 118), 62))
	var under := UI.label("Department wars. Two brains, eight algorithms, one campus.", 18, UI.MUTED, 400)
	under.position = Vector2(0, 88)
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
			"left_brain": _brain["left"], "right_brain": _brain["right"], "mode": _mode})
	)
	add_child(go)
	var how := UI.button("How the AI works", UI.PANEL_LIGHT, UI.WHITE, 15)
	how.position = Vector2(430, 618)
	how.size = Vector2(210, 40)
	how.pressed.connect(_show_how)
	add_child(how)
	var meet := UI.button("Meet the warriors", UI.PANEL_LIGHT, UI.WHITE, 15)
	meet.position = Vector2(650, 618)
	meet.size = Vector2(210, 40)
	meet.pressed.connect(_show_roster)
	add_child(meet)
	_note = UI.label("", 13, UI.DIM, 400)
	_note.position = Vector2(0, 676)
	_note.size = Vector2(UI.SCREEN.x, 20)
	_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_note)
	var at := 440.0
	for mode in [["classic", "Classic: two legs"], ["power", "Power: one minute"]]:
		var made := UI.button(str(mode[1]), UI.PANEL_LIGHT, UI.WHITE, 15, 800)
		made.position = Vector2(at, 124)
		made.size = Vector2(195, 42)
		made.pressed.connect(func() -> void:
			_mode = str(mode[0])
			_refresh()
		)
		add_child(made)
		_mode_buttons[mode[0]] = made
		at += 205.0
	_refresh()
	if open_how:
		_show_how()


func _build_side(side: String) -> void:
	var x := 130.0 if side == "left" else 730.0
	var sheet := UI.panel(UI.PANEL, 20, UI.PANEL_LINE, 2)
	sheet.position = Vector2(x, 180)
	sheet.size = Vector2(420, 330)
	add_child(sheet)

	var seat := UI.label("", 13, UI.MUTED, 400)
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
	for brain in ["alphabeta", "mcts", "easy", "human"]:
		var made := UI.small_button(str(brains[brain]["name"]), 90)
		made.position = Vector2(at, 388)
		made.custom_minimum_size = Vector2(90, 40)
		made.size = Vector2(90, 40)
		made.pressed.connect(func() -> void:
			_brain[side] = brain
			_refresh()
		)
		add_child(made)
		buttons[brain] = made
		at += 94.0
	var blurb := UI.wrapped("", 372, 13, UI.MUTED)
	blurb.position = Vector2(x + 24, 444)
	add_child(blurb)
	_boxes[side] = {"icon": icon, "short": short, "full": full, "motto": motto, "buttons": buttons, "blurb": blurb, "seat": seat}


func _refresh() -> void:
	for mode in _mode_buttons:
		UI.choice_style(_mode_buttons[mode], mode == _mode, UI.GOLD)
	_note.text = str(NOTES[_mode])
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
		box["blurb"].text = str(power_blurbs[_brain[side]]) if _mode == "power" else str(brains[_brain[side]]["blurb"])
		var where := "Top of the arena." if side == "left" else "Bottom of the arena."
		if _mode == "classic":
			where += " Plays first in leg 1." if side == "left" else " Plays first in leg 2."
		box["seat"].text = where


func _show_roster() -> void:
	show_roster("")


## Open the warriors screen, at the named department or at the one picked for the top side.
func show_roster(department: String) -> void:
	var roster := RosterScreen.new()
	roster.departments = departments
	roster.rules = rules
	roster.first = int(_pick["left"])
	for place in departments.size():
		if str(departments[place]["id"]) == department:
			roster.first = place
	roster.closed.connect(roster.queue_free)
	add_child(roster)


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
	var lead := UI.wrapped("Every one was taught in the course and is used the way it was taught. The classic game has turns, nothing is hidden and nothing is random, so each algorithm fits exactly.", 980, 14, UI.MUTED)
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
		sheet.add_child(UI.fitted(str(HOW[place][1]), Vector2(262, y + 10), 760, 14))

	var fuzzy_rules := UI.wrapped("The whole fuzzy rule base:   IF distance is near OR health is low THEN priority is high.   IF distance is medium OR health is medium THEN priority is medium.   IF distance is far OR health is full THEN priority is low.", 980, 13, UI.MUTED)
	fuzzy_rules.position = Vector2(40, 496)
	sheet.add_child(fuzzy_rules)
	var power_words := UI.wrapped("In Power mode there are no turns, so the two brains look only at the next 18 seconds and score how much the towers changed by then.", 980, 13, UI.MUTED)
	power_words.position = Vector2(40, 540)
	sheet.add_child(power_words)

	var back := UI.button("Back", UI.GOLD, UI.INK, 16)
	back.position = Vector2(455, 580)
	back.size = Vector2(150, 44)
	back.pressed.connect(func() -> void:
		_how.queue_free()
		_how = null
	)
	sheet.add_child(back)
	add_child(_how)
