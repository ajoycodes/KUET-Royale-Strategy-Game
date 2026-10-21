extends Node
## Small sound effects, made from sine waves when the game starts.
## There are no audio files in the project.

const RATE := 22050

var muted := false
var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0


func _ready() -> void:
	for i in 8:
		var player := AudioStreamPlayer.new()
		player.volume_db = -8.0
		add_child(player)
		_players.append(player)
	_streams["tap"] = _notes([[660.0, 0.05]], 0.25)
	_streams["hover"] = _notes([[880.0, 0.025]], 0.10)
	_streams["deploy"] = _sweep(320.0, 760.0, 0.14, 0.45)
	_streams["search"] = _notes([[1200.0, 0.02]], 0.07)
	_streams["hit"] = _sweep(420.0, 260.0, 0.07, 0.30)
	_streams["shot"] = _sweep(900.0, 500.0, 0.08, 0.22)
	_streams["out"] = _buzz(150.0, 0.18, 0.30)
	_streams["tower"] = _thump(0.30, 0.9)
	_streams["think"] = _notes([[520.0, 0.04], [0.0, 0.03], [620.0, 0.04]], 0.14)
	_streams["ding"] = _chord([880.0, 1320.0], 0.40, 0.40)
	_streams["win"] = _notes([[523.0, 0.11], [659.0, 0.11], [784.0, 0.11], [1047.0, 0.30]], 0.45)
	_streams["lose"] = _notes([[392.0, 0.16], [330.0, 0.16], [262.0, 0.34]], 0.40)


func play(sound: String, pitch: float = 1.0) -> void:
	if muted or not _streams.has(sound):
		return
	var player := _players[_next]
	_next = (_next + 1) % _players.size()
	player.stream = _streams[sound]
	player.pitch_scale = pitch
	player.play()


func _wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32000.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = RATE
	stream.stereo = false
	stream.data = data
	return stream


## One note after another. A frequency of 0 is a rest.
func _notes(notes: Array, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	for note in notes:
		var frequency: float = note[0]
		var length: float = note[1]
		var count := int(length * RATE)
		for i in count:
			var t := float(i) / RATE
			var fade := exp(-4.0 * t / length) * minf(1.0, t * 400.0)
			var wave := 0.0
			if frequency > 0.0:
				wave = sin(TAU * frequency * t) + 0.25 * sin(TAU * frequency * 2.0 * t)
			samples.append(wave * fade * volume)
	return _wav(samples)


func _chord(frequencies: Array, length: float, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	var count := int(length * RATE)
	for i in count:
		var t := float(i) / RATE
		var wave := 0.0
		for frequency in frequencies:
			wave += sin(TAU * float(frequency) * t)
		samples.append(wave / frequencies.size() * exp(-6.0 * t / length) * minf(1.0, t * 400.0) * volume)
	return _wav(samples)


func _sweep(from: float, to: float, length: float, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	var count := int(length * RATE)
	var phase := 0.0
	for i in count:
		var k := float(i) / count
		phase += TAU * lerpf(from, to, k) / RATE
		samples.append(sin(phase) * sin(PI * k) * volume)
	return _wav(samples)


func _buzz(frequency: float, length: float, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	var count := int(length * RATE)
	for i in count:
		var t := float(i) / RATE
		var wave := sin(TAU * frequency * t) + 0.5 * sin(TAU * frequency * 3.0 * t) + 0.3 * sin(TAU * frequency * 5.0 * t)
		samples.append(wave * 0.55 * (1.0 - float(i) / count) * volume)
	return _wav(samples)


func _thump(length: float, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	var noise := RandomNumberGenerator.new()
	noise.seed = 7
	var count := int(length * RATE)
	for i in count:
		var t := float(i) / RATE
		var knock := noise.randf_range(-1.0, 1.0) * exp(-60.0 * t)
		var body := sin(TAU * 95.0 * t) * exp(-14.0 * t)
		samples.append((knock * 0.6 + body) * volume)
	return _wav(samples)
