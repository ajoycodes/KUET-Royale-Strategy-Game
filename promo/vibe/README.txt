The 60-second battle film: demo/KUET-Royale-film.mp4 (1080p, 30 fps, 1800 frames).

To change only the words, the cards or the score: edit src/film.tsx or tools/battle_music.py, then from the promo folder

    python3 vibe/tools/battle_music.py vibe/public/battle.wav
    npx remotion render vibe/src/index.ts Film out.mp4 --public-dir=vibe/public --concurrency=4 --timeout=180000 --crf=15 --audio-bitrate=320k

To change a picture: edit tools/shots.py. It needs the real-game clips as raw frames first, once:

    cd vibe/work/cuts; for c in siege bridge upper last; do ffmpeg -i \$c.mp4 -f rawvideo -pix_fmt rgb24 \$c.rgb; done

Then, from the vibe folder:

    python3 tools/film.py sample <shot>      a sheet of nine frames of one shot, in work/samples
    python3 tools/film.py render <shot>      the shot as video, in work/shots

Rendering every shot from nothing needs about 12 GB of free space for work/litcache, which can be deleted afterwards.
Join the shots into public/film_base.mp4 in the order given in src/film.tsx, then render Film as above.
Keep the words free of course, algorithm-name and algorithm-count wording. ../recording/ says how the game footage was captured.

The lettering is made by tools/lettering.py from the sheets of letters in work/sheets (render the GlyphSheet and LineSheet compositions to make them again).
art/logo_menu.png and art/logo_bar.png in the game are copies of public/text/logo_menu.png and logo_bar.png.

To put a new film in the game: Godot plays only Ogg Theora, and Homebrew's ffmpeg has no Theora encoder. The ffmpeg inside the Python package imageio-ffmpeg does:

    <that ffmpeg> -i demo/KUET-Royale-film.mp4 -vf scale=1280:720:flags=lanczos -c:v libtheora -q:v 7 -g 30 -c:a libvorbis -q:a 6 -ar 44100 intro/KUET-Royale-film.ogv
