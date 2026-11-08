class_name IntroScreen
extends Control
## The film that opens the game. The Skip button, or the end of the film, goes on to the menu.
## A copy of the game without the film goes straight to the menu.

signal finished

const FILM := "res://intro/KUET-Royale-film.ogv"
const FADE := 0.2

var over := false

var _player: VideoStreamPlayer
var _leaving := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN
	z_index = 100
	mouse_filter = Control.MOUSE_FILTER_STOP
	var black := ColorRect.new()
	black.color = Color.BLACK
	black.size = UI.SCREEN
	black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(black)
	if not FileAccess.file_exists(FILM):
		_end.call_deferred()
		return
	var stream := VideoStreamTheora.new()
	stream.file = FILM
	_player = VideoStreamPlayer.new()
	_player.stream = stream
	_player.expand = true
	_player.size = UI.SCREEN
	_player.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_player.finished.connect(_end)
	add_child(_player)
	_player.play()
	# In the black bar under the picture, clear of the film's words.
	var skip := UI.button("Skip", UI.PANEL_LIGHT, UI.WHITE, 15)
	skip.size = Vector2(104, 44)
	skip.position = UI.SCREEN - skip.size - Vector2(16, 10)
	skip.pressed.connect(_skip)
	add_child(skip)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		_skip()


## A short fade, so that the sound does not stop dead.
func _skip() -> void:
	if _leaving or over:
		return
	_leaving = true
	var tween := create_tween().set_parallel(true)
	tween.tween_property(self, "modulate:a", 0.0, FADE)
	tween.tween_property(_player, "volume_db", -60.0, FADE)
	await tween.finished
	_end()


func _end() -> void:
	if over:
		return
	over = true
	if _player != null:
		_player.stop()
	finished.emit()
	queue_free()
