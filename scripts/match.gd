class_name MatchScreen
extends Control
## One match on screen: the battlefield in the middle, a thinking panel for each
## side, both decks along the bottom. Python decides everything; this script
## asks for the next card and then plays back what it is told happened.

signal done(action: String)
signal _chosen(card: int, lane: String)
signal _overlay_closed(answer: String)

const BOARD_AT := Vector2(472, 50)
const PANEL_AT := {"left": Vector2(12, 50), "right": Vector2(820, 50)}
const LEGEND := [
	["uniform_cost", "Uniform-cost", 116.0],
	["astar", "A*", 50.0],
	["best_first", "Best-first", 96.0],
	["breadth_first", "Breadth-first", 116.0],
]

var config := {}             # left, right, left_brain, right_brain, and for demos: auto, robot, seed

var _view := {}
var _colors := {}
var _board: BoardView
var _panels := {}
var _hands := {"left": [], "right": []}
var _names := {}             # unit number -> card name
var _status: Label
var _talk: Label
var _talk_dot: Panel
var _overlay: Control
var _speed := 1.0
var _paused := false
var _tokens := 0
var _alive := true
var _picked := -1
var _picking_side := ""
var _hint := {}
var _bet := ""
var _speed_buttons := {}
var _pause_button: Button
var _step_button: Button
var _hint_button: Button


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = UI.SCREEN
	_speed = float(config.get("speed", 1.0))
	_build_chrome()
	_begin()


func _exit_tree() -> void:
	_alive = false


# ------------------------------------------------------------------ set-up

func _build_chrome() -> void:
	var title := UI.title("KUET Royale", 22, UI.GOLD, 8)
	title.position = Vector2(16, 6)
	add_child(title)

	_status = UI.label("Opening the arena...", 15, UI.WHITE, 800)
	_status.position = Vector2(340, 10)
	_status.size = Vector2(600, 24)
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_status)

	var x := 1018.0
	for value in [1.0, 2.0, 4.0]:
		var made := UI.small_button("%dx" % int(value), 40)
		made.position = Vector2(x, 8)
		made.pressed.connect(_set_speed.bind(value))
		add_child(made)
		_speed_buttons[value] = made
		x += 44.0
	_pause_button = UI.small_button("Pause", 64)
	_pause_button.position = Vector2(x, 8)
	_pause_button.pressed.connect(_toggle_pause)
	add_child(_pause_button)
	var menu := UI.small_button("Menu", 50)
	menu.position = Vector2(x + 68.0, 8)
	menu.pressed.connect(func() -> void: _leave("menu"))
	add_child(menu)
	_step_button = UI.small_button("Step", 56, UI.GOLD, UI.INK)
	_step_button.position = Vector2(950, 8)
	_step_button.visible = false
	_step_button.pressed.connect(func() -> void: _tokens += 1)
	add_child(_step_button)
	_set_speed(_speed)

	# One strip along the bottom: what just happened, and what each highlight colour means.
	var strip := UI.panel(Color("0d2238"), 12)
	strip.position = Vector2(12, 684)
	strip.size = Vector2(1256, 30)
	add_child(strip)
	_talk_dot = UI.panel(UI.MUTED, 6)
	_talk_dot.position = Vector2(24, 693)
	_talk_dot.size = Vector2(12, 12)
	add_child(_talk_dot)
	_talk = UI.fitted("", Vector2(44, 688), 720, 14, UI.WHITE, 800)
	add_child(_talk)
	_hint_button = UI.small_button("Hint", 60, UI.GOLD, UI.INK)
	_hint_button.position = Vector2(776, 683)
	_hint_button.visible = false
	_hint_button.pressed.connect(_on_hint)
	add_child(_hint_button)
	var legend_x := 866.0
	for entry in LEGEND:
		var dot := UI.panel(UI.SEARCH_COLOR[entry[0]], 6)
		dot.position = Vector2(legend_x, 693)
		dot.size = Vector2(12, 12)
		add_child(dot)
		var words := UI.label(str(entry[1]), 12, UI.MUTED, 400)
		words.position = Vector2(legend_x + 18, 689)
		add_child(words)
		legend_x += float(entry[2])


func _begin() -> void:
	var arguments: Array = ["new", "--left", config["left"], "--right", config["right"],
		"--left-brain", config["left_brain"], "--right-brain", config["right_brain"]]
	if config.has("seed"):
		arguments.append_array(["--seed", str(config["seed"])])
	var reply: Dictionary = await Bridge.ask(arguments)
	if not _alive:
		return
	if not bool(reply.get("ok", false)):
		_fail(str(reply.get("error", "The AI did not answer.")))
		return
	_view = reply["view"]
	_colors = UI.side_colors(_view)
	_build_match()
	await _intro()
	if _alive:
		_run()


func _build_match() -> void:
	_board = BoardView.new()
	_board.position = BOARD_AT
	_board.setup(_view, _colors)
	_board.speed = _speed
	_board.lane_chosen.connect(_on_lane_chosen)
	add_child(_board)
	move_child(_board, 0)

	for side in ["left", "right"]:
		var panel := ThinkingPanel.new()
		panel.position = PANEL_AT[side]
		panel.setup(_view["sides"][side], side, _colors[side])
		add_child(panel)
		_panels[side] = panel
		var deck: Array = _view["sides"][side]["deck"]
		for place in deck.size():
			var card := CardView.new()
			card.position = panel.position + panel.card_spot(place)
			card.setup(deck[place], _colors[side])
			card.picked.connect(_on_card_picked.bind(side))
			add_child(card)
			_hands[side].append(card)
	_refresh()


# ---------------------------------------------------------------- the loop

func _run() -> void:
	while _alive:
		if bool(_view["leg_over"]):
			var go_on: bool = await _leg_over()
			if not go_on or not _alive:
				return
			continue
		var side := str(_view["to_move"])
		var brain := str(_view["sides"][side]["brain"])
		_panels["left"].set_active(side == "left")
		_panels["right"].set_active(side == "right")
		var arguments: Array = ["step"]
		if brain == "human":
			var pick: Array = await _human_turn(side)
			if not _alive:
				return
			arguments.append_array(["--card", str(pick[0]), "--lane", str(pick[1])])
		else:
			await _gate()
			if not _alive:
				return
			_panels[side].set_thinking(true)
			Sfx.play("think")
		var reply: Dictionary = await Bridge.ask(arguments)
		if not _alive:
			return
		_panels[side].set_thinking(false)
		if bool(reply.get("timeout", false)):
			# No answer came. Look at the match as it now stands and carry on from there:
			# if the card was not played after all, the loop simply asks again.
			var look: Dictionary = await Bridge.ask(["view"])
			if not _alive:
				return
			if not bool(look.get("ok", false)):
				_fail(str(look.get("error", "The AI did not answer.")))
				return
			_view = look["view"]
			for unit in _view["units"]:
				_names[int(unit["unit"])] = str(unit["card"])
			for hand_side in ["left", "right"]:
				for card in _hands[hand_side]:
					card.set_used(bool(_view["sides"][hand_side]["deck"][card.index]["used"]))
			_board.sync_units(_view["units"])
			_board.reset_towers(_view)
			_refresh()
			_say("The AI was slow to answer. Carrying on.", UI.GOLD)
			continue
		if not bool(reply.get("ok", false)):
			_fail(str(reply.get("error", "The AI did not answer.")))
			return
		await _show_reply(reply)


func _show_reply(reply: Dictionary) -> void:
	var move: Dictionary = reply["move"]
	var side := str(move["side"])
	_panels[side].show_thinking(reply["thinking"])
	var comments: Array = reply["comments"]
	_say(UI.lane_words(str(comments[0]["text"])), _colors[side])
	_hands[side][int(move["index"])].set_used(true)
	var deployed: Dictionary = reply["deployed"]
	_names[int(deployed["unit"])] = str(deployed["card"])
	_board.add_unit(deployed)
	Sfx.play("deploy")
	_status.text = _status_text(int(_view["play"]) + 1)
	await _wait(0.55)

	var steps: Array = reply["steps"]
	for place in steps.size():
		await _gate()
		if not _alive:
			return
		var lines: Array = []
		for comment in comments:
			if int(comment["step"]) == place:
				lines.append(str(comment["text"]))
		await _show_step(steps[place], lines)
		if not _alive:
			return
	_view = reply["view"]
	_board.sync_units(_view["units"])
	_refresh()


func _show_step(step: Dictionary, lines: Array) -> void:
	# 1. Units that changed their mind: show the searches that decided where they go.
	var searches: Array = step["searches"]
	for place in searches.size():
		await _show_search(searches[place], place < 2)
		if not _alive:
			return

	# 2. A unit with several enemies in range: show the fuzzy priorities it compared.
	for attack in step["attacks"]:
		if attack.has("choices"):
			for choice in attack["choices"]:
				var at: Vector2 = _target_point(choice["target"], _foe_of(int(attack["unit"])))
				_board.float_text(at + Vector2(0, -26), str(choice["priority"]), UI.GOLD, 14, 14.0, 1.0 / _speed)

	# 3. Everybody acts at the same moment.
	var longest := 0.0
	for move in step["moves"]:
		longest = maxf(longest, _board.walk(int(move["unit"]), move["path"], 0.17 / _speed))
	for attack in step["attacks"]:
		var attacker: UnitPiece = _board.piece(int(attack["unit"]))
		if attacker == null:
			continue
		attacker.hop()
		var target_at := _board.tile_centre(attack["at"])
		_board.line(PackedVector2Array([attacker.centre(), target_at]), _colors[attacker.side], 0.35 / _speed, 3.0)
		if not (attack["splash"] as Array).is_empty():
			_board.glow(attack["at"], UI.SEARCH_COLOR["breadth_first"], 0.9)
	if not (step["attacks"] as Array).is_empty():
		Sfx.play("hit")
	for shot in step["shots"]:
		var struck: UnitPiece = _board.piece(int(shot["target"]))
		if struck != null:
			_board.line(PackedVector2Array([_board.tower_centre(str(shot["side"])), struck.centre()]), UI.WHITE, 0.3 / _speed, 2.5)
			Sfx.play("shot")
	await get_tree().create_timer(maxf(longest, 0.28 / _speed)).timeout
	if not _alive:
		return

	# 4. All the damage lands together.
	for hurt in step["hurt"]:
		var struck: UnitPiece = _board.piece(int(hurt["unit"]))
		if struck != null:
			_board.float_text(struck.centre() + Vector2(0, -22), "-%d" % int(hurt["damage"]), UI.RED)
	for side in ["left", "right"]:
		var health := int(step["towers"][side])
		if int(step["tower_hurt"][side]) > 0:
			Sfx.play("tower")
		_board.set_tower(side, health)
		_panels[side].set_tower(health)
	if not (step["dead"] as Array).is_empty():
		Sfx.play("out")
	_board.sync_units(step["units"], true)
	_refresh_damage({"left": int(step["towers"]["left"]), "right": int(step["towers"]["right"])})
	if not lines.is_empty():
		_say(UI.lane_words(str(lines[lines.size() - 1])))
	await _wait(0.18)


func _show_search(search: Dictionary, in_full: bool) -> void:
	var who := str(_names.get(int(search["unit"]), "A unit"))
	var target_search := str(search["target_search"])
	var route_search := str(search["route_search"])
	var target_color: Color = UI.SEARCH_COLOR[target_search]
	var route_color: Color = UI.SEARCH_COLOR[route_search]
	if not in_full or _speed > 2.0:
		_board.route_line(search["route"], route_color, 1.2 / _speed)
		return
	Sfx.play("search")
	if target_search == route_search:
		_say("%s: breadth-first search finds the nearest target and the fewest steps to it." % who, route_color)
		await _sweep(search["route_explored"], route_color)
	else:
		_say("%s: uniform-cost search finds the enemy that is cheapest to reach." % who, target_color)
		await _sweep(search["target_explored"], target_color)
		if not _alive:
			return
		await _wait(0.3)
		_say("%s: %s plans the route. It costs %d." % [who, str(UI.SEARCH_NAME[route_search]), int(search["cost"])], route_color)
		await _sweep(search["route_explored"], route_color)
	if not _alive:
		return
	_board.route_line(search["route"], route_color, 1.6 / _speed)
	_board.glow(search["goal"], UI.WHITE, 1.0)
	await _wait(0.4)


## Light tiles in the order a search explored them, a few per frame.
func _sweep(tiles: Array, color: Color) -> void:
	var per_frame := maxi(1, int(ceil(float(tiles.size()) * _speed / 20.0)))
	var place := 0
	while place < tiles.size() and _alive:
		for _i in per_frame:
			if place < tiles.size():
				_board.glow(tiles[place], color)
				place += 1
		await get_tree().process_frame


func _foe_of(number: int) -> String:
	var made: UnitPiece = _board.piece(number)
	if made == null:
		return "right"
	return "right" if made.side == "left" else "left"


func _target_point(target: Variant, tower_side: String) -> Vector2:
	if typeof(target) == TYPE_STRING:
		return _board.tower_centre(tower_side)
	var made: UnitPiece = _board.piece(int(target))
	return made.centre() if made != null else _board.tower_centre(tower_side)


# ------------------------------------------------------- a person's turn

func _human_turn(side: String) -> Array:
	_picked = -1
	_picking_side = side
	_hint = {}
	_say("Your move. Click one of your cards, then a lane.", _colors[side])
	for card in _hands[side]:
		card.set_pickable(true)
	_hint_button.visible = not bool(config.get("robot", false))
	if bool(config.get("robot", false)):
		_robot_plays(side)
	var got: Array = await _chosen
	_picking_side = ""
	_hint_button.visible = false
	_board.stop_lane_pick()
	for card in _hands[side]:
		card.set_pickable(false)
		card.set_selected(false)
		card.set_hinted(false)
	return got


func _on_card_picked(index: int, side: String) -> void:
	if side != _picking_side:
		return
	_picked = index
	for card in _hands[side]:
		card.set_selected(card.index == index)
	var hint_lane := ""
	if not _hint.is_empty() and int(_hint["index"]) == index:
		hint_lane = str(_hint["lane"])
	_board.start_lane_pick(side, hint_lane)
	_say("Now click the left lane or the right lane on your half of the arena.", _colors[side])


func _on_lane_chosen(lane: String) -> void:
	if _picking_side != "" and _picked >= 0:
		_chosen.emit(_picked, lane)


func _on_hint() -> void:
	if _picking_side == "":
		return
	_hint_button.disabled = true
	var reply: Dictionary = await Bridge.ask(["hint"])
	_hint_button.disabled = false
	if not _alive or _picking_side == "" or not bool(reply.get("ok", false)):
		return
	_hint = reply["hint"]
	for card in _hands[_picking_side]:
		card.set_hinted(card.index == int(_hint["index"]))
	_say("Alpha-beta would play %s in the %s lane." % [str(_hint["card"]), str(UI.LANE_WORD[str(_hint["lane"])])], UI.GOLD)
	if _picked == int(_hint["index"]):
		_board.start_lane_pick(_picking_side, str(_hint["lane"]))


## For demos without a mouse: play whatever alpha-beta suggests.
func _robot_plays(side: String) -> void:
	await _wait(0.6)
	var reply: Dictionary = await Bridge.ask(["hint"])
	if not _alive or _picking_side != side or not bool(reply.get("ok", false)):
		return
	_on_card_picked(int(reply["hint"]["index"]), side)
	await _wait(0.6)
	if _alive and _picking_side == side:
		_on_lane_chosen(str(reply["hint"]["lane"]))


# --------------------------------------------------------------- overlays

func _open_overlay(width: float, height: float) -> Panel:
	_close_overlay()
	_overlay = Control.new()
	_overlay.size = UI.SCREEN
	_overlay.z_index = 50
	var dim := ColorRect.new()
	dim.color = Color(0.03, 0.05, 0.07, 0.72)
	dim.size = UI.SCREEN
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_overlay.add_child(dim)
	var sheet := UI.panel(UI.PANEL, 20, UI.PANEL_LINE, 2)
	sheet.size = Vector2(width, height)
	sheet.position = (UI.SCREEN - sheet.size) / 2.0
	sheet.mouse_filter = Control.MOUSE_FILTER_STOP
	_overlay.add_child(sheet)
	add_child(_overlay)
	UI.pop_in(sheet, 0.22)
	return sheet


func _close_overlay() -> void:
	if _overlay != null:
		_overlay.queue_free()
		_overlay = null


func _overlay_button(sheet: Panel, text: String, answer: String, at: Vector2, width: float, fill: Color = UI.PANEL_LIGHT, ink: Color = UI.WHITE) -> Button:
	var made := UI.button(text, fill, ink, 15)
	made.position = at
	made.size = Vector2(width, 42)
	made.pressed.connect(func() -> void: _overlay_closed.emit(answer))
	sheet.add_child(made)
	return made


func _centered(sheet: Panel, text: String, y: float, text_size: int, color: Color, weight: int = 400) -> Label:
	var made := UI.label(text, text_size, color, weight)
	made.position = Vector2(20, y)
	made.size = Vector2(sheet.size.x - 40, text_size + 10)
	made.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sheet.add_child(made)
	return made


func _wait_overlay(seconds_if_auto: float) -> String:
	if bool(config.get("auto", false)):
		get_tree().create_timer(seconds_if_auto).timeout.connect(func() -> void: _overlay_closed.emit("auto"))
	var answer: String = await _overlay_closed
	_close_overlay()
	return answer


func _intro() -> void:
	var sheet := _open_overlay(860, 500)
	var left: Dictionary = _view["sides"]["left"]
	var right: Dictionary = _view["sides"]["right"]
	_centered(sheet, "%s against %s" % [str(left["short"]), str(right["short"])], 22, 30, UI.WHITE, 800)
	_centered(sheet, "Two legs. Each side plays first once. The side that does more damage to the enemy tower wins.", 66, 14, UI.MUTED)

	for side in ["left", "right"]:
		var info: Dictionary = _view["sides"][side]
		var x := 40.0 if side == "left" else 450.0
		var head := UI.label("%s %s" % [str(info["emoji"]), str(info["short"])], 22, _colors[side], 800)
		head.position = Vector2(x, 106)
		sheet.add_child(head)
		var brain := UI.label(str(info["brain_name"]) if str(info["brain"]) != "human" else "You", 14, UI.WHITE, 800)
		brain.position = Vector2(x + 130, 113)
		sheet.add_child(brain)
		var deck: Array = info["deck"]
		var slots: Array = _view["rules"]["slots"]
		for place in deck.size():
			var card: Dictionary = deck[place]
			var y := 150.0 + place * 44.0
			var row := UI.panel(UI.PANEL_LIGHT, 10)
			row.position = Vector2(x, y)
			row.size = Vector2(370, 38)
			sheet.add_child(row)
			var slot := UI.label(str(slots[place]), 12, UI.MUTED, 400)
			slot.position = Vector2(x + 12, y + 10)
			sheet.add_child(slot)
			var icon := UI.emoji(str(card["icon"]), 20)
			icon.position = Vector2(x + 70, y + 2)
			icon.size = Vector2(34, 34)
			sheet.add_child(icon)
			var title := UI.label(str(card["name"]), 15, UI.WHITE, 800)
			title.position = Vector2(x + 110, y + 8)
			sheet.add_child(title)
			var cost := UI.label("cost %d" % int(card["cost"]), 13, UI.GOLD, 800)
			cost.position = Vector2(x + 300, y + 10)
			sheet.add_child(cost)
		var tried := 0
		var undone := 0
		for entry in info["deck_trace"]:
			if str(entry["step"]) == "try":
				tried += 1
			else:
				undone += 1
		var note := UI.wrapped("Built by CSP backtracking with MRV and LCV: %d choices, %d taken back. Total cost %d (it must be %d or %d)." % [
			tried, undone, int(info["deck_cost"]), int(_view["rules"]["cost_least"]), int(_view["rules"]["cost_limit"])], 370, 12, UI.MUTED)
		note.position = Vector2(x, 330)
		sheet.add_child(note)

	var watching := str(left["brain"]) != "human" and str(right["brain"]) != "human"
	if watching:
		_centered(sheet, "Who do you think will win?", 386, 16, UI.WHITE, 800)
		_overlay_button(sheet, str(left["short"]), "left", Vector2(180, 428), 150, _colors["left"], UI.INK)
		_overlay_button(sheet, "Just watch", "", Vector2(355, 428), 150)
		_overlay_button(sheet, str(right["short"]), "right", Vector2(530, 428), 150, _colors["right"], UI.INK)
	else:
		_centered(sheet, "On your turn, click a card and then a lane. The Hint button asks alpha-beta.", 392, 14, UI.MUTED)
		_overlay_button(sheet, "Start", "", Vector2(355, 428), 150, UI.GOLD, UI.INK)
	var answer := await _wait_overlay(2.6)
	if answer == "left" or answer == "right":
		_bet = answer
	_announce_leg()


func _announce_leg() -> void:
	var first := str(_view["first"])
	_say("Leg %d. %s plays first." % [int(_view["leg"]), str(_view["sides"][first]["short"])], _colors[first])


func _leg_over() -> bool:
	## Returns true if another leg follows.
	_panels["left"].set_active(false)
	_panels["right"].set_active(false)
	var legs: Array = _view["legs"]
	var leg: Dictionary = legs[int(_view["leg"]) - 1]
	await _wait(0.8)
	if not _alive:
		return false
	if bool(_view["match_over"]):
		await _match_over()
		return false

	var sheet := _open_overlay(700, 330)
	Sfx.play("ding")
	_centered(sheet, "Leg %d is over" % int(leg["number"]), 26, 28, UI.WHITE, 800)
	_score_line(sheet, 84, int(leg["damage"]["left"]), int(leg["damage"]["right"]))
	_centered(sheet, "damage done to the enemy tower in this leg", 136, 13, UI.MUTED)
	var point := UI.wrapped(_turning_point_text(leg), 620, 14, UI.WHITE)
	point.position = Vector2(40, 172)
	point.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sheet.add_child(point)
	var next_first := str(legs[int(_view["leg"])]["first"])
	_overlay_button(sheet, "Start leg %d: %s plays first" % [int(_view["leg"]) + 1, str(_view["sides"][next_first]["short"])],
		"", Vector2(200, 262), 300, UI.GOLD, UI.INK)
	await _wait_overlay(3.2)
	if not _alive:
		return false

	var reply: Dictionary = await Bridge.ask(["next"])
	if not _alive:
		return false
	if not bool(reply.get("ok", false)):
		_fail(str(reply.get("error", "The AI did not answer.")))
		return false
	_view = reply["view"]
	_names.clear()
	_board.clear_units()
	_board.reset_towers(_view)
	for side in ["left", "right"]:
		_panels[side].set_tower(int(_view["sides"][side]["tower"]))
		_panels[side].show_idle(str(_view["sides"][side]["brain_blurb"]))
		for card in _hands[side]:
			card.set_used(false)
	_refresh()
	_announce_leg()
	await _wait(0.8)
	return true


func _match_over() -> void:
	var left: Dictionary = _view["sides"]["left"]
	var right: Dictionary = _view["sides"]["right"]
	var winner := str(_view["winner"])
	var sheet := _open_overlay(720, 440)
	var human_side := ""
	for side in ["left", "right"]:
		if str(_view["sides"][side]["brain"]) == "human":
			human_side = side
	Sfx.play("lose" if human_side != "" and winner != human_side and winner != "draw" else "win")

	var headline := "A draw"
	var tint := UI.WHITE
	if winner != "draw":
		headline = "%s wins the match" % str(_view["sides"][winner]["short"])
		tint = _colors[winner]
	_centered(sheet, headline, 26, 32, tint, 800)
	_score_line(sheet, 88, int(_view["damage"]["left"]), int(_view["damage"]["right"]))
	_centered(sheet, "total damage done over two legs", 140, 13, UI.MUTED)

	var y := 178.0
	for leg in _view["legs"]:
		var first := str(_view["sides"][str(leg["first"])]["short"])
		var line := "Leg %d (%s first):  %s %d,  %s %d.  %s" % [int(leg["number"]), first, str(left["short"]), int(leg["damage"]["left"]),
			str(right["short"]), int(leg["damage"]["right"]), _turning_point_text(leg)]
		var row := UI.wrapped(line, 640, 13, UI.MUTED)
		row.position = Vector2(40, y)
		sheet.add_child(row)
		y += 52.0

	var verdict := ""
	if _bet != "":
		verdict = "You called it." if _bet == winner else ("Nobody won, so no call." if winner == "draw" else "You backed the other side.")
	elif human_side != "":
		verdict = "You won." if winner == human_side else ("Level with the machine." if winner == "draw" else "The machine won this one.")
	_centered(sheet, verdict, 300, 18, UI.GOLD, 800)

	_overlay_button(sheet, "Play again", "again", Vector2(60, 366), 190, UI.GOLD, UI.INK)
	_overlay_button(sheet, "Swap the brains", "swap", Vector2(265, 366), 190)
	_overlay_button(sheet, "Menu", "menu", Vector2(470, 366), 190)
	var answer := await _wait_overlay(6.0)
	if _alive:
		_leave("menu" if answer == "auto" else answer)


func _score_line(sheet: Panel, y: float, left_score: int, right_score: int) -> void:
	var left := UI.label("%s  %d" % [str(_view["sides"]["left"]["short"]), left_score], 34, _colors["left"], 800)
	left.position = Vector2(20, y)
	left.size = Vector2(sheet.size.x / 2.0 - 40, 44)
	left.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	sheet.add_child(left)
	var colon := UI.label(":", 34, UI.MUTED, 800)
	colon.position = Vector2(sheet.size.x / 2.0 - 20, y - 2)
	colon.size = Vector2(40, 44)
	colon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sheet.add_child(colon)
	var right := UI.label("%d  %s" % [right_score, str(_view["sides"]["right"]["short"])], 34, _colors["right"], 800)
	right.position = Vector2(sheet.size.x / 2.0 + 20, y)
	right.size = Vector2(sheet.size.x / 2.0 - 40, 44)
	sheet.add_child(right)


func _turning_point_text(leg: Dictionary) -> String:
	var point: Variant = leg.get("turning_point")
	if point == null:
		return "Nobody slipped: every card played was the best one available."
	var who := str(_view["sides"][str(point["side"])]["short"])
	return "Turning point: card %d. %s played %s in the %s lane. %s in the %s lane was %d better." % [
		int(point["play"]), who, str(point["move"]["card"]), str(UI.LANE_WORD[str(point["move"]["lane"])]),
		str(point["best"]["card"]), str(UI.LANE_WORD[str(point["best"]["lane"])]), int(point["lost"])]


func _fail(message: String) -> void:
	_alive = false
	var sheet := _open_overlay(680, 240)
	_centered(sheet, "Something went wrong", 26, 24, UI.RED, 800)
	var words := UI.wrapped(message, 600, 14, UI.WHITE)
	words.position = Vector2(40, 76)
	sheet.add_child(words)
	var back := UI.button("Menu", UI.PANEL_LIGHT, UI.WHITE, 15)
	back.position = Vector2(265, 176)
	back.size = Vector2(150, 42)
	back.pressed.connect(func() -> void: done.emit("menu"))
	sheet.add_child(back)


# ---------------------------------------------------------------- helpers

func _leave(action: String) -> void:
	_alive = false
	done.emit(action)


func _say(text: String, color: Color = UI.MUTED) -> void:
	_talk.text = text
	_talk_dot.add_theme_stylebox_override("panel", UI.box(color, 5))


func _status_text(play: int) -> String:
	var first := str(_view["sides"][str(_view["first"])]["short"])
	return "Leg %d of 2    Card %d of %d    %s plays first" % [int(_view["leg"]), mini(play, int(_view["plays"])), int(_view["plays"]), first]


func _refresh() -> void:
	_status.text = _status_text(int(_view["play"]))
	for side in ["left", "right"]:
		_panels[side].set_tower(int(_view["sides"][side]["tower"]))
	_refresh_damage({"left": int(_view["sides"]["left"]["tower"]), "right": int(_view["sides"]["right"]["tower"])})


## Damage so far: finished legs, plus what the towers have lost in the leg being played.
func _refresh_damage(towers: Dictionary) -> void:
	var full := int(_view["rules"]["tower_health"])
	var done_left := 0
	var done_right := 0
	var legs: Array = _view["legs"]
	for place in legs.size():
		var leg: Dictionary = legs[place]
		if bool(leg["finished"]) and place != int(_view["leg"]) - 1:
			done_left += int(leg["damage"]["left"])
			done_right += int(leg["damage"]["right"])
	_panels["left"].set_damage(done_left + full - int(towers["right"]))
	_panels["right"].set_damage(done_right + full - int(towers["left"]))


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds / _speed).timeout


## Hold here while the match is paused. The Step button lets one beat through.
func _gate() -> void:
	while _alive and _paused and _tokens <= 0:
		await get_tree().process_frame
	if _tokens > 0:
		_tokens -= 1


func _set_speed(value: float) -> void:
	_speed = value
	if _board != null:
		_board.speed = value
	for key in _speed_buttons:
		UI.choice_style(_speed_buttons[key], is_equal_approx(float(key), value), UI.GOLD)


func _toggle_pause() -> void:
	_paused = not _paused
	_tokens = 0
	_pause_button.text = "Resume" if _paused else "Pause"
	_step_button.visible = _paused
