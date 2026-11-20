import React from 'react';
import {Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {BAR, drift, fade, Full, FONT, glide, GREY, ramp, settle, Warrior, WHITE, Words} from './kit';

// ------------------------------------------------------------------ opening words

export const Opening: React.FC<{length: number}> = () => {
	const frame = useCurrentFrame();
	return (
		<Full style={{display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000', transform: `scale(${1 + frame * 0.00022})`}}>
			<div style={{position: 'absolute'}}>
				<Words text="Four departments." at={14} out={BAR - 26} size={104} />
			</div>
			<div style={{position: 'absolute'}}>
				<Words text="One arena." at={BAR + 2} out={2 * BAR - 24} size={104} />
			</div>
		</Full>
	);
};

// ------------------------------------------------------------------ four departments, one long stage

// nudge: a big letter's built-in side space, taken off so that the name starts exactly where the motto does.
const DEPARTMENTS = [
	{id: 'cse', short: 'CSE', motto: 'Fast, cheap and clever.', nudge: -4, color: '#58a6ee', front: [0, 1, 4, 7], back: [2, 3, 5, 6]},
	{id: 'eee', short: 'EEE', motto: 'Hits hard, breaks easily.', nudge: -6, color: '#f2d24b', front: [0, 1, 4, 7], back: [2, 3, 5, 6]},
	{id: 'me', short: 'ME', motto: 'Heavy, slow and hard to stop.', nudge: -6, color: '#f28c38', front: [0, 1, 3, 5], back: [2, 4, 6, 7]},
	{id: 'ce', short: 'CE', motto: 'Slow to arrive, slower to leave.', nudge: -6, color: '#b48cf0', front: [0, 1, 4, 7], back: [2, 3, 5, 6]},
];
const STAGE = 1920;
const TEXT_X = 110;

// The camera slides from department to department in the last beat of each bar, and keeps drifting while it rests.
const DRIFT = 0.5;
const stageX = (frame: number) => {
	let x = (frame - BAR / 2) * DRIFT;
	for (let place = 1; place < DEPARTMENTS.length; place++) {
		x += ramp(frame, place * BAR - 30, place * BAR + 22, 0, STAGE - BAR * DRIFT, glide);
	}
	return x;
};

export const Departments: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	const x = stageX(frame);
	return (
		<Full style={{background: '#000', overflow: 'hidden', opacity: fade(frame, length, 10, 12)}}>
			{DEPARTMENTS.map((department, place) => {
				const home = place * STAGE;
				const start = place * BAR;
				const away = home - x;
				if (Math.abs(away) > STAGE) return null;
				const near = interpolate(Math.abs(away), [500, 1300], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
				const picture = frame - start + 30;
				return (
					<React.Fragment key={department.id}>
						{/* A soft pool of the department's colour on the floor. */}
						<div
							style={{
								position: 'absolute',
								left: 1180 + away,
								top: 760,
								width: 1500,
								height: 280,
								marginLeft: -750,
								borderRadius: '50%',
								background: department.color,
								opacity: 0.17 * near,
								filter: 'blur(90px)',
							}}
						/>
						{/* The back row, smaller and softer, moves more slowly. */}
						{department.back.map((card, seat) => (
							<div key={card} style={{position: 'absolute', left: 862 + seat * 235 + away * 0.9, top: 262, opacity: 0.46 * near, filter: 'blur(2px)'}}>
								<Warrior dept={department.id} place={card} frame={picture + seat * 5} scale={0.6} />
							</div>
						))}
						{/* The front row. */}
						{department.front.map((card, seat) => (
							<div
								key={card}
								style={{
									position: 'absolute',
									left: 520 + seat * 330 + away,
									top: 500,
									opacity: near,
									transform: `translateY(${(1 - ramp(frame, start - 26 + seat * 3, start + 34 + seat * 3)) * 56}px)`,
								}}
							>
								<Warrior dept={department.id} place={card} frame={picture + seat * 7} scale={0.92} />
							</div>
						))}
						{/* The name, a little ahead of the warriors. */}
						<div style={{position: 'absolute', left: TEXT_X + away * 1.06, top: 96, width: 1200, opacity: near}}>
							<div style={{fontFamily: FONT, fontWeight: 700, fontSize: 190, letterSpacing: '-0.03em', color: department.color, lineHeight: 1, marginLeft: department.nudge}}>
								{department.short}
							</div>
							<div style={{fontFamily: FONT, fontWeight: 600, fontSize: 52, letterSpacing: '-0.018em', color: WHITE, marginTop: 10}}>
								{department.motto}
							</div>
						</div>
					</React.Fragment>
				);
			})}
		</Full>
	);
};

// ------------------------------------------------------------------ the cards

const CARDS = ['cse_7', 'eee_4', 'me_0', 'ce_0', 'cse_6', 'eee_1', 'me_5', 'ce_2', 'eee_5', 'cse_3', 'me_3', 'ce_5'];
const CARD_W = 560;
const CARD_H = 472;

export const Cards: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	const slide = interpolate(frame, [0, length], [120, -1880], {easing: drift});
	return (
		<Full style={{background: '#000', overflow: 'hidden', opacity: fade(frame, length, 10, 16)}}>
			<div style={{position: 'absolute', top: 249, width: '100%', transform: 'translateY(-50%)', display: 'flex', justifyContent: 'center', gap: '0.24em', fontSize: 92}}>
				<Words text="32 warriors." at={6} size={92} />
				<Words text="One special each." at={18} size={92} color={GREY} />
			</div>
			{CARDS.map((card, place) => {
				const start = 4 + place * 5;
				return (
					<div
						key={card}
						style={{
							position: 'absolute',
							left: slide + place * (CARD_W + 28),
							top: 409,
							width: CARD_W,
							height: CARD_H,
							borderRadius: 24,
							overflow: 'hidden',
							opacity: ramp(frame, start, start + 26),
							transform: `translateY(${(1 - ramp(frame, start, start + 54)) * 150}px)`,
						}}
					>
						<Img src={staticFile(`cards/${card}.png`)} style={{width: '100%', height: '100%'}} />
					</div>
				);
			})}
		</Full>
	);
};

// ------------------------------------------------------------------ the end

const LINEUP: [string, number][] = [
	['cse', 0], ['eee', 7], ['me', 3], ['ce', 0], ['cse', 7], ['eee', 4], ['me', 5], ['ce', 7],
];

export const Ending: React.FC<{length: number}> = ({length}) => {
	const frame = useCurrentFrame();
	const scale = interpolate(frame, [0, length], [1.0, 1.035], {easing: Easing.linear});
	const out = ramp(frame, length - 34, length - 6, 1, 0, Easing.linear);
	return (
		<Full style={{background: '#000', display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: out}}>
			<div style={{position: 'absolute', top: 218, width: '100%', textAlign: 'center', transform: `scale(${scale})`}}>
				<Words text="KUET Royale" at={8} size={176} weight={700} stagger={7} style={{letterSpacing: '-0.03em', position: 'relative', left: -4.5}} />
				<Words text="Department Wars." at={40} size={58} color={GREY} style={{marginTop: 18}} />
			</div>
			<div style={{position: 'absolute', left: 0, right: 0, top: 610, display: 'flex', justifyContent: 'center', gap: 2}}>
				{LINEUP.map(([dept, place], seat) => {
					const start = 54 + seat * 4;
					return (
						<div key={seat} style={{opacity: ramp(frame, start, start + 34), transform: `translateY(${(1 - ramp(frame, start, start + 60)) * 70}px)`}}>
							<Warrior dept={dept} place={place} frame={frame} scale={0.46} />
						</div>
					);
				})}
			</div>
		</Full>
	);
};
