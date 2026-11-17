class_name UnitPiece
extends Control
## One unit on the arena. If its card has a figure in characters.gd, the
## figure is drawn; otherwise a coloured disc with the card's icon. Under it
## sit a health bar and a small dot in the colour of the path search it walks by.

const AREA := Vector2(52, 76)
const ANCHOR := Vector2(26, 50)          # the point of the piece that sits on the middle of its tile
const FEET := Vector2(26, 60)
const BODY := Vector2(26, 34)            # the middle of the body
const FIGURE_SIZE := 1.12

var number := -1
var side := "left"
var card := ""
var full := 1
var health := 1
var color := Color.WHITE
var walks := "careful"
var walking := false
var swing := 0.0                          # 0 to 1 through an attack, for the weapon

var _icon: Label
var _flash := 0.0
var _shown_health := 1.0
var _time := 0.0


func _init() -> void:
	size = AREA
	pivot_offset = ANCHOR
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_icon = UI.emoji("", 21)
	_icon.position = BODY - Vector2(18, 18)
	_icon.size = Vector2(36, 36)
	add_child(_icon)


func setup(info: Dictionary, side_color: Color) -> void:
	number = int(info["unit"])
	side = str(info["side"])
	card = str(info["card"])
	full = int(info["full"])
	health = int(info["health"])
	_shown_health = float(health)
	walks = str(info["walks"])
	color = side_color
	_icon.text = str(info["icon"])
	_icon.visible = not Characters.has(card)
	_time = float(number) * 0.37              # so that figures do not all bob in step
	queue_redraw()


## Put the piece on the tile whose middle is `centre`.
func place(centre: Vector2) -> void:
	position = centre - ANCHOR


## The middle of the body, where blows land and numbers float up from.
func centre() -> Vector2:
	return position + BODY


func set_health(value: int) -> void:
	if value < health:
		_flash = 1.0
	health = value
	var tween := create_tween()
	tween.tween_method(_show_health, _shown_health, float(value), 0.25)


func _show_health(value: float) -> void:
	_shown_health = value
	queue_redraw()


func hop() -> void:
	## A quick lunge when the unit attacks, and a swing of its weapon.
	var tween := create_tween()
	tween.tween_property(self, "scale", Vector2(1.15, 1.15), 0.07)
	tween.tween_property(self, "scale", Vector2.ONE, 0.14)
	var blow := create_tween()
	blow.tween_method(func(value: float) -> void: swing = value, 0.0, 1.0, 0.32)
	blow.tween_callback(func() -> void: swing = 0.0)


func leave() -> void:
	## The unit is out: shrink, fade, and go.
	var tween := create_tween().set_parallel(true)
	tween.tween_property(self, "scale", Vector2(0.2, 0.2), 0.3)
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	tween.chain().tween_callback(queue_free)


func _process(delta: float) -> void:
	_time += delta
	if _flash > 0.0:
		_flash = maxf(0.0, _flash - delta * 3.5)
	if _flash > 0.0 or Characters.has(card):
		queue_redraw()


func _draw() -> void:
	if Characters.has(card):
		Characters.draw(self, FEET, FIGURE_SIZE, card, color, _time, walking, swing)
		if _flash > 0.0:
			draw_circle(BODY, 22.0, Color(1, 0.15, 0.15, 0.45 * _flash))
	else:
		var middle := BODY
		draw_set_transform(Vector2(26, 54), 0.0, Vector2(1.0, 0.36))
		draw_circle(Vector2.ZERO, 17.0, Color(0, 0, 0, 0.30))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		draw_circle(middle, 18.5, Color("0d2238"))
		draw_circle(middle, 16.5, color)
		draw_circle(middle, 13.0, color.lightened(0.55))
		if _flash > 0.0:
			draw_circle(middle, 16.5, Color(1, 0.2, 0.2, 0.65 * _flash))
	# Health, with the walking style as the colour of its search at the left end.
	var bar := Rect2(Vector2(13, 66), Vector2(32, 6))
	draw_rect(bar.grow(1.5), Color("0d2238"))
	draw_rect(bar, Color("3a4658"))
	var part := clampf(_shown_health / float(full), 0.0, 1.0)
	var fill := UI.GREEN if part > 0.5 else (UI.GOLD if part > 0.25 else UI.RED)
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * part, bar.size.y)), fill)
	draw_circle(Vector2(8, 69), 5.0, Color("0d2238"))
	draw_circle(Vector2(8, 69), 3.4, UI.SEARCH_COLOR[UI.WALK_SEARCH[walks]])
