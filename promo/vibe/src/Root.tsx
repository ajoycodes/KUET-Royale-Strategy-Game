import {Composition} from 'remotion';
import {Film, FILM_FPS, FILM_FRAMES} from './film';
import {Boards, SCREENS} from './screens';
import {CELL, GlyphSheet, LINE_ROW, LineSheet, LINES} from './sheets';

export const Root = () => (
	<>
		<Composition id="GlyphSheet" component={GlyphSheet} durationInFrames={1} fps={30} width={CELL * 6} height={CELL * 5} defaultProps={{font: 'titan'}} />
		<Composition id="LineSheet" component={LineSheet} durationInFrames={1} fps={30} width={3840} height={LINE_ROW * LINES.length} />
		<Composition id="Film" component={Film} durationInFrames={FILM_FRAMES} fps={FILM_FPS} width={1920} height={1080} />
		<Composition id="Boards" component={Boards} durationInFrames={SCREENS.length} fps={30} width={1920} height={1080} />
	</>
);
