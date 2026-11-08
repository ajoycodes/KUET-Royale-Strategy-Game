import React from 'react';
import {Easing, Sequence, useCurrentFrame} from 'remotion';
import shots from './shots.json';
import {BAR, fade, Footage, Full, glide, GREY, Key, ramp, WHITE, Words} from './kit';

type Shot = keyof typeof shots;

// Every frame keeps this distance from the edge of the film, and captions start at TEXT_X.
const MARGIN = 60;
const TEXT_X = 110;

const whole: Key = {f: 0, cx: 640, cy: 360, s: 1.5};

// The whole scene grows very slowly, together, so that frames and words never move against each other.
const push = (frame: number) => `scale(${1 + frame * 0.00008})`;

// A frame of footage that rises into place and settles.
const Frame: React.FC<{at?: number; x: number; y: number; w: number; h: number; radius?: number; children: React.ReactNode}> = ({
	at = 0,
	x,
	y,
	w,
	h,
	radius = 26,
	children,
}) => {
	const frame = useCurrentFrame();
	const up = ramp(frame, at, at + 62);
	return (
		<div
			style={{
				position: 'absolute',
				left: x,
				top: y,
				width: w,
				height: h,
				borderRadius: radius,
				overflow: 'hidden',
				opacity: ramp(frame, at, at + 22, 0, 1, Easing.linear),
				transform: `translateY(${(1 - up) * 70}px) scale(${0.97 + up * 0.03})`,
			}}
		>
			{children}
		</div>
	);
};

// A caption beside a frame: the block of words is centred on the frame's middle line.
const Caption: React.FC<{lines: string[]; x?: number; at?: number; size?: number; width?: number; white?: number}> = ({
	lines,
	x = TEXT_X,
	at = 6,
	size = 88,
	width = 720,
	white = 1,
}) => (
	<div style={{position: 'absolute', left: x, top: 542, width, transform: 'translateY(-50%)'}}>
		{lines.map((line, place) => (
			<Words key={line} text={line} at={at + place * 14} size={size} color={place >= white ? GREY : WHITE} />
		))}
	</div>
);

// A heading centred above a frame, in the middle of the space between the frame and the top of the film.
const Heading: React.FC<{text: string; second?: string; above: number; at?: number; size?: number}> = ({text, second, above, at = 4, size = 88}) => (
	<div
		style={{
			position: 'absolute',
			left: 0,
			right: 0,
			top: above / 2,
			transform: 'translateY(-50%)',
			display: 'flex',
			justifyContent: 'center',
			gap: '0.24em',
			fontSize: size,
		}}
	>
		<Words text={text} at={at} size={size} />
		{second ? <Words text={second} at={at + 12} size={size} color={GREY} /> : null}
	</div>
);

// The arena and a side's panel, from the arena's left edge to the panel's right edge, top to bottom of the arena.
const ARENA_AND_PANEL = {x: 656, y: MARGIN, w: 1204, h: 960};
const ARENA_AND_PANEL_KEY: Key = {f: 0, cx: 865, cy: 364, s: 1.486};
// The arena alone, rim to rim, ending on its bottom edge.
const ARENA = {x: 1140, y: MARGIN, w: 720, h: 960};
const arenaKeys = (length: number): Key[] => [{f: 0, cx: 640, cy: 420, s: 2}, {f: length, cx: 640, cy: 444, s: 2}];
// The whole screen, centred under a heading.
const SCREEN = {x: 240, y: 210, w: 1440, h: 810};
const SCREEN_KEY: Key = {f: 0, cx: 640, cy: 360, s: 1.125};

// ------------------------------------------------------------------ the title, and the game rising under it

export const TitleRise: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	const come = ramp(frame, 8, 130);
	const fill = ramp(frame, 150, length, 0, 1, glide);
	const tilt = 44 * (1 - come);
	const y = (1 - come) * 620 + (1 - fill) * 330;
	const scale = 0.7 + fill * 0.3;
	return (
		<Full style={{background: '#000', overflow: 'hidden'}}>
			<div style={{position: 'absolute', top: 66, width: '100%', textAlign: 'center'}}>
				<Words text="KUET Royale" at={0} out={150} size={150} weight={700} stagger={6} style={{letterSpacing: '-0.03em', position: 'relative', left: -3.5}} />
			</div>
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					width: 1920,
					height: 1080,
					transformOrigin: '50% 0%',
					transform: `perspective(2600px) translateY(${y}px) rotateX(${tilt}deg) scale(${scale})`,
					borderRadius: 34 * (1 - fill),
					overflow: 'hidden',
					boxShadow: '0 0 0 1.5px rgba(255,255,255,0.09)',
				}}
			>
				<Footage shot="title" width={1920} height={1080} keys={[whole]} />
			</div>
		</Full>
	);
};

// ------------------------------------------------------------------ picking and dropping

export const Pick: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{background: '#000', opacity: fade(frame, length, 10, 12), transform: push(frame)}}>
			<Heading text="Pick your four." above={SCREEN.y} />
			<Frame {...SCREEN}>
				<Footage shot="pick" rate={1.15} width={SCREEN.w} height={SCREEN.h} keys={[SCREEN_KEY]} />
			</Frame>
		</Full>
	);
};

export const Drop: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{background: '#000', opacity: fade(frame, length, 10, 12), transform: push(frame)}}>
			<Caption lines={['Drop them', 'anywhere', 'on your half.']} white={2} width={520} />
			<Frame {...ARENA_AND_PANEL} at={2}>
				<Footage shot="drop" width={ARENA_AND_PANEL.w} height={ARENA_AND_PANEL.h} keys={[ARENA_AND_PANEL_KEY]} />
			</Frame>
		</Full>
	);
};

// ------------------------------------------------------------------ the fight

export const Fight: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{background: '#000', opacity: fade(frame, length, 10, 14), transform: push(frame)}}>
			<Caption lines={['Then let them', 'fight.']} width={900} />
			<Frame {...ARENA}>
				<Footage shot="fight" width={ARENA.w} height={ARENA.h} keys={arenaKeys(length)} easing={Easing.linear} />
			</Frame>
		</Full>
	);
};

export const Towers: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{background: '#000', opacity: fade(frame, length, 10, 12), transform: push(frame)}}>
			<Caption lines={['Towers', 'fight back.']} x={1180} />
			<Frame x={MARGIN} y={MARGIN} w={1040} h={960}>
				<Footage shot="towers" width={1040} height={960} keys={[{f: 0, cx: 640, cy: 517.85, s: 2.889}]} />
			</Frame>
		</Full>
	);
};

// ------------------------------------------------------------------ the two AIs

const SPLIT = 186;

// Covers the foot of the button the crop has cut through, in the colour of the panel behind it.
const PanelTop: React.FC = () => <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 13, background: '#1d4c7e'}} />;

export const Think: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	const half = Math.round((length - SPLIT) / 2);
	return (
		<Full style={{background: '#000'}}>
			<Sequence durationInFrames={SPLIT}>
				<Full style={{opacity: fade(frame, SPLIT, 10, 14), transform: push(frame)}}>
					<Heading text="Two AIs." second="Watch them think." above={196} at={2} />
					<Frame x={110} y={196} w={720} h={824} at={2}>
						<Footage shot="tiles" width={720} height={824} keys={[{f: 0, cx: 640, cy: 478, s: 2}]} />
					</Frame>
					<Frame x={850} y={196} w={960} h={402} at={10}>
						<Footage shot="alphaPanel" width={960} height={402} keys={[{f: 0, cx: 236, cy: 533.5, s: 2.2}]} />
						<PanelTop />
					</Frame>
					<Frame x={850} y={618} w={960} h={402} at={18}>
						<Footage shot="mctsPanel" width={960} height={402} keys={[{f: 0, cx: 1044, cy: 533.5, s: 2.2}]} />
						<PanelTop />
					</Frame>
				</Full>
			</Sequence>
			<Sequence from={SPLIT} durationInFrames={half + 6}>
				<Tree shot="alphaTree" length={half + 6} />
			</Sequence>
			<Sequence from={SPLIT + half} durationInFrames={length - SPLIT - half}>
				<Tree shot="mctsTree" length={length - SPLIT - half} />
			</Sequence>
		</Full>
	);
};

// A brain's tree, framed exactly on the sheet the game draws it on.
const Tree: React.FC<{shot: Shot; length: number}> = ({shot, length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{opacity: fade(frame, length, 8, 8), transform: push(frame)}}>
			<Frame x={150} y={MARGIN} w={1620} h={960} radius={30} at={-40}>
				<Footage shot={shot} width={1620} height={960} keys={[{f: 0, cx: 640, cy: 360, s: 1.5}]} />
			</Frame>
		</Full>
	);
};

// ------------------------------------------------------------------ Power mode

const CUT = BAR / 2;

export const Power: React.FC<{length: number}> = () => {
	const frame = useCurrentFrame();
	return (
		<Full style={{background: '#000'}}>
			<Sequence durationInFrames={BAR}>
				<Full style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
					<div style={{textAlign: 'center', transform: `scale(${1 + frame * 0.0006})`}}>
						<Words text="Power mode." at={0} out={BAR - 18} size={190} weight={700} stagger={7} style={{letterSpacing: '-0.03em'}} />
					</div>
				</Full>
			</Sequence>
			{POWER_CUTS.map((cut, place) => (
				<Sequence key={cut.shot} from={BAR + place * CUT} durationInFrames={cut.bars * BAR + 6}>
					<PowerCut {...cut} length={cut.bars * BAR + 6} />
				</Sequence>
			))}
		</Full>
	);
};

type Box = {x: number; y: number; w: number; h: number};

const PowerCut: React.FC<{shot: Shot; box: Box; keys: Key[]; words: string; heading?: boolean; length: number}> = ({shot, box, keys, words, heading, length}) => {
	const frame = useCurrentFrame();
	return (
		<Full style={{opacity: fade(frame, length, 5, 6), transform: push(frame)}}>
			{heading ? <Heading text={words} above={box.y} at={2} /> : <Caption lines={[words]} at={2} width={box.x - TEXT_X - 20} />}
			<Frame {...box} at={-30}>
				<Footage shot={shot} width={box.w} height={box.h} keys={keys} easing={Easing.linear} />
			</Frame>
		</Full>
	);
};

const POWER_CUTS: {shot: Shot; bars: number; words: string; box: Box; keys: Key[]; heading?: boolean}[] = [
	{shot: 'clock', bars: 0.5, words: 'One minute.', box: {x: 900, y: MARGIN, w: 960, h: 960}, keys: [{f: 0, cx: 640, cy: 180, s: 2.667}]},
	{shot: 'coins', bars: 0.5, words: 'Earn coins.', box: {x: 600, y: 148, w: 1260, h: 784}, keys: [{f: 0, cx: 1044, cy: 310, s: 2.8}]},
	{shot: 'spend', bars: 0.5, words: 'Spend them.', box: ARENA_AND_PANEL, keys: [ARENA_AND_PANEL_KEY]},
	{shot: 'melee', bars: 0.5, words: 'No turns.', box: ARENA, keys: arenaKeys(78)},
	{shot: 'castle', bars: 1, words: 'First tower down ends it.', box: SCREEN, heading: true, keys: [SCREEN_KEY]},
];
