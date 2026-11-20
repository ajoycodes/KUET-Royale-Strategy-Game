extends Node
## Recording only: the whole game runs inside a 4K SubViewport and every frame is piped straight into ffmpeg.
## A SubViewport keeps drawing when the window is covered or on another desktop, so a take can never freeze.
##     godot --path . --fixed-fps 60 -- --cap-out out.mp4 --cap-frames 600 <the game's own flags>

var _view: SubViewport
var _ffmpeg := {}
var _stdio: FileAccess
var _frames := 0
var _total := 0
var _done := false
var _rolling := false
var _still := ""


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var out: String = args[args.find("--cap-out") + 1]
	_total = int(args[args.find("--cap-frames") + 1])
	_view = SubViewport.new()
	_view.size = Vector2i(3840, 2160)
	_view.size_2d_override = Vector2i(1280, 720)
	_view.size_2d_override_stretch = true
	_view.oversampling_override = 3.0
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_view.audio_listener_enable_2d = false
	add_child(_view)
	await get_tree().process_frame
	Touch.reparent(_view)
	_still = out if out.ends_with(".png") else ""
	if _still != "":
		_view.add_child(load("res://main.tscn").instantiate())
		process_priority = 100000
		_rolling = true
		return
	_ffmpeg = OS.execute_with_pipe("/opt/homebrew/bin/ffmpeg", ["-hide_banner", "-loglevel", "error", "-nostats", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
		"-s", "3840x2160", "-r", "60", "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-pix_fmt", "yuv420p", "-g", "30", "-bf", "0", "-movflags", "+faststart", out])
	_stdio = _ffmpeg["stdio"]
	# Only now the game: ffmpeg must not inherit the pipe of a Python call that is already running.
	_view.add_child(load("res://main.tscn").instantiate())
	process_priority = 100000       # after everything else has moved
	_rolling = true


func _process(delta: float) -> void:
	if _rolling and not _done:
		RenderingServer.force_draw(false, delta)      # draws even when the system says the window cannot be seen
		_grab()
		OS.delay_msec(45)       # the brains think in real time, so a slower recording keeps their pauses short on film


func _grab() -> void:
	var image := _view.get_texture().get_image()
	if _still != "":
		_frames += 1
		if _frames >= _total:
			_done = true
			image.save_png(_still)
			print("captured still")
			get_tree().quit()
		return
	if image.get_format() != Image.FORMAT_RGB8:
		image.convert(Image.FORMAT_RGB8)
	_stdio.store_buffer(image.get_data())
	_frames += 1
	if _frames >= _total:
		_done = true
		_stdio.close()
		_finish()


func _finish() -> void:
	while OS.is_process_running(int(_ffmpeg["pid"])):
		await get_tree().create_timer(0.1).timeout
	print("captured ", _frames, " frames")
	get_tree().quit()
