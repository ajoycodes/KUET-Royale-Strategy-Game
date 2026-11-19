class_name PowerScreen
extends MatchScreen
## Power mode on screen: one minute, no turns, coins for drops. Python plays one
## beat at a time. The next beat is asked for as soon as the last one starts to
## play, so that the clock keeps running while a brain thinks.

var _beat_length := 0.6
var _next_reply := {}
var _asking := false
var _queued := {"left": [], "right": []}     # a person's drops, waiting for the next beat to carry them
var _flights: Array = []                     # for each beat asked for and not yet shown, the drops it carries


func _begin() -> void:
	var arguments: Array = ["power_new", "--left", config["left"], "--right", config["right"],
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
	_beat_length = float(_view["beat_seconds"])
	_build_match()
	await _intro()
	if _alive:
		_run()


func _build_match() -> void:
	_board = BoardView.new()
	_board.position = BOARD_AT
	_board.setup(_view, _colors)
	_board.speed = _speed
	_board.tile_chosen.connect(_on_tile_chosen)
	add_child(_board)
	move_child(_board, 0)
	_status.add_theme_font_size_override("font_size", 24)
	_status.position.y = 4
	_status.size.y = 32

	for side in ["left", "right"]:
		var panel := ThinkingPanel.new()
		panel.position = PANEL_AT[side]
		panel.coins_mode = true
		panel.damage_note = "this minute"
		panel.setup(_view["sides"][side], side, _colors[side])
		panel.look.connect(_open_search.bind(side))
		add_child(panel)
		_panels[side] = panel
		for place in int(_view["sides"][side]["hand"].size()):
			_hands[side].append(_new_card(side, place, _view["sides"][side]["hand"][place]))
	_refresh_power()


func _new_card(side: String, place: int, card: Dictionary) -> CardView:
	var made := CardView.new()
	made.position = _panels[side].position + _panels[side].card_spot(place)
	made.setup(card, _colors[side])
	made.picked.connect(_on_card_picked.bind(side))
	add_child(made)
	return made


# ---------------------------------------------------------------- the loop

func _run() -> void:
	_ask_next()
	while _alive:
		while _alive and (_asking or (_paused and _tokens <= 0)):
			await get_tree().process_frame
		if not _alive:
			return
		if _tokens > 0:
			_tokens -= 1
		var reply := _next_reply
		_next_reply = {}
		if bool(reply.get("timeout", false)):
			var lost: Dictionary = _flights.pop_front()
			for side in lost:
				_board.clear_ghost(lost[side]["tile"])
			_refresh_power()
			_say("The AI was slow to answer. Carrying on.", UI.GOLD)
			_ask_next()
			continue
		if not bool(reply.get("ok", false)):
			_fail(str(reply.get("error", "The AI did not answer.")))
			return
		var over := bool(reply["view"]["over"])
		if not over:
			_ask_next()
		await _show_beat(reply)
		if not _alive:
			return
		if over:
			await _final_sheet()
			return


func _ask_next() -> void:
	var arguments: Array = ["power_beat"]
	var carried := {}
	for side in ["left", "right"]:
		if not _queued[side].is_empty():
			var drop: Dictionary = _queued[side].pop_front()
			arguments.append_array(["--drop", "%s:%d:%d" % [side, int(drop["card"]), int(drop["spot"])]])
			carried[side] = drop
	_flights.append(carried)
	_asking = true
	var reply: Dictionary = await Bridge.ask(arguments)
	_asking = false
	_next_reply = reply


func _show_beat(reply: Dictionary) -> void:
	var length := _beat_length / _speed
	var carried: Dictionary = _flights[0]        # it stays on the list until _view has charged its coins, below
	for side in carried:
		_board.clear_ghost(carried[side]["tile"])
	if not (reply["refused"] as Array).is_empty():
		_say("That drop could not be paid for.", UI.RED)
	var dropped := PackedStringArray()
	for unit in reply["deployed"]:
		_names[int(unit["unit"])] = str(unit["card"])
		_board.add_unit(unit)
		Sfx.play("deploy")
		var side := str(unit["side"])
		var short := str(_view["sides"][side]["short"])
		if (reply["deployed"] as Array).size() == 2:
			dropped.append("%s drops %s." % [short, str(unit["card"])])     # two whole sentences would not fit the strip
		else:
			dropped.append("%s drops %s in the %s." % [short, str(unit["card"]), UI.lane_words(str(unit["move"]["where"]))])
	if not dropped.is_empty():
		_say(" ".join(dropped), _colors[str(reply["deployed"][-1]["side"])])
	for side in reply["thinking"]:
		var thinking: Dictionary = reply["thinking"][side]
		if str(thinking["choices"][0]["card"]) != "Hold on":
			_panels[side].show_thinking(thinking)

	var step: Dictionary = reply["step"]
	for search in step["searches"]:
		_board.route_line(search["route"], UI.SEARCH_COLOR[str(search["route_search"])], 0.9 / _speed)
	# A walk must be over before the next beat starts.
	var farthest := 2
	for move in step["moves"]:
		farthest = maxi(farthest, (move["path"] as Array).size())
	_act(step, minf(0.17 / _speed, length * 0.5 / float(farthest - 1)), length * 0.4)
	await get_tree().create_timer(length * 0.5).timeout
	if not _alive:
		return
	_land(step)
	_flights.pop_front()
	_view = reply["view"]
	_refresh_power()
	await get_tree().create_timer(length * 0.5).timeout
	if _alive and bool(config.get("robot", false)):
		_robot_drops()


# ---------------------------------------------------------- a person's drops

func _is_person(side: String) -> bool:
	return str(_view["sides"][side]["brain"]) == "human"


## What a side has spent that the last beat shown does not yet know about.
func _spending(side: String) -> int:
	var total := 0
	for drop in _queued[side]:
		total += int(drop["cost"])
	for carried in _flights:
		if carried.has(side):
			total += int(carried[side]["cost"])
	return total


func _on_its_way(side: String, index: int) -> bool:
	for drop in _queued[side]:
		if int(drop["card"]) == index:
			return true
	for carried in _flights:
		if carried.has(side) and int(carried[side]["card"]) == index:
			return true
	return false


func _on_card_picked(index: int, side: String) -> void:
	if not _is_person(side):
		return
	if _picked == index and _picking_side == side:
		_stop_picking()
		return
	_stop_picking()
	_picked = index
	_picking_side = side
	for card in _hands[side]:
		card.set_selected(card.index == index)
	_board.start_tile_pick(_view["sides"][side]["drops"])
	_say("Now click any glowing tile on your half of the arena.", _colors[side])


func _on_tile_chosen(spot: int) -> void:
	if _picking_side == "" or _picked < 0:
		return
	var side := _picking_side
	var coins: int = int(_view["sides"][side]["coins"]) - _spending(side)
	for card in _hands[side]:
		if card.index == _picked:
			if card.cost > coins:
				_say("Not enough coins for that yet.", UI.RED)
				return
			var tile: Array = _view["sides"][side]["drops"][spot]
			_queued[side].append({"card": _picked, "spot": spot, "cost": card.cost, "tile": tile})
			_board.add_ghost(tile, _colors[side])
	_stop_picking()
	_refresh_power()


func _stop_picking() -> void:
	if _picking_side != "":
		for card in _hands[_picking_side]:
			card.set_selected(false)
	_picked = -1
	_picking_side = ""
	_board.stop_tile_pick()


## For demos without a mouse: drop whatever can be paid for, on a random tile of its half.
func _robot_drops() -> void:
	for side in ["left", "right"]:
		if not _is_person(side) or not _queued[side].is_empty():
			continue
		var coins: int = int(_view["sides"][side]["coins"]) - _spending(side)
		for card in _hands[side]:
			if card.cost <= coins and not _on_its_way(side, card.index):
				_on_card_picked(card.index, side)
				_on_tile_chosen(randi_range(0, (_view["sides"][side]["drops"] as Array).size() - 1))
				return


# ---------------------------------------------------------------- showing it

func _refresh_power() -> void:
	var seconds := int(_view["seconds_left"])
	_status.text = "%d:%02d" % [seconds / 60, seconds % 60]
	_status.add_theme_color_override("font_color", UI.RED if seconds <= 10 else UI.WHITE)
	var rules: Dictionary = _view["rules"]
	for side in ["left", "right"]:
		var info: Dictionary = _view["sides"][side]
		_panels[side].set_tower(int(info["tower"]))
		_refresh_hand(side, info)
		var coins := int(info["coins"]) - _spending(side)
		var coming := float(int(_view["beat"]) % int(rules["coin_every"])) / float(rules["coin_every"])
		_panels[side].set_coins(float(coins) + (0.0 if coins >= int(rules["coins_most"]) else coming), int(rules["coins_most"]), str(info["next"]))
	_refresh_damage({})


func _refresh_damage(_towers: Dictionary) -> void:
	_panels["left"].set_damage(int(_view["damage"]["left"]))
	_panels["right"].set_damage(int(_view["damage"]["right"]))


## A played card is gone from the hand: the new one takes its place on the tray.
func _refresh_hand(side: String, info: Dictionary) -> void:
	var coming := {}
	for card in info["hand"]:
		coming[int(card["index"])] = card
	for card in _hands[side]:
		coming.erase(card.index)
	var indexes := []
	for card in info["hand"]:
		indexes.append(int(card["index"]))
	for place in _hands[side].size():
		var shown: CardView = _hands[side][place]
		if not indexes.has(shown.index) and not coming.is_empty():
			var key: int = coming.keys()[0]
			var fresh := _new_card(side, place, coming[key])
			coming.erase(key)
			shown.queue_free()
			_hands[side][place] = fresh
			UI.pop_in(fresh, 0.2)
	var coins := int(info["coins"]) - _spending(side)
	var person := _is_person(side)
	for card in _hands[side]:
		var waiting := _on_its_way(side, card.index)
		var payable: bool = card.cost <= coins and not waiting
		card.set_dim(not payable)
		card.set_pickable(person and payable)
	# A card that was selected can stop being payable when another drop was made first.
	if _picking_side == side:
		var still := false
		for card in _hands[side]:
			still = still or (card.index == _picked and card.cost <= coins)
		if not still:
			_stop_picking()


# ---------------------------------------------------------------- the sheets

func _intro() -> void:
	var sheet := _open_overlay(760, 420)
	var left: Dictionary = _view["sides"]["left"]
	var right: Dictionary = _view["sides"]["right"]
	_centered(sheet, "%s against %s" % [str(left["short"]), str(right["short"])], 22, 30, UI.WHITE, 800)
	_centered(sheet, "Power mode: one minute, no turns", 66, 16, UI.GOLD, 800)
	var rules: Dictionary = _view["rules"]
	var lines := [
		"You hold four of your eight warriors. Play one and the next comes in.",
		"A warrior costs coins. You start with %d and earn one every %.1f seconds, up to %d." % [int(left["coins"]), float(rules["coin_every"]) * _beat_length, int(rules["coins_most"])],
		"Click a card, then any tile on your half. Drop as fast as you can pay.",
		"A fallen tower ends it at once. If not, the most damage wins when the clock stops.",
	]
	var y := 112.0
	for line in lines:
		var row := UI.wrapped(str(line), 660, 15, UI.WHITE)
		row.position = Vector2(50, y)
		sheet.add_child(row)
		y += 38.0
	var watching := not _is_person("left") and not _is_person("right")
	if watching:
		_centered(sheet, "Who do you think will win?", 280, 16, UI.WHITE, 800)
		_overlay_button(sheet, str(left["short"]), "left", Vector2(130, 330), 150, _colors["left"], UI.INK)
		_overlay_button(sheet, "Just watch", "", Vector2(305, 330), 150)
		_overlay_button(sheet, str(right["short"]), "right", Vector2(480, 330), 150, _colors["right"], UI.INK)
	else:
		_overlay_button(sheet, "Start", "", Vector2(305, 330), 150, UI.GOLD, UI.INK)
	var answer := await _wait_overlay(2.6)
	if answer == "left" or answer == "right":
		_bet = answer
	_say("Go!", UI.GOLD)


func _final_sheet() -> void:
	_stop_picking()
	await get_tree().create_timer(0.6).timeout
	if not _alive:
		return
	var winner := str(_view["winner"])
	var person := ""
	for side in ["left", "right"]:
		if _is_person(side):
			person = side
	if _is_person("left") and _is_person("right"):
		person = ""                             # two people: no machine to win or lose to
	var sheet := _open_overlay(720, 470)
	Sfx.play("lose" if person != "" and winner != person and winner != "draw" else "win")
	var headline := "A draw"
	var tint := UI.WHITE
	if winner != "draw":
		headline = "%s wins" % str(_view["sides"][winner]["short"])
		tint = _colors[winner]
	_centered(sheet, headline, 26, 32, tint, 800)
	_score_line(sheet, 84, int(_view["damage"]["left"]), int(_view["damage"]["right"]))
	var fallen := int(_view["sides"]["left"]["tower"]) <= 0 or int(_view["sides"]["right"]["tower"]) <= 0
	_centered(sheet, "damage done. A tower fell with %d seconds left." % int(_view["seconds_left"]) if fallen else "damage done in one minute", 134, 13, UI.MUTED)
	if winner != "draw":
		var cheer := MatchScreen.Cheer.new()
		cheer.position = Vector2(30, 170)
		cheer.size = Vector2(660, 130)
		for card in _view["sides"][winner]["hand"]:
			cheer.cards.append(str(card["name"]))
		cheer.color = _colors[winner]
		sheet.add_child(cheer)
	var verdict := ""
	if _bet != "":
		verdict = "You called it." if _bet == winner else ("Nobody won, so no call." if winner == "draw" else "You backed the other side.")
	elif person != "":
		verdict = "You won." if winner == person else ("Level with the machine." if winner == "draw" else "The machine won this one.")
	_centered(sheet, verdict, 320, 18, UI.GOLD, 800)
	_overlay_button(sheet, "Play again", "again", Vector2(60, 390), 190, UI.GOLD, UI.INK)
	_overlay_button(sheet, "Swap the brains", "swap", Vector2(265, 390), 190)
	_overlay_button(sheet, "Menu", "menu", Vector2(470, 390), 190)
	var answer := await _wait_overlay(6.0)
	if _alive:
		_leave("menu" if answer == "auto" else answer)
