import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {BattleCard, BAR, CHUNK, EMBER, Forged, GOLD, ICE, Line, Plate, STEEL} from './kit';

const FIRE = 'rgba(255,110,30,.7)';
const COLD = 'rgba(90,160,255,.75)';

const Centre: React.FC<{top: number; children: React.ReactNode}> = ({top, children}) => (
	<div style={{position: 'absolute', left: 0, right: 0, top, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: 'translateY(-50%)'}}>{children}</div>
);

const Charge = () => (
	<Plate src="charge">
		<Centre top={300}>
			<Forged text="FOUR ARMIES." size={132} glow={FIRE} />
		</Centre>
	</Plate>
);

const Faceoff = () => (
	<Plate src="faceoff">
		<div style={{position: 'absolute', left: 90, top: BAR + 26}}>
			<Forged text="CSE" size={124} fill={ICE} glow={COLD} />
			<Line text="Fast, cheap and clever." size={34} style={{marginTop: 4}} />
		</div>
		<div style={{position: 'absolute', right: 90, top: BAR + 26, textAlign: 'right'}}>
			<Forged text="ME" size={124} fill={EMBER} glow={FIRE} />
			<Line text="Heavy, slow and hard to stop." size={34} style={{marginTop: 4}} />
		</div>
		<Centre top={800}>
			<Forged text="VS" size={150} fill={GOLD} glow="rgba(255,235,180,.8)" />
		</Centre>
	</Plate>
);

const Champion = () => (
	<Plate src="champion">
		<div style={{position: 'absolute', left: 110, top: 540, transform: 'translateY(-50%)'}}>
			<Forged text="CAPACITOR" size={118} fill={GOLD} glow="rgba(255,225,110,.6)" />
			<Line text="A sturdy wall that soaks up hits." size={38} style={{marginTop: 14}} />
			<Line text="And when it falls, everyone near it pays." size={38} style={{marginTop: 4}} />
		</div>
	</Plate>
);

const Clash = () => (
	<Plate src="clash">
		<Centre top={892}>
			<Forged text="HOLD THE BRIDGE." size={96} glow={FIRE} />
		</Centre>
	</Plate>
);

const Gameplay = () => (
	<Plate src="gameplay">
		<Centre top={166}>
			<Forged text="EVERY DROP COUNTS." size={86} glow={FIRE} />
		</Centre>
	</Plate>
);

const CSE_COLOURS: [string, string] = ['#2f76cf', '#0d2c63'];

const Table = () => (
	<Plate src="table">
		<Centre top={170}>
			<Forged text="CHOOSE YOUR FOUR." size={96} fill={GOLD} glow={FIRE} />
		</Centre>
		{[
			{name: 'COMPILER', hero: 'compiler', cost: 5, special: 'Armour', x: 266, y: 276, r: -6},
			{name: 'LOGIC BOMBER', hero: 'logic-bomber', cost: 4, special: 'Splash', x: 620, y: 256, r: -2},
			{name: 'STACK RUNNER', hero: 'stack-runner', cost: 2, special: 'Last blast', x: 974, y: 256, r: 2},
			{name: 'CLOUD DRONE', hero: 'cloud-drone', cost: 3, special: 'Hover', x: 1328, y: 276, r: 6},
		].map((card) => (
			<div key={card.name} style={{position: 'absolute', left: card.x, top: card.y, transform: `rotate(${card.r}deg)`}}>
				<BattleCard name={card.name} hero={card.hero} cost={card.cost} special={card.special} color={CSE_COLOURS} w={326} />
			</div>
		))}
		<Centre top={B_LINE}>
			<Line text="One tank. One shooter. One runner. One surprise." size={36} />
		</Centre>
	</Plate>
);
const B_LINE = 1080 - BAR - 34;

const Power = () => (
	<Plate src="power">
		<Centre top={300}>
			<Forged text="POWER MODE" size={166} fill={ICE} glow={COLD} />
			<Line text="One minute. No turns." size={44} style={{marginTop: 10}} />
		</Centre>
	</Plate>
);

const Castle = () => (
	<Plate src="castle">
		<Centre top={200}>
			<Forged text="CASTLE DOWN." size={132} fill={EMBER} glow={FIRE} />
		</Centre>
	</Plate>
);

const TitleEnd: React.FC<{chunky?: boolean}> = ({chunky}) => (
	<Plate src="title">
		<Centre top={chunky ? 262 : 270}>
			{chunky ? (
				<Forged text="KUET ROYALE" size={188} fill={GOLD} glow={FIRE} font={CHUNK} weight={400} spacing={0.015} />
			) : (
				<Forged text="KUET ROYALE" size={172} fill={GOLD} glow={FIRE} style={{left: -4}} />
			)}
			<div style={{height: 6}} />
			<Forged text="DEPARTMENT WARS" size={50} fill={STEEL} glow={FIRE} spacing={0.2} font={chunky ? CHUNK : undefined} weight={chunky ? 400 : 900} />
			<Line text="Choose your side." size={40} style={{marginTop: 18}} />
		</Centre>
	</Plate>
);

export const SCREENS: React.FC[] = [Charge, Faceoff, Champion, Clash, Gameplay, Table, Power, Castle, () => <TitleEnd />, () => <TitleEnd chunky />];

export const Boards: React.FC = () => (
	<AbsoluteFill>
		{SCREENS.map((Screen, place) => (
			<Sequence key={place} from={place} durationInFrames={1}>
				<Screen />
			</Sequence>
		))}
	</AbsoluteFill>
);
