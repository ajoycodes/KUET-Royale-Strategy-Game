import React from 'react';
import {Easing, Img, interpolate, OffthreadVideo, staticFile, useCurrentFrame} from 'remotion';
import {loadFont} from '@remotion/google-fonts/InterTight';
import shots from './shots.json';

const {fontFamily} = loadFont('normal', {weights: ['500', '600', '700'], subsets: ['latin']});

export const FONT = fontFamily;
export const WHITE = '#f5f5f7';
export const GREY = '#8e8e93';

// A beat is 36 frames at 60 fps and 100 beats a minute. Every scene starts on a bar or half a bar.
export const BAR = 144;

// The long, soft settle that gives the whole film its feel.
export const settle = Easing.bezier(0.16, 1, 0.3, 1);
export const glide = Easing.bezier(0.62, 0, 0.2, 1);
export const drift = Easing.bezier(0.3, 0.1, 0.6, 0.9);

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const ramp = (frame: number, from: number, to: number, a = 0, b = 1, easing = settle) =>
	interpolate(frame, [from, to], [a, b], {...clamp, easing});

// Words that rise out of a soft blur one after another, and leave the same way.
export const Words: React.FC<{
	text: string;
	at?: number;
	out?: number;
	size?: number;
	color?: string;
	weight?: number;
	style?: React.CSSProperties;
	stagger?: number;
}> = ({text, at = 0, out, size = 88, color = WHITE, weight = 600, style, stagger = 4}) => {
	const frame = useCurrentFrame();
	const leaving = out === undefined ? 0 : ramp(frame, out, out + 20, 0, 1, Easing.bezier(0.4, 0, 1, 1));
	const words = text.split(' ');
	return (
		<div
			style={{
				fontFamily: FONT,
				fontSize: size,
				fontWeight: weight,
				color,
				letterSpacing: '-0.018em',
				lineHeight: 1.06,
				...style,
			}}
		>
			{words.map((word, place) => {
				const start = at + place * stagger;
				const showing = ramp(frame, start, start + 46);
				return (
					<span
						key={place}
						style={{
							display: 'inline-block',
							marginRight: place < words.length - 1 ? '0.24em' : 0,
							opacity: Math.min(1, ramp(frame, start, start + 24)) * (1 - leaving),
							transform: `translateY(${(1 - showing) * 0.42 - leaving * 0.14}em)`,
							filter: `blur(${(1 - showing) * 16 + leaving * 12}px)`,
						}}
					>
						{word}
					</span>
				);
			})}
		</div>
	);
};

export type Camera = {cx: number; cy: number; s: number};
export type Key = Camera & {f: number};

// Where the camera is on a list of stops: it eases between stops and rests on none of them.
export const cameraAt = (frame: number, keys: Key[], easing = glide): Camera => {
	if (keys.length === 1) return keys[0];
	const stops = keys.map((key) => key.f);
	const mix = (pick: (key: Key) => number) => interpolate(frame, stops, keys.map(pick), {...clamp, easing});
	return {cx: mix((key) => key.cx), cy: mix((key) => key.cy), s: mix((key) => key.s)};
};

// The game's own screen seen through a window. A camera says which point of the 1280 x 720 screen is at the
// window's centre, and how many output pixels one screen pixel covers: 1.5 is the whole screen at 1080p.
// Each shot is a small file holding only the part of the screen it needs (shots.json).
export const Footage: React.FC<{
	shot: keyof typeof shots;
	width: number;
	height: number;
	keys: Key[];
	rate?: number;
	easing?: (t: number) => number;
	style?: React.CSSProperties;
}> = ({shot, width, height, keys, rate = 1, easing, style}) => {
	const frame = useCurrentFrame();
	const {cx, cy, s} = cameraAt(frame, keys, easing);
	const [x, y, w, h] = shots[shot].crop;
	return (
		<div style={{position: 'relative', width, height, overflow: 'hidden', background: '#000', ...style}}>
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					width: 1280,
					height: 720,
					transformOrigin: '0 0',
					transform: `translate(${width / 2 - cx * s}px, ${height / 2 - cy * s}px) scale(${s})`,
				}}
			>
				<OffthreadVideo src={staticFile(`shots/${shot}.mp4`)} playbackRate={rate} muted style={{position: 'absolute', left: x, top: y, width: w, height: h}} />
			</div>
		</div>
	);
};

// One warrior, cut from a department's strip of eight. Their idle motion plays from the frame number given.
export const Warrior: React.FC<{dept: string; place: number; frame: number; scale: number; style?: React.CSSProperties}> = ({
	dept,
	place,
	frame,
	scale,
	style,
}) => {
	const number = String(Math.max(0, Math.min(199, Math.round(frame)))).padStart(3, '0');
	return (
		<div style={{position: 'relative', width: 480 * scale, height: 540 * scale, overflow: 'hidden', ...style}}>
			<Img
				src={staticFile(`figs/${dept}/${number}.png`)}
				style={{position: 'absolute', left: -480 * place * scale, top: 0, width: 3840 * scale, height: 540 * scale, maxWidth: 'none'}}
			/>
		</div>
	);
};

export const Full: React.FC<{style?: React.CSSProperties; children?: React.ReactNode}> = ({style, children}) => (
	<div style={{position: 'absolute', inset: 0, ...style}}>{children}</div>
);

export const fade = (frame: number, length: number, inn = 14, out = 14) =>
	Math.min(ramp(frame, 0, inn, 0, 1, Easing.linear), ramp(frame, length - out, length, 1, 0, Easing.linear));
