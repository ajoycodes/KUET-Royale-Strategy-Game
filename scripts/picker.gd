class_name PickerScreen
extends Control
## A person chooses their own four warriors, under the same rules the CSP solver
## keeps: four different cards, one of each role, and a total cost in the limits.

signal chosen(names: Array)
signal cancelled

const GRID_AT := Vector2(30, 112)
const GAP := 10.0
const METER := Rect2(120, 70, 440, 22)
const COST_MOST := 18

var info := {}
var rules := {}
var seat := ""

var _cards: Array = []
var _picks: Array = []
var _color := Color.WHITE
var _go: Button
var _ask_solver: Button
var _message: Label
var _total: Label
var _slots: Array = []


func _ready() -> void:
	size = UI.SCREEN
	_color = Color(str(info["color"]))
	var title := UI.title("Pick four %s warriors" % str(info["short"]), 30, UI.GOLD, 8)
	title.position = Vector2(30, 12)
	add_child(title)
	add_child(UI.fitted("For the %s side of the arena" % seat, Vector2(30 + 480, 24), 270, 15, UI.MUTED))

	_total = UI.label("", 16, UI.WHITE, 800)
	_total.position = Vector2(30, 66)
	_total.size = Vector2(90, 26)
	add_child(_total)
	add_child(UI.fitted("A deck costs %d or %d" % [int(rules["cost_least"]), int(rules["cost_limit"])], Vector2(572, 70), 170, 13, UI.MUTED))

	var x := 760.0
	for slot in rules["slots"]:
		if str(slot) == "Free":
			continue
		var chip := UI.panel(UI.PANEL_LIGHT, 10)
		chip.position = Vector2(x, 62)
		chip.size = Vector2(160, 38)
		add_child(chip)
		var word := UI.label("", 14, UI.WHITE, 800)
		word.size = chip.size
		word.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		word.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		chip.add_child(word)
		_slots.append({"role": str(slot), "chip": chip, "word": word})
		x += 166.0

	var cards: Array = info["cards"]
	for number in cards.size():
		var card := WarriorCard.new()
		card.position = GRID_AT + Vector2((number % 4) * (WarriorCard.AREA.x + GAP), (number / 4) * (WarriorCard.AREA.y + GAP))
		add_child(card)
		card.setup(cards[number], _color, true)
		card.clicked.connect(_on_card)
		_cards.append(card)

	var back := UI.button("Back", UI.PANEL_LIGHT, UI.WHITE, 15)
	back.position = Vector2(30, 656)
	back.size = Vector2(110, 48)
	back.pressed.connect(func() -> void: cancelled.emit())
	add_child(back)
	_message = UI.fitted("", Vector2(160, 668), 650, 15, UI.WHITE, 800)
	add_child(_message)
	_ask_solver = UI.button("Let CSP choose", UI.PANEL_LIGHT, UI.WHITE, 15)
	_ask_solver.position = Vector2(830, 656)
	_ask_solver.size = Vector2(190, 48)
	_ask_solver.pressed.connect(_on_solver)
	add_child(_ask_solver)
	_go = UI.button("Use these four", UI.GOLD, UI.INK, 16, 800)
	_go.position = Vector2(1030, 656)
	_go.size = Vector2(220, 48)
	_go.pressed.connect(func() -> void: chosen.emit(_picks.duplicate()))
	add_child(_go)
	_refresh()


func _on_card(card: Dictionary) -> void:
	var name := str(card["name"])
	if _picks.has(name):
		_picks.erase(name)
	elif _picks.size() >= 4:
		_message.text = "You have four already. Click one to put it back."
		return
	else:
		_picks.append(name)
	_refresh()


func _on_solver() -> void:
	_ask_solver.disabled = true
	var reply: Dictionary = await Bridge.ask(["deck", "--left", str(info["id"])])
	if not is_inside_tree():
		return
	_ask_solver.disabled = false
	if bool(reply.get("ok", false)):
		_picks = reply["deck"]
		_refresh()
		_message.text = "The CSP solver chose these. Change them if you like."
	else:
		_message.text = str(reply.get("error", "The AI did not answer."))


func _cost() -> int:
	var total := 0
	for card in info["cards"]:
		if _picks.has(str(card["name"])):
			total += int(card["cost"])
	return total


func _has_role(role: String) -> bool:
	for card in info["cards"]:
		if _picks.has(str(card["name"])) and str(card["role"]) == role:
			return true
	return false


## What still stands in the way, in one sentence, or "" when the four are legal.
func _problem() -> String:
	var missing := []
	for slot in _slots:
		if not _has_role(str(slot["role"])):
			missing.append(str(slot["role"]))
	if _picks.size() < 4:
		var left := 4 - _picks.size()
		var line := "Pick %d more." % left
		if not missing.is_empty():
			line += " You still need: %s." % ", ".join(PackedStringArray(missing))
		return line
	if not missing.is_empty():
		return "A deck needs one of each role. Swap one for a %s." % str(missing[0])
	var cost := _cost()
	if cost > int(rules["cost_limit"]):
		return "These cost %d. Swap one for a cheaper warrior." % cost
	if cost < int(rules["cost_least"]):
		return "These cost only %d. Swap one for a warrior that costs more." % cost
	return ""


func _refresh() -> void:
	for card in _cards:
		card.set_chosen(_picks.has(str(card.card["name"])))
	var cost := _cost()
	_total.text = "Cost %d" % cost
	var legal: bool = cost >= int(rules["cost_least"]) and cost <= int(rules["cost_limit"])
	_total.add_theme_color_override("font_color", UI.GREEN if legal else (UI.RED if cost > int(rules["cost_limit"]) else UI.WHITE))
	for slot in _slots:
		var has: bool = _has_role(str(slot["role"]))
		slot["word"].text = ("✓  " if has else "") + str(slot["role"])
		slot["word"].add_theme_color_override("font_color", UI.INK if has else UI.WHITE)
		slot["chip"].add_theme_stylebox_override("panel", UI.box(UI.GREEN if has else UI.PANEL_LIGHT, 10))
	var problem := _problem()
	_message.text = problem if problem != "" else "A legal deck. Ready when you are."
	_go.disabled = problem != ""
	queue_redraw()


func _draw() -> void:
	# The cost so far, against the band a legal deck must land in.
	var part := METER.size.x / float(COST_MOST)
	draw_style_box(UI.box(Color("0d2238"), 8), METER.grow(3.0))
	draw_style_box(UI.box(Color("3a4658"), 6), METER)
	var cost := _cost()
	if cost > 0:
		var over: bool = cost > int(rules["cost_limit"])
		draw_style_box(UI.box(UI.RED if over else UI.GOLD, 6), Rect2(METER.position, Vector2(part * mini(cost, COST_MOST), METER.size.y)))
	var from := float(int(rules["cost_least"]) - 1) * part
	var band := Rect2(METER.position + Vector2(from, -3), Vector2(part * 2.0, METER.size.y + 6))
	draw_style_box(UI.box(Color(0, 0, 0, 0), 4, UI.GREEN, 3), band)
