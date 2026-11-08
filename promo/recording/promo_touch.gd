extends CanvasLayer
## Recording only: a soft dot that shows where the person taps.

var _dot: Control
var _at := Vector2(640, 800)
var _alpha := 0.0
var _press := 0.0
var _ripple := 1.0


func _ready() -> void:
	layer = 120
	_dot = Control.new()
	_dot.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dot.size = Vector2(1280, 720)
	_dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dot.draw.connect(_paint)
	add_child(_dot)


func _process(_delta: float) -> void:
	_dot.queue_redraw()


func _paint() -> void:
	if _alpha < 0.01:
		return
	var radius := 15.0 * (1.0 - 0.2 * _press)
	if _ripple < 1.0:
		_dot.draw_arc(_at, 15.0 + 24.0 * _ripple, 0.0, TAU, 72, Color(1, 1, 1, 0.55 * (1.0 - _ripple) * _alpha), 1.6, true)
	_dot.draw_circle(_at, radius + 3.0, Color(0.05, 0.1, 0.18, 0.16 * _alpha))
	_dot.draw_circle(_at, radius, Color(1, 1, 1, 0.42 * _alpha))
	_dot.draw_arc(_at, radius, 0.0, TAU, 72, Color(1, 1, 1, 0.9 * _alpha), 1.4, true)


func go(to: Vector2, seconds: float = 0.45) -> void:
	if _alpha < 0.5:
		_at = to + Vector2(70, 90)
	var tween := create_tween().set_parallel(true)
	tween.tween_property(self, "_at", to, seconds).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "_alpha", 1.0, 0.18)
	await tween.finished


func tap() -> void:
	var tween := create_tween()
	tween.tween_property(self, "_press", 1.0, 0.07)
	tween.tween_property(self, "_press", 0.0, 0.12)
	_ripple = 0.0
	var ring := create_tween()
	ring.tween_property(self, "_ripple", 1.0, 0.42).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await tween.finished


func away() -> void:
	var tween := create_tween()
	tween.tween_property(self, "_alpha", 0.0, 0.22)
	await tween.finished
