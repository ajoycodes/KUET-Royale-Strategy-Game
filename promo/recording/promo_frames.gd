extends Node
## Recording only: every warrior's walk, stand and attack as frames with see-through backgrounds, for the film.
##     godot --path . res://promo_frames.tscn -- --out <folder>

const SIDE := 1500
const SIZE := 20.0
const FEET := Vector2(750, 1340)
const RUN_FRAMES := 12
const STAND_FRAMES := 8
const HIT_FRAMES := 10
const WALK_PERIOD := 0.6    # seconds for one whole walk cycle at the speed the figures are drawn with

var _view: SubViewport
var _paper: Control
var _job := {}


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var out: String = args[args.find("--out") + 1]
	_view = SubViewport.new()
	_view.size = Vector2i(SIDE, SIDE)
	_view.transparent_bg = true
	_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_paper = Control.new()
	_paper.size = Vector2(SIDE, SIDE)
	_paper.draw.connect(_paint)
	_view.add_child(_paper)
	add_child(_view)
	await get_tree().process_frame
	for department in GalleryScreen.DEPARTMENTS:
		for name in department[2]:
			var slug := str(name).to_lower().replace(" ", "-").replace("/", "")
			var period := _walk_period(name)
			for i in RUN_FRAMES:
				await _save({"name": name, "color": department[1], "time": period * i / RUN_FRAMES, "moving": true, "swing": 0.0}, "%s/%s_run_%02d.png" % [out, slug, i])
			for i in STAND_FRAMES:
				await _save({"name": name, "color": department[1], "time": 2.0 * i / STAND_FRAMES, "moving": false, "swing": 0.0}, "%s/%s_idle_%02d.png" % [out, slug, i])
			for i in HIT_FRAMES:
				await _save({"name": name, "color": department[1], "time": 0.7, "moving": false, "swing": float(i) / (HIT_FRAMES - 1)}, "%s/%s_hit_%02d.png" % [out, slug, i])
	print("frames done")
	get_tree().quit()


## One whole cycle of this figure's legs or wings, so that the frames loop without a jump.
func _walk_period(name: String) -> float:
	var look: Dictionary = Characters.LOOK[name]
	match str(look["kind"]):
		"hero":
			return TAU / (14.0 if str(look.get("pose", "")) == "run" else 10.0)
		"mech":
			return TAU / 7.0
		"scorpion":
			return TAU / 16.0
		"cloudrider":
			return TAU / 3.0
		"jet":
			return TAU / 3.2
		"spark":
			return TAU / 3.5
		"hawk":
			return TAU / 8.0
	return 1.0


func _save(job: Dictionary, path: String) -> void:
	_job = job
	_paper.queue_redraw()
	await get_tree().process_frame
	RenderingServer.force_draw(false, 0.0)
	_view.get_texture().get_image().save_png(path)


func _paint() -> void:
	if not _job.is_empty():
		Characters.draw(_paper, FEET, SIZE, _job["name"], _job["color"], _job["time"], _job["moving"], _job["swing"])
