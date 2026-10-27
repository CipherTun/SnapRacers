#!/usr/bin/env python3
"""Plays each cup's flavour instrument in music.py on a short phrase over a
light kick and hat beat, through render_pop, so it can be heard in place.

  uv run --with numpy --with scipy tools/sound/inst_demo.py OUT_DIR [names...]

Each comes out as inst_<name>.ogg, six bars long. Nothing in sound/ is changed.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import music as m  # noqa: E402
from synth import write_ogg  # noqa: E402

BARS = 6


def tune(*lines):
    """Hand written bars, played over and over for the demo's length."""
    written = m.bars(*lines)
    return m.melody(16, *[written[b % len(written)] for b in range(BARS)])


def beat(pattern):
    return m.drums(pattern, BARS)


def pitched(pattern, hz):
    """A drum pattern played at one pitch."""
    return [(at, hz, steps, v) for at, _f, steps, v in beat(pattern)]


def chords(*names):
    return [names[b % len(names)] for b in range(BARS)]


# Each demo: (bpm, the parts on top of the beat, the chords for a quiet pad
# under them or None).
DEMOS = {
    "clavinet": (150, lambda: [
        m.part(m.clavinet, tune("E4:1 .:1 E4:1 G4:1 .:1 A4:1 .:1 E4:1 B4:1 .:1 A4:1 G4:1 .:1 E4:1 D4:1 .:1",
                                "E4:1 .:1 G4:1 .:1 A4:1 B4:1 .:1 D5:1 .:1 B4:1 A4:1 .:1 G4:1 .:1 E4:2"), 0.6, -0.1, 0.1),
        m.part(m.clavinet, m.comp(chords("Em7", "A7"), ".x...x.x..x...x.", 4), 0.25, 0.3, 0.1),
    ], ["Em7", "A7"]),
    "anvil": (150, lambda: [
        m.part(m.snap_snare, beat("....x.......x..."), 0.3, 0.05, 0.12),
        m.part(m.anvil, beat("..x.....x..x..x.", ), 0.35, 0.25, 0.15),
    ], None),
    "banjo": (150, lambda: [
        m.part(m.banjo, tune("G4:1 B4:1 D5:1 G4:1 B4:1 D5:1 G4:1 B4:1 G4:1 C5:1 E5:1 G4:1 C5:1 E5:1 G4:1 C5:1",
                             "F#4:1 A4:1 D5:1 F#4:1 A4:1 D5:1 F#4:1 A4:1 G4:1 B4:1 D5:1 G5:1 .:1 D5:1 B4:2"), 0.55, -0.15, 0.12),
    ], ["G", "C", "D", "G"]),
    "pop_whistle": (150, lambda: [
        m.part(m.pop_whistle, tune("E6:3 D6:3 C6:2 D6:4 G5:4", "A5:3 B5:3 C6:2 E6:6 .:2",
                                   "F6:3 E6:3 D6:2 C6:4 A5:4", "B5:3 C6:3 D6:2 C6:6 .:2"), 0.45, 0.1, 0.2, 0.15),
    ], ["C", "G", "F", "C"]),
    "timpani": (145, lambda: [
        m.part(m.timpani, tune("D2:4 .:4 A1:4 .:4", "D2:4 .:2 A1:2 D2:1 D2:1 D2:1 D2:1 D2:1 D2:1 D2:1 D2:1"), 0.6, 0.0, 0.15),
        m.part(m.brass, m.comp(chords("Dm", "Bb"), "x.......x.x.....", 4), 0.15, -0.2, 0.2),
    ], ["Dm", "Bb"]),
    "choir": (145, lambda: [
        m.part(m.choir, m.held(chords("Dm", "Bb", "F", "C"), 3) + m.held(chords("Dm", "Bb", "F", "C"), 4)[::3], 0.45, 0.0, 0.3),
    ], None),
    "anthem_guitar": (150, lambda: [
        m.part(m.anthem_guitar, tune("Bb4:3 C5:3 Eb5:2 F5:6 Eb5:2", "G5:4 F5:4 Eb5:4 C5:4",
                                     "Ab5:3 G5:3 F5:2 Eb5:4 C5:4", "Bb4:6 C5:2 Eb5:8"), 0.5, 0.0, 0.2, 0.15),
    ], ["Eb", "Bb", "Ab", "Eb"]),
    "stadium_clap": (150, lambda: [
        m.part(m.stadium_clap, beat("....x.......x..."), 0.6, 0.0, 0.2),
    ], None),
    "chug": (155, lambda: [
        m.part(m.chug, m.bassline(chords("E", "G", "A", "C"), "r.r.r.rrr.r.r.r-", 2), 0.5, 0.0, 0.05),
        m.part(m.snap_snare, beat("....x.......x..."), 0.3, 0.05, 0.12),
    ], None),
    "tom": (155, lambda: [
        m.part(m.snap_snare, beat("....x.......x..."), 0.3, 0.05, 0.12),
        m.part(m.tom, [(b * 16 + 12 + k, hz, 1, 0.8) for b in range(1, BARS, 2) for k, hz in enumerate((220.0, 165.0, 123.0, 92.0))]
               + [(b * 16 + 8 + k, hz, 1, 0.8) for b in range(0, BARS, 2) for k, hz in enumerate((196.0, 196.0, 147.0, 147.0, 110.0, 110.0, 92.0, 92.0))],
               0.5, 0.0, 0.12),
    ], None),
    "vocoder_lead": (150, lambda: [
        m.part(m.vocoder_lead, tune("C5:2 .:1 C5:1 Eb5:2 G5:2 .:2 F5:2 Eb5:4", "D5:2 .:1 D5:1 F5:2 Ab5:4 G5:2 F5:2 D5:2"),
               0.5, 0.0, 0.15, 0.2),
        m.part(m.pop_pluck, m.arps(chords("Cm", "Bb"), 4, (0, 1, 2, 3), 1), 0.15, 0.3, 0.1, 0.1),
    ], ["Cm", "Bb"]),
    "fair_organ": (150, lambda: [
        m.part(m.fair_organ, tune("G5:2 E5:2 C5:2 E5:2 G5:4 C6:4", "B5:2 A5:2 G5:2 F5:2 E5:2 D5:2 C5:4"), 0.5, 0.0, 0.15),
        m.part(m.fair_organ, m.comp(chords("C", "G7"), "....x.......x...", 4), 0.2, -0.3, 0.1),
    ], ["C", "G7"]),
    "calliope": (150, lambda: [
        m.part(m.calliope, tune("C6:1 D6:1 E6:1 F6:1 G6:2 E6:2 C6:2 .:2 G5:4", "A5:1 B5:1 C6:1 D6:1 E6:2 D6:2 B5:2 G5:2 C6:4"),
               0.45, 0.1, 0.2),
    ], ["C", "G7"]),
    "pop_accordion": (160, lambda: [
        m.part(m.pop_accordion, tune("A5:2 .:2 F5:2 A5:2 C6:4 A5:4", "G5:2 .:2 E5:2 G5:2 Bb5:4 G5:4"), 0.5, 0.0, 0.15),
        m.part(m.pop_accordion, m.comp(chords("F", "C7"), "..x...x...x...x.", 4), 0.2, 0.0, 0.1),
        m.part(m.pop_bass, m.bassline(chords("F", "C7"), "r.......5.......", 2), 0.3),
    ], None),
    "yodel": (160, lambda: [
        m.part(m.yodel, tune("G4:2 E5:2 C5:2 G5:2 E5:2 C5:2 G4:4", "A4:2 F5:2 D5:2 A5:2 F5:2 D5:2 G4:4",
                             "G4:2 E5:2 G4:2 E5:2 C5:2 G5:4 .:2", "F5:2 E5:2 D5:2 B4:2 C5:8"), 0.5, 0.0, 0.2, 0.1),
    ], ["C", "G7", "C", "G7"]),
    "pop_twang": (150, lambda: [
        m.part(m.pop_twang, tune("E3:2 .:1 E3:1 G3:2 A3:2 B3:4 D4:2 B3:2", "E4:3 D4:3 B3:2 A3:4 G3:2 E3:2"), 0.55, -0.1, 0.25, 0.15),
        m.part(m.brush, beat("ooooXoooooooXooo"), 0.35, 0.2, 0.08),
    ], ["Em", "Em"]),
    "brush": (155, lambda: [
        m.part(m.brush, beat("ooooXoooooooXooo"), 0.55, 0.1, 0.1),
    ], None),
    "pop_marimba": (150, lambda: [
        m.part(m.pop_marimba, tune("A5:1 .:1 C6:1 E6:1 .:1 A5:1 D6:2 C6:2 B5:1 .:1 G5:2 E5:2",
                                   "A5:1 .:1 C6:1 E6:1 .:1 G6:1 E6:2 D6:2 C6:1 .:1 B5:2 A5:2"), 0.5, 0.1, 0.15, 0.1),
    ], ["Am", "G"]),
    "conga": (150, lambda: [
        m.part(m.conga, pitched("x......x..x.....", 180.0), 0.45, -0.3, 0.08),
        m.part(m.conga, pitched("..o.oX.o....X.ox", 260.0), 0.4, 0.3, 0.08),
    ], None),
    "wood_flute": (145, lambda: [
        m.part(m.wood_flute, tune("E5:3 D5:3 C5:2 A4:8", "C5:3 D5:3 E5:2 G5:4 E5:4", "A5:3 G5:3 E5:2 D5:4 C5:4", "B4:6 C5:2 A4:8"),
               0.5, 0.0, 0.25, 0.15),
    ], ["Am", "C", "F", "E"]),
    "air_flute": (140, lambda: [
        m.part(m.air_flute, tune("F#5:4 A5:4 D6:6 C#6:2", "B5:4 A5:4 F#5:8", "G5:4 B5:4 E6:6 D6:2", "C#6:4 A5:4 E5:8"),
               0.5, 0.0, 0.3, 0.2),
    ], ["D", "Bm", "G", "A"]),
    "open_pad": (140, lambda: [
        m.part(m.open_pad, m.held(chords("D", "Bm", "G", "A"), 3), 0.5, 0.0, 0.3),
        m.part(m.chime, tune("A5:4 .:4 F#5:4 .:4", "D6:4 .:4 B5:4 .:4"), 0.2, 0.2, 0.3, 0.2),
    ], None),
    "wah_guitar": (150, lambda: [
        m.part(m.wah_guitar, m.comp(chords("F#m7", "Bm7"), "x.xx..x.x.xx..x.", 3), 0.4, -0.2, 0.08),
        m.part(m.slap_bass, m.bassline(chords("F#m7", "Bm7"), "r..o..r.r..o.5o.", 2), 0.4),
    ], None),
    "e_piano": (150, lambda: [
        m.part(m.e_piano, m.comp(chords("F#m7", "Dmaj7", "Bm7", "C#m7"), "x.....x...x.....", 3), 0.5, 0.0, 0.2),
        m.part(m.e_piano, tune("C#5:2 E5:2 A5:3 G#5:3 F#5:6", "E5:2 F#5:2 G#5:3 A5:3 C#6:6"), 0.35, 0.1, 0.25, 0.15),
    ], None),
    "horn_section": (150, lambda: [
        m.part(m.horn_section, tune("C#5:2 .:2 E5:2 F#5:2 .:2 A5:2 G#5:2 F#5:2", "E5:3 F#5:3 A5:2 .:4 C#6:2 .:2"), 0.5, 0.0, 0.15),
        m.part(m.horn_section, m.comp(chords("F#m7", "Bm7"), "......x....x....", 4), 0.25, 0.0, 0.15),
    ], ["F#m7", "Bm7"]),
}


def demo(name):
    bpm, make, pad = DEMOS[name]
    kicks = beat("x...x...x...x...")
    parts = [m.part(m.punch_kick, kicks, 0.45), m.part(m.tick, beat("x.ox.ox.x.ox.oxo"), 0.18, 0.35)] + make()
    if pad:
        parts.append(m.part(m.pump_pad, m.held(chords(*pad), 3), 0.15, 0.0, 0.3, 0.0, 0.4))
    return m.render_pop(bpm, BARS, parts, kicks, wet=0.15, level=-14.0)


def main():
    out = sys.argv[1]
    only = set(sys.argv[2:])
    os.makedirs(out, exist_ok=True)
    for name in DEMOS:
        if only and name not in only:
            continue
        start = time.time()
        write_ogg(os.path.join(out, "inst_" + name + ".ogg"), demo(name), 3)
        print("made", name, "%.1f s" % (time.time() - start))


if __name__ == "__main__":
    main()
