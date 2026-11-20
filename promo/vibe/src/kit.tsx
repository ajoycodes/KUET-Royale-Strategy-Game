import React from 'react';
import {Img, staticFile} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Cinzel';
import {loadFont as loadChunk} from '@remotion/google-fonts/LilitaOne';
import {loadFont as loadBody} from '@remotion/google-fonts/Nunito';

const {fontFamily: EPIC} = loadFont('normal', {weights: ['800', '900'], subsets: ['latin']});
const {fontFamily: CHUNK} = loadChunk();
const {fontFamily: BODY} = loadBody('normal', {weights: ['700', '800'], subsets: ['latin']});
export {BODY, CHUNK, EPIC};

export const GOLD = 'linear-gradient(180deg,#fff6cf 0%,#ffdc7a 30%,#d8962e 52%,#ffe7a0 60%,#f0b048 78%,#9c5c16 100%)';
export const STEEL = 'linear-gradient(180deg,#ffffff 0%,#eef2f7 34%,#9eabbd 52%,#f3f6fa 60%,#c6d0dd 78%,#6f7f94 100%)';
export const ICE = 'linear-gradient(180deg,#ffffff 0%,#d8ecff 34%,#6fa8ea 52%,#e4f2ff 60%,#a9cdf5 78%,#3f6fb4 100%)';
export const VIOLET = 'linear-gradient(180deg,#ffffff 0%,#ecdcff 34%,#9a72e0 52%,#f0e6ff 60%,#c9acf2 78%,#5f3ea8 100%)';
export const EMBER = 'linear-gradient(180deg,#fff0d0 0%,#ffc27a 34%,#e0701e 52%,#ffd7a0 60%,#f59a44 78%,#a03f0c 100%)';

// Forged letters: a dark edge, a glow of the scene's light behind them, and a metal face.
export const Forged: React.FC<{
	text: string;
	size: number;
	fill?: string;
	glow?: string;
	font?: string;
	weight?: number;
	spacing?: number;
	style?: React.CSSProperties;
	align?: React.CSSProperties['textAlign'];
}> = ({text, size, fill = STEEL, glow = 'rgba(255,120,40,.55)', font = EPIC, weight = 900, spacing = 0.02, style, align = 'center'}) => {
	const common: React.CSSProperties = {
		fontFamily: font,
		fontWeight: weight,
		fontSize: size,
		lineHeight: 1.04,
		letterSpacing: `${spacing}em`,
		// The space after the last letter would push centred words off centre.
		marginRight: `-${spacing}em`,
		whiteSpace: 'pre',
		textAlign: align,
	};
	return (
		<div style={{position: 'relative', display: 'inline-block', ...style}}>
			<div
				style={{
					...common,
					color: '#060810',
					WebkitTextStroke: `${size * 0.05}px #060810`,
					textShadow: `0 ${size * 0.03}px 0 #060810, 0 0 ${size * 0.28}px ${glow}, 0 ${size * 0.06}px ${size * 0.16}px rgba(0,0,0,.85)`,
				}}
			>
				{text}
			</div>
			<div style={{...common, position: 'absolute', left: 0, top: 0, backgroundImage: fill, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent'}}>{text}</div>
		</div>
	);
};

// The small line under a big one.
export const Line: React.FC<{text: string; size?: number; style?: React.CSSProperties}> = ({text, size = 38, style}) => (
	<div style={{fontFamily: BODY, fontWeight: 800, fontSize: size, color: '#f2ece0', letterSpacing: '.01em', textShadow: '0 2px 16px rgba(0,0,0,.95), 0 1px 3px rgba(0,0,0,.9)', ...style}}>{text}</div>
);

// Black bars above and below, as in a film.
export const BAR = 96;
export const Bars: React.FC = () => (
	<>
		<div style={{position: 'absolute', left: 0, right: 0, top: 0, height: BAR, background: '#000'}} />
		<div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: BAR, background: '#000'}} />
	</>
);

export const Plate: React.FC<{src: string; bars?: boolean; children?: React.ReactNode}> = ({src, bars = true, children}) => (
	<div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: '#000'}}>
		<Img src={staticFile(`plates/${src}.jpg`)} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
		{children}
		{bars ? <Bars /> : null}
	</div>
);

// The cost, in a gold coin.
export const Coin: React.FC<{value: number; size: number; style?: React.CSSProperties}> = ({value, size, style}) => (
	<div
		style={{
			width: size,
			height: size,
			borderRadius: '50%',
			border: `${size * 0.07}px solid #1a0f06`,
			background: 'radial-gradient(circle at 38% 30%, #fff3b8 0%, #ffcf4a 42%, #c9801e 100%)',
			boxShadow: `inset 0 ${size * 0.04}px 0 rgba(255,255,255,.65), inset 0 ${-size * 0.06}px 0 rgba(110,55,0,.5), 0 ${size * 0.05}px ${size * 0.14}px rgba(0,0,0,.7)`,
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'center',
			boxSizing: 'border-box',
			fontFamily: CHUNK,
			fontSize: size * 0.58,
			color: '#2a1606',
			...style,
		}}
	>
		{value}
	</div>
);

// A warrior's card, in the firelight.
export const BattleCard: React.FC<{name: string; hero: string; cost: number; special: string; color: [string, string]; w: number; style?: React.CSSProperties}> = ({name, hero, cost, special, color, w, style}) => {
	const h = w * 1.42;
	const u = w / 100;
	const size = w * 1.5;
	const windowBottom = h - 27 * u;
	return (
		<div style={{position: 'relative', width: w, height: h, ...style}}>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					borderRadius: 5 * u,
					border: `${0.9 * u}px solid #1a0f06`,
					background: 'linear-gradient(180deg,#5a3a1e 0%,#3d2613 55%,#2a190c 100%)',
					boxShadow: `inset 0 0 0 ${0.8 * u}px #c9963e, inset 0 ${1.2 * u}px ${1 * u}px rgba(255,220,150,.4), 0 ${3 * u}px ${9 * u}px rgba(0,0,0,.85), 0 0 ${10 * u}px rgba(255,120,40,.22)`,
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
					background: `radial-gradient(ellipse 80% 70% at 50% 42%, ${color[0]} 0%, ${color[1]} 62%, #060a18 100%)`,
					boxSizing: 'border-box',
				}}
			>
				<Img src={staticFile(`lit/${hero}.png`)} style={{position: 'absolute', width: size, height: size, left: (w - 10 * u - 1.4 * u - size) / 2, top: windowBottom - 5 * u - (size * 1340) / 1500 - 1 * u}} />
			</div>
			<div style={{position: 'absolute', left: 0, right: 0, top: windowBottom + 2.2 * u, textAlign: 'center'}}>
				<Forged text={name} size={name.length > 11 ? 8 * u : 9.6 * u} fill={GOLD} glow="rgba(255,150,60,.3)" />
			</div>
			<div style={{position: 'absolute', left: 0, right: 0, bottom: 4.6 * u, textAlign: 'center', fontFamily: BODY, fontWeight: 800, fontSize: 5 * u, color: '#e8d9bd', textShadow: '0 1px 4px rgba(0,0,0,.9)'}}>{special}</div>
			<Coin value={cost} size={21 * u} style={{position: 'absolute', left: -5 * u, top: -5 * u}} />
		</div>
	);
};
