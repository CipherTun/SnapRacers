# Driver tools

The driver pieces are modelled here in Python, the same way the kart parts are in `tools/parts`, and with its `kit.py`. Nothing is downloaded or copied.

- `figure.py` has the rig's numbers: where the hips, shoulders, elbows and wrists are, how the arms swing and where the hands rest. It writes them to `data/characters/figure.json`, and `CharacterRig.figure_mismatches()` checks the rig's constants match.
- `make_characters.py` makes the pieces into `characters/meshes`, one OBJ per piece per colour region, each in its bone's own space. Left and right are both made, never mirrored. It lists them in `data/characters/pieces_made.json`, and writes `data/characters/clipping.json`, how far the pieces go into each other in the rig's poses, which `tests/character_test.gd` checks.

- `shapes.py` has the shapes the pieces are made of.
- `necks.py` makes what's worn around the neck, one function a style. Each comes out cut back from the torso, the neck post and the head, a hairline off them, and in colour regions: main in the piece's colour, dark and light shades of it, and fixed colours like gold and white listed in `COLOURS`.
- `hair.py` makes the hairdos, mostly a moulded cap with a few broad lobes, and a cut version of each that stops at the hat line (`CUT_Y`) for under hats. `pieces_made.json` gives the cut's top and radius.
- `beards.py` makes the raised facial hair: the full, long and braided beards and sideburns. The rest of the facial hair is printed in `scripts/character/face_print.gd`.
- `headgear.py` makes the hats, helmets and hoods, one function a style, each at most 1,500 triangles. `HAIR` says what hair shows under each: hats have the cut hair, helmets and hoods hide it, and what's worn on the hair (headband, tiara, party hat, horns) has the full hair: the bands are made again for every hairdo, snug on it, and the party hat gets a fit for every hairdo in `pieces_made.json`.

- `torsos.py` makes the torsos: the standard torso with each style printed on as flat colour regions, and a raised buckle on the belted ones. Each region is saved with only the faces that show, so the cuts between regions don't count against the 1,500 triangles a piece.
- `arms.py` makes the arm styles for each side and their hands, from the `sleeve`, `hands` and other settings in `data/characters/pieces.json`. Sleeves, cuffs and gloves are colour regions; the few raised bits (a rolled cuff, a watch, a pad) are cut back from where the torso, hips and legs are as the arm swings through every pose. Regions the same as one already made, like the hands, share its file.
- `legs.py` makes the leg styles: the standard hips and legs with each style printed on as colour regions, and a few raised bits like boots, knee plates, big feet and skirts. The hips go on the rig and each leg is made standing, seated and astride on the legs bone. Skirts and gowns have their own shape for each pose: a bell standing, a drape over the legs sitting, and a drape round each leg astride, kept off the seat and out from between the legs.

So far it makes the bare figure (hips, legs standing and seated, torso with its collar, neck, arms, hands and the stud on the head), the neck pieces, hair, raised facial hair, headgear, torsos, arms and legs. Back pieces are still made in `scripts/character/looks`. The clipping report checks each neck piece against the torso, neck and head and against the arms and hands in every pose. It checks hair and beards against the head, stud, face and each other, and against the torso, every neck piece and the arms with the head turned all the way either side. Torso and arm styles with raised bits are checked against the neck pieces, the arms, hands and legs, each other and the hair and headgear as the head turns; the printed ones have the figure's own shape. Every leg style's hips and legs are checked against each other, the torso, the arms and hands and the raised torsos and arms in every pose, and sitting in a kart against the seat. `tests/character_test.gd` also checks the back pieces don't reach into any style's legs.

```
uv run --with manifold3d --with numpy tools/characters/make_characters.py
```

After making them, run the Godot import (`tools/run-tests.sh` does it first thing). If a mesh came out empty once, Godot keeps it marked as broken even after it's fixed, so delete its `.obj.import` file and import again.

`tools/shots/character_shots.gd` takes pictures of the figure to check them. `--only=necks,faces` makes just the sheets of every neck piece and every face; `hair`, `facial_hair` and `combos` make the hair, cut, beard and seated driver sheets, `torsos`, `arms` and `outfits` the torso, arm and whole outfit sheets, and `legs` every leg style standing, seated and astride and a few outfits in karts and on bikes.
