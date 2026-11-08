extends Node
## Recording only: runs the game small and quickly, and saves 8K pictures of the screen on the frames asked for.
##     godot --path . --fixed-fps 60 res://promo_shots.tscn -- --shots 100,200 --out <folder> <the game's own flags>

var _view: SubViewport
var _shots: Array = []
var _out := ""
var _frames := 0
var _rolling := false


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	_out = args[args.find("--out") + 1]
	for word in str(args[args.find("--shots") + 1]).split(","):
		_shots.append(int(word))
	_view = SubViewport.new()
	_small()
	_view.size_2d_override = Vector2i(1280, 720)
	_view.size_2d_override_stretch = true
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_view.audio_listener_enable_2d = false
	add_child(_view)
	await get_tree().process_frame
	Touch.reparent(_view)
	_view.add_child(load("res://main.tscn").instantiate())
	process_priority = 100000
	_rolling = true


func _small() -> void:
	_view.size = Vector2i(1280, 720)
	_view.oversampling_override = 1.0


func _process(delta: float) -> void:
	if not _rolling:
		return
	_frames += 1
	if _shots.has(_frames + 1):
		_view.size = Vector2i(7680, 4320)
		_view.oversampling_override = 6.0
	RenderingServer.force_draw(false, delta)
	if _shots.has(_frames):
		_view.get_texture().get_image().save_png("%s/s%d.png" % [_out, _frames])
		print("shot ", _frames)
		if not _shots.has(_frames + 1):
			_small()
	OS.delay_msec(12)
	if _frames >= int(_shots.max()):
		print("shots done")
		get_tree().quit()
