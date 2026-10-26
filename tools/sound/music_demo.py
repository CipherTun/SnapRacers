#!/usr/bin/env python3
"""Makes the arcade pop demos in music.POP into Ogg files to listen to, next
to copies of the tunes they would replace.

  uv run --with numpy --with scipy tools/sound/music_demo.py OUT_DIR [names...]

Each demo comes out as new_<name>.ogg and the shipped tune as old_<name>.ogg.
Nothing in sound/ is changed.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

import music  # noqa: E402
from synth import write_ogg  # noqa: E402

SOUND = os.path.join(os.path.dirname(__file__), "..", "..", "sound", "music")


def main():
    out = sys.argv[1]
    only = set(sys.argv[2:])
    os.makedirs(out, exist_ok=True)
    for name, make in music.POP.items():
        if only and name not in only:
            continue
        write_ogg(os.path.join(out, "new_" + name + ".ogg"), make(), 3)
        shutil.copyfile(os.path.join(SOUND, name + ".ogg"), os.path.join(out, "old_" + name + ".ogg"))
        print("made", name)


if __name__ == "__main__":
    main()
