class_name GalleryScreen
extends Control
## A sheet of every unit figure, a department to a row, to judge how they look.
##     godot --path . -- --gallery

const DEPARTMENTS := [
	["CSE", Color("58a6ee"), ["Compiler", "Kernel", "Algorithmist", "Optimizer", "Logic Bomber", "Debugger", "Stack Runner", "Cloud Drone"]],
	["EEE", Color("f2d24b"), ["Capacitor", "Transformer", "Signal Processor", "Circuit Engineer", "Oscillator", "Power Engineer", "Relay Runner", "Electron"]],
	["ME", Color("f28c38"), ["Heavy Machine", "Gearwheel Guard", "Robotic Arm", "Steel Rain Cannon", "Mech Warrior", "Gear Runner", "Mini-Bot", "Quadcopter"]],
	["CE", Color("b48cf0"), ["Excavator", "Road Roller", "Site Engineer", "Crane Operator", "Seismic Crew", "Surveyor", "Construction Crew", "Survey Drone"]],
]
const ROW := 170.0
const COLUMN := 148.0
const LEFT := 90.0
const TOP := 16.0
const FIGURE := 2.25

var _time := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN
	for row in DEPARTMENTS.size():
		var department: Array = DEPARTMENTS[row]
		var short := UI.title(str(department[0]), 24, department[1], 8)
		short.position = Vector2(12, TOP + row * ROW + 64)
		add_child(short)
		var cards: Array = department[2]
		for place in cards.size():
			var name_label := UI.fitted(str(cards[place]), Vector2(LEFT + place * COLUMN, TOP + row * ROW + 140), COLUMN - 6, 13,
				UI.WHITE, 800, HORIZONTAL_ALIGNMENT_CENTER)
			add_child(name_label)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, UI.SCREEN), UI.NIGHT)
	for row in DEPARTMENTS.size():
		var department: Array = DEPARTMENTS[row]
		var band := Rect2(Vector2(LEFT - 6, TOP + row * ROW + 4), Vector2(COLUMN * 8, ROW - 34))
		draw_style_box(UI.box(UI.GRASS, 14), band)
		draw_style_box(UI.box(UI.GRASS_ALT, 14), Rect2(band.position + Vector2(0, band.size.y - 34), Vector2(band.size.x, 34)))
		var cards: Array = department[2]
		for place in cards.size():
			var feet := Vector2(LEFT + place * COLUMN + COLUMN / 2.0 - 3, TOP + row * ROW + 124)
			Characters.draw(self, feet, FIGURE, str(cards[place]), department[1], _time + place * 0.4, false)
