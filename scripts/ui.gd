class_name UI
extends RefCounted
## Shared look of the game: colours, fonts and small factories for labels,
## panels and buttons. Nothing in here knows the rules.

const SCREEN := Vector2(1280, 720)

const NIGHT := Color("123152")           # the window behind everything
const NIGHT_LIGHT := Color("1a4270")
const PANEL := Color("1d4c7e")
const PANEL_LIGHT := Color("2a639f")
const PANEL_LINE := Color("4f8fcf")
const WHITE := Color("ffffff")
const MUTED := Color("c2d8ee")
const DIM := Color("8fb0d0")
const INK := Color("2b2118")
const INK_SOFT := Color("6a5a48")
const GOLD := Color("ffcf3f")
const RED := Color("f0483e")
const GREEN := Color("67d24d")
const WOOD := Color("9a6638")
const WOOD_DARK := Color("6b4423")
const WOOD_LIGHT := Color("c08a52")
const PAPER := Color("f7edd4")
const PAPER_DIM := Color("e4d3ac")

# The battlefield.
const GRASS := Color("86cd50")
const GRASS_ALT := Color("79c145")
const GRASS_RIM := Color("3f8f34")
const ROAD := Color("e6d29c")
const ROAD_EDGE := Color("cfb97f")
const MUD := Color("8d6b47")
const MUD_DARK := Color("6f5235")
const RIVER := Color("3fa9ea")
const RIVER_LIGHT := Color("9bdcff")
const BRIDGE := Color("b98552")
const BRIDGE_DARK := Color("86592f")
const STONE := Color("d3d7e0")
const STONE_DARK := Color("8d95a6")

# One colour per path search, used wherever that search shows on screen.
const SEARCH_COLOR := {
	"uniform_cost": Color("2f6bff"),
	"breadth_first": Color("ff5fd2"),
	"astar": Color("ffd84a"),
	"best_first": Color("ff7a2f"),
}
const SEARCH_NAME := {
	"uniform_cost": "Uniform-cost search",
	"breadth_first": "Breadth-first search",
	"astar": "A* search",
	"best_first": "Best-first search",
}
const WALK_SEARCH := {"careful": "astar", "reckless": "best_first", "hover": "breadth_first"}
const WALK_NAME := {"careful": "Careful", "reckless": "Reckless", "hover": "Hover"}

const SEAT_WORD := {"left": "Top", "right": "Bottom"}

static var _fonts := {}
static var _art := {}


static func font(weight: int = 400) -> Font:
	## Two faces only. On macOS a system family ignores the weight it is asked
	## for, so the bold face and the regular face come from different families.
	var bold := weight >= 600
	if not _fonts.has(bold):
		var made := SystemFont.new()
		if bold:
			made.font_names = PackedStringArray(["Arial Rounded MT Bold", "Avenir Next", "Nunito", "Segoe UI", "Arial"])
			made.font_weight = 700
		else:
			made.font_names = PackedStringArray(["Avenir", "Helvetica Neue", "Segoe UI", "Arial"])
			made.font_weight = 400
		made.allow_system_fallback = true
		_fonts[bold] = made
	return _fonts[bold]


static func label(text: String, size: int = 16, color: Color = WHITE, weight: int = 400) -> Label:
	var made := Label.new()
	made.text = text
	made.add_theme_font_override("font", font(weight))
	made.add_theme_font_size_override("font_size", size)
	made.add_theme_color_override("font_color", color)
	made.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return made


## Chunky text with a dark edge, for names and scores.
static func title(text: String, size: int, color: Color = WHITE, edge: int = 8) -> Label:
	var made := label(text, size, color, 800)
	made.add_theme_color_override("font_outline_color", Color("0d2238"))
	made.add_theme_constant_override("outline_size", edge)
	return made


## A picture from the art folder. The folder is kept out of Godot's import step, so that a fresh copy of the project runs as it is.
static func art(file: String) -> Texture2D:
	if not _art.has(file):
		var made: Texture2D = null
		var bytes := FileAccess.get_file_as_bytes("res://art/" + file)
		if not bytes.is_empty():
			var image := Image.new()
			if image.load_png_from_buffer(bytes) == OK:
				image.generate_mipmaps()
				made = ImageTexture.create_from_image(image)
		_art[file] = made
	return _art[file]


## The game's name in carved metal, centred on a point. The letters sit in the exact middle of the picture.
## Without the picture, plain gold letters.
static func logo(file: String, middle: Vector2, area: Vector2, plain_size: int) -> Control:
	var texture := art(file)
	if texture == null:
		var plain := title("KUET Royale", plain_size, GOLD, plain_size / 4)
		plain.size = area
		plain.position = middle - area / 2.0
		plain.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		plain.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		return plain
	var made := TextureRect.new()
	made.texture = texture
	made.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	made.stretch_mode = TextureRect.STRETCH_SCALE
	made.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	made.mouse_filter = Control.MOUSE_FILTER_IGNORE
	made.size = area
	made.position = middle - area / 2.0
	return made


## Sentences from the rules say "top lane" and "bottom lane". On the upright arena those are left and right.
static func lane_words(text: String) -> String:
	return text.replace("top lane", "left lane").replace("bottom lane", "right lane")


static func wrapped(text: String, width: float, size: int = 16, color: Color = WHITE, weight: int = 400) -> Label:
	var made := label(text, size, color, weight)
	made.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	made.custom_minimum_size = Vector2(width, 0)
	made.size = Vector2(width, 0)
	return made


## A one-line label of a fixed width. Text that does not fit ends in "...".
static func fitted(text: String, at: Vector2, width: float, size: int = 14, color: Color = WHITE, weight: int = 400,
		align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var made := label(text, size, color, weight)
	made.clip_text = true                    # before the size, or the label refuses to be narrower than its text
	made.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	made.horizontal_alignment = align
	made.position = at
	made.size = Vector2(width, size + 8)
	return made


## A small button for the top bar.
static func small_button(text: String, width: float, fill: Color = PANEL_LIGHT, ink: Color = WHITE) -> Button:
	var made := button(text, fill, ink, 13)
	for state in ["normal", "hover", "pressed", "disabled"]:
		var style: StyleBoxFlat = made.get_theme_stylebox(state).duplicate()
		style.content_margin_left = 4
		style.content_margin_right = 4
		style.content_margin_top = 4
		style.content_margin_bottom = 4
		made.add_theme_stylebox_override(state, style)
	made.custom_minimum_size = Vector2(width, 32)
	made.size = Vector2(width, 32)
	return made


static func emoji(text: String, size: int) -> Label:
	var made := Label.new()
	made.text = text
	made.add_theme_font_size_override("font_size", size)
	made.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	made.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	made.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return made


static func box(fill: Color, radius: int = 14, border: Color = Color(0, 0, 0, 0), border_width: int = 0) -> StyleBoxFlat:
	var made := StyleBoxFlat.new()
	made.bg_color = fill
	made.set_corner_radius_all(radius)
	made.border_color = border
	made.set_border_width_all(border_width)
	made.anti_aliasing = true
	return made


static func panel(fill: Color = PANEL, radius: int = 16, border: Color = Color(0, 0, 0, 0), border_width: int = 0) -> Panel:
	var made := Panel.new()
	made.add_theme_stylebox_override("panel", box(fill, radius, border, border_width))
	made.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return made


static func button(text: String, fill: Color = PANEL_LIGHT, ink: Color = WHITE, size: int = 16, weight: int = 600) -> Button:
	var made := Button.new()
	made.text = text
	made.focus_mode = Control.FOCUS_NONE
	made.add_theme_font_override("font", font(weight))
	made.add_theme_font_size_override("font_size", size)
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		made.add_theme_color_override(state, ink)
	made.add_theme_color_override("font_disabled_color", Color(ink, 0.4))
	var normal := box(fill, 10, fill.lightened(0.16), 2)
	normal.content_margin_left = 16
	normal.content_margin_right = 16
	normal.content_margin_top = 8
	normal.content_margin_bottom = 8
	var hover: StyleBoxFlat = normal.duplicate()
	hover.bg_color = fill.lightened(0.12)
	var pressed: StyleBoxFlat = normal.duplicate()
	pressed.bg_color = fill.darkened(0.12)
	var disabled: StyleBoxFlat = normal.duplicate()
	disabled.bg_color = Color(fill, 0.45)
	made.add_theme_stylebox_override("normal", normal)
	made.add_theme_stylebox_override("hover", hover)
	made.add_theme_stylebox_override("pressed", pressed)
	made.add_theme_stylebox_override("disabled", disabled)
	made.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	made.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	made.pressed.connect(func() -> void: Sfx.play("tap"))
	return made


## A button that looks chosen or not, for picking one of a few.
static func choice_style(made: Button, chosen: bool, color: Color) -> void:
	var fill := color if chosen else PANEL_LIGHT
	var ink := INK if chosen else WHITE
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		made.add_theme_color_override(state, ink)
	var margin := 4 if made.size.x < 100 else 14
	for state in ["normal", "hover", "pressed"]:
		var style := box(fill if state != "hover" else fill.lightened(0.1), 10, fill.lightened(0.16), 2)
		style.content_margin_left = margin
		style.content_margin_right = margin
		style.content_margin_top = 4 if margin == 4 else 8
		style.content_margin_bottom = 4 if margin == 4 else 8
		made.add_theme_stylebox_override(state, style)


## Scale a control around its own centre: out and back, for a little bounce.
static func bounce(node: Control, amount: float = 1.18, time: float = 0.28) -> void:
	node.pivot_offset = node.size / 2.0
	var tween := node.create_tween()
	tween.tween_property(node, "scale", Vector2(amount, amount), time * 0.4).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(node, "scale", Vector2.ONE, time * 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## Pop a control into view from nothing.
static func pop_in(node: Control, time: float = 0.3) -> void:
	node.pivot_offset = node.size / 2.0
	node.scale = Vector2(0.2, 0.2)
	node.modulate.a = 0.0
	var tween := node.create_tween().set_parallel(true)
	tween.tween_property(node, "scale", Vector2.ONE, time).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(node, "modulate:a", 1.0, time * 0.6)


static func number(value: float) -> String:
	var whole := str(int(round(value)))
	var out := ""
	var count := 0
	for i in range(whole.length() - 1, -1, -1):
		out = whole[i] + out
		count += 1
		if count % 3 == 0 and i > 0:
			out = "," + out
	return out


## The two sides of a match must never look the same, even in a mirror match.
static func side_colors(view: Dictionary) -> Dictionary:
	var left := Color(str(view["sides"]["left"]["color"]))
	var right := Color(str(view["sides"]["right"]["color"]))
	if left.is_equal_approx(right):
		right = right.lightened(0.45)
	return {"left": left, "right": right}
