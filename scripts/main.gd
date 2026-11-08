extends Control
## Plays the opening film, then switches between the menu and a match.
##
## Started with none of the flags below, the game opens with the film.
## For demos without a mouse:
##     godot --path . -- --watch              straight into alpha-beta against MCTS, overlays close themselves
##     godot --path . -- --watch --speed 4    the same, faster
##     godot --path . -- --play               a "person" on the left who plays whatever alpha-beta suggests
##     godot --path . -- --watch --power      a one-minute power match between the two brains (--play --power: with a "person" on the left)
##     godot --path . -- --menu               straight to the menu, without the film
##     godot --path . -- --how                the menu with the "How the AI works" page open
##     godot --path . -- --warriors           the warriors screen (--warriors eee: open at that department)
##     godot --path . -- --picker             the troop picker for CSE
##     godot --path . -- --gallery            a sheet of the unit figures
##     godot --path . -- --uitest             a scripted player clicks through a whole match and prints PASS or FAIL
##     godot --path . -- --seed 7             with --watch or --play: always the same match
##     godot --path . -- --watch --left eee --right ce      pick the departments
##     godot --path . -- --watch --tour       also open each brain's decision tree once, by itself

var _menu: MenuScreen
var _match: MatchScreen
var _config := {}
var _departments: Array = []
var _brains := {}
var _power_blurbs := {}
var _rules := {}
var _picker: PickerScreen


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var arguments := OS.get_cmdline_user_args()
	var waiting := UI.label("Opening the arena...", 22, UI.MUTED, 800)
	waiting.size = UI.SCREEN
	waiting.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	waiting.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(waiting)
	var intro: IntroScreen = null
	if arguments.is_empty() or arguments.has("--uitest"):
		intro = IntroScreen.new()
		add_child(intro)
	var problem := ""
	var reply: Dictionary = await Bridge.ask(["departments"])
	waiting.queue_free()
	if bool(reply.get("ok", false)):
		_departments = reply["departments"]
		_brains = reply["brains"]
		_power_blurbs = reply["power_blurbs"]
		_rules = reply["deck_rules"]
	else:
		problem = str(reply.get("error", "The AI did not answer."))

	var demo := {}
	if problem == "" and _departments.size() >= 1:
		var left := str(_departments[0]["id"])
		var right := str(_departments[mini(1, _departments.size() - 1)]["id"])
		for entry in _departments:
			if str(entry["id"]) == "me":
				right = "me"
		if arguments.has("--watch"):
			demo = {"left": left, "right": right, "left_brain": "alphabeta", "right_brain": "mcts", "auto": true}
		elif arguments.has("--play"):
			demo = {"left": left, "right": right, "left_brain": "human", "right_brain": "alphabeta", "auto": true, "robot": true}
	if arguments.has("--gallery"):
		add_child(GalleryScreen.new())
		return
	if arguments.has("--uitest"):
		add_child(UiTest.new())
	if intro != null and not intro.over:
		await intro.finished
	if not demo.is_empty():
		var at := arguments.find("--speed")
		if at >= 0 and at + 1 < arguments.size():
			demo["speed"] = float(arguments[at + 1])
		at = arguments.find("--seed")
		if at >= 0 and at + 1 < arguments.size():
			demo["seed"] = int(arguments[at + 1])
		for key in ["left", "right"]:
			at = arguments.find("--" + key)
			if at >= 0 and at + 1 < arguments.size():
				demo[key] = arguments[at + 1]
		demo["tour"] = arguments.has("--tour")
		if arguments.has("--power"):
			demo["mode"] = "power"
		_start(demo)
	else:
		_show_menu(problem, arguments.has("--how"))
		if arguments.has("--warriors"):
			var open_at := arguments.find("--warriors") + 1
			_menu.call_deferred("show_roster", arguments[open_at] if open_at < arguments.size() else "")
		elif arguments.has("--picker"):
			_config = {"left": str(_departments[0]["id"]), "right": str(_departments[1]["id"]), "left_brain": "human", "right_brain": "mcts"}
			_menu.hide()
			_show_picker("left")


func _show_menu(problem: String = "", how: bool = false) -> void:
	_menu = MenuScreen.new()
	_menu.departments = _departments
	_menu.brains = _brains
	_menu.power_blurbs = _power_blurbs
	_menu.rules = _rules
	_menu.problem = problem
	_menu.open_how = how
	_menu.start.connect(_on_menu_start)
	add_child(_menu)


func _on_menu_start(config: Dictionary) -> void:
	_menu.hide()
	_route(config)


## A person in a classic match first picks their own four warriors. Power mode plays all eight.
func _route(config: Dictionary) -> void:
	_config = config
	if str(config.get("mode", "classic")) == "classic":
		for side in ["left", "right"]:
			if str(config[side + "_brain"]) == "human" and not config.has(side + "_deck"):
				_show_picker(side)
				return
	_start(config)


func _show_picker(side: String) -> void:
	for entry in _departments:
		if str(entry["id"]) == str(_config[side]):
			_picker = PickerScreen.new()
			_picker.info = entry
	_picker.rules = _rules
	_picker.seat = str(UI.SEAT_WORD[side]).to_lower()
	_picker.chosen.connect(func(names: Array) -> void:
		_config[side + "_deck"] = names
		_close_picker()
		_route(_config)
	)
	_picker.cancelled.connect(func() -> void:
		_close_picker()
		if _menu == null:
			_show_menu()
		_menu.show()
	)
	add_child(_picker)


func _close_picker() -> void:
	_picker.queue_free()
	_picker = null


func _start(config: Dictionary) -> void:
	_config = config
	if _menu != null:
		_menu.queue_free()
		_menu = null
	_match = PowerScreen.new() if str(config.get("mode", "classic")) == "power" else MatchScreen.new()
	_match.config = config
	_match.done.connect(_on_match_done)
	add_child(_match)


func _on_match_done(action: String) -> void:
	var old := _match
	_match = null
	old.hide()
	get_tree().create_timer(3.0).timeout.connect(old.queue_free)   # let its last animations finish quietly
	var next := _config.duplicate()
	next.erase("seed")
	match action:
		"again":
			_start(next)
		"swap":
			next["left_brain"] = _config["right_brain"]
			next["right_brain"] = _config["left_brain"]
			next.erase("left_deck")           # each deck was picked for its department by the person who was there
			next.erase("right_deck")
			_route(next)
		_:
			_show_menu()
