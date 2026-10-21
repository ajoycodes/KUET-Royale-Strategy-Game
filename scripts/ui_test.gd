class_name UiTest
extends Node
## A scripted player for checking the screens without a person:
##     godot --path . -- --uitest
## It sends real mouse clicks to the buttons, cards and lanes (the same events a
## mouse makes), plays a whole match as the left side, and prints PASS or FAIL
## for each thing it checks.

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


func _button(text: String) -> Button:
	for made in _find("Button"):
		var button := made as Button
		if button.text == text and button.is_visible_in_tree() and not button.disabled:
			return button
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


func _run() -> void:
	await _wait(1.5)
	# The menu: choose "You" for the left side, then start.
	var mine := _button("You")
	_check(mine != null, "the menu offers You as a brain")
	if mine == null:
		return _finish()
	await _click(_centre(mine))
	await _wait(0.3)
	var start := _button("Start the match")
	_check(start != null, "the menu has a Start button")
	await _click(_centre(start))
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
		var lane := "top"
		if not screen._hint.is_empty() and int(screen._hint["index"]) == card.index:
			lane = str(screen._hint["lane"])
		var area: Rect2 = screen._board._lane_rect("left", lane)
		await _click(screen._board.get_global_transform() * area.get_center())
		var played := await _until(func() -> bool: return card.used, 15.0)
		_check(played, "clicking a lane plays the card (turn %d)" % (turns + 1))
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
	_finish()


func _finish() -> void:
	print("UITEST DONE  %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(0 if _failed == 0 else 1)
