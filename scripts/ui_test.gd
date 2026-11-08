class_name UiTest
extends Node
## A scripted player for checking the screens without a person:
##     godot --path . -- --uitest
## It sends real mouse clicks to the buttons, cards and tiles (the same events a
## mouse makes), looks at the warriors screen and the troop picker, plays a whole
## match as the left side and then a power match, and prints PASS or FAIL for each
## thing it checks.

var _passed := 0
var _failed := 0


func _ready() -> void:
	_run()


func _check(ok: bool, what: String) -> void:
	if ok:
		_passed += 1
		print("UITEST PASS  ", what)
	else:
		_failed += 1
		print("UITEST FAIL  ", what)


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout


## A mouse click at a point on the screen, delivered to the game exactly as a
## mouse would deliver it (it works without a window, too).
func _click(at: Vector2) -> void:
	var move := InputEventMouseMotion.new()
	move.position = at
	move.global_position = at
	get_viewport().push_input(move, true)
	await get_tree().process_frame
	for down in [true, false]:
		var press := InputEventMouseButton.new()
		press.button_index = MOUSE_BUTTON_LEFT
		press.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
		press.pressed = down
		press.position = at
		press.global_position = at
		get_viewport().push_input(press, true)
		await get_tree().process_frame


func _centre(node: Control) -> Vector2:
	return node.get_global_rect().get_center()


func _find(type_name: String, from: Node = null) -> Array:
	var found: Array = []
	var start: Node = from if from != null else get_tree().root
	for child in start.get_children():
		if child.is_class(type_name) or (child.get_script() != null and child.get_script().get_global_name() == type_name):
			found.append(child)
		found.append_array(_find(type_name, child))
	return found


## The button with this text. The one made last is on top: an overlay's Menu, not the top bar's.
func _button(text: String) -> Button:
	var found: Button = null
	for made in _find("Button"):
		var button := made as Button
		if button.text == text and button.is_visible_in_tree() and not button.disabled:
			found = button
	return found


## The "You" button of the left side, which is made before the right side's.
func _you_on_the_left() -> Button:
	for made in _find("Button"):
		if (made as Button).text == "You" and (made as Button).is_visible_in_tree():
			return made
	return null


func _match() -> MatchScreen:
	var screens := _find("MatchScreen")
	return screens[0] if not screens.is_empty() else null


## Wait until `test` is true, up to `limit` seconds.
func _until(test: Callable, limit: float) -> bool:
	var waited := 0.0
	while waited < limit:
		if test.call():
			return true
		await _wait(0.1)
		waited += 0.1
	return false


func _tile_point(screen: MatchScreen, tile: Array) -> Vector2:
	return screen._board.get_global_transform() * screen._board.tile_centre(tile)


func _labels_with(words: String) -> int:
	var count := 0
	for made in _find("Label"):
		if (made as Label).is_visible_in_tree() and (made as Label).text.contains(words):
			count += 1
	return count


func _check_home_pages() -> void:
	await _click(_centre(_button("How the AI works")))
	await _wait(0.3)
	_check(_labels_with("Monte Carlo Tree Search") == 1, "How the AI works lists the algorithms")
	_check(_labels_with("Lab 0") == 0, "How the AI works shows no lab numbers")
	await _click(_centre(_button("Back")))
	await _wait(0.2)

	await _click(_centre(_button("Meet the warriors")))
	await _wait(0.3)
	var cards := _find("WarriorCard")
	_check(cards.size() == 8, "the warriors screen shows eight warriors")
	_check(_labels_with("Hover") >= 1 and _labels_with("Health") == 8, "each warrior shows its numbers and its special")
	var first_name := str(cards[0].card["name"])
	await _click(_centre(_button("CE")))
	await _wait(0.3)
	var after: Array = []
	for card in _find("WarriorCard"):
		if not card.is_queued_for_deletion():
			after.append(card)
	_check(after.size() == 8 and str(after[0].card["name"]) != first_name, "a department tab shows that department's warriors")
	await _click(_centre(_button("Back")))
	await _wait(0.3)
	_check(_find("RosterScreen").is_empty(), "Back closes the warriors screen")


func _check_picker() -> void:
	var picker: PickerScreen = _find("PickerScreen")[0]
	_check(_button("Use these four") == null, "a person cannot start before picking")
	var others: Array = []
	for card in _find("WarriorCard"):
		if str(card.card["role"]) != "Tank":
			others.append(card)
	for place in 4:
		await _click(_centre(others[place]))
	await _wait(0.1)
	_check(picker._picks.size() == 4, "clicking warriors picks them")
	_check(_button("Use these four") == null and picker._message.text.contains("Tank"), "a deck with no Tank is refused, and says why")
	await _click(_centre(others[4]))
	await _wait(0.1)
	_check(picker._picks.size() == 4, "a fifth warrior cannot be added")
	await _click(_centre(_button("Let CSP choose")))
	_check(await _until(func() -> bool: return _button("Use these four") != null, 10.0), "Let CSP choose gives a legal deck")
	_check(picker._cost() >= int(picker.rules["cost_least"]) and picker._cost() <= int(picker.rules["cost_limit"]), "the cost of the deck is inside the limits")
	await _click(_centre(_button("Use these four")))


func _check_intro() -> void:
	var intros := _find("IntroScreen")
	_check(not intros.is_empty(), "the game opens with the film")
	if intros.is_empty():
		return
	_check(_find("MenuScreen").is_empty(), "the menu waits behind the film")
	_check(not _find("VideoStreamPlayer").is_empty() and (_find("VideoStreamPlayer")[0] as VideoStreamPlayer).is_playing(), "the film is playing")
	var skip := _button("Skip")
	_check(skip != null, "the film has a Skip button")
	if skip != null:
		await _click(_centre(skip))
	_check(await _until(func() -> bool: return _find("IntroScreen").is_empty() and not _find("MenuScreen").is_empty(), 5.0), "Skip goes on to the menu")


func _run() -> void:
	await _wait(1.5)
	await _check_intro()
	await _wait(0.5)
	await _check_home_pages()
	# The menu: choose "You" for the left side, then start.
	var mine := _you_on_the_left()
	_check(mine != null, "the menu offers You as a brain")
	if mine == null:
		return _finish()
	await _click(_centre(mine))
	await _wait(0.3)
	var start := _button("Start the match")
	_check(start != null, "the menu has a Start button")
	await _click(_centre(start))
	_check(await _until(func() -> bool: return not _find("PickerScreen").is_empty(), 10.0), "a person gets the troop picker first")
	await _wait(0.3)
	await _check_picker()
	_check(await _until(func() -> bool: return _button("Start") != null, 30.0), "the intro sheet appears with a Start button")
	await _wait(0.6)                         # let the sheet finish popping in
	await _click(_centre(_button("Start")))

	var screen := _match()
	_check(screen != null, "the match screen is open")
	var turns := 0
	var tried_hint := false
	var tried_pause := false
	var tried_tree := false
	while screen != null and is_instance_valid(screen):
		var my_turn := await _until(func() -> bool: return screen._picking_side == "left" or _button("Start leg 2: ME plays first") != null or _button("Play again") != null, 40.0)
		if not my_turn:
			_check(false, "the game waits for the left side or ends")
			break
		var next_leg := _button("Start leg 2: ME plays first")
		if next_leg != null:
			_check(true, "leg 1 ends with its result sheet")
			await _wait(0.6)
			await _click(_centre(next_leg))
			await _wait(1.0)
			continue
		if _button("Play again") != null:
			_check(true, "the match ends with the final sheet")
			await _wait(3.0)                     # leave the final sheet up for a moment, for recordings
			break

		var hand: Array = screen._hands["left"]
		var card: CardView = null
		if not tried_hint:
			# Ask for a hint, then play exactly what it says.
			tried_hint = true
			await _click(_centre(screen._hint_button))
			var hinted := await _until(func() -> bool: return not screen._hint.is_empty(), 10.0)
			_check(hinted, "the Hint button gets alpha-beta's suggestion")
			_check(screen._talk.text.begins_with("Alpha-beta would play"), "the hint is said in the message strip")
			for entry in hand:
				if entry.index == int(screen._hint.get("index", -1)):
					card = entry
		if card == null:
			for entry in hand:
				if not entry.used:
					card = entry
					break
		var unused_before := 0
		for entry in hand:
			unused_before += 0 if entry.used else 1
		await _click(_centre(card))
		await _wait(0.2)
		_check(screen._picked == card.index, "clicking a card selects it")
		var drops: Array = screen._view["sides"]["left"]["drops"]
		var spot: int = drops.size() - 1 - turns          # tiles well away from the lanes
		if not screen._hint.is_empty() and int(screen._hint["index"]) == card.index:
			spot = int(screen._hint["spot"])
		await _click(_tile_point(screen, drops[spot]))
		var played := await _until(func() -> bool: return card.used, 15.0)
		_check(played, "clicking a tile plays the card (turn %d, tile %s)" % [turns + 1, str(drops[spot])])
		turns += 1

		if played and not tried_tree and _button("Show the tree") != null:
			# Open the other side's decision as a tree, then go back to the match.
			tried_tree = true
			await _wait(0.3)
			await _click(_centre(_button("Show the tree")))
			await _wait(0.8)
			_check(not _find("SearchView").is_empty(), "Show the tree opens the decision as a tree")
			_check(screen._paused, "the match waits while the tree is open")
			await _wait(1.0)
			await _click(_centre(_button("Back to the match")))
			await _wait(0.4)
			_check(_find("SearchView").is_empty() and not screen._paused, "Back to the match closes it and carries on")

		if not tried_pause and played:
			# Pause while the battle plays out, and check that Step moves it on by one beat.
			tried_pause = true
			await _wait(0.4)
			await _click(_centre(_button("Pause")))
			await _wait(5.0)                     # the battle step under way finishes; nothing after it starts
			_check(screen._paused, "Pause stops the match")
			var step := _button("Step")
			_check(step != null, "a Step button appears while paused")
			var before: String = screen._talk.text
			await _wait(1.5)
			var still: bool = screen._talk.text == before
			_check(still, "nothing moves on while paused")
			if step != null:
				await _click(_centre(step))
				await _wait(1.0)
			await _click(_centre(_button("Resume")))
			await _wait(0.2)
			_check(not screen._paused, "Resume carries on")
			await _click(_centre(_button("4x")))
			_check(is_equal_approx(screen._speed, 4.0), "the 4x button speeds the match up")
	_check(turns == 8, "the left side played all eight of its cards over two legs (%d)" % turns)
	await _click(_centre(_button("Menu")))
	await _check_power()
	_finish()


func _check_power() -> void:
	_check(await _until(func() -> bool: return _button("Power: one minute") != null, 10.0), "the menu offers power mode")
	await _wait(0.3)
	await _click(_centre(_button("Power: one minute")))
	await _wait(0.2)
	await _click(_centre(_you_on_the_left()))
	await _wait(0.2)
	await _click(_centre(_button("Start the match")))
	_check(await _until(func() -> bool: return _button("Start") != null, 15.0), "power mode goes straight to its intro sheet")
	await _wait(0.6)
	await _click(_centre(_button("Start")))
	var screens := _find("PowerScreen")
	_check(not screens.is_empty(), "the power screen is open")
	if screens.is_empty():
		return
	var screen: PowerScreen = screens[0]
	await _wait(2.0)
	_check(screen._status.text.begins_with("0:5"), "the clock runs down from one minute (%s)" % screen._status.text)
	var drops := 0
	var cycled := false
	var hand_before: Array = []
	for card in screen._hands["left"]:
		hand_before.append(card.index)
	var waited := 0.0
	while waited < 120.0 and is_instance_valid(screen) and _button("Play again") == null:
		var payable: CardView = null
		for card in screen._hands["left"]:
			if card._pickable:
				payable = card
				break
		if payable != null:
			var coins_before := int(screen._view["sides"]["left"]["coins"]) - screen._spending("left")
			await _click(_centre(payable))
			if screen._picked != payable.index:
				continue
			var tiles: Array = screen._view["sides"]["left"]["drops"]
			await _click(_tile_point(screen, tiles[drops % tiles.size()]))
			if drops == 0:
				_check(int(screen._view["sides"]["left"]["coins"]) - screen._spending("left") == coins_before - payable.cost, "a drop takes its coins at once")
				_check(not screen._board._ghosts.is_empty(), "a ring marks where the drop will land")
				await _click(_centre(_button("4x")))
			drops += 1
		for card in screen._hands["left"]:
			if not hand_before.has(card.index):
				cycled = true
		await _wait(0.2)
		waited += 0.2
	_check(drops >= 5, "a person can keep dropping warriors (%d)" % drops)
	_check(cycled, "a played card is replaced by the next one")
	_check(_button("Play again") != null, "the power match ends with its final sheet")
	var towers: Array = [int(screen._view["sides"]["left"]["tower"]), int(screen._view["sides"]["right"]["tower"])]
	_check(int(screen._view["seconds_left"]) == 0 or towers.min() <= 0, "it ended on the clock or with a fallen tower")
	await _wait(2.0)


func _finish() -> void:
	print("UITEST DONE  %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(0 if _failed == 0 else 1)
