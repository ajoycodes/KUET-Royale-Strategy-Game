extends Node
## Recording only: runs a real match and saves the stretches asked for as raw 1080p frames of one region of the arena,
## drawn directly at that size, so they are as sharp as the screen can be.
##     godot --path . --fixed-fps 60 res://promo_cuts.tscn -- --out <folder> --cuts name:start:end:x:y:w,... <the game's own flags>

const OUT_W := 1920
const OUT_H := 1080

var _view: SubViewport
var _cuts: Array = []
var _out := ""
var _frames := 0
var _rolling := false
var _file: FileAccess
var _now := {}


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	_out = args[args.find("--out") + 1]
	for word in str(args[args.find("--cuts") + 1]).split(","):
		var bits := word.split(":")
		_cuts.append({"name": bits[0], "start": int(bits[1]), "end": int(bits[2]), "x": float(bits[3]), "y": float(bits[4]), "w": float(bits[5])})
	_view = SubViewport.new()
	_view.size = Vector2i(1280, 720)
	_view.size_2d_override = Vector2i(1280, 720)
	_view.size_2d_override_stretch = true
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_view.audio_listener_enable_2d = false
	add_child(_view)
	await get_tree().process_frame
	Touch.reparent(_view)
	Touch.visible = false
	_view.add_child(load("res://main.tscn").instantiate())
	process_priority = 100000
	_rolling = true


func _begin(cut: Dictionary) -> void:
	_now = cut
	_view.size = Vector2i(OUT_W, OUT_H)
	_view.oversampling_override = OUT_W / float(cut["w"])
	# The stretch from 1280 to 1920 is 1.5; the rest of the zoom goes in the canvas transform.
	var zoom := OUT_W / float(cut["w"]) / 1.5
	_view.canvas_transform = Transform2D(0.0, Vector2(zoom, zoom), 0.0, Vector2(-float(cut["x"]) * zoom, -float(cut["y"]) * zoom))
	_file = FileAccess.open("%s/%s.rgb" % [_out, cut["name"]], FileAccess.WRITE)


func _end() -> void:
	_file.close()
	_file = null
	_now = {}
	_view.canvas_transform = Transform2D.IDENTITY
	_view.size = Vector2i(1280, 720)
	_view.oversampling_override = 1.0
	print("cut done")


func _process(delta: float) -> void:
	if not _rolling:
		return
	_frames += 1
	for cut in _cuts:
		if _frames == int(cut["start"]) - 1:
			_begin(cut)
	RenderingServer.force_draw(false, delta)
	if not _now.is_empty() and _frames >= int(_now["start"]) and (_frames - int(_now["start"])) % 2 == 0:
		var image := _view.get_texture().get_image()
		image.convert(Image.FORMAT_RGB8)
		_file.store_buffer(image.get_data())
	if not _now.is_empty() and _frames >= int(_now["end"]):
		_end()
	OS.delay_msec(10)
	var last := 0
	for cut in _cuts:
		last = maxi(last, int(cut["end"]))
	if _frames > last:
		print("cuts done")
		get_tree().quit()
