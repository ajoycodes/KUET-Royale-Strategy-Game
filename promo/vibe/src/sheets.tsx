import React from 'react';
import {loadFont as lilita} from '@remotion/google-fonts/LilitaOne';
import {loadFont as titan} from '@remotion/google-fonts/TitanOne';

// White letters on black, for tools/lettering.py to turn into bevelled metal.
const FONTS: Record<string, string> = {lilita: lilita().fontFamily, titan: titan().fontFamily};
export const CELL = 640;
export const GLYPH_SIZE = 500;
export const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ.';
export const LINE_ROW = 240;
export const LINE_SIZE = 150;
export const LINES = [
	'Fast, cheap and clever.',
	'Heavy, slow and hard to stop.',
	'A sturdy wall that soaks up hits.',
	'And when it falls, everyone near it pays.',
	'One tank. One shooter. One runner. One surprise.',
	'One minute. No turns.',
	'Choose your side.',
	'Armour',
	'Splash',
	'Last blast',
	'Hover',
];

export const GlyphSheet: React.FC<{font: string}> = ({font}) => (
	<div style={{position: 'absolute', inset: 0, background: '#000'}}>
		{CHARS.split('').map((char, place) => (
			<div
				key={char}
				style={{
					position: 'absolute',
					left: (place % 6) * CELL,
					top: Math.floor(place / 6) * CELL,
					width: CELL,
					height: CELL,
					lineHeight: `${CELL}px`,
					textAlign: 'center',
					color: '#fff',
					fontFamily: FONTS[font],
					fontSize: GLYPH_SIZE,
				}}
			>
				{char}
			</div>
		))}
	</div>
);

export const LineSheet: React.FC = () => (
	<div style={{position: 'absolute', inset: 0, background: '#000'}}>
		{LINES.map((line, place) => (
			<div key={line} style={{position: 'absolute', left: 40, top: place * LINE_ROW, height: LINE_ROW, lineHeight: `${LINE_ROW}px`, color: '#fff', fontFamily: FONTS.lilita, fontSize: LINE_SIZE, whiteSpace: 'pre'}}>
				{line}
			</div>
		))}
	</div>
);
