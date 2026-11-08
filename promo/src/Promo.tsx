import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';
import {BAR, Full} from './kit';
import {Drop, Fight, Pick, Power, Think, TitleRise, Towers} from './scenes_game';
import {Cards, Departments, Ending, Opening} from './scenes_static';

export const TOTAL = 25 * BAR;

// Scene lengths in bars. They add up to 25 bars, which is 60.0 seconds at 100 beats a minute.
const SCENES: [React.FC<{length: number}>, number][] = [
	[Opening, 2],
	[TitleRise, 2],
	[Pick, 1.5],
	[Drop, 1.5],
	[Fight, 2],
	[Departments, 4],
	[Cards, 2],
	[Towers, 1.5],
	[Think, 2.5],
	[Power, 4],
	[Ending, 2],
];

export const Promo: React.FC = () => {
	let at = 0;
	return (
		<Full style={{background: '#000'}}>
			<Audio src={staticFile('music.wav')} volume={1.2} />
			{SCENES.map(([Scene, bars], place) => {
				const from = at;
				const length = bars * BAR;
				at += length;
				return (
					<Sequence key={place} from={from} durationInFrames={length}>
						<Scene length={length} />
					</Sequence>
				);
			})}
		</Full>
	);
};
