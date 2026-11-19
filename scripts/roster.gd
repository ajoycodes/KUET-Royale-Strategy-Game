class_name RosterScreen
extends Control
## Every warrior of every department, with all their numbers and their special.
## It opens from the home screen and lies over it.

signal closed

const GRID_AT := Vector2(30, 112)
const GAP := 10.0

var departments: Array = []
var rules := {}
var first := 0

var _tabs: Array = []
var _cards: Array = []
var _lead: Label


func _ready() -> void:
	size = UI.SCREEN
	var back_sheet := ColorRect.new()
	back_sheet.color = UI.NIGHT
	back_sheet.size = UI.SCREEN
	back_sheet.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(back_sheet)

	var title := UI.title("Meet the warriors", 34, UI.GOLD, 8)
	title.position = Vector2(30, 12)
	add_child(title)
	_lead = UI.fitted("", Vector2(30, 62), 760, 14, UI.MUTED)
	add_child(_lead)
	add_child(UI.fitted("Towers hit back too: %d health, and %d damage to the closest enemy within %d tiles, every battle step." % [
		int(rules["tower_health"]), int(rules["tower_damage"]), int(rules["tower_range"])], Vector2(30, 84), 760, 13, UI.WHITE))

	var x := 824.0
	for place in departments.size():
		var made := UI.button(str(departments[place]["short"]), UI.PANEL_LIGHT, UI.WHITE, 16)
		made.position = Vector2(x, 22)
		made.size = Vector2(100, 44)
		made.pressed.connect(_show.bind(place))
		add_child(made)
		_tabs.append(made)
		x += 106.0

	var back := UI.button("Back", UI.GOLD, UI.INK, 16)
	back.position = Vector2(565, 660)
	back.size = Vector2(150, 44)
	back.pressed.connect(func() -> void: closed.emit())
	add_child(back)
	_show(first)


func _show(place: int) -> void:
	for card in _cards:
		card.queue_free()
	_cards.clear()
	var info: Dictionary = departments[place]
	var color := Color(str(info["color"]))
	_lead.text = "%s %s. %s" % [str(info["emoji"]), str(info["name"]), str(info["motto"])]
	for tab in _tabs.size():
		UI.choice_style(_tabs[tab], tab == place, color)
	var cards: Array = info["cards"]
	for number in cards.size():
		var card := WarriorCard.new()
		card.position = GRID_AT + Vector2((number % 4) * (WarriorCard.AREA.x + GAP), (number / 4) * (WarriorCard.AREA.y + GAP))
		add_child(card)
		card.setup(cards[number], color)
		_cards.append(card)
