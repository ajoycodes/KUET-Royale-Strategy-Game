How the footage was recorded. None of this is in the game itself.

Make a scratch copy of the game, apply game-changes.diff to it, and put promo_root.gd, promo_touch.gd
and promo_figures.gd in its scripts folder and promo_root.tscn beside project.godot. Then, one at a time:

    godot --path . --fixed-fps 60 -- --cap-out person.mp4 --cap-frames 4500 --promo-person --seed 7
    godot --path . --fixed-fps 60 -- --cap-out power.mp4 --cap-frames 4140 --promo-power --seed 5
    godot --path . --fixed-fps 60 -- --cap-out tour.mp4 --cap-frames 2400 --watch --tour --left eee --right ce --seed 11

The game runs in a 4K SubViewport and every frame is piped into ffmpeg, so a take keeps going when the
window is covered or on another desktop. Godot's own --write-movie freezes in that case.

The warrior line-ups come from running --promo-figures on black and on white (music/matte.py cuts them out).
Then: python3 music/cut_shots.py <folder of recordings> public/shots, python3 music/make_music.py public/music.wav,
and npm run render.

For the battle film (vibe/): res://promo_frames.tscn exports every warrior's walk, stand and attack frames, res://promo_heroes.tscn the
castles, and res://promo_cuts.tscn the real-game clips, for example

    godot --path . --fixed-fps 60 res://promo_cuts.tscn -- --out <folder> --cuts siege:2100:2340:460:476:362 --promo-power --seed 5
