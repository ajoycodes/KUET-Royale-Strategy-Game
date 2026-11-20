class_name PromoFigures
extends Control
## Recording only: all 32 warriors, a department to a row, on a flat ground.

var ground := Color.BLACK
var _time := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, UI.SCREEN), ground)
	for row in GalleryScreen.DEPARTMENTS.size():
		var department: Array = GalleryScreen.DEPARTMENTS[row]
		var cards: Array = department[2]
		for place in cards.size():
			Characters.draw(self, Vector2(80 + place * 160, 158 + row * 180), 2.7, str(cards[place]), department[1], _time + place * 0.4, false)
