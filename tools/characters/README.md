# Driver tools

The driver pieces are modelled here in Python, the same way the kart parts are in `tools/parts`, and with its `kit.py`. Nothing is downloaded or copied.

- `figure.py` has the rig's numbers: where the hips, shoulders, elbows and wrists are, how the arms swing and where the hands rest. It writes them to `data/characters/figure.json`, and `CharacterRig.figure_mismatches()` checks the rig's constants match.
- `make_characters.py` makes the pieces into `characters/meshes`, one OBJ per piece per colour region, each in its bone's own space. Left and right are both made, never mirrored. It lists them in `data/characters/pieces_made.json`, and writes `data/characters/clipping.json`, how far the pieces go into each other in the rig's poses, which `tests/character_test.gd` checks.

So far it makes the bare figure: hips, legs (standing and seated), torso with its collar, neck, arms, hands and the stud on the head. The other pieces are still made in `scripts/character/looks`.

```
uv run --with manifold3d --with numpy tools/characters/make_characters.py
```

After making them, run the Godot import (`tools/run-tests.sh` does it first thing). If a mesh came out empty once, Godot keeps it marked as broken even after it's fixed, so delete its `.obj.import` file and import again.

`tools/shots/character_shots.gd` takes pictures of the figure to check them.
