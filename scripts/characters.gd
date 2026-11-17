class_name Characters
extends RefCounted
## The warriors that stand on the arena, drawn from simple shapes. No picture
## files are used, and every figure is an original design.
##
## A figure is drawn in its own small coordinate system: (0, 0) is the ground
## between its feet, up is negative y, and it is about 40 wide and 50 tall.
## Whoever draws it says where the feet go and how big it should be.
##
## Each card has a "look" in LOOK: the kind of body, and the helmet, armour,
## weapon and shield that make it that card. The department's colour is the
## armour; each department also has its own glow (cyan, lightning, ember, amber).

const OUT := Color("0d2238")             # the dark edge round every shape
const EDGE := 1.5                        # how thick that edge is
const SKIN := Color("f2c29b")
const HAIR := Color("3b2a21")
const STEEL := Color("dde3ec")
const STEEL_DARK := Color("8e99ad")
const GOLD := Color("f2c24b")
const IVORY := Color("f3e7c9")
const LEATHER := Color("6e4325")
const WOOD := Color("8a5a33")
const DARK := Color("1b2740")
const CYAN := Color("6fe9ff")
const ZAP := Color("fff27a")
const EMBER := Color("ff8a3d")
const AMBER := Color("ffc857")
const GREEN_GLOW := Color("7dff6b")
const RED_GLOW := Color("ff4a3d")

const LOOK := {
	# CSE: cyber knights. Cyan glow.
	"Compiler": {"kind": "hero", "build": "heavy", "helm": "great", "cape": true, "emblem": "server", "weapon": "sword", "offhand": "tower", "glow": CYAN},
	"Kernel": {"kind": "hero", "build": "heavy", "helm": "crest", "cape": true, "emblem": "core", "weapon": "hammer", "offhand": "round", "glow": CYAN},
	"Algorithmist": {"kind": "hero", "build": "normal", "helm": "hood", "cape": true, "weapon": "staff", "glow": CYAN},
	"Optimizer": {"kind": "hero", "build": "light", "helm": "mask", "emblem": "chevron", "weapon": "bow", "glow": CYAN},
	"Logic Bomber": {"kind": "hero", "build": "normal", "helm": "goggles", "emblem": "diamond", "weapon": "bomb", "offhand": "bomb", "glow": CYAN},
	"Debugger": {"kind": "hero", "build": "light", "helm": "ninja", "weapon": "dagger", "offhand": "dagger", "glow": GREEN_GLOW},
	"Stack Runner": {"kind": "hero", "build": "light", "helm": "winged", "emblem": "chevron", "pose": "run", "streaks": true, "glow": CYAN},
	"Cloud Drone": {"kind": "cloudrider", "helm": "winged", "weapon": "spear", "glow": CYAN},
	# EEE: storm warriors. Lightning glow.
	"Capacitor": {"kind": "hero", "build": "heavy", "helm": "horned", "cape": true, "emblem": "bolt", "weapon": "mace", "offhand": "battery", "glow": ZAP},
	"Transformer": {"kind": "hero", "build": "heavy", "helm": "visor", "emblem": "bolt", "weapon": "gauntlet", "offhand": "gauntlet", "coils": true, "glow": ZAP},
	"Signal Processor": {"kind": "hero", "build": "normal", "helm": "visor", "emblem": "bolt", "weapon": "rifle", "glow": ZAP},
	"Circuit Engineer": {"kind": "hero", "build": "normal", "helm": "crown", "cape": true, "weapon": "staff", "lightning": true, "glow": ZAP},
	"Oscillator": {"kind": "hero", "build": "normal", "helm": "visor", "weapon": "gauntlet", "offhand": "gauntlet", "waves": true, "glow": ZAP},
	"Power Engineer": {"kind": "hero", "build": "normal", "helm": "mask", "emblem": "bolt", "weapon": "gauntlet", "offhand": "gauntlet", "lightning": true, "glow": ZAP},
	"Relay Runner": {"kind": "hero", "build": "light", "helm": "winged", "weapon": "spear", "pose": "run", "streaks": true, "glow": ZAP},
	"Electron": {"kind": "spark", "glow": ZAP},
	# ME: iron warriors and machines. Ember glow.
	"Heavy Machine": {"kind": "mech", "arm": "hammer", "glow": EMBER},
	"Gearwheel Guard": {"kind": "hero", "build": "heavy", "helm": "great", "cape": true, "emblem": "gear", "weapon": "axe", "offhand": "gear", "glow": EMBER},
	"Robotic Arm": {"kind": "hero", "build": "normal", "helm": "visor", "emblem": "gear", "weapon": "blaster", "glow": EMBER},
	"Steel Rain Cannon": {"kind": "mech", "arm": "cannons", "glow": EMBER},
	"Mech Warrior": {"kind": "hero", "build": "normal", "helm": "kabuto", "cape": true, "weapon": "katana", "glow": EMBER},
	"Gear Runner": {"kind": "scorpion", "scale": 0.82, "glow": EMBER},
	"Mini-Bot": {"kind": "hero", "build": "light", "helm": "robot", "weapon": "dagger", "offhand": "dagger", "glow": EMBER},
	"Quadcopter": {"kind": "jet", "glow": EMBER},
	# CE: earth warriors. Amber glow.
	"Excavator": {"kind": "scorpion", "scale": 1.12, "buckets": true, "glow": AMBER},
	"Road Roller": {"kind": "hero", "build": "heavy", "helm": "horned", "cape": true, "emblem": "hazard", "weapon": "hammer", "offhand": "roller", "glow": AMBER},
	"Site Engineer": {"kind": "hero", "build": "normal", "helm": "warhat", "emblem": "hazard", "weapon": "crossbow", "glow": AMBER},
	"Crane Operator": {"kind": "hero", "build": "normal", "helm": "warhat", "weapon": "hook", "offhand": "round", "glow": AMBER},
	"Seismic Crew": {"kind": "hero", "build": "heavy", "helm": "hood", "weapon": "sledge", "rocks": true, "glow": AMBER},
	"Surveyor": {"kind": "hero", "build": "light", "helm": "mask", "weapon": "spear", "offhand": "round", "glow": AMBER},
	"Construction Crew": {"kind": "hero", "build": "normal", "helm": "warhat", "weapon": "pickaxe", "pose": "run", "streaks": true, "glow": AMBER},
	"Survey Drone": {"kind": "hawk", "glow": AMBER},
}


static func has(card: String) -> bool:
	return LOOK.has(card)


## Draw the figure of `card` with its feet at `at`. `time` keeps it alive,
## `moving` makes it walk, and `swing` (0 to 1) is how far through an attack it is.
static func draw(canvas: CanvasItem, at: Vector2, size: float, card: String, color: Color, time: float, moving: bool, swing: float = 0.0) -> void:
	if not LOOK.has(card):
		return
	var look: Dictionary = LOOK[card]
	var pen := Pen.new(canvas, at, size)
	var strike := sin(clampf(swing, 0.0, 1.0) * PI)
	match str(look["kind"]):
		"hero":
			_hero(pen, look, color, time, moving, strike)
		"mech":
			_mech(pen, look, color, time, moving, strike)
		"scorpion":
			_scorpion(pen, look, color, time, moving, strike)
		"cloudrider":
			_cloudrider(pen, look, color, time, strike)
		"jet":
			_jet(pen, look, color, time, strike)
		"spark":
			_spark(pen, look, time, strike)
		"hawk":
			_hawk(pen, look, color, time, strike)
	pen.done()


# ------------------------------------------------------------- a warrior

static func _hero(pen: Pen, look: Dictionary, color: Color, time: float, moving: bool, strike: float) -> void:
	var build := str(look.get("build", "normal"))
	var half := 12.0 if build == "heavy" else (9.0 if build == "normal" else 7.5)
	var running := str(look.get("pose", "")) == "run"
	var glow: Color = look.get("glow", CYAN)
	var step := sin(time * (14.0 if running else 10.0)) if moving else (0.7 if running else 0.0)
	var bob := absf(step) * 1.1 if moving else sin(time * 2.2) * 0.4
	var lean := 2.5 if running else 0.0
	var top := -28.0 - bob
	var waist := -9.0 - bob

	pen.shadow(half + 5.0)
	if look.get("streaks", false):
		for line in [[-21.0, -27.0, 8.0], [-23.0, -19.0, 9.0], [-20.0, -11.0, 7.0]]:
			pen.stroke(Vector2(line[0], line[1] - bob), Vector2(line[0] + line[2], line[1] - bob), Color(glow, 0.9), 1.8)
	if look.get("cape", false):
		var flutter := sin(time * 3.0) * 1.5 + (2.5 if moving else 0.0)
		pen.poly([Vector2(-half + 1, top + 2), Vector2(half - 1, top + 2), Vector2(half + 4 + flutter, -2), Vector2(-half - 4 + flutter * 0.5, -2)],
			color.darkened(0.45))
	if look.get("rocks", false):
		for rock in [[Vector2(-17, -3), 3.0], [Vector2(16, -2), 2.5], [Vector2(-12, 0), 2.0]]:
			pen.disc(rock[0] + Vector2(0, -absf(sin(time * 4.0 + rock[1])) * 3.0), float(rock[1]), Color("9b8b78"))

	# Legs and boots.
	var thick := 6.0 if build == "heavy" else 4.6
	var left_foot := Vector2(-4.5 - step * (6.0 if running else 2.0), -maxf(-step, 0.0) * (3.0 if running else 0.0))
	var right_foot := Vector2(4.5 + step * (6.0 if running else 2.0), -maxf(step, 0.0) * (3.0 if running else 0.0))
	pen.limb(Vector2(-3.5 + lean, waist), left_foot + Vector2(0, -2), thick, color.darkened(0.35))
	pen.limb(Vector2(3.5 + lean, waist), right_foot + Vector2(0, -2), thick, color.darkened(0.35))
	pen.box(Rect2(left_foot + Vector2(-3.5, -3.5), Vector2(7, 4)), STEEL_DARK, 1.5)
	pen.box(Rect2(right_foot + Vector2(-3.5, -3.5), Vector2(7, 4)), STEEL_DARK, 1.5)

	var shoulder_l := Vector2(-half + lean, top + 4)
	var shoulder_r := Vector2(half + lean, top + 4)
	var hand_l := Vector2(-half - 5 + lean, -15 - bob + (step * 2.0 if not running else -step * 3.0))
	var hand_r := Vector2(half + 5 + lean, -15 - bob - (step * 2.0 if not running else -step * 3.0))
	if running:
		hand_l = Vector2(-half - 3 + lean, -20 - bob + step * 3.0)
	if look.get("coils", false):
		for side in [-1.0, 1.0]:
			pen.disc(Vector2(side * (half + 3), top + 1), 5.0, STEEL_DARK)
			for ring in 3:
				pen.stroke(Vector2(side * (half + 3) - 4, top - 2 + ring * 2.5), Vector2(side * (half + 3) + 4, top - 2 + ring * 2.5), GOLD, 1.3)

	# The body: armour in the department's colour, a belt and an emblem.
	pen.box(Rect2(-half + lean, top, half * 2.0, waist - top + 1), color, 4.5)
	pen.box(Rect2(-half + 1.5 + lean, waist - 6, half * 2.0 - 3, 4.5), color.darkened(0.25), 2.0, false)
	pen.box(Rect2(-half + lean, waist - 2.5, half * 2.0, 3.5), LEATHER, 1.0)
	pen.dot(Vector2(lean, waist - 0.8), 1.5, GOLD)
	_emblem(pen, str(look.get("emblem", "")), Vector2(lean, top + 7), glow)
	if build == "heavy":
		pen.disc(shoulder_l + Vector2(0, -1), 5.0, STEEL)
		pen.disc(shoulder_r + Vector2(0, -1), 5.0, STEEL)

	# The head and helmet.
	_helm(pen, str(look.get("helm", "")), Vector2(lean * 1.4, top - 8.5), color, glow, time)

	# Left arm and whatever it holds, then the right arm and its weapon.
	pen.limb(shoulder_l, hand_l, 3.8 if build != "heavy" else 4.6, color.darkened(0.2))
	_offhand(pen, str(look.get("offhand", "")), hand_l, color, glow, time)
	pen.limb(shoulder_r, hand_r, 3.8 if build != "heavy" else 4.6, color.darkened(0.2))
	pen.disc(hand_r, 2.3, STEEL_DARK)
	_weapon(pen, str(look.get("weapon", "")), hand_r, -0.35 - strike * 1.5, color, glow, time)

	if look.get("lightning", false):
		var flick := int(time * 12.0) % 3
		_bolt(pen, [hand_r + Vector2(3, -2), hand_r + Vector2(7, -6 - flick), hand_r + Vector2(5, -8), hand_r + Vector2(10, -13)], glow)
		_bolt(pen, [hand_l + Vector2(-3, -2), hand_l + Vector2(-6, -7 + flick), hand_l + Vector2(-4, -9), hand_l + Vector2(-9, -14)], glow)
	if look.get("waves", false):
		for ring in 3:
			var grow := fmod(time * 1.5 + ring / 3.0, 1.0)
			pen.ring(hand_r + Vector2(4, -4), 3.0 + grow * 9.0, Color(glow, 1.0 - grow), 1.5)
			pen.ring(hand_l + Vector2(-4, -4), 3.0 + grow * 9.0, Color(glow, 1.0 - grow), 1.5)


static func _emblem(pen: Pen, emblem: String, at: Vector2, glow: Color) -> void:
	match emblem:
		"server":
			pen.box(Rect2(at + Vector2(-5, -3), Vector2(10, 2.5)), DARK, 1.0, false)
			pen.box(Rect2(at + Vector2(-5, 1), Vector2(10, 2.5)), DARK, 1.0, false)
			pen.dot(at + Vector2(3, -1.7), 0.9, GREEN_GLOW)
			pen.dot(at + Vector2(3, 2.3), 0.9, glow)
		"core":
			pen.glow(at, 4.5, glow)
			pen.disc(at, 2.6, glow, 1.0)
		"bolt":
			pen.poly([at + Vector2(1, -5), at + Vector2(-3, 1), at + Vector2(0, 1), at + Vector2(-1, 5), at + Vector2(3, -1), at + Vector2(0, -1)], GOLD, 0.9)
		"gear":
			for tooth in 8:
				pen.dot(at + Vector2(4.2, 0).rotated(tooth * TAU / 8.0), 1.3, GOLD)
			pen.disc(at, 3.4, GOLD, 0.9)
			pen.dot(at, 1.3, DARK)
		"chevron":
			pen.poly([at + Vector2(-5, -2), at + Vector2(0, 2), at + Vector2(5, -2), at + Vector2(5, 1), at + Vector2(0, 5), at + Vector2(-5, 1)], GOLD, 0.9)
		"diamond":
			pen.poly([at + Vector2(0, -4.5), at + Vector2(4, 0), at + Vector2(0, 4.5), at + Vector2(-4, 0)], glow, 0.9)
		"hazard":
			pen.poly([at + Vector2(0, -4.5), at + Vector2(5, 4), at + Vector2(-5, 4)], AMBER, 0.9)
			pen.box(Rect2(at + Vector2(-0.6, -1.5), Vector2(1.2, 3)), DARK, 0.5, false)


static func _helm(pen: Pen, helm: String, head: Vector2, color: Color, glow: Color, time: float) -> void:
	match helm:
		"great":
			# A closed knight's helm with a glowing slit.
			pen.box(Rect2(head + Vector2(-9, -10), Vector2(18, 19)), STEEL, 5.0)
			pen.box(Rect2(head + Vector2(-7.5, -2), Vector2(15, 3)), DARK, 1.0, false)
			pen.dot(head + Vector2(-3, -0.5), 1.1, glow)
			pen.dot(head + Vector2(3, -0.5), 1.1, glow)
			pen.stroke(head + Vector2(0, 2.5), head + Vector2(0, 7), STEEL_DARK, 1.2)
			pen.box(Rect2(head + Vector2(-1.5, -13), Vector2(3, 4)), color, 1.0)
		"crest":
			# A plumed helm with a T-shaped opening.
			pen.poly([head + Vector2(-2, -10), head + Vector2(-8, -17), head + Vector2(4, -19), head + Vector2(9, -14), head + Vector2(3, -10)], color.lightened(0.25))
			pen.disc(head, 9.2, STEEL)
			pen.box(Rect2(head + Vector2(-6, -2), Vector2(12, 2.6)), DARK, 1.0, false)
			pen.box(Rect2(head + Vector2(-1.3, -1), Vector2(2.6, 8)), DARK, 1.0, false)
			pen.dot(head + Vector2(-3.2, -0.7), 1.0, glow)
			pen.dot(head + Vector2(3.2, -0.7), 1.0, glow)
		"visor":
			# A rounded armoured helm with a glowing visor band.
			pen.disc(head, 9.0, STEEL)
			pen.box(Rect2(head + Vector2(-8, -3), Vector2(16, 5)), DARK, 2.0, false)
			pen.box(Rect2(head + Vector2(-6.5, -1.6), Vector2(13, 2.2)), glow, 1.0, false)
			pen.box(Rect2(head + Vector2(-3, 4.5), Vector2(6, 3)), STEEL_DARK, 1.0, false)
		"horned":
			# A horned war helm over a fierce face.
			pen.poly([head + Vector2(-7, -5), head + Vector2(-15, -9), head + Vector2(-16, -17), head + Vector2(-11, -11), head + Vector2(-5, -9)], IVORY)
			pen.poly([head + Vector2(7, -5), head + Vector2(15, -9), head + Vector2(16, -17), head + Vector2(11, -11), head + Vector2(5, -9)], IVORY)
			pen.disc(head + Vector2(0, 1), 8.6, SKIN)
			pen.poly([head + Vector2(-9, -1), head + Vector2(-8, -8), head + Vector2(0, -11), head + Vector2(8, -8), head + Vector2(9, -1)], STEEL)
			pen.box(Rect2(head + Vector2(-1.3, -2), Vector2(2.6, 6)), STEEL_DARK, 0.8)
			_eyes(pen, head + Vector2(0, 1.5), 3.4, OUT, true)
			pen.poly([head + Vector2(-6, 4), head + Vector2(6, 4), head + Vector2(3, 10), head + Vector2(-3, 10)], Color("8a5a33"), 0.9)
		"hood":
			# A deep hood: only the eyes glow.
			pen.poly([head + Vector2(0, -13), head + Vector2(10, -2), head + Vector2(9, 9), head + Vector2(-9, 9), head + Vector2(-10, -2)], color.darkened(0.3))
			pen.disc(head + Vector2(0, 1.5), 6.2, DARK, 0.0)
			pen.glow(head + Vector2(-2.6, 1), 2.4, glow)
			pen.glow(head + Vector2(2.6, 1), 2.4, glow)
			pen.dot(head + Vector2(-2.6, 1), 1.2, glow)
			pen.dot(head + Vector2(2.6, 1), 1.2, glow)
		"ninja":
			# A wrapped mask with a headband whose ends fly.
			pen.disc(head, 8.6, Color("2a2f45"))
			pen.box(Rect2(head + Vector2(-6.5, -2.5), Vector2(13, 4.5)), SKIN, 2.0, false)
			_eyes(pen, head + Vector2(0, -0.3), 2.8, OUT, true)
			pen.stroke(head + Vector2(-8, -5), head + Vector2(-15, -3 + sin(time * 8.0) * 2.0), OUT, 3.6)
			pen.stroke(head + Vector2(-8, -5), head + Vector2(-15, -3 + sin(time * 8.0) * 2.0), color, 1.8)
			pen.box(Rect2(head + Vector2(-8.6, -6.5), Vector2(17.2, 3)), color, 1.0)
		"kabuto":
			# A samurai helm with a golden crescent and a dark face guard.
			pen.arc(head + Vector2(0, -8), 7.0, PI * 1.1, PI * 1.9, OUT, 4.4)
			pen.arc(head + Vector2(0, -8), 7.0, PI * 1.1, PI * 1.9, GOLD, 2.4)
			pen.disc(head, 9.0, color.darkened(0.15))
			pen.box(Rect2(head + Vector2(-11, -2), Vector2(22, 3.5)), color.darkened(0.35), 1.5)
			pen.box(Rect2(head + Vector2(-6, 1), Vector2(12, 7)), DARK, 2.5, false)
			pen.dot(head + Vector2(-2.6, 3.5), 1.1, glow)
			pen.dot(head + Vector2(2.6, 3.5), 1.1, glow)
		"mask":
			# A hero's face with a mask across the eyes.
			pen.disc(head + Vector2(0, -1.5), 9.0, HAIR)
			pen.dot(head + Vector2(0, 1), 8.0, SKIN)
			pen.oval(head + Vector2(-1, -5.5), 7.0, 3.0, HAIR, false)
			pen.box(Rect2(head + Vector2(-7.5, -1.2), Vector2(15, 4.2)), color.darkened(0.3), 2.0)
			pen.dot(head + Vector2(-3, 0.9), 1.3, Color.WHITE)
			pen.dot(head + Vector2(3, 0.9), 1.3, Color.WHITE)
			pen.stroke(head + Vector2(-2, 5.5), head + Vector2(2, 5.5), Color("a8553f"), 1.1)
		"goggles":
			pen.disc(head + Vector2(0, -1.5), 9.0, HAIR)
			pen.dot(head + Vector2(0, 1), 8.0, SKIN)
			pen.box(Rect2(head + Vector2(-9, -3.5), Vector2(18, 3)), LEATHER, 1.0, false)
			pen.disc(head + Vector2(-3.4, -1.8), 3.0, glow)
			pen.disc(head + Vector2(3.4, -1.8), 3.0, glow)
			pen.dot(head + Vector2(-3, 3.2), 1.0, OUT)
			pen.dot(head + Vector2(3, 3.2), 1.0, OUT)
			pen.stroke(head + Vector2(-2.5, 6), head + Vector2(2.5, 5), Color("a8553f"), 1.1)
		"winged":
			# A helm with small wings, for the quick ones.
			for side in [-1.0, 1.0]:
				var beat := sin(time * 9.0) * 1.5
				pen.poly([head + Vector2(side * 7, -4), head + Vector2(side * 16, -10 - beat), head + Vector2(side * 14, -6), head + Vector2(side * 17, -5 - beat), head + Vector2(side * 9, -1)], Color.WHITE)
			pen.disc(head + Vector2(0, 1), 8.0, SKIN)
			pen.poly([head + Vector2(-8.5, 0), head + Vector2(-8, -7), head + Vector2(0, -10), head + Vector2(8, -7), head + Vector2(8.5, 0), head + Vector2(5, -2), head + Vector2(-5, -2)], GOLD)
			_eyes(pen, head + Vector2(0, 1.8), 3.2, OUT, true)
		"crown":
			# A crown of lightning over glowing eyes.
			for spike in 5:
				var x := -6.0 + spike * 3.0
				pen.poly([head + Vector2(x - 1.6, -6), head + Vector2(x, -13 - (spike % 2) * 3.0), head + Vector2(x + 1.6, -6)], GOLD, 0.9)
			pen.disc(head + Vector2(0, -1), 8.8, HAIR)
			pen.dot(head + Vector2(0, 1.5), 7.8, SKIN)
			pen.glow(head + Vector2(-3, 1), 2.2, glow)
			pen.glow(head + Vector2(3, 1), 2.2, glow)
			pen.dot(head + Vector2(-3, 1), 1.2, Color.WHITE)
			pen.dot(head + Vector2(3, 1), 1.2, Color.WHITE)
			pen.box(Rect2(head + Vector2(-7.5, -7), Vector2(15, 2.5)), GOLD, 1.0)
		"warhat":
			# A war helm shaped like a hard hat, with a lamp.
			pen.disc(head + Vector2(0, 1.5), 8.0, SKIN)
			pen.poly([head + Vector2(-9, -2), head + Vector2(-8, -9), head + Vector2(0, -12), head + Vector2(8, -9), head + Vector2(9, -2)], color)
			pen.box(Rect2(head + Vector2(-11, -3), Vector2(22, 2.8)), color.darkened(0.25), 1.2)
			pen.disc(head + Vector2(0, -8), 2.2, glow, 1.0)
			_eyes(pen, head + Vector2(0, 2.5), 3.2, OUT, true)
			pen.box(Rect2(head + Vector2(-6, 5), Vector2(12, 3.5)), Color("8a5a33"), 1.5, false)
		"robot":
			pen.stroke(head + Vector2(0, -8), head + Vector2(0, -13), OUT, 1.4)
			pen.dot(head + Vector2(0, -14), 1.8, glow)
			pen.box(Rect2(head + Vector2(-8, -8), Vector2(16, 15)), STEEL, 4.0)
			pen.disc(head + Vector2(0, -0.5), 4.0, DARK, 0.8)
			pen.glow(head + Vector2(0, -0.5), 3.0, glow)
			pen.dot(head + Vector2(0, -0.5), 1.8, glow)
		_:
			pen.disc(head + Vector2(0, -1.5), 9.0, HAIR)
			pen.dot(head + Vector2(0, 1), 8.0, SKIN)
			_eyes(pen, head + Vector2(0, 1.5), 3.2, OUT, true)


## Two eyes, with eyebrows angled down for a fierce look.
static func _eyes(pen: Pen, at: Vector2, apart: float, ink: Color, fierce: bool) -> void:
	pen.dot(at + Vector2(-apart, 0), 1.2, ink)
	pen.dot(at + Vector2(apart, 0), 1.2, ink)
	if fierce:
		pen.stroke(at + Vector2(-apart - 2, -3), at + Vector2(-apart + 1.5, -1.8), ink, 1.1)
		pen.stroke(at + Vector2(apart + 2, -3), at + Vector2(apart - 1.5, -1.8), ink, 1.1)


# ---------------------------------------------------------------- weapons

## A weapon held at `hand`, drawn upright and then turned by `angle`.
static func _weapon(pen: Pen, weapon: String, hand: Vector2, angle: float, color: Color, glow: Color, time: float) -> void:
	if weapon == "":
		return
	pen.turn(hand, angle)
	var o := Vector2.ZERO
	match weapon:
		"sword":
			pen.poly([o + Vector2(-1.9, -3), o + Vector2(1.9, -3), o + Vector2(1.9, -20), o + Vector2(0, -24), o + Vector2(-1.9, -20)], STEEL)
			pen.stroke(o + Vector2(0, -5), o + Vector2(0, -20), Color.WHITE, 0.8)
			pen.box(Rect2(o + Vector2(-5, -3.5), Vector2(10, 2.6)), GOLD, 1.0)
			pen.box(Rect2(o + Vector2(-1.2, -1), Vector2(2.4, 5)), LEATHER, 0.8)
			pen.dot(o + Vector2(0, 4.8), 1.6, GOLD)
		"katana":
			pen.poly([o + Vector2(-1.2, -3), o + Vector2(1.2, -3), o + Vector2(2.6, -16), o + Vector2(3.6, -24), o + Vector2(1.2, -17)], STEEL)
			pen.disc(o + Vector2(0, -3), 2.4, GOLD, 0.8)
			pen.box(Rect2(o + Vector2(-1.2, -1.5), Vector2(2.4, 7)), DARK, 0.8)
		"dagger":
			pen.poly([o + Vector2(-1.5, -2), o + Vector2(1.5, -2), o + Vector2(0, -11)], STEEL)
			pen.box(Rect2(o + Vector2(-3, -2.5), Vector2(6, 2)), color, 0.6)
			pen.box(Rect2(o + Vector2(-1, -1), Vector2(2, 4)), DARK, 0.6)
		"hammer":
			pen.limb(o + Vector2(0, 5), o + Vector2(0, -16), 2.2, WOOD)
			pen.box(Rect2(o + Vector2(-6, -24), Vector2(12, 8)), STEEL, 2.0)
			pen.box(Rect2(o + Vector2(-6, -21.5), Vector2(12, 2.4)), GOLD, 0.6, false)
		"sledge":
			pen.limb(o + Vector2(0, 6), o + Vector2(0, -18), 2.4, WOOD)
			pen.box(Rect2(o + Vector2(-8, -27), Vector2(16, 10)), STEEL_DARK, 2.5)
			pen.box(Rect2(o + Vector2(-8, -27), Vector2(4, 10)), STEEL, 1.5, false)
		"mace":
			pen.limb(o + Vector2(0, 5), o + Vector2(0, -14), 2.2, LEATHER)
			for spike in 6:
				pen.disc(o + Vector2(0, -19) + Vector2(6, 0).rotated(spike * TAU / 6.0), 1.6, STEEL_DARK, 0.8)
			pen.disc(o + Vector2(0, -19), 5.0, STEEL)
			pen.glow(o + Vector2(0, -19), 2.5, glow)
		"axe":
			pen.limb(o + Vector2(0, 5), o + Vector2(0, -20), 2.2, WOOD)
			pen.poly([o + Vector2(1, -22), o + Vector2(9, -26), o + Vector2(11, -18), o + Vector2(9, -11), o + Vector2(1, -14)], STEEL)
			pen.stroke(o + Vector2(10, -25), o + Vector2(10.5, -12), Color.WHITE, 0.9)
		"spear":
			pen.limb(o + Vector2(0, 8), o + Vector2(0, -24), 1.8, WOOD)
			pen.poly([o + Vector2(-2.6, -24), o + Vector2(2.6, -24), o + Vector2(0, -32)], STEEL)
			pen.poly([o + Vector2(-2, -22), o + Vector2(2, -22), o + Vector2(0, -18)], color, 0.8)
		"staff":
			pen.limb(o + Vector2(0, 7), o + Vector2(0, -21), 2.0, WOOD)
			pen.arc(o + Vector2(0, -24), 4.5, PI * 0.15, PI * 0.85, GOLD, 1.6)
			pen.glow(o + Vector2(0, -26), 5.5 + sin(time * 5.0), glow)
			pen.disc(o + Vector2(0, -26), 3.4, glow, 1.0)
		"bow":
			pen.arc(o + Vector2(-6, -8), 12.0, -PI * 0.42, PI * 0.42, OUT, 3.6)
			pen.arc(o + Vector2(-6, -8), 12.0, -PI * 0.42, PI * 0.42, WOOD, 2.0)
			var top := o + Vector2(-6, -8) + Vector2(12, 0).rotated(-PI * 0.42)
			var bottom := o + Vector2(-6, -8) + Vector2(12, 0).rotated(PI * 0.42)
			pen.stroke(top, bottom, Color.WHITE, 0.7)
			pen.stroke(o + Vector2(-4, -8), o + Vector2(9, -8), STEEL_DARK, 1.2)
			pen.poly([o + Vector2(9, -10), o + Vector2(13, -8), o + Vector2(9, -6)], glow, 0.8)
		"crossbow":
			pen.box(Rect2(o + Vector2(-1.8, -14), Vector2(3.6, 15)), WOOD, 1.2)
			pen.arc(o + Vector2(0, -6), 9.0, -PI * 0.85, -PI * 0.15, OUT, 3.6)
			pen.arc(o + Vector2(0, -6), 9.0, -PI * 0.85, -PI * 0.15, STEEL_DARK, 2.0)
			pen.poly([o + Vector2(-1.5, -14), o + Vector2(1.5, -14), o + Vector2(0, -19)], glow, 0.8)
		"bomb":
			pen.disc(o + Vector2(0, -5), 4.6, DARK)
			pen.dot(o + Vector2(-1.6, -6.6), 1.2, Color(1, 1, 1, 0.7))
			pen.stroke(o + Vector2(1.5, -9.5), o + Vector2(3.5, -12), LEATHER, 1.2)
			pen.glow(o + Vector2(3.5, -12.5), 2.4 + sin(time * 20.0), glow)
			pen.dot(o + Vector2(3.5, -12.5), 1.3, Color.WHITE)
		"rifle":
			pen.box(Rect2(o + Vector2(-1.8, -22), Vector2(3.6, 24)), DARK, 1.2)
			pen.box(Rect2(o + Vector2(-2.8, -6), Vector2(5.6, 8)), color.darkened(0.2), 1.2)
			pen.arc(o + Vector2(0, -24), 4.0, PI * 1.15, PI * 1.85, STEEL, 1.6)
			pen.glow(o + Vector2(0, -23), 2.2, glow)
		"blaster":
			pen.box(Rect2(o + Vector2(-3.4, -14), Vector2(6.8, 15)), STEEL, 2.0)
			pen.box(Rect2(o + Vector2(-3.4, -9), Vector2(6.8, 2.4)), color, 0.6, false)
			pen.glow(o + Vector2(0, -15), 4.0 + sin(time * 8.0), glow)
			pen.disc(o + Vector2(0, -14.5), 2.2, glow, 0.8)
		"gauntlet":
			pen.disc(o + Vector2(0, -1.5), 3.6, STEEL)
			pen.glow(o + Vector2(0, -1.5), 3.0, glow)
		"hook":
			for link in 5:
				pen.disc(o + Vector2(sin(time * 4.0 + link) * 0.8, -3.5 - link * 3.2), 1.0, STEEL_DARK, 0.7)
			pen.arc(o + Vector2(2.5, -22), 3.6, -PI * 0.1, PI * 1.1, OUT, 3.8)
			pen.arc(o + Vector2(2.5, -22), 3.6, -PI * 0.1, PI * 1.1, STEEL, 2.0)
		"pickaxe":
			pen.limb(o + Vector2(0, 5), o + Vector2(0, -20), 2.2, WOOD)
			pen.poly([o + Vector2(-10, -18), o + Vector2(0, -24), o + Vector2(10, -18), o + Vector2(0, -21)], STEEL)
	pen.straight()


static func _offhand(pen: Pen, item: String, hand: Vector2, color: Color, glow: Color, time: float) -> void:
	match item:
		"tower":
			pen.box(Rect2(hand + Vector2(-6, -15), Vector2(11, 19)), color.lightened(0.15), 2.5)
			pen.box(Rect2(hand + Vector2(-4, -12), Vector2(7, 2)), DARK, 0.8, false)
			pen.box(Rect2(hand + Vector2(-4, -8), Vector2(7, 2)), DARK, 0.8, false)
			pen.dot(hand + Vector2(1.5, -11), 0.8, GREEN_GLOW)
			pen.glow(hand + Vector2(-0.5, -1), 2.5, glow)
		"round":
			pen.disc(hand + Vector2(-1, -4), 7.5, STEEL)
			pen.disc(hand + Vector2(-1, -4), 5.6, color.lightened(0.1), 0.0)
			pen.disc(hand + Vector2(-1, -4), 2.0, GOLD, 0.9)
		"gear":
			for tooth in 10:
				pen.disc(hand + Vector2(-1, -4) + Vector2(8.2, 0).rotated(tooth * TAU / 10.0 + time * 0.6), 1.8, STEEL_DARK, 0.9)
			pen.disc(hand + Vector2(-1, -4), 7.4, STEEL)
			pen.disc(hand + Vector2(-1, -4), 3.0, color, 0.9)
		"battery":
			pen.box(Rect2(hand + Vector2(-6, -14), Vector2(10, 17)), DARK, 2.0)
			pen.box(Rect2(hand + Vector2(-3, -16), Vector2(4, 2.5)), GOLD, 0.8)
			for bar in 3:
				pen.box(Rect2(hand + Vector2(-4, -11 + bar * 4.5), Vector2(6, 3)), glow if bar > 0 or sin(time * 4.0) > 0.0 else DARK.lightened(0.2), 0.8, false)
		"roller":
			pen.box(Rect2(hand + Vector2(-9, -9), Vector2(16, 10)), STEEL_DARK, 4.0)
			for line in 3:
				pen.stroke(hand + Vector2(-6 + line * 4.5, -8), hand + Vector2(-6 + line * 4.5, 0), STEEL, 1.0)
		"dagger":
			_weapon(pen, "dagger", hand, 0.35, color, glow, time)
		"bomb":
			_weapon(pen, "bomb", hand, 0.2, color, glow, time)
		"gauntlet":
			_weapon(pen, "gauntlet", hand, 0.0, color, glow, time)
		_:
			pen.disc(hand, 2.3, STEEL_DARK)


static func _bolt(pen: Pen, points: Array, glow: Color) -> void:
	for place in range(points.size() - 1):
		pen.stroke(points[place], points[place + 1], Color(glow, 0.5), 3.0)
	for place in range(points.size() - 1):
		pen.stroke(points[place], points[place + 1], Color.WHITE, 1.0)


# ------------------------------------------------------------ machines

## A walking war machine with a pilot behind glass.
static func _mech(pen: Pen, look: Dictionary, color: Color, time: float, moving: bool, strike: float) -> void:
	var glow: Color = look.get("glow", EMBER)
	var step := sin(time * 7.0) if moving else 0.0
	var bob := absf(step) * 1.4 if moving else sin(time * 1.8) * 0.3
	pen.shadow(18.0)
	# Legs: thick pistons and wide feet.
	for side in [-1.0, 1.0]:
		var lift := maxf(step * side, 0.0) * 2.5
		pen.box(Rect2(Vector2(side * 9 - 4, -14 - bob - lift), Vector2(8, 11)), STEEL_DARK, 2.0)
		pen.box(Rect2(Vector2(side * 9 - 6.5, -4 - lift), Vector2(13, 4.5)), DARK, 1.8)
	# The body and the cockpit.
	pen.box(Rect2(Vector2(-15, -38 - bob), Vector2(30, 25)), color, 6.0)
	pen.box(Rect2(Vector2(-13, -20 - bob), Vector2(26, 5)), color.darkened(0.3), 2.0, false)
	pen.box(Rect2(Vector2(-8, -35 - bob), Vector2(16, 10)), DARK, 4.0)
	pen.box(Rect2(Vector2(-6, -33 - bob), Vector2(5, 3)), Color(1, 1, 1, 0.35), 1.0, false)
	pen.glow(Vector2(-2.5, -29.5 - bob), 1.8, glow)
	pen.glow(Vector2(2.5, -29.5 - bob), 1.8, glow)
	pen.dot(Vector2(-2.5, -29.5 - bob), 1.0, glow)
	pen.dot(Vector2(2.5, -29.5 - bob), 1.0, glow)
	for vent in 3:
		pen.box(Rect2(Vector2(-9 + vent * 7, -24 - bob), Vector2(4, 2)), DARK, 0.6, false)
	if str(look.get("arm", "")) == "cannons":
		# Two cannons on the shoulders, aimed ahead, with a hot glow inside.
		for side in [-1.0, 1.0]:
			pen.box(Rect2(Vector2(side * 14 - 4, -47 - bob + strike * 2.0), Vector2(8, 13)), STEEL, 2.5)
			pen.glow(Vector2(side * 14, -47 - bob + strike * 2.0), 3.0 + strike * 3.0, glow)
			pen.disc(Vector2(side * 14, -46.5 - bob + strike * 2.0), 2.2, DARK, 0.8)
		pen.disc(Vector2(-19, -22 - bob), 4.6, STEEL)
		pen.disc(Vector2(19, -22 - bob), 4.6, STEEL)
	else:
		# A shield arm and a great hammer arm.
		pen.box(Rect2(Vector2(-25, -34 - bob), Vector2(10, 20)), STEEL, 3.0)
		pen.box(Rect2(Vector2(-23, -30 - bob), Vector2(6, 2)), color, 0.6, false)
		pen.limb(Vector2(14, -30 - bob), Vector2(19, -20 - bob), 5.0, STEEL_DARK)
		_weapon(pen, "sledge", Vector2(19, -20 - bob), -0.2 - strike * 1.3, color, glow, time)


## A war scorpion: armoured body, two claws and a glowing sting held high.
static func _scorpion(pen: Pen, look: Dictionary, color: Color, time: float, moving: bool, strike: float) -> void:
	var glow: Color = look.get("glow", EMBER)
	var scale := float(look.get("scale", 1.0))
	var buckets := bool(look.get("buckets", false))
	pen.zoom(scale)
	var scuttle := sin(time * 16.0) if moving else 0.0
	pen.shadow(19.0)
	# The tail curls up from behind and over the body.
	var sway := sin(time * 2.5) * 1.5
	var tail := [Vector2(0, -12), Vector2(1, -19), Vector2(3, -25), Vector2(4 + sway * 0.5, -31), Vector2(2 + sway, -36)]
	for place in tail.size():
		pen.disc(tail[place] + Vector2(0, -strike * place * 0.8), 4.4 - place * 0.4, color.darkened(0.1 + place * 0.04))
	var tip: Vector2 = tail[tail.size() - 1] + Vector2(0, -strike * 4.0)
	pen.poly([tip + Vector2(-2.5, -1), tip + Vector2(2.5, -1.5), tip + Vector2(-3.5, 6.5)], STEEL)
	pen.glow(tip + Vector2(-3, 6), 2.6, glow)
	# Six legs.
	for side in [-1.0, 1.0]:
		for leg in 3:
			var hip := Vector2(side * 6, -7 + leg * 2.0)
			var knee := hip + Vector2(side * 7, -4 + scuttle * side * (1.0 if leg % 2 == 0 else -1.0))
			var foot := hip + Vector2(side * 12, 6 - leg)
			pen.limb(hip, knee, 2.0, DARK)
			pen.limb(knee, foot, 1.8, DARK)
	# The body: armour plates in the department's colour.
	pen.oval(Vector2(0, -8), 11.5, 7.5, color)
	for plate in 3:
		pen.stroke(Vector2(-8 + plate * 1.5, -12 + plate * 3.0), Vector2(8 - plate * 1.5, -12 + plate * 3.0), color.darkened(0.35), 1.2)
	# Two claws, opening and snapping.
	var snap := 0.25 + 0.25 * sin(time * 3.0) + strike * 0.5
	for side in [-1.0, 1.0]:
		var elbow := Vector2(side * 13, -13)
		pen.limb(Vector2(side * 8, -9), elbow, 3.0, color.darkened(0.2))
		var claw := elbow + Vector2(side * 4, -6)
		pen.limb(elbow, claw, 3.4, color.darkened(0.2))
		if buckets:
			# A digger's bucket with teeth.
			pen.box(Rect2(claw + Vector2(-4.5, -7), Vector2(9, 7)), STEEL_DARK, 1.5)
			for tooth in 3:
				pen.poly([claw + Vector2(-4 + tooth * 3, -7), claw + Vector2(-2.5 + tooth * 3, -10), claw + Vector2(-1 + tooth * 3, -7)], STEEL, 0.8)
		else:
			pen.poly([claw, claw + Vector2(side * 6, -5 - snap * 4.0), claw + Vector2(side * 2, -3)], STEEL)
			pen.poly([claw, claw + Vector2(-side * 3, -6 - snap * 2.0), claw + Vector2(side * 1, -2)], STEEL)
	# Eyes.
	pen.glow(Vector2(-2.5, -6.5), 2.0, RED_GLOW)
	pen.glow(Vector2(2.5, -6.5), 2.0, RED_GLOW)
	pen.dot(Vector2(-2.5, -6.5), 1.1, RED_GLOW)
	pen.dot(Vector2(2.5, -6.5), 1.1, RED_GLOW)
	pen.zoom(1.0)


# --------------------------------------------------------------- flyers

## A sky knight riding a small storm cloud.
static func _cloudrider(pen: Pen, look: Dictionary, color: Color, time: float, strike: float) -> void:
	var glow: Color = look.get("glow", CYAN)
	var lift := sin(time * 3.0) * 1.6
	pen.oval(Vector2(0, 1), 9.0, 3.0, Color(0, 0, 0, 0.22), false)
	# Rain under the cloud.
	for drop in 3:
		var fall := fmod(time * 1.6 + drop * 0.33, 1.0)
		pen.stroke(Vector2(-6 + drop * 6, -6 + lift + fall * 5.0), Vector2(-6.5 + drop * 6, -4 + lift + fall * 5.0), Color(glow, 1.0 - fall), 1.2)
	var base := Vector2(0, -10 + lift)
	var puffs := [[Vector2(-8, 0), 5.5], [Vector2(7, 0), 6.0], [Vector2(0, -2.5), 6.5]]
	for puff in puffs:
		pen.dot(base + puff[0], float(puff[1]) + EDGE, OUT)
	for puff in puffs:
		pen.dot(base + puff[0], float(puff[1]), Color.WHITE)
	# The knight, from the waist up.
	var top := base.y - 22.0
	pen.box(Rect2(Vector2(-8, top), Vector2(16, 17)), color, 4.5)
	pen.box(Rect2(Vector2(-8, base.y - 9), Vector2(16, 3)), LEATHER, 1.0)
	_emblem(pen, "chevron", Vector2(0, top + 6), glow)
	_helm(pen, str(look.get("helm", "winged")), Vector2(0, top - 8), color, glow, time)
	pen.limb(Vector2(-8, top + 4), Vector2(-12, top + 12), 3.6, color.darkened(0.2))
	pen.limb(Vector2(8, top + 4), Vector2(13, top + 10), 3.6, color.darkened(0.2))
	_weapon(pen, str(look.get("weapon", "spear")), Vector2(13, top + 10), -0.25 - strike * 1.4, color, glow, time)


## An armoured trooper flying on a jet pack, with an arm blaster.
static func _jet(pen: Pen, look: Dictionary, color: Color, time: float, strike: float) -> void:
	var glow: Color = look.get("glow", EMBER)
	var lift := sin(time * 3.2) * 1.8
	pen.oval(Vector2(0, 1), 9.0, 3.0, Color(0, 0, 0, 0.22), false)
	var top := -34.0 + lift
	# Flames under the pack.
	for side in [-1.0, 1.0]:
		var flicker := 3.0 + absf(sin(time * 25.0 + side)) * 4.0
		pen.poly([Vector2(side * 7 - 2.5, top + 23), Vector2(side * 7 + 2.5, top + 23), Vector2(side * 7, top + 23 + flicker * 1.6)], glow, 0.0)
		pen.poly([Vector2(side * 7 - 1.2, top + 23), Vector2(side * 7 + 1.2, top + 23), Vector2(side * 7, top + 23 + flicker)], Color.WHITE, 0.0)
		pen.box(Rect2(Vector2(side * 7 - 3.5, top + 6), Vector2(7, 17)), STEEL_DARK, 2.5)
	# Legs hanging, body, helmet, blaster arm.
	pen.limb(Vector2(-3, top + 18), Vector2(-4.5, top + 26), 4.4, color.darkened(0.35))
	pen.limb(Vector2(3, top + 18), Vector2(4.5, top + 26), 4.4, color.darkened(0.35))
	pen.box(Rect2(Vector2(-8.5, top), Vector2(17, 19)), color, 4.5)
	pen.box(Rect2(Vector2(-8.5, top + 13), Vector2(17, 3)), LEATHER, 1.0)
	_emblem(pen, "gear", Vector2(0, top + 6), glow)
	_helm(pen, "visor", Vector2(0, top - 8), color, glow, time)
	pen.limb(Vector2(-8.5, top + 4), Vector2(-12, top + 13), 3.6, color.darkened(0.2))
	pen.limb(Vector2(8.5, top + 4), Vector2(13, top + 12), 3.6, color.darkened(0.2))
	_weapon(pen, "blaster", Vector2(13, top + 12), -0.5 - strike * 0.8, color, glow, time)


## A living spark: a bright core with angry eyes and electrons circling it.
static func _spark(pen: Pen, look: Dictionary, time: float, strike: float) -> void:
	var glow: Color = look.get("glow", ZAP)
	var lift := sin(time * 3.5) * 2.0
	var core := Vector2(0, -22 + lift)
	pen.oval(Vector2(0, 1), 7.0, 2.4, Color(0, 0, 0, 0.2), false)
	pen.glow(core, 13.0 + strike * 4.0 + sin(time * 6.0), glow)
	for orbit in 2:
		var tilt := time * (1.6 if orbit == 0 else -1.2) + orbit * 1.4
		pen.turn(core, tilt)
		pen.ring_oval(Vector2.ZERO, 15.0, 5.5, Color(Color.WHITE, 0.9), 1.3)
		pen.dot(Vector2(15.0, 0).rotated(time * 4.0 + orbit * PI) * Vector2(1.0, 5.5 / 15.0), 2.0, glow)
		pen.straight()
	pen.disc(core, 9.0, Color("fff8d2"))
	pen.disc(core, 6.5, glow, 0.0)
	_eyes(pen, core + Vector2(0, -0.5), 3.0, OUT, true)
	pen.stroke(core + Vector2(-2.5, 4), core + Vector2(2.5, 4), OUT, 1.2)
	var flick := int(time * 10.0) % 4
	_bolt(pen, [core + Vector2(8, 2), core + Vector2(13, 5 + flick), core + Vector2(11, 8), core + Vector2(16, 12)], glow)
	_bolt(pen, [core + Vector2(-8, 2), core + Vector2(-13, 6 - flick), core + Vector2(-11, 9), core + Vector2(-16, 13)], glow)


## A mechanical hawk with a scanning eye.
static func _hawk(pen: Pen, look: Dictionary, color: Color, time: float, strike: float) -> void:
	var glow: Color = look.get("glow", AMBER)
	var lift := sin(time * 3.0) * 1.8
	var body := Vector2(0, -24 + lift)
	var flap := sin(time * 8.0) * 4.0 - strike * 4.0
	pen.oval(Vector2(0, 1), 10.0, 3.0, Color(0, 0, 0, 0.22), false)
	for side in [-1.0, 1.0]:
		pen.poly([body + Vector2(side * 4, -3), body + Vector2(side * 20, -10 + flap), body + Vector2(side * 22, -4 + flap),
			body + Vector2(side * 17, -1 + flap * 0.6), body + Vector2(side * 19, 3 + flap * 0.5), body + Vector2(side * 5, 3)], STEEL)
		for feather in 3:
			pen.stroke(body + Vector2(side * (9 + feather * 3.5), -2 + flap * 0.4), body + Vector2(side * (11 + feather * 3.5), 2 + flap * 0.4), STEEL_DARK, 1.0)
	pen.poly([body + Vector2(-3, 6), body + Vector2(3, 6), body + Vector2(5, 13), body + Vector2(0, 11), body + Vector2(-5, 13)], color.darkened(0.25))
	pen.oval(body, 7.0, 9.0, color)
	pen.disc(body + Vector2(0, -9), 6.0, color.lightened(0.15))
	pen.poly([body + Vector2(-2, -7), body + Vector2(2, -7), body + Vector2(0, -2.5)], GOLD, 0.9)
	pen.glow(body + Vector2(-2.5, -10), 2.4, glow)
	pen.dot(body + Vector2(-2.5, -10), 1.2, glow)
	pen.dot(body + Vector2(2.5, -10), 1.1, OUT)
	pen.stroke(body + Vector2(-5.5, -13), body + Vector2(-1, -11.5), OUT, 1.1)
	pen.stroke(body + Vector2(5.5, -13), body + Vector2(1, -11.5), OUT, 1.1)
	for talon in [-1.0, 1.0]:
		pen.limb(body + Vector2(talon * 2.5, 8), body + Vector2(talon * 3.5, 13), 1.6, GOLD)


# ----------------------------------------------------------------- the pen

## Draws simple shapes with a dark edge, in the figure's own coordinates.
class Pen:
	var canvas: CanvasItem
	var origin: Vector2
	var size: float
	var _zoom := 1.0
	var _at := Vector2.ZERO
	var _angle := 0.0

	func _init(on: CanvasItem, feet: Vector2, how_big: float) -> void:
		canvas = on
		origin = feet
		size = how_big
		_frame()

	func _frame() -> void:
		var scale := size * _zoom
		canvas.draw_set_transform(origin + _at * scale, _angle, Vector2(scale, scale))

	## Draw everything that follows `factor` times larger, around the feet.
	func zoom(factor: float) -> void:
		_zoom = factor
		_frame()

	## Draw what follows around `point`, turned by `angle`; straight() undoes it.
	func turn(point: Vector2, angle: float) -> void:
		_at = point
		_angle = angle
		_frame()

	func straight() -> void:
		_at = Vector2.ZERO
		_angle = 0.0
		_frame()

	func done() -> void:
		canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	func shadow(width: float) -> void:
		oval(Vector2(0, 0.5), width, width * 0.3, Color(0, 0, 0, 0.26), false)

	## A filled circle with no edge.
	func dot(centre: Vector2, radius: float, fill: Color) -> void:
		canvas.draw_circle(centre, radius, fill)

	## A filled circle with a dark edge.
	func disc(centre: Vector2, radius: float, fill: Color, edge: float = Characters.EDGE) -> void:
		if edge > 0.0:
			canvas.draw_circle(centre, radius + edge, Characters.OUT)
		canvas.draw_circle(centre, radius, fill)

	## A soft halo of light.
	func glow(centre: Vector2, radius: float, color: Color) -> void:
		for ring in 3:
			canvas.draw_circle(centre, radius * (1.0 + ring * 0.45), Color(color, 0.22 - ring * 0.06))

	func ring(centre: Vector2, radius: float, color: Color, width: float) -> void:
		canvas.draw_arc(centre, radius, 0.0, TAU, 28, color, width, true)

	func arc(centre: Vector2, radius: float, from: float, to: float, color: Color, width: float) -> void:
		canvas.draw_arc(centre, radius, from, to, 18, color, width, true)

	## The outline of an ellipse, in the current frame.
	func ring_oval(centre: Vector2, across: float, down: float, color: Color, width: float) -> void:
		var points := PackedVector2Array()
		for place in 33:
			points.append(centre + Vector2(cos(place * TAU / 32.0) * across, sin(place * TAU / 32.0) * down))
		canvas.draw_polyline(points, color, width, true)

	func oval(centre: Vector2, across: float, down: float, fill: Color, edged: bool = true) -> void:
		var scale := size * _zoom
		var middle := origin + (_at + centre.rotated(_angle)) * scale
		if edged:
			canvas.draw_set_transform(middle, _angle, Vector2((across + Characters.EDGE) * scale, (down + Characters.EDGE) * scale))
			canvas.draw_circle(Vector2.ZERO, 1.0, Characters.OUT)
		canvas.draw_set_transform(middle, _angle, Vector2(across * scale, down * scale))
		canvas.draw_circle(Vector2.ZERO, 1.0, fill)
		_frame()

	## A rectangle with rounded corners.
	func box(area: Rect2, fill: Color, corner: float = 3.0, edged: bool = true) -> void:
		if edged:
			_rounded(area.grow(Characters.EDGE), corner + Characters.EDGE, Characters.OUT)
		_rounded(area, corner, fill)

	func _rounded(area: Rect2, corner: float, fill: Color) -> void:
		var r := minf(corner, minf(area.size.x, area.size.y) / 2.0)
		canvas.draw_rect(Rect2(area.position + Vector2(r, 0), area.size - Vector2(2.0 * r, 0)), fill)
		canvas.draw_rect(Rect2(area.position + Vector2(0, r), area.size - Vector2(0, 2.0 * r)), fill)
		for corner_at in [area.position + Vector2(r, r), Vector2(area.end.x - r, area.position.y + r),
				Vector2(area.position.x + r, area.end.y - r), area.end - Vector2(r, r)]:
			canvas.draw_circle(corner_at, r, fill)

	## A filled shape with a dark edge.
	func poly(points: Array, fill: Color, edge: float = Characters.EDGE) -> void:
		var shape := PackedVector2Array(points)
		canvas.draw_colored_polygon(shape, fill)
		if edge > 0.0:
			shape.append(shape[0])
			canvas.draw_polyline(shape, Characters.OUT, edge * 1.2, true)

	## A thick line with round ends and a dark edge: an arm or a leg.
	func limb(from: Vector2, to: Vector2, width: float, fill: Color) -> void:
		stroke(from, to, Characters.OUT, width + 2.0 * Characters.EDGE)
		stroke(from, to, fill, width)

	## A line with round ends.
	func stroke(from: Vector2, to: Vector2, color: Color, width: float) -> void:
		canvas.draw_line(from, to, color, width)
		canvas.draw_circle(from, width / 2.0, color)
		canvas.draw_circle(to, width / 2.0, color)
