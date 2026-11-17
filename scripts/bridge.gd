extends Node
## The link to the Python side. Every question is answered by running
## ai/bridge.py once, on a background thread so the screen keeps moving.
##
##     var reply: Dictionary = await Bridge.ask(["step", "--card", "3", "--spot", "7"])

signal answered(id: int, reply: Dictionary)

const PATIENCE_MSEC := 15000         # a call normally answers within two seconds

var python := ""
var problem := ""
var _bridge := ""
var _session := ""
var _next_id := 0
var _threads := {}
var _started := {}                   # id -> when the call began, for calls still waiting
var _given_up := {}                  # ids whose thread never came back
var _matches := 0


func _ready() -> void:
	_bridge = ProjectSettings.globalize_path("res://ai/bridge.py")
	_session = _session_path(0)
	python = _find_python()
	if python == "":
		problem = "Python 3 was not found. Install it from python.org, or set the KUET_ROYALE_PYTHON environment variable to its full path."
	elif not FileAccess.file_exists(_bridge):
		problem = "The AI folder is missing. Expected to find: " + _bridge


func _find_python() -> String:
	var candidates: Array[String] = []
	var chosen := OS.get_environment("KUET_ROYALE_PYTHON")
	if chosen != "":
		candidates.append(chosen)
	if OS.get_name() == "Windows":
		candidates.append_array(["python", "py", "python3"])
	else:
		candidates.append_array(["python3", "/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3", "python"])
	for candidate in candidates:
		var output: Array = []
		if OS.execute(candidate, PackedStringArray(["--version"]), output, true) == 0:
			return candidate
	return ""


func _session_path(number: int) -> String:
	## One file per match and per running copy of the game, so a late answer
	## from an old match, or a second window, can never touch the current one.
	return ProjectSettings.globalize_path("user://match_%d_%d.json" % [OS.get_process_id(), number])


## Ask the Python side something. Session arguments are added for you.
func ask(arguments: Array) -> Dictionary:
	if problem != "":
		return {"ok": false, "error": problem}
	if str(arguments[0]) == "new" or str(arguments[0]) == "power_new":
		_matches += 1
		_session = _session_path(_matches)
	var id := _next_id
	_next_id += 1
	var thread := Thread.new()
	_threads[id] = thread
	_started[id] = Time.get_ticks_msec()
	thread.start(_run.bind(id, arguments, _session))
	while true:
		var got: Array = await answered
		if int(got[0]) == id:
			return got[1]
	return {}


func _run(id: int, arguments: Array, session: String) -> void:
	var reply_path := ProjectSettings.globalize_path("user://reply_%d_%d.json" % [OS.get_process_id(), id])
	var full := PackedStringArray([_bridge])
	for argument in arguments:
		full.append(str(argument))
	full.append_array(PackedStringArray(["--session", session, "--out", reply_path]))
	var output: Array = []
	OS.execute(python, full, output, true)
	var reply := {}
	if FileAccess.file_exists(reply_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(reply_path))
		if typeof(parsed) == TYPE_DICTIONARY:
			reply = parsed
		DirAccess.remove_absolute(reply_path)
	if reply.is_empty():
		var everything := "\n".join(PackedStringArray(output))
		var last_line := ""
		for line in everything.split("\n"):
			if line.strip_edges() != "":
				last_line = line.strip_edges()
		push_error("The AI did not answer.\n" + everything)
		reply = {"ok": false, "error": "The AI did not answer. " + last_line}
	_finish.call_deferred(id, reply)


func _finish(id: int, reply: Dictionary) -> void:
	if _threads.has(id):
		_threads[id].wait_to_finish()
		_threads.erase(id)
	if _given_up.has(id):
		_given_up.erase(id)              # too late: whoever asked has moved on
		return
	_started.erase(id)
	answered.emit(id, reply)


## A call that never comes back must not freeze the game. After a while the
## asker is told so, and can look at the match again and carry on.
func _process(_delta: float) -> void:
	if _started.is_empty():
		return
	var now := Time.get_ticks_msec()
	for id in _started.keys():
		if now - int(_started[id]) > PATIENCE_MSEC:
			_started.erase(id)
			_given_up[id] = true
			answered.emit(id, {"ok": false, "timeout": true, "error": "The AI took too long to answer."})


func _exit_tree() -> void:
	for id in _threads:
		if not _given_up.has(id):        # a thread that is stuck would hold the window open for ever
			_threads[id].wait_to_finish()
	for number in range(_matches + 1):
		if FileAccess.file_exists(_session_path(number)):
			DirAccess.remove_absolute(_session_path(number))
