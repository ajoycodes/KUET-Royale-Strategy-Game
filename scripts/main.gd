extends Control
## Switches between the menu and a match.
##
## For demos without a mouse:
##     godot --path . -- --watch              straight into alpha-beta against MCTS, overlays close themselves
##     godot --path . -- --watch --speed 4    the same, faster
##     godot --path . -- --play               a "person" on the left who plays whatever alpha-beta suggests
##     godot --path . -- --how                the menu with the "How the AI works" page open
##     godot --path . -- --gallery            a sheet of the unit figures
##     godot --path . -- --uitest             a scripted player clicks through a whole match and prints PASS or FAIL
##     godot --path . -- --seed 7             with --watch or --play: always the same match
##     godot --path . -- --watch --left eee --right ce      pick the departments

var _menu: MenuScreen
var _match: MatchScreen
var _config := {}
var _departments: Array = []
var _brains := {}


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var waiting := UI.label("Opening the arena...", 22, UI.MUTED, 800)
	waiting.size = UI.SCREEN
	waiting.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	waiting.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(waiting)
	var problem := ""
	var reply: Dictionary = await Bridge.ask(["departments"])
	waiting.queue_free()
	if bool(reply.get("ok", false)):
		_departments = reply["departments"]
		_brains = reply["brains"]
	else:
		problem = str(reply.get("error", "The AI did not answer."))

	var arguments := OS.get_cmdline_user_args()
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
		_start(demo)
	else:
		_show_menu(problem, arguments.has("--how"))


func _show_menu(problem: String = "", how: bool = false) -> void:
	_menu = MenuScreen.new()
	_menu.departments = _departments
	_menu.brains = _brains
	_menu.problem = problem
	_menu.open_how = how
	_menu.start.connect(_on_menu_start)
	add_child(_menu)


func _on_menu_start(config: Dictionary) -> void:
	_menu.queue_free()
	_menu = null
	_start(config)


func _start(config: Dictionary) -> void:
	_config = config
	_match = MatchScreen.new()
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
			_start(next)
		_:
			_show_menu()
