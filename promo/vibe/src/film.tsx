import React from 'react';
import {Audio, Easing, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {BAR, Bars, Coin} from './kit';
import index from './text_index.json';

type Name = keyof typeof index;

export const FILM_FPS = 30;
export const FILM_FRAMES = 1800;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// When each shot starts, in frames of the finished film.
const SHOT = {battlefield: 0, faceoff: 420, champion: 660, clash: 780, siege: 900, cards: 1020, storm: 1140, real1: 1260, rush: 1320, real2: 1380, lastBlow: 1440, castle: 1500, title: 1620};

// A picture of forged letters (tools/lettering.py). With shine, a band of light runs across the metal only.
const Art: React.FC<{name: Name; sweep?: number}> = ({name, sweep}) => {
	const {w, h} = index[name];
	const fill: React.CSSProperties = {position: 'absolute', left: 0, top: 0, width: w, height: h};
	const band = sweep === undefined ? '' : `linear-gradient(105deg, transparent ${sweep - 13}%, #000 ${sweep}%, transparent ${sweep + 13}%)`;
	return (
		<div style={{position: 'relative', width: w, height: h}}>
			<Img src={staticFile(`text/${name}.png`)} style={fill} />
			{sweep === undefined ? null : <Img src={staticFile(`text/${name}_shine.png`)} style={{...fill, maskImage: band, WebkitMaskImage: band}} />}
		</div>
	);
};

// Big letters that land with a hit: they come in large and blurred, go slightly past, and settle.
// A band of light then runs across the metal, and they keep growing very slowly.
const Slam: React.FC<{at: number; out?: number; name: Name; origin?: string}> = ({at, out, name, origin}) => {
	const frame = useCurrentFrame();
	const age = frame - at;
	if (age < 0 || (out !== undefined && frame >= out + 8)) return null;
	const land = interpolate(age, [0, 4, 9], [1.55, 0.975, 1], {...clamp, easing: Easing.bezier(0.2, 0.7, 0.3, 1)});
	const blur = interpolate(age, [0, 4], [14, 0], clamp);
	const opacity = interpolate(age, [0, 2], [0, 1], clamp) * (out === undefined ? 1 : interpolate(frame, [out, out + 8], [1, 0], clamp));
	const grow = 1 + Math.max(age - 9, 0) * 0.00042;
	const sweep = age >= 3 && age <= 28 ? interpolate(age, [3, 28], [-20, 120], clamp) : undefined;
	return (
		<div style={{opacity, filter: blur > 0.1 ? `blur(${blur}px)` : undefined, transform: `scale(${land * grow})`, transformOrigin: origin ?? '50% 50%'}}>
			<Art name={name} sweep={sweep} />
		</div>
	);
};

// Smaller lines rise softly into place.
const Soft: React.FC<{at: number; name: Name}> = ({at, name}) => {
	const frame = useCurrentFrame();
	const age = frame - at;
	if (age < 0) return null;
	const show = interpolate(age, [0, 12], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
	return (
		<div style={{opacity: show, transform: `translateY(${(1 - show) * 14}px)`}}>
			<Art name={name} />
		</div>
	);
};

// The ink of each picture sits exactly in its middle, so the middle of the picture is what gets placed.
const Middle: React.FC<{y: number; children: React.ReactNode}> = ({y, children}) => (
	<div style={{position: 'absolute', left: 0, right: 0, top: y, display: 'flex', justifyContent: 'center', transform: 'translateY(-50%)'}}>{children}</div>
);

// Ink starting exactly at x from the left, or ending exactly x from the right.
const FromLeft: React.FC<{x: number; y: number; name: Name; children: React.ReactNode}> = ({x, y, name, children}) => {
	const {w, h, ink_w: ink} = index[name];
	return <div style={{position: 'absolute', left: x - (w - ink) / 2, top: y - h / 2}}>{children}</div>;
};

const FromRight: React.FC<{x: number; y: number; name: Name; children: React.ReactNode}> = ({x, y, name, children}) => {
	const {w, h, ink_w: ink} = index[name];
	return <div style={{position: 'absolute', right: x - (w - ink) / 2, top: y - h / 2}}>{children}</div>;
};

// ---------------------------------------------------------------- the words of each shot

const Battlefield = () => (
	<>
		<Middle y={222}>
			<Slam at={120} out={288} name="four_armies" />
		</Middle>
		<Middle y={222}>
			<Slam at={330} name="one_battlefield" />
		</Middle>
	</>
);

const Faceoff = () => (
	<>
		<FromLeft x={90} y={172} name="cse">
			<Slam at={45} name="cse" />
		</FromLeft>
		<FromLeft x={90} y={250} name="line_cse">
			<Soft at={51} name="line_cse" />
		</FromLeft>
		<FromRight x={90} y={172} name="me">
			<Slam at={120} name="me" />
		</FromRight>
		<FromRight x={90} y={250} name="line_me">
			<Soft at={126} name="line_me" />
		</FromRight>
		<Middle y={800}>
			<Slam at={180} name="vs" />
		</Middle>
	</>
);

const Champion = () => (
	<>
		<FromLeft x={110} y={480} name="capacitor">
			<Slam at={0} name="capacitor" />
		</FromLeft>
		<FromLeft x={110} y={572} name="line_cap1">
			<Soft at={15} name="line_cap1" />
		</FromLeft>
		<FromLeft x={110} y={620} name="line_cap2">
			<Soft at={45} name="line_cap2" />
		</FromLeft>
	</>
);

const Clash = () => (
	<Middle y={892}>
		<Slam at={60} name="hold_bridge" />
	</Middle>
);

// A soft dark band behind a headline on the real game, so that words floating in the game do not fight with it.
const TopShade: React.FC = () => <div style={{position: 'absolute', left: 0, right: 0, top: BAR, height: 230, background: 'linear-gradient(180deg, rgba(4,6,10,.92) 0%, rgba(4,6,10,.78) 48%, rgba(4,6,10,0) 100%)'}} />;

const Siege = () => (
	<>
		<TopShade />
		<Middle y={166}>
			<Slam at={0} name="every_drop" />
		</Middle>
	</>
);

// One card, dropped onto the table on the beat.
const CARDS: {name: Name; hero: string; cost: number; special: Name; x: number; y: number; r: number; at: number}[] = [
	{name: 'card_compiler', hero: 'compiler', cost: 5, special: 'special_armour', x: 266, y: 276, r: -6, at: 15},
	{name: 'card_logic_bomber', hero: 'logic-bomber', cost: 4, special: 'special_splash', x: 620, y: 256, r: -2, at: 30},
	{name: 'card_stack_runner', hero: 'stack-runner', cost: 2, special: 'special_blast', x: 974, y: 256, r: 2, at: 45},
	{name: 'card_cloud_drone', hero: 'cloud-drone', cost: 3, special: 'special_hover', x: 1328, y: 276, r: 6, at: 60},
];

const DroppedCard: React.FC<(typeof CARDS)[number]> = ({name, hero, cost, special, x, y, r, at}) => {
	const frame = useCurrentFrame();
	const age = frame - at;
	const start = age + 6;
	if (start < 0) return null;
	const fall = interpolate(start, [0, 6], [0, 1], {...clamp, easing: Easing.bezier(0.5, 0, 1, 0.7)});
	const scale = interpolate(fall, [0, 1], [1.5, 1]) * (age >= 0 ? 1 + 0.035 * Math.exp(-age / 2) * Math.cos(age * 1.4) : 1);
	const glow = age >= 0 ? Math.exp(-age / 6) : 0;
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				opacity: interpolate(start, [0, 2], [0, 1], clamp),
				transform: `translateY(${(1 - fall) * -330}px) rotate(${r + (1 - fall) * r * 2.4}deg) scale(${scale})`,
				filter: `drop-shadow(0 0 ${44 * glow}px rgba(255,180,90,${0.95 * glow}))`,
			}}
		>
			<BattleCardFilm name={name} hero={hero} cost={cost} special={special} />
		</div>
	);
};

const COLOURS: [string, string] = ['#2f76cf', '#0d2c63'];

const BattleCardFilm: React.FC<{name: Name; hero: string; cost: number; special: Name}> = ({name, hero, cost, special}) => {
	const w = 326;
	const h = w * 1.42;
	const u = w / 100;
	const size = w * 1.5;
	const windowBottom = h - 27 * u;
	return (
		<div style={{position: 'relative', width: w, height: h}}>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					borderRadius: 5 * u,
					border: `${0.9 * u}px solid #1a0f06`,
					background: 'linear-gradient(180deg,#5a3a1e 0%,#3d2613 55%,#2a190c 100%)',
					boxShadow: `inset 0 0 0 ${0.8 * u}px #c9963e, inset 0 ${1.2 * u}px ${1 * u}px rgba(255,220,150,.4), 0 ${3 * u}px ${9 * u}px rgba(0,0,0,.85)`,
					boxSizing: 'border-box',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 5 * u,
					right: 5 * u,
					top: 5 * u,
					height: windowBottom - 5 * u,
					borderRadius: 3 * u,
					overflow: 'hidden',
					border: `${0.7 * u}px solid #c9963e`,
					background: `radial-gradient(ellipse 80% 70% at 50% 42%, ${COLOURS[0]} 0%, ${COLOURS[1]} 62%, #060a18 100%)`,
					boxSizing: 'border-box',
				}}
			>
				<Img src={staticFile(`lit/${hero}.png`)} style={{position: 'absolute', width: size, height: size, left: (w - 10 * u - 1.4 * u - size) / 2, top: windowBottom - 5 * u - (size * 1340) / 1500 - 1 * u}} />
			</div>
			<Middle y={windowBottom + 12 * u}>
				<Art name={name} />
			</Middle>
			<Middle y={windowBottom + 21 * u}>
				<Art name={special} />
			</Middle>
			<Coin value={cost} size={21 * u} style={{position: 'absolute', left: -5 * u, top: -5 * u}} />
		</div>
	);
};

const Cards = () => {
	const frame = useCurrentFrame();
	return (
		<div style={{position: 'absolute', inset: 0, transform: `scale(${1 + frame * 0.00035})`}}>
			<Middle y={170}>
				<Slam at={0} name="choose_four" />
			</Middle>
			{CARDS.map((card) => (
				<DroppedCard key={card.name} {...card} />
			))}
			<Middle y={1080 - BAR - 36}>
				<Soft at={66} name="line_cards" />
			</Middle>
		</div>
	);
};

const Storm = () => (
	<>
		<Middle y={258}>
			<Slam at={60} name="power_mode" />
		</Middle>
		<Middle y={410}>
			<Soft at={72} name="line_power" />
		</Middle>
	</>
);

const Cut: React.FC<{name: Name; y?: number}> = ({name, y = 166}) => (
	<Middle y={y}>
		<Slam at={0} name={name} />
	</Middle>
);

const CastleWords = () => (
	<Middle y={200}>
		<Slam at={30} name="castle_down" />
	</Middle>
);

const Title = () => {
	const frame = useCurrentFrame();
	const out = interpolate(frame, [158, 176], [1, 0], clamp);
	return (
		<div style={{opacity: out, position: 'absolute', inset: 0}}>
			<Middle y={272}>
				<Slam at={30} name="kuet_royale" />
			</Middle>
			<Middle y={452}>
				<Soft at={48} name="department_wars" />
			</Middle>
			<Middle y={500}>
				<Soft at={66} name="line_title" />
			</Middle>
		</div>
	);
};

// ---------------------------------------------------------------- the film

const At: React.FC<{from: number; length: number; children: React.ReactNode}> = ({from, length, children}) => (
	<Sequence from={from} durationInFrames={length} layout="none">
		{children}
	</Sequence>
);

export const Film: React.FC = () => (
	<div style={{position: 'absolute', inset: 0, background: '#000'}}>
		<OffthreadVideo src={staticFile('film_base.mp4')} muted style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
		<Audio src={staticFile('battle.wav')} />
		<At from={SHOT.battlefield} length={420}><Battlefield /></At>
		<At from={SHOT.faceoff} length={240}><Faceoff /></At>
		<At from={SHOT.champion} length={120}><Champion /></At>
		<At from={SHOT.clash} length={120}><Clash /></At>
		<At from={SHOT.siege} length={120}><Siege /></At>
		<At from={SHOT.cards} length={120}><Cards /></At>
		<At from={SHOT.storm} length={120}><Storm /></At>
		<At from={SHOT.real1} length={60}><Cut name="one_minute" /></At>
		<At from={SHOT.rush} length={60}><Cut name="no_turns" /></At>
		<At from={SHOT.real2} length={60}><Cut name="hit_hard" y={890} /></At>
		<At from={SHOT.lastBlow} length={60}><TopShade /><Cut name="finish_it" /></At>
		<At from={SHOT.castle} length={120}><CastleWords /></At>
		<At from={SHOT.title} length={180}><Title /></At>
		<Bars />
	</div>
);
