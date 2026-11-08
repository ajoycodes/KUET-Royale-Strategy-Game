extends Node
## Recording only: every warrior as a large picture with a see-through background, in three poses.
##     godot --path . res://promo_heroes.tscn -- --out <folder>

const SIDE := 1500
const SIZE := 20.0
const FEET := Vector2(750, 1340)

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
	var poses := {"idle": [0.7, false, 0.0], "hit": [0.7, false, 0.5], "run": [0.35, true, 0.0]}
	for department in GalleryScreen.DEPARTMENTS:
		for name in department[2]:
			for pose in poses:
				var values: Array = poses[pose]
				_job = {"name": name, "color": department[1], "time": values[0], "moving": values[1], "swing": values[2]}
				_paper.queue_redraw()
				await get_tree().process_frame
				RenderingServer.force_draw(false, 0.0)
				_view.get_texture().get_image().save_png("%s/%s_%s.png" % [out, str(name).to_lower().replace(" ", "-").replace("/", ""), pose])
	for department in GalleryScreen.DEPARTMENTS:
		for broken in [false, true]:
			_job = {"castle": true, "broken": broken, "color": department[1]}
			_paper.queue_redraw()
			await get_tree().process_frame
			RenderingServer.force_draw(false, 0.0)
			_view.get_texture().get_image().save_png("%s/castle-%s_%s.png" % [out, str(department[0]).to_lower(), "ruin" if broken else "whole"])
	print("heroes done")
	get_tree().quit()


## The game's castle, as it is drawn on the board, without its health bar and with a flag on top.
func _castle(color: Color) -> void:
	var c := _paper
	var edge := Color("0d2238")
	c.draw_set_transform(Vector2(750, 980), 0.0, Vector2(13, 13))
	var middle := Vector2.ZERO
	var keep := Rect2(middle + Vector2(-34, -20), Vector2(68, 44))
	c.draw_line(Vector2(0, -27), Vector2(0, -60), edge, 4.0)
	c.draw_line(Vector2(0, -27), Vector2(0, -60), UI.WOOD_LIGHT, 2.0)
	c.draw_colored_polygon(PackedVector2Array([Vector2(1, -60), Vector2(25, -52), Vector2(1, -44)]), edge)
	c.draw_colored_polygon(PackedVector2Array([Vector2(2, -58), Vector2(21, -52), Vector2(2, -46)]), color)
	c.draw_style_box(UI.box(edge, 8), keep.grow(3.0))
	c.draw_style_box(UI.box(UI.STONE, 6), keep)
	c.draw_rect(Rect2(keep.position + Vector2(0, 30), Vector2(keep.size.x, 14)), UI.STONE_DARK)
	for tooth in 4:
		var block := Rect2(keep.position + Vector2(2 + tooth * 17.3, -9), Vector2(12, 11))
		c.draw_rect(block.grow(2.5), edge)
		c.draw_rect(block, UI.STONE)
	var banner := Rect2(middle + Vector2(-17, -27), Vector2(34, 30))
	c.draw_style_box(UI.box(edge, 9), banner.grow(3.0))
	c.draw_style_box(UI.box(color, 7), banner)
	c.draw_style_box(UI.box(edge, 8), Rect2(middle + Vector2(-12, 8), Vector2(24, 16)))
	c.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _ruin(color: Color) -> void:
	var c := _paper
	var edge := Color("0d2238")
	c.draw_set_transform(Vector2(750, 980), 0.0, Vector2(13, 13))
	var keep := PackedVector2Array([Vector2(-34, 24), Vector2(-34, -6), Vector2(-20, -14), Vector2(-8, -2), Vector2(6, -16), Vector2(18, -4), Vector2(34, -10), Vector2(34, 24)])
	c.draw_colored_polygon(keep, UI.STONE_DARK)
	keep.append(keep[0])
	c.draw_polyline(keep, edge, 3.0, true)
	c.draw_line(Vector2(-12, 0), Vector2(-4, 16), edge, 2.0)
	c.draw_line(Vector2(10, -6), Vector2(14, 12), edge, 2.0)
	for stone in [Vector2(-40, 20), Vector2(38, 18), Vector2(-26, 26), Vector2(28, 27)]:
		c.draw_circle(stone, 5.0, edge)
		c.draw_circle(stone, 3.6, UI.STONE)
	c.draw_style_box(UI.box(color.darkened(0.4), 4), Rect2(Vector2(-12, 6), Vector2(24, 12)))
	c.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _paint() -> void:
	if _job.has("castle"):
		if _job["broken"]:
			_ruin(_job["color"])
		else:
			_castle(_job["color"])
	elif not _job.is_empty():
		Characters.draw(_paper, FEET, SIZE, _job["name"], _job["color"], _job["time"], _job["moving"], _job["swing"])
