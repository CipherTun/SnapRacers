"""SnapRacers' music, written out note by note and played by a little
tracker built on synth.py.

Each tune is bars of sixteen steps. The melody is written by hand as (note,
steps) pairs, and the chords under it are named once for each bar, which the
bass, the arpeggios and the pads are all worked out from. Drums come from
patterns of steps.

Every tune loops. Anything still ringing past the end (the reverb, a long
note) is folded back onto the start, so it goes around without a gap.

The tunes are chill funk: swung sixteenths, a soft kit, a finger bass,
chicken scratch guitar and electric piano, with horns on the hooks. They are
written in sections (intro, groove A and B, hook, breakdown) and mixed on a
warm bus by render_funk. Each cup adds its own instrument on top. The
palette instruments from the old arcade pop tunes are kept for the cup
flavours.
"""

import numpy as np

from synth import (
    adsr, bandpass, blep_saw, blep_square, circular_filter, compress, decay, drive, drive_clean, echo,
    highpass, limit, lowpass, noise, note_freq, partials, phase_of, plucked, reverb, rng, sine,
    supersaw, seconds, times, vowel, wah, widen,
)

# Chords by name, as the notes in them from the root up, in semitones.
SHAPES = {
    "": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10], "sus": [0, 5, 7], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9],
    "9": [0, 4, 7, 10, 14], "m9": [0, 3, 7, 10, 14], "maj9": [0, 4, 7, 11, 14], "69": [0, 4, 7, 9, 14],
    "13": [0, 4, 10, 14, 21], "7sus": [0, 5, 7, 10], "m11": [0, 3, 10, 14, 17],
}
ROOTS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
         "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def chord_notes(name, octave):
    """A chord like "Am7" as Hz from `octave` up."""
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    shape = SHAPES[name[len(root):]]
    base = 12 * (octave + 1) + ROOTS[root]
    return [440.0 * 2.0 ** ((base + s - 69) / 12.0) for s in shape]


# Instruments. Each makes one note: (Hz, seconds, how hard) to samples.

def kick(_f, _d, v):
    n = seconds(0.3)
    body = sine(np.geomspace(160, 45, n), n) * decay(n, 0.28)
    click = highpass(noise(n, 1), 3000) * decay(n, 0.004) * 0.3
    return drive(body + click, 1.5) * v


def snare(_f, _d, v):
    n = seconds(0.2)
    rattle = bandpass(noise(n, 2), 1200, 7000) * decay(n, 0.13)
    tone = sine(np.geomspace(230, 180, n), n) * decay(n, 0.06)
    return (rattle * 0.8 + tone * 0.6) * v


def steel(f, d, v):
    """A steel drum: a bright ringing note with the pan's out of tune
    overtones, hit hard and dying away."""
    n = seconds(max(d, 0.5))
    tone = sine(f, n) + sine(f * 2.0, n) * 0.5 * decay(n, 0.25) + sine(f * 2.98, n) * 0.22 * decay(n, 0.12)
    ping = sine(f * 4.1, n) * decay(n, 0.02) * 0.3
    return (tone + ping) * decay(n, 0.45) * adsr(n, 0.001, 0.0, 1.0, 0.03) * 0.7 * v


def hand_drum(f, d, v):
    """A hand drum: a thump that drops a little in pitch, and the slap of the
    hand on the skin."""
    n = seconds(0.35)
    body = sine(np.geomspace(f * 1.4, f, n), n) * decay(n, 0.16)
    slap = bandpass(noise(n, 7), 800, 4000) * decay(n, 0.01) * 0.4
    return drive(body + slap, 1.2) * v


def chime(f, d, v):
    """A glockenspiel: a bright bar that rings on, with a high glassy
    overtone that dies away first."""
    n = seconds(max(d, 0.9))
    tone = sine(f, n) + sine(f * 2.76, n) * 0.35 * decay(n, 0.12) + sine(f * 5.4, n) * 0.12 * decay(n, 0.03)
    return tone * decay(n, 0.9) * adsr(n, 0.001, 0.0, 1.0, 0.03) * 0.5 * v


# Making patterns.

def melody(steps_per_bar, *bars):
    """Hand written (note, steps) pairs, bar by bar, to (step, Hz, steps). A
    note of "." is a rest."""
    out = []
    at = 0
    for bar_index, bar in enumerate(bars):
        start = bar_index * steps_per_bar
        at = start
        for name, length in bar:
            if name != ".":
                out.append((at, note_freq(name), length))
            at += length
        assert at - start == steps_per_bar, "bar %d is %d steps" % (bar_index, at - start)
    return out


def drums(pattern, bars, offset=0):
    """A drum pattern like "x...x...x...x..." repeated for `bars` bars. X is
    an accent and o a soft hit."""
    out = []
    for b in range(bars):
        for i, c in enumerate(pattern):
            if c in "xXo":
                out.append((offset + b * len(pattern) + i, 0.0, 1, {"x": 0.8, "X": 1.0, "o": 0.45}[c]))
    return out


def bassline(chords, rhythm, octave=2, offset=0):
    """A bass part from the chord roots. Rhythm is sixteen steps of "r" (the
    root), "o" (an octave up), "5" (the fifth), "-" (hold) or "." (rest)."""
    out = []
    for b, name in enumerate(chords):
        root = chord_notes(name, octave)[0]
        fifth = root * 2.0 ** (7 / 12)
        i = 0
        while i < len(rhythm):
            c = rhythm[i]
            if c in "ro5":
                length = 1
                while i + length < len(rhythm) and rhythm[i + length] == "-":
                    length += 1
                f = {"r": root, "o": root * 2.0, "5": fifth}[c]
                out.append((offset + b * 16 + i, f, length))
                i += length
            else:
                i += 1
    return out


def arps(chords, octave=4, order=(0, 1, 2, 3, 2, 1), every=1, offset=0):
    """Up and down the chord, a note every `every` steps."""
    out = []
    for b, name in enumerate(chords):
        notes = chord_notes(name, octave)
        notes = notes + [notes[0] * 2.0]
        for k, step in enumerate(range(0, 16, every)):
            out.append((offset + b * 16 + step, notes[order[k % len(order)] % len(notes)], every))
    return out


def held(chords, octave=4, offset=0, length=16):
    """Each chord held for the bar."""
    out = []
    for b, name in enumerate(chords):
        for f in chord_notes(name, octave):
            out.append((offset + b * 16, f, length))
    return out


def comp(chords, rhythm, octave=4, offset=0):
    """Chords stabbed on the steps marked "x" in a sixteen step rhythm."""
    out = []
    for b, name in enumerate(chords):
        for i, c in enumerate(rhythm):
            if c == "x":
                for f in chord_notes(name, octave):
                    out.append((offset + b * 16 + i, f, 2))
    return out


# Pop palette instruments the flavour instruments and funk tunes borrow.
# Instruments here may give back (2, n) stereo.

def punch_kick(_f, _d, v):
    n = seconds(0.4)
    t = times(n)
    body = sine(48.0 + 150.0 * np.exp(-t / 0.025), n) * np.exp(-t / 0.12)
    knock = sine(np.geomspace(330, 120, n), n) * decay(n, 0.03) * 0.3
    click = highpass(noise(n, 21), 3000) * decay(n, 0.005) * 0.4
    return drive(body * 1.3 + knock + click, 2.2) * adsr(n, 0.0005, 0.0, 1.0, 0.03) * 0.9 * v


def snap_snare(_f, _d, v):
    n = seconds(0.3)
    body = sine(np.geomspace(280, 185, n), n) * decay(n, 0.09)
    rattle = bandpass(noise(n, 22), 1500, 9000) * decay(n, 0.16)
    snap = highpass(noise(n, 23), 5000) * decay(n, 0.02)
    return drive(body * 0.8 + rattle * 0.9 + snap * 0.6, 1.8) * 0.8 * v


def tick(_f, _d, v):
    """A closed hat."""
    n = seconds(0.08)
    return highpass(noise(n, 25), 8000, order=4) * decay(n, 0.025) * 0.6 * v


def shaker(_f, _d, v):
    n = seconds(0.09)
    t = times(n)
    env = np.clip(t / 0.012, 0.0, 1.0) * np.exp(-t / 0.03)
    return bandpass(noise(n, 29), 5000, 12000) * env * 0.7 * v


def cowbell(_f, _d, v):
    n = seconds(0.3)
    tone = blep_square(560.0, n) + blep_square(845.0, n)
    return bandpass(tone, 500, 3000) * decay(n, 0.2) * adsr(n, 0.001, 0.0, 1.0, 0.02) * 0.35 * v


def pop_bass(f, d, v):
    """A fat synth bass: a sub sine under a saw that's bright as it starts."""
    n = seconds(d)
    tone = sine(f, n) * 0.4 + blep_saw(f, n) * 0.6
    env = decay(n, 0.09)
    tone = lowpass(tone, 350) * (1.0 - env) + lowpass(tone, 2400) * env
    return drive(tone * adsr(n, 0.003, 0.06, 0.85, 0.02), 1.8) * 0.8 * v


def slap_bass(f, d, v):
    """A slap bass: a thumb on the string, bright for a moment and round
    after."""
    n = seconds(max(d, 0.1))
    tone = blep_saw(f, n) * 0.55 + sine(f, n) * 0.5 + blep_square(f * 2.0, n, 0.3) * 0.15 * decay(n, 0.05)
    env = decay(n, 0.05)
    tone = lowpass(tone, 500) * (1.0 - env) + lowpass(tone, 4000) * env
    thumb = bandpass(noise(n, 30), 800, 4000) * decay(n, 0.006) * 0.5
    return drive((tone + thumb) * adsr(n, 0.001, 0.12, 0.6, 0.03), 2.0) * 0.8 * v


def brass(f, d, v):
    """Synth brass: three saws that scoop up into the note and open bright
    for a moment."""
    n = seconds(d + 0.1)
    t = times(n)
    scoop = 1.0 - 0.015 * np.exp(-t / 0.03)
    tone = supersaw(f * scoop, n, 3, 0.005, seed=int(f) % 89) * 1.2
    bright = np.clip(t / 0.025, 0.0, 1.0) * (0.5 + 0.5 * np.exp(-t / 0.12))
    tone = lowpass(tone, 700) * (1.0 - bright) + lowpass(tone, 4200) * bright
    return drive(tone * adsr(n, 0.008, 0.1, 0.75, 0.06), 1.4) * 0.6 * v


def pump_pad(f, d, v):
    n = seconds(d + 0.3)
    tone = lowpass(supersaw(f, n, 5, 0.007, seed=int(f) % 83), 2200)
    return tone * adsr(n, 0.03, 0.3, 0.75, 0.3) * 0.35 * v


def pop_pluck(f, d, v):
    n = seconds(max(d, 0.18))
    tone = blep_saw(f, n) * 0.5 + blep_square(f * 2.0, n) * 0.2
    env = decay(n, 0.06)
    tone = lowpass(tone, 900) * (1.0 - env) + lowpass(tone, 6000) * env
    return tone * decay(n, 0.2) * adsr(n, 0.001, 0.0, 1.0, 0.02) * 0.8 * v


# Flavour for each cup, played over the band. Some give back (2, n) stereo.

def clavinet(f, d, v):
    """A funky clavinet: a string hit near the pickup, so it's bright and
    nasal, damped short as the key comes up."""
    n = seconds(d + 0.03)
    string = plucked(f, n, 0.07, 1.5, 0.5, harmonics=30)
    nasal = bandpass(string, 900, 2600)
    tone = highpass(string, f * 0.7) * 0.6 + nasal * 0.9
    return drive_clean(tone * adsr(n, 0.001, 0.15, 0.7, 0.025), 1.8) * 0.65 * v


def anvil(_f, _d, v):
    """An anvil clank for the foundry: a hammer on steel, ringing with out of
    tune overtones."""
    n = seconds(0.7)
    ring = partials(1180.0, n, [(1.0, 0.6, 0.6), (1.59, 0.45, 0.4), (2.36, 0.35, 0.3), (3.11, 0.25, 0.18), (4.43, 0.2, 0.1)])
    hit = bandpass(noise(n, 31), 2000, 9000) * decay(n, 0.008) * 0.6
    return (ring + hit) * adsr(n, 0.0005, 0.0, 1.0, 0.05) * 0.45 * v


def banjo(f, d, v):
    """A banjo-ish pluck: picked close to the bridge so it twangs, honking
    through its drum skin and dying away quickly."""
    n = seconds(max(d, 0.3) + 0.15)
    string = plucked(f, n, 0.11, 0.8, 1.3, stretch=0.0001)
    pick = bandpass(noise(n, 32), 2000, 7000) * decay(n, 0.004) * 0.25
    tone = string + bandpass(string, 1000, 2800) * 0.8 + pick
    return tone * adsr(n, 0.0008, 0.0, 1.0, 0.04) * 0.4 * v


def pop_whistle(f, d, v):
    """Somebody whistling: a pure note that slides up into place, with a
    wavering vibrato and a little breath."""
    n = seconds(d + 0.06)
    t = times(n)
    scoop = 1.0 - 0.04 * np.exp(-t / 0.025)
    vib = 1.0 + 0.009 * np.sin(2 * np.pi * 5.8 * t) * np.clip((t - 0.12) * 4.0, 0.0, 1.0)
    tone = sine(f * scoop * vib, n) + sine(f * 2.0 * scoop * vib, n) * 0.04
    breath = bandpass(noise(n, 33), f * 0.85, f * 1.2) * 0.12 + highpass(noise(n, 34), 5000) * 0.015
    return (tone + breath) * adsr(n, 0.03, 0.05, 0.85, 0.06) * 0.6 * v


def timpani(f, d, v):
    """A timpani: a big skin hit with a soft mallet. Its modes sit near 1,
    1.5, 2 and 2.5 times the note, and the pitch sags a little as it's hit."""
    n = seconds(max(d, 1.6))
    sag = 1.0 + 0.02 * decay(n, 0.08)
    modes = [(1.0, 1.0, 1.8), (1.5, 0.45, 1.1), (1.99, 0.3, 0.8), (2.44, 0.18 * v, 0.5), (2.98, 0.1 * v, 0.35), (0.62, 0.7, 0.12)]
    tone = partials(f * sag, n, modes)
    mallet = lowpass(noise(n, 35), 1500) * decay(n, 0.02) * 0.4
    return drive(tone + mallet, 1.3) * adsr(n, 0.001, 0.0, 1.0, 0.1) * 0.7 * v


def choir(f, d, v):
    """A choir pad singing "aah": three voices a side, each a little out of
    tune with its own vibrato, swelling in slowly. Stereo."""
    n = seconds(d + 0.5)
    t = times(n)
    sides = []
    for seed in (41, 141):
        r = rng(seed + int(f))
        buzz = np.zeros(n)
        for _ in range(3):
            vib = 1.0 + 0.004 * np.sin(2 * np.pi * r.uniform(4.6, 5.6) * t + r.uniform(0.0, 6.3))
            buzz += blep_saw(f * (1.0 + r.uniform(-0.005, 0.005)) * vib, n, r.uniform())
        sides.append(vowel(buzz, "a") + highpass(noise(n, seed), 5000) * 0.01)
    return np.stack(sides) * adsr(n, 0.25, 0.3, 0.8, 0.4) * 0.5 * v


def anthem_guitar(f, d, v):
    """A guitar-ish lead for anthems: a driven string that bends up into the
    note, a wide vibrato as it holds and a speaker's dark top."""
    n = seconds(d + 0.1)
    t = times(n)
    bend = 2.0 ** (-np.exp(-t / 0.03) / 12.0)
    vib = 1.0 + 0.008 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) * 3.0, 0.0, 1.0)
    string = blep_saw(f * bend * vib, n) * 0.7 + blep_square(f * 1.003 * bend * vib, n, 0.4) * 0.3
    tone = drive_clean(lowpass(string, 3000) * 2.0, 4.0)
    tone = highpass(lowpass(tone, 4200, order=4), 150) + bandpass(tone, 1200, 2500) * 0.4
    return tone * adsr(n, 0.004, 0.2, 0.85, 0.07) * 0.38 * v


def stadium_clap(_f, _d, v):
    """A stadium of hands: a dozen claps a few milliseconds apart spread
    across both sides, and the stands ringing after. Stereo."""
    n = seconds(0.6)
    r = rng(42)
    out = np.zeros((2, n))
    for k in range(12):
        at = seconds(r.uniform(0.0, 0.022))
        burst = bandpass(noise(n - at, 300 + k), r.uniform(800, 1300), r.uniform(4000, 7000)) * decay(n - at, r.uniform(0.02, 0.04))
        pan = r.uniform(-1.0, 1.0)
        out[0, at:] += burst * np.cos((pan + 1.0) * np.pi / 4.0)
        out[1, at:] += burst * np.sin((pan + 1.0) * np.pi / 4.0)
    stands = np.stack([bandpass(noise(n, s), 700, 4000) for s in (43, 143)]) * decay(n, 0.4) * adsr(n, 0.01, 0.0, 1.0, 0.0) * 0.12
    return (out * 0.35 + stands) * adsr(n, 0.0005, 0.0, 1.0, 0.05) * 0.8 * v


def chug(f, d, v):
    """A distorted synth guitar chug: a power chord (the note, its fifth and
    octave) driven hard and palm muted, so it's short and dark unless held.
    Two takes, one each side. Stereo."""
    n = seconds(d + 0.05)
    mute = decay(n, 0.1 if d < 0.25 else 0.8)
    sides = []
    for k, cents in enumerate((-4.0, 5.0)):
        g = 2.0 ** (cents / 1200.0)
        x = sum(blep_saw(f * g * ratio, n, 0.37 * j + 0.2 * k) for j, ratio in enumerate((1.0, 1.4983, 2.0)))
        x = drive_clean(lowpass(x, 2500) * 2.5, 5.0)
        x = lowpass(x, 700) * (1.0 - mute) + lowpass(x, 4500, order=4) * mute
        sides.append(highpass(x, 90))
    return np.stack(sides) * adsr(n, 0.002, 0.05, 0.9, 0.03) * 0.4 * v


def tom(f, d, v):
    """A tom for fills: a skin that drops a little in pitch, with the stick's
    crack on top. Play them high to low for a roll down the kit."""
    n = seconds(0.6)
    t = times(n)
    body = partials(f * (1.0 + 0.5 * np.exp(-t / 0.03)), n, [(1.0, 1.0, 0.45), (1.6, 0.3, 0.15)])
    crack = bandpass(noise(n, 36), 1500, 7000) * decay(n, 0.01) * 0.35
    return drive(body + crack, 1.6) * adsr(n, 0.0005, 0.0, 1.0, 0.05) * 0.75 * v


def vocoder_lead(f, d, v):
    """A robot singer: a buzzy saw sung through a vowel that moves from "oh"
    to "ee" over each note, with a breath of noise at the start."""
    n = seconds(d + 0.06)
    t = times(n)
    buzz = blep_saw(f, n) * 0.6 + blep_saw(f * 1.005, n, 0.5) * 0.4 + noise(n, 37) * 0.15 * decay(n, 0.03)
    motion = np.clip(t / max(d, 0.08), 0.0, 1.0)
    sung = vowel(buzz, "o", motion, "i") * 2.2 + highpass(noise(n, 38), 4000) * decay(n, 0.015) * 0.1
    return sung * adsr(n, 0.005, 0.08, 0.85, 0.05) * 0.7 * v


def fair_organ(f, d, v):
    """A fairground band organ: flue pipes at the note, the octave and the
    twelfth, a reedy stop under them and a quick tremolo."""
    n = seconds(d + 0.04)
    t = times(n)
    flue = partials(f, n, [(1.0, 1.0, 99.0), (2.0, 0.6, 99.0), (3.0, 0.35, 99.0), (4.0, 0.25, 99.0), (6.0, 0.1, 99.0), (8.0, 0.06, 99.0)])
    reed = lowpass(blep_square(f, n, 0.25), 2800) * 0.35
    chiff = bandpass(noise(n, 39), 1500, 6000) * decay(n, 0.015) * 0.1
    trem = 1.0 + 0.12 * np.sin(2 * np.pi * 6.5 * t)
    return (flue * 0.5 + reed + chiff) * trem * adsr(n, 0.006, 0.03, 0.9, 0.03) * 0.5 * v


def calliope(f, d, v):
    """A steam calliope: whistle pipes, each a little out of tune, a pure
    note with a puff of steam and a quick wide vibrato."""
    n = seconds(d + 0.05)
    t = times(n)
    off = 1.0 + rng(int(f * 10)).uniform(-0.006, 0.006)
    vib = 1.0 + 0.01 * np.sin(2 * np.pi * 7.0 * t)
    tone = partials(f * off * vib, n, [(1.0, 1.0, 99.0), (2.0, 0.3, 99.0), (3.0, 0.1, 99.0)])
    steam = bandpass(noise(n, 40), f * 0.7, f * 1.6) * 0.15 + highpass(noise(n, 44), 3000) * decay(n, 0.03) * 0.15
    return (tone + steam) * adsr(n, 0.015, 0.05, 0.9, 0.05) * 0.55 * v


def pop_accordion(f, d, v):
    """A musette accordion: three reeds, one in tune and one each a little
    sharp and flat beating against it, the bellows pushing into each note.
    Stereo, the out of tune reeds either side."""
    n = seconds(d + 0.05)
    t = times(n)

    def reed(cents, ph):
        g = 2.0 ** (cents / 1200.0)
        return lowpass(blep_square(f * g, n, 0.32, ph) * 0.7 + blep_saw(f * g, n, ph) * 0.3, 3200)
    mid, sharp, flat = reed(0.0, 0.0), reed(14.0, 0.3), reed(-12.0, 0.6)
    bellows = adsr(n, 0.025, 0.12, 0.8, 0.05) * (1.0 + 0.05 * np.sin(2 * np.pi * 4.0 * t))
    return np.stack([mid + sharp * 0.8 + flat * 0.4, mid + flat * 0.8 + sharp * 0.4]) * bellows * 0.3 * v


def yodel(f, d, v):
    """A yodel-like lead: low notes sung full in the chest ("oh"), high ones
    flipped up light and pure, and every note cracks in from a third below."""
    n = seconds(d + 0.08)
    t = times(n)
    vib = 1.0 + 0.007 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) * 4.0, 0.0, 1.0)
    pitch = f * 2.0 ** (-3.0 * np.exp(-t / 0.018) / 12.0) * vib
    chest = vowel(blep_saw(pitch, n), "o") * 1.6
    head = sine(pitch, n) + sine(pitch * 2.0, n) * 0.12 + bandpass(noise(n, 45), f * 0.9, f * 2.5) * 0.05
    w = np.clip((f - 500.0) / 60.0, 0.0, 1.0)
    return (chest * (1.0 - w) + head * w * 0.8) * adsr(n, 0.01, 0.08, 0.85, 0.06) * 0.6 * v


def pop_twang(f, d, v):
    """A twangy guitar: a bridge pickup's bright snappy pluck that rings on,
    with a gentle wobble from the vibrato arm as it holds."""
    n = seconds(d + 0.3)
    t = times(n)
    wob = 1.0 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.2) * 3.0, 0.0, 1.0)
    string = plucked(f * wob, n, 0.09, 2.0, 0.7, harmonics=30)
    tone = drive_clean(string * 1.4 + bandpass(string, 1400, 3500) * 0.8, 1.6)
    return tone * adsr(n, 0.0008, 0.3, 0.75, 0.25) * 0.55 * v


def brush(_f, _d, v):
    """A brushed snare for the train beat: soft hits are a swish of wires,
    accents a slap with the snare buzzing under it."""
    n = seconds(0.25)
    t = times(n)
    swish = np.clip(t / 0.012, 0.0, 1.0) * np.exp(-t / 0.05)
    wires = bandpass(noise(n, 46), 1500, 9000) * swish
    slap = bandpass(noise(n, 47), 400, 4000) * decay(n, 0.06) + sine(np.geomspace(220, 180, n), n) * decay(n, 0.05) * 0.4
    accent = np.clip((v - 0.5) * 2.5, 0.0, 1.0)
    return (wires * 0.7 + slap * accent) * adsr(n, 0.0005, 0.0, 1.0, 0.03) * 0.6 * v


def pop_marimba(f, d, v):
    """A marimba: a round wooden bar, its overtones (tuned near 4 and 10
    times the note) ringing for a moment, brighter the harder it's hit."""
    n = seconds(max(d, 0.6))
    tone = partials(f, n, [(1.0, 1.0, 0.55), (3.93, 0.3 * v, 0.08), (9.2, 0.08 * v, 0.02)])
    mallet = bandpass(noise(n, 48), 300, 2500) * decay(n, 0.004) * 0.15
    return (tone + mallet) * adsr(n, 0.001, 0.0, 1.0, 0.03) * 0.75 * v


def conga(f, d, v):
    """A conga: an open tone that sags a little in pitch, and on accents a
    slap of fingers on the skin's edge."""
    n = seconds(0.4)
    t = times(n)
    tone = partials(f * (1.0 + 0.06 * np.exp(-t / 0.02)), n, [(1.0, 1.0, 0.3), (1.59, 0.25, 0.08), (2.14, 0.12, 0.05)])
    accent = np.clip((v - 0.5) * 2.5, 0.0, 1.0)
    slap = bandpass(noise(n, 49), 1200, 6000) * decay(n, 0.015) * 0.6 * accent
    thumb = lowpass(noise(n, 50), 600) * decay(n, 0.01) * 0.2
    return drive(tone + slap + thumb, 1.3) * adsr(n, 0.0008, 0.0, 1.0, 0.04) * 0.7 * v


def _flute(f, d, v, air, chiff, attack, seed):
    """A flute's note: a soft tone that overblows for a moment as it starts,
    with breath around it and a chiff of air at the start."""
    n = seconds(d + 0.08)
    t = times(n)
    vib = 1.0 + 0.007 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.15) * 3.0, 0.0, 1.0)
    tone = partials(f * vib, n, [(1.0, 1.0, 99.0), (2.0, 0.15, 99.0), (3.0, 0.06, 99.0), (2.0, 0.35, 0.05)])
    breath = bandpass(noise(n, seed), f * 0.8, f * 3.0) * air + highpass(noise(n, seed + 1), 4000) * air * 0.2
    puff = bandpass(noise(n, seed + 2), 2500, 7000) * decay(n, 0.025) * chiff
    return (tone + breath + puff) * adsr(n, attack, 0.06, 0.85, 0.08) * 0.55 * v


def wood_flute(f, d, v):
    """A wooden flute for the jungle: hollow and a little breathy, with a
    clear chiff."""
    return _flute(f, d, v, 0.12, 0.3, 0.025, 51)


def air_flute(f, d, v):
    """An airy flute for the sky: more breath than note, soft at the start."""
    return _flute(f, d, v, 0.3, 0.08, 0.06, 54)


def open_pad(f, d, v):
    """An open pad for the sky: soft detuned saws that swell in slowly, an
    octave up shimmer and a little air on top. Stereo."""
    n = seconds(d + 0.6)
    body = lowpass(supersaw(f, n, 5, 0.006, seed=int(f) % 79), 1800)
    shimmer = lowpass(supersaw(f * 2.0, n, 3, 0.004, seed=int(f) % 73), 5000) * 0.25
    air = np.stack([highpass(noise(n, s), 6000) for s in (57, 157)]) * 0.02
    return (body + shimmer + air) * adsr(n, 0.4, 0.4, 0.8, 0.6) * 0.35 * v


def wah_guitar(f, d, v):
    """A funk guitar through a wah that opens with each pick and closes again
    as the note holds."""
    n = seconds(d + 0.08)
    t = times(n)
    string = drive_clean(plucked(f, n, 0.15, 0.8, 0.8) * 2.0, 2.0)
    position = np.clip(t / 0.05, 0.0, 1.0) * (0.25 + 0.75 * np.exp(-t / 0.2))
    tone = wah(string, position) * 1.8 + string * 0.15
    return tone * adsr(n, 0.001, 0.05, 0.85, 0.03) * 0.6 * v


def e_piano(f, d, v):
    """An electric piano: a sine that barks when hit hard (a little FM), a
    tine's ping on top and a tremolo that sways between the sides. Stereo."""
    n = seconds(d + 0.4)
    t = times(n)
    p = phase_of(f, n)
    index = (0.5 + 1.5 * v) * decay(n, 0.4) * min(1.0, 700.0 / f)
    tone = np.sin(2 * np.pi * p + index * np.sin(2 * np.pi * p))
    tine = partials(f, n, [(4.0, 0.06, 0.05), (7.0, 0.03, 0.02)])
    body = (tone + tine) * decay(n, 2.5) * adsr(n, 0.002, 0.0, 1.0, 0.25)
    sway = 0.3 * np.sin(2 * np.pi * 4.8 * t)
    return np.stack([body * (1.0 - sway), body * (1.0 + sway)]) * 0.4 * v


def horn_section(f, d, v):
    """A brass section: trumpet and sax on the note either side, a trombone
    an octave down in the middle, each a moment apart, scooping up and
    brightening as they push. Stereo."""
    n = seconds(d + 0.1)

    def horn(g, seed, late, dark):
        r = rng(seed)
        m = n - seconds(late)
        t = times(m)
        scoop = 1.0 - 0.03 * np.exp(-t / 0.04)
        vib = 1.0 + 0.004 * np.sin(2 * np.pi * r.uniform(5.0, 6.0) * t) * np.clip((t - 0.2) * 3.0, 0.0, 1.0)
        x = blep_saw(f * g * scoop * vib, m, r.uniform())
        bright = np.clip(t / 0.04, 0.0, 1.0) * (0.55 + 0.45 * np.exp(-t / 0.15))
        x = lowpass(x, 900) * (1.0 - bright) + lowpass(x, 4500 * dark) * bright
        x = (x + bandpass(x, 1000, 1800) * 0.6) * adsr(m, 0.015, 0.1, 0.8, 0.07)
        return np.concatenate([np.zeros(n - m), x])
    trumpet = horn(1.0, 61, 0.0, 1.0)
    sax = horn(1.003, 62, 0.008, 0.7)
    bone = horn(0.5, 63, 0.004, 0.8) * 0.8
    return drive(np.stack([trumpet + sax * 0.5 + bone * 0.7, sax + trumpet * 0.5 + bone * 0.7]), 1.3) * 0.3 * v


# Writing songs in sections.

def bars(*lines):
    """Bars written as text, like "E5:2 A5:2 .:4", to (note, steps) pairs."""
    return [[(w.split(":")[0], int(w.split(":")[1])) for w in line.split()] for line in lines]


def song(*sections):
    """Sections as (name, chords), to [(name, first bar, chords)] and every
    chord in order."""
    out = []
    chords = []
    for name, ch in sections:
        out.append((name, len(chords), ch))
        chords = chords + ch
    return out, chords


def shift(notes, steps):
    return [(n[0] + steps,) + tuple(n[1:]) for n in notes]


def octave(notes, k):
    return [(n[0], n[1] * 2.0 ** k) + tuple(n[2:]) for n in notes]


def part(instrument, notes, loud, pan=0.0, verb=0.0, echo_send=0.0, duck=0.0):
    """One part of a tune. `duck` is how far it drops with each kick."""
    return {"instrument": instrument, "notes": notes, "loud": loud, "pan": pan,
            "verb": verb, "echo": echo_send, "duck": duck}


def pump(kicks, step, length, total):
    """How much a part drops after each kick (notes from drums()), 0 to 1,
    a value a sample. It wraps around the loop's end."""
    beat = step * 4.0
    n = seconds(beat * 0.6)
    t = times(n)
    shape = np.minimum(t / 0.004, 1.0) * (1.0 - np.clip(t / (beat * 0.6), 0.0, 1.0) ** 2) ** 2
    out = np.zeros(total)
    for note in kicks:
        idx = (seconds(note[0] * step) + np.arange(n)) % total
        out[idx] = np.maximum(out[idx], shape)
    return out[np.arange(length) % total]


def render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.0):
    """Plays the parts for inst_demo.py and mixes them on a bus: reverb and a
    dotted eighth echo, the tail folded back onto the start, then width,
    glue compression and a limiter, all wrapping around so it loops. `level` is
    the RMS it comes out at, in dBFS."""
    step = 60.0 / bpm / 4.0
    total = seconds(bar_count * 16 * step)
    spill = seconds(3.0)
    length = total + spill
    bus = np.zeros((2, length))
    verb = np.zeros((2, length))
    echoes = np.zeros((2, length))
    for p in parts:
        mono = np.zeros(length)
        wide = np.zeros((2, length))
        for note in p["notes"]:
            at, f, steps = note[0], note[1], note[2]
            v = note[3] if len(note) > 3 else 1.0
            sound = p["instrument"](f, steps * step, v)
            s = seconds(at * step) % total
            end = min(s + sound.shape[-1], length)
            if sound.ndim == 1:
                mono[s:end] += sound[: end - s]
            else:
                wide[:, s:end] += sound[:, : end - s]
        pan = p["pan"]
        track = np.stack([mono * np.cos((pan + 1.0) * np.pi / 4.0), mono * np.sin((pan + 1.0) * np.pi / 4.0)]) * np.sqrt(2.0)
        track += wide * np.array([[min(1.0, 1.0 - pan)], [min(1.0, 1.0 + pan)]])
        if p["duck"]:
            track *= 1.0 - p["duck"] * pump(kicks, step, length, total)
        track *= p["loud"]
        bus += track
        verb += track * p["verb"]
        echoes += track * p["echo"]
    bus[0] += reverb(verb[0], 1.0, 1.0) * wet * 3.0
    bus[1] += reverb(verb[1], 1.0, 0.93) * wet * 3.0
    # Fold what rings on past the end back onto the start.
    for x in (bus, echoes):
        x[:, :spill] += x[:, total:total + spill]
    out = bus[:, :total] + echo(echoes[:, :total], seconds(3 * step), 0.4, 6)
    out = np.stack([circular_filter(side, low=28.0) for side in out])
    out = widen(out, 1.15)
    out = compress(out / np.max(np.abs(out)), -14.0, 2.5, 0.005, 0.12)
    for _ in range(3):
        out *= 10.0 ** (level / 20.0) / np.sqrt(np.mean(out ** 2))
        out = limit(out, 0.84)
    return out


def in_sections(form, names, make):
    """Notes from `make(first step, chords)` for each section named."""
    out = []
    for name, start, chords in form:
        if name in names:
            out += make(start * 16, chords)
    return out


# Chill funk. One soft band for every tune: a round kick, a snare with
# ghost notes and rimshots, soft hats, a finger bass with slides and dead
# notes, chicken scratch guitar, e_piano chords and horns on the hooks, all
# on swung sixteenths and sitting under the tune. Each cup adds its own
# colour on top. Notes may carry a fifth item, a dict of extras for the
# instrument (like {"slide": -2.0} or {"dead": True}).

def soft_kick(_f, _d, v):
    """A round kick: a low sine that drops quickly into its note, with a
    felt beater on top."""
    n = seconds(0.35)
    t = times(n)
    body = sine(52.0 + 70.0 * np.exp(-t / 0.03), n) * np.exp(-t / 0.16)
    felt = lowpass(noise(n, 71), 1500) * decay(n, 0.006) * 0.25
    return drive(body + felt, 1.3) * adsr(n, 0.001, 0.0, 1.0, 0.04) * 0.85 * v


def soft_snare(_f, _d, v):
    """A snare played lightly. Soft hits (ghost notes) are mostly the wires,
    the backbeat has the drum's body under it."""
    n = seconds(0.25)
    accent = np.clip((v - 0.3) * 2.0, 0.0, 1.0)
    body = sine(np.geomspace(240, 190, n), n) * decay(n, 0.07) * accent
    wires = lowpass(bandpass(noise(n, 72), 1200, 8000), 6000) * decay(n, 0.05 + 0.08 * accent)
    return (body * 0.7 + wires * 0.8) * adsr(n, 0.0008, 0.0, 1.0, 0.03) * 0.7 * v


def rimshot(_f, _d, v):
    """A cross stick: the stick laid across the rim, a woody click."""
    n = seconds(0.12)
    tone = sine(1750.0, n) * decay(n, 0.012) * 0.5 + sine(520.0, n) * decay(n, 0.03) * 0.6
    click = bandpass(noise(n, 73), 1500, 5000) * decay(n, 0.008)
    return (tone + click) * adsr(n, 0.0003, 0.0, 1.0, 0.02) * 0.6 * v


def soft_hat(_f, _d, v):
    """A closed hat played with the tip of the stick, soft and a little dark."""
    n = seconds(0.07)
    x = lowpass(highpass(noise(n, 74), 6000, order=4), 12000)
    return x * decay(n, 0.018 + 0.012 * v) * 0.5 * v


def soft_open_hat(_f, _d, v):
    n = seconds(0.35)
    x = lowpass(highpass(noise(n, 75), 5500, order=4), 11000)
    return x * decay(n, 0.16) * adsr(n, 0.002, 0.0, 1.0, 0.04) * 0.35 * v


def finger_bass(f, d, v, slide=0.0, dead=False):
    """A round finger bass, mostly the note itself and a little brighter as
    it's plucked. `slide` glides in from that many semitones away, and a dead
    note is just the thump of a muted string."""
    if dead:
        n = seconds(0.07)
        thump = sine(f, n) * 0.6 + lowpass(noise(n, 76), 500) * 0.5
        return thump * decay(n, 0.02) * adsr(n, 0.001, 0.0, 1.0, 0.01) * 0.7 * v
    n = seconds(d + 0.03)
    t = times(n)
    glide = 2.0 ** (slide / 12.0 * np.exp(-t / 0.035)) if slide else 1.0
    tone = sine(f * glide, n) * 0.6 + plucked(f * glide, n, 0.25, 1.8, 1.2, harmonics=12) * 0.8
    finger = lowpass(noise(n, 77), 800) * decay(n, 0.005) * 0.15
    tone = lowpass(tone + finger, 1400)
    return drive(tone * adsr(n, 0.004, 0.15, 0.8, 0.03), 1.3) * 0.8 * v


def scratch_guitar(f, d, v, dead=False):
    """A clean funk guitar, no effects. A dead note is the chicken scratch:
    the strings muted under the hand, just the pick's click and a choked
    note."""
    if dead:
        n = seconds(0.05)
        string = plucked(f, n, 0.1, 0.05, 1.0, harmonics=25)
        click = bandpass(noise(n, 78 + int(f) % 7), 1500, 5000) * decay(n, 0.008)
        return (bandpass(string, 400, 4000) * 0.8 + click * 0.5) * decay(n, 0.015) * 0.6 * v
    n = seconds(min(d, 0.25) + 0.03)
    string = plucked(f, n, 0.12, 0.6, 0.9, harmonics=30)
    tone = highpass(string, 250) + bandpass(string, 1500, 3500) * 0.4
    return tone * adsr(n, 0.001, 0.08, 0.6, 0.03) * 0.55 * v


def vibes(f, d, v):
    """A vibraphone: soft mallets on metal bars, a pure ring with the motor's
    slow tremolo swaying between the sides. Stereo."""
    n = seconds(max(d + 0.6, 1.2))
    t = times(n)
    tone = partials(f, n, [(1.0, 1.0, 1.4), (4.0, 0.12, 0.2), (10.0, 0.03, 0.05)])
    mallet = lowpass(noise(n, 79), 2000) * decay(n, 0.003) * 0.05
    body = (tone + mallet) * adsr(n, 0.002, 0.0, 1.0, 0.1)
    sway = 0.25 * np.sin(2 * np.pi * 5.0 * t)
    return np.stack([body * (1.0 - sway), body * (1.0 + sway)]) * 0.45 * v


# The drums, for telling the drum and band levels apart on the bus.
FUNK_KIT = {soft_kick, soft_snare, rimshot, soft_hat, soft_open_hat, shaker, conga, cowbell, hand_drum,
            brush, tom, anvil, stadium_clap, timpani}


# Writing funk parts.

def kit(pattern, count, offset=0):
    """A drum pattern repeated for `count` bars. "X" is an accent, "x" a
    normal hit, "o" soft and "g" a ghost note."""
    out = []
    for b in range(count):
        for i, c in enumerate(pattern):
            if c in "Xxog":
                out.append((offset + b * len(pattern) + i, 0.0, 1, {"X": 1.0, "x": 0.75, "o": 0.45, "g": 0.22}[c]))
    return out


def kit_parts(form, rules):
    """Drum parts for each section of the form a rule names, played by kit()
    with its ghost notes."""
    out = []
    for name, start, chords in form:
        for names, pattern in rules:
            if name in names:
                out += kit(pattern, len(chords), start * 16)
    return out


def pitched(notes, hz):
    """Drum hits played at one pitch, for congas and the like."""
    return [(n[0], hz) + tuple(n[2:]) for n in notes]


def midi_of(f):
    return int(round(69 + 12 * np.log2(f / 440.0)))


def hz_of(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def voicing(name, low=55, top=None):
    """A chord as Hz, rootless when it has four notes or more, each note
    moved into the octave above MIDI note `low`. `top` keeps only the
    highest few."""
    notes = [midi_of(f) for f in chord_notes(name, 0)]
    if len(notes) >= 4:
        notes = notes[1:]
    placed = sorted({low + (m - low) % 12 for m in notes})
    if top:
        placed = placed[-top:]
    return [hz_of(m) for m in placed]


def runs(rhythm):
    """A sixteen step rhythm to (step, character, steps held), each "-"
    after a hit holding it on."""
    out = []
    i = 0
    while i < len(rhythm):
        c = rhythm[i]
        length = 1
        while i + length < len(rhythm) and rhythm[i + length] == "-":
            length += 1
        if c not in ".-":
            out.append((i, c, length))
        i += length
    return out


def keys_comp(chords, rhythm, low=55, offset=0):
    """Chords from voicing() played to a rhythm: "X", "x" and "o" start a
    chord, hard to soft, "-" holds it and "." rests."""
    out = []
    for b, name in enumerate(chords):
        notes = voicing(name, low)
        for i, c, length in runs(rhythm):
            for f in notes:
                out.append((offset + b * 16 + i, f, length, {"X": 1.0, "x": 0.75, "o": 0.45}[c]))
    return out


def finger_line(chords, rhythm, low=33, offset=0):
    """A finger bass part from the chords, the root kept in the octave above
    MIDI note `low`. "r" is the root, "o" the octave, "5" the fifth, "7" the
    seventh, "3" the third, "s" the root slid into from a tone below, "O" the
    octave slid up from the root, "x" a dead note, "-" holds and "." rests."""
    out = []
    for b, name in enumerate(chords):
        shape = [midi_of(f) for f in chord_notes(name, 0)]
        root = low + (shape[0] - low) % 12
        seventh = shape[3] - shape[0] if len(shape) > 3 else 10
        pitch = {"r": 0, "o": 12, "5": 7, "7": seventh, "3": shape[1] - shape[0], "s": 0, "O": 12, "x": 0}
        extra = {"s": {"slide": -2.0}, "O": {"slide": -12.0}, "x": {"dead": True}}
        for i, c, length in runs(rhythm):
            v = 0.45 if c == "x" else (1.0 if i == 0 else 0.8)
            out.append((offset + b * 16 + i, hz_of(root + pitch[c]), length, v, extra.get(c, {})))
    return out


def scratch(chords, rhythm, low=62, offset=0):
    """Chicken scratch guitar on the top three notes of each chord: "x" and
    "X" an open stab, "-" a muted scratch, "." rests. Each string sounds a
    moment after the last, down on the beat and up off it."""
    out = []
    for b, name in enumerate(chords):
        notes = voicing(name, low, 3)
        for i, c in enumerate(rhythm):
            if c == ".":
                continue
            order = notes if i % 2 == 0 else notes[::-1]
            v = {"X": 1.0, "x": 0.8, "-": 0.5}[c]
            for k, f in enumerate(order):
                out.append((offset + b * 16 + i + k * 0.04, f, 1, v, {"dead": c == "-"}))
    return out


def swing(notes, amount=0.6):
    """Swung sixteenths: each note on an off sixteenth is pushed late, so the
    pair splits `amount` to 1 - `amount` instead of half and half."""
    return [(n[0] + (2.0 * amount - 1.0) * (int(np.floor(n[0])) % 2),) + tuple(n[1:]) for n in notes]


def feel(notes, seed, timing=0.02, loud=0.08):
    """A player's small unevenness, in steps and how hard: each note a touch
    early or late and a little harder or softer, the same every render."""
    r = rng(seed)
    out = []
    for n in notes:
        v = n[3] if len(n) > 3 else 1.0
        out.append((n[0] + r.normal(0.0, timing), n[1], n[2], v * (1.0 + r.uniform(-loud, loud))) + tuple(n[4:]))
    return out


LAST_BALANCE = {}


def render_funk(bpm, bar_count, parts, swing_amount=0.6, room=0.12, level=-13.0):
    """Plays a funk tune's parts on swung sixteenths and mixes them warm: a
    short room, an echo send, the tail folded back onto the start, a gentle
    tilt down in the highs, light glue compression and a limiter, all
    wrapping around so it loops. `level` is the RMS it comes out at, in dBFS.
    The drums' and the band's RMS before the bus go in LAST_BALANCE."""
    step = 60.0 / bpm / 4.0
    total = seconds(bar_count * 16 * step)
    spill = seconds(3.0)
    length = total + spill
    groups = {"drums": np.zeros((2, length)), "band": np.zeros((2, length))}
    verb = np.zeros((2, length))
    echoes = np.zeros((2, length))
    for k, p in enumerate(parts):
        mono = np.zeros(length)
        wide = np.zeros((2, length))
        for note in feel(swing(p["notes"], swing_amount), 100 + k):
            at, f, steps, v = note[:4]
            extra = note[4] if len(note) > 4 else {}
            sound = p["instrument"](f, steps * step, v, **extra)
            s = seconds(at * step) % total
            end = min(s + sound.shape[-1], length)
            if sound.ndim == 1:
                mono[s:end] += sound[: end - s]
            else:
                wide[:, s:end] += sound[:, : end - s]
        pan = p["pan"]
        track = np.stack([mono * np.cos((pan + 1.0) * np.pi / 4.0), mono * np.sin((pan + 1.0) * np.pi / 4.0)]) * np.sqrt(2.0)
        track += wide * np.array([[min(1.0, 1.0 - pan)], [min(1.0, 1.0 + pan)]])
        track *= p["loud"]
        groups["drums" if p["instrument"] in FUNK_KIT else "band"] += track
        verb += track * p["verb"]
        echoes += track * p["echo"]
    bus = groups["drums"] + groups["band"]
    bus[0] += reverb(verb[0], 1.0, 0.75) * room * 3.0
    bus[1] += reverb(verb[1], 1.0, 0.7) * room * 3.0
    # Fold what rings on past the end back onto the start.
    for x in (bus, echoes, groups["drums"], groups["band"]):
        x[:, :spill] += x[:, total:total + spill]
    for name, x in groups.items():
        LAST_BALANCE[name] = 20.0 * np.log10(np.sqrt(np.mean(x[:, :total] ** 2)) + 1e-12)
    out = bus[:, :total] + echo(echoes[:, :total], seconds(3 * step), 0.3, 4)
    out = np.stack([circular_filter(side, low=30.0, tilt=-0.5) for side in out])
    out = widen(out, 1.1)
    out = compress(out / np.max(np.abs(out)), -18.0, 1.8, 0.02, 0.25)
    for _ in range(3):
        out *= 10.0 ** (level / 20.0) / np.sqrt(np.mean(out ** 2))
        out = limit(out, 0.84)
    return out


def bars_at(form, names, lines):
    """Hand written bars played from the start of each section named."""
    return in_sections(form, names, lambda at, _c: shift(melody(16, *lines), at))


def in_turn(form, names, rhythms, make):
    """Notes from `make(chords, rhythm, first step)` for each bar of the
    sections named, taking the rhythms in turn."""
    out = []
    for name, start, chords in form:
        if name in names:
            for i, c in enumerate(chords):
                out += make([c], rhythms[i % len(rhythms)], (start + i) * 16)
    return out


def last_bar(form, names, rhythm, make):
    """Notes from `make(chords, rhythm, first step)` on the last bar of each
    section named."""
    return in_sections(form, names, lambda at, c: make(c[-1:], rhythm, at + 16 * (len(c) - 1)))


# The sections every funk race shares: a four bar build on the groove's
# first chords, groove A, a lift, the hook, a breakdown on the hook's first
# chords, groove A again and the hook to close, which runs back into the build.
BAND = ("a", "b", "hook", "a2", "hook2")
QUIET = "................"


def funk_form(groove, lift, hook_chords):
    return song(("intro", groove[:4]), ("a", groove), ("b", lift), ("hook", hook_chords),
                ("break", hook_chords[:4]), ("a2", groove[:4]), ("hook2", hook_chords))


def kit_bar(_chords, rhythm, at):
    return kit(rhythm, 1, at)


def funk_kit(form, kick, backbeat, hats="xgogxgogxgogxgog", loud=(0.52, 0.34, 0.2), snare=soft_snare,
             fill="....X..g.g..oxox"):
    """The soft kit through the band sections, with the build in the intro:
    hats in its second bar, kick and ghost notes in the third, the full beat
    and a snare pickup in the fourth. `kick` and `backbeat` are rhythms taken
    bar by bar in turn, and an open hat comes every other bar."""
    k, s, h = loud
    build = lambda rhythms: in_turn(form, ("intro",), rhythms, kit_bar)
    return [
        part(soft_kick, in_turn(form, BAND, kick, kit_bar) + build([QUIET, QUIET, "X.......x.......", kick[0]]), k),
        part(snare, in_turn(form, BAND, backbeat, kit_bar) + build([QUIET, QUIET, ".......g.g.....g", fill]), s, 0.05, 0.12),
        part(soft_hat, in_turn(form, BAND, [hats], kit_bar) + build([QUIET, "x.o.x.o.x.o.x.o.", hats, hats]), h, 0.3),
        part(soft_open_hat, in_turn(form, BAND, [QUIET, "..............o."], kit_bar), h * 0.7, 0.3),
    ]


def funk_bass(form, lines, breakdown="r-----.x5-----s.", low=33):
    """The finger bass from the first bar, its lines taken bar by bar in turn,
    and held longer in the breakdown."""
    play = lambda c, r, at: finger_line(c, r, low, at)
    return in_turn(form, ("intro",) + BAND, lines, play) + in_turn(form, ("break",), [breakdown], play)


def comping(form, names, rhythm, low=55):
    """Chords from keys_comp() through the sections named."""
    return in_sections(form, names, lambda at, c: keys_comp(c, rhythm, low, at))


def fill_down(form, names, pitches=(240.0, 200.0, 165.0, 135.0), loud=0.7):
    """A tom fill down the kit over the last four steps of each section named."""
    out = []
    for name, start, chords in form:
        if name in names:
            end = (start + len(chords)) * 16
            out += [(end - 4 + k, f, 1, loud + 0.1 * k) for k, f in enumerate(pitches)]
    return out


def funk_menu():
    """The garage and the menus: a groove in G that builds up over four bars,
    e_piano and bass first, then hats, kick and a little snare pickup, then
    busy finger bass and e_piano stabs in the pocket with the main theme's
    hook on soft vibes."""
    bpm = 97
    groove = ["Gmaj9", "Em9", "Am9", "D9"] * 2
    hook_chords = ["Cmaj9", "D9", "Bm7", "Em9", "Am9", "D9", "Gmaj9", "D7sus"]
    form, chords = song(("intro", groove[:4]), ("a", groove), ("hook", hook_chords), ("break", hook_chords[:4]),
                        ("a2", groove[:4]), ("hook2", hook_chords))
    hook = bars(
        "B5:2 D6:2 .:1 E6:3 D6:4 .:4",
        "A5:2 .:2 A5:1 B5:1 A5:2 F#5:4 .:4",
        "B5:2 D6:2 .:1 E6:3 D6:2 F#6:2 .:4",
        "G6:3 F#6:1 E6:2 D6:2 B5:4 .:4",
        "C6:2 E6:2 .:1 G6:3 E6:2 C6:2 .:4",
        "A5:2 .:2 A5:1 B5:1 C6:2 D6:4 .:4",
        "B5:2 D6:2 .:1 E6:3 D6:2 B5:2 A5:2 G5:2",
        "G5:6 .:6 A5:2 B5:2",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 A5:2 B5:1 C6:1 D6:4",
                  ".:16", ".:16", ".:16", ".:8 F#6:2 E6:1 D6:1 A5:4")
    bar_count = len(chords)
    band = ("a", "hook", "a2", "hook2")
    drum = lambda c, r, at: kit(r, 1, at)
    backbeat = ["....X..g.g..X..g", "....X..g.g..Xg.g"]
    lines = ["r-.xr.5O.xr-x7s.", "r-.x.rO.x.5-7.xs"]
    quiet = "................"
    build = lambda rhythms, make: in_turn(form, ("intro",), rhythms, make)
    parts = [
        part(soft_kick, in_turn(form, band, ["X.....x...x.....", "X.....x...x..x.."], drum)
             + build([quiet, quiet, "X.......x.......", "X.....x...x....."], drum), 0.55),
        part(soft_snare, in_turn(form, ("a", "hook", "a2"), backbeat, drum)
             + in_turn(form, ("hook2",), backbeat * 3 + [backbeat[0], "....X..g.g.gX.gg"], drum)
             + build([quiet, quiet, ".......g.g.....g", "....X..g.g..oxox"], drum), 0.34, 0.05, 0.12),
        part(soft_hat, kit_parts(form, [(band, "xgogxgogxgogxgog")])
             + build([quiet, "x.o.x.o.x.o.x.o.", "xgogxgogxgogxgog", "xgogxgogxgogxgog"], drum), 0.2, 0.3),
        part(soft_open_hat, in_turn(form, band, ["................", "..............o."], drum), 0.14, 0.3),
        part(shaker, kit_parts(form, [(("hook", "hook2"), "ogxgogxgogxgogxg")]), 0.1, -0.35),
        part(finger_bass, in_turn(form, band, lines, lambda c, r, at: finger_line(c, r, 33, at))
             + build(["r-.x....5-.x7-s.", lines[1], lines[0], lines[1]], lambda c, r, at: finger_line(c, r, 33, at))
             + in_sections(form, ("break",), lambda at, c: finger_line(c, "r-.x..5-.x7-..s.", 33, at)), 0.62),
        part(e_piano, in_sections(form, ("intro", "a", "a2"), lambda at, c: keys_comp(c, "x-.o..x-.o.x-...", 55, at))
             + in_sections(form, ("hook", "hook2"), lambda at, c: keys_comp(c, "..x-..o.x-..o.x.", 55, at))
             + in_sections(form, ("break",), lambda at, c: keys_comp(c, "x--.o..x-..o.x--", 55, at)), 0.42, -0.1, 0.2),
        part(scratch_guitar, in_sections(form, band, lambda at, c: scratch(c, "-.-x-.x.-.-x-.x-", 62, at))
             + build([quiet, quiet, "-.-x-.x.-.-x-.x-", "-.-x-.x.-.-x-.x-"], lambda c, r, at: scratch(c, r, 62, at)), 0.22, 0.35, 0.08),
        part(vibes, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4])
             + bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]), 0.5, 0.15, 0.3, 0.15),
        part(e_piano, octave(bars_at(form, ("hook2",), hook), -1), 0.22, -0.2, 0.2),
    ]
    return render_funk(bpm, bar_count, parts, 0.6, 0.14, -15.0)


def funk_race_one():
    """The Baseplate Cup and the main theme: a laid back groove in D, the
    hook on horns with the e_piano carrying it in the intro."""
    bpm = 110
    groove = ["Dmaj9", "Bm9", "Em9", "A9"] * 2
    lift = ["G9", "F#m7", "Em9", "A7sus"] * 2
    hook_chords = ["Gmaj9", "A9", "F#m7", "Bm9", "Em9", "A9", "Dmaj9", "A7sus"]
    form, chords = song(("intro", hook_chords[4:]), ("a", groove), ("b", lift), ("hook", hook_chords),
                        ("break", hook_chords[:4]), ("a2", groove[:4]), ("hook2", hook_chords))
    hook = bars(
        "F#5:2 A5:2 .:1 B5:3 A5:2 F#5:2 .:4",
        "E5:2 .:2 E5:1 F#5:1 E5:2 C#5:4 .:4",
        "F#5:2 A5:2 .:1 B5:3 A5:2 C#6:2 .:4",
        "D6:3 C#6:1 B5:2 A5:2 F#5:4 .:4",
        "G5:2 B5:2 .:1 D6:3 B5:2 G5:2 .:4",
        "E5:2 .:2 E5:1 F#5:1 G5:2 A5:4 .:4",
        "F#5:2 A5:2 .:1 B5:3 A5:2 F#5:2 E5:2 D5:2",
        "D5:6 .:6 E5:2 F#5:2",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 E5:1 F#5:1 A5:2 B5:2 A5:2",
                  ".:16", ".:16", ".:16", ".:8 C#6:2 B5:1 A5:1 F#5:2 E5:2")
    riff = bars(
        "G4:1 .:1 B4:1 D5:2 .:1 F5:2 .:2 E5:1 D5:1 B4:2 .:2",
        "F#4:1 .:1 A4:1 C#5:2 .:1 E5:2 .:8",
        "E4:1 .:1 G4:1 B4:2 .:1 D5:2 .:2 F#5:2 E5:2 .:2",
        "D5:3 C#5:1 B4:2 A4:2 .:8",
        "G4:1 .:1 B4:1 D5:2 .:1 F5:2 .:2 E5:1 D5:1 B4:2 .:2",
        "F#4:1 .:1 A4:1 C#5:2 .:1 E5:2 .:8",
        "E4:1 .:1 G4:1 B4:2 .:1 D5:2 .:2 F#5:2 E5:2 .:2",
        "D5:2 E5:2 G5:2 A5:2 .:8",
    )
    bar_count = len(chords)
    band = ("a", "b", "hook", "a2", "hook2")
    hooks = bars_at(form, ("hook", "hook2"), hook)
    parts = [
        part(soft_kick, kit_parts(form, [(band, "x.....x..x......"), (("intro",), "x.......x.......")]), 0.52),
        part(rimshot, kit_parts(form, [(("intro", "a", "a2"), "....x.......x...")]), 0.3, 0.1, 0.1),
        part(soft_snare, kit_parts(form, [(("b", "hook", "hook2"), "....x..g.g..x..g"), (("a", "a2"), ".......g.g...g.g")]), 0.34, 0.05, 0.12),
        part(soft_hat, kit_parts(form, [(band + ("intro",), "xgogxgogxgogxgog")]), 0.16, 0.3),
        part(soft_open_hat, kit_parts(form, [(("hook", "hook2"), "..............o.")]), 0.14, 0.3),
        part(finger_bass, in_sections(form, band + ("intro",), lambda at, c: finger_line(c, "r--.x.rO.x5-7.s.", 33, at))
             + in_sections(form, ("break",), lambda at, c: finger_line(c, "r-----.x5---7-s.", 33, at)), 0.62),
        part(e_piano, in_sections(form, ("a", "a2", "intro"), lambda at, c: keys_comp(c, "x--.....x-.o....", 55, at))
             + in_sections(form, ("b",), lambda at, c: keys_comp(c, "..x-...x..x-..o.", 55, at))
             + in_sections(form, ("hook", "hook2", "break"), lambda at, c: keys_comp(c, "x-------..o.x---", 55, at)), 0.4, -0.15, 0.2),
        part(e_piano, bars_at(form, ("intro",), hook[4:]) + bars_at(form, ("break",), hook[:4])
             + octave(bars_at(form, ("hook2",), hook), 1), 0.36, 0.1, 0.25, 0.12),
        part(scratch_guitar, in_sections(form, ("a", "hook", "a2", "hook2"), lambda at, c: scratch(c, "-.-.x.--.-.-x.-.", 62, at)), 0.24, 0.35, 0.08),
        part(wah_guitar, bars_at(form, ("b",), riff) + bars_at(form, ("a", "a2"), answer), 0.3, -0.3, 0.12, 0.1),
        part(horn_section, hooks + last_bar(form, ("b",), "......x..X--....", lambda c, r, at: keys_comp(c, r, 62, at)), 0.5, 0.0, 0.2, 0.08),
    ]
    return render_funk(bpm, bar_count, parts, 0.6, 0.12, -14.0)


def funk_race_beach():
    """The Island Cup: a laid back calypso funk in F, steel drums on the hook
    over congas, a shaker and a lilting finger bass."""
    bpm = 104
    groove = ["Fmaj9", "Dm9", "Gm9", "C9"] * 2
    lift = ["Bbmaj9", "Am7", "Gm9", "C9"]
    hook_chords = ["Bbmaj9", "C9", "Fmaj9", "Dm9", "Gm9", "C9", "F69", "C9"]
    form, chords = song(("intro", hook_chords[4:]), ("a", groove), ("b", lift), ("hook", hook_chords),
                        ("break", hook_chords[:4]), ("a2", groove[:4]), ("hook2", hook_chords))
    hook = bars(
        "D6:2 D6:1 F6:3 D6:2 C6:2 .:6",
        "E6:2 E6:1 G6:3 E6:2 D6:2 C6:4 .:2",
        "A5:3 C6:3 F6:2 E6:4 .:4",
        "D6:3 C6:3 A5:2 .:8",
        "Bb5:2 Bb5:1 D6:3 Bb5:2 A5:2 .:6",
        "G5:2 G5:1 Bb5:3 C6:2 E6:2 G6:4 .:2",
        "A6:3 G6:3 F6:2 D6:3 C6:3 A5:2",
        "C6:8 .:4 A5:2 Bb5:2",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 G5:2 A5:1 Bb5:1 C6:2 .:2",
                  ".:16", ".:16", ".:16", ".:8 E6:2 D6:1 C6:1 Bb5:2 G5:2")
    bar_count = len(chords)
    band = ("a", "b", "hook", "a2", "hook2")
    tune = (bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("intro",), hook[4:])
            + bars_at(form, ("break",), hook[:4]))
    parts = [
        part(soft_kick, kit_parts(form, [(band, "x..x....x..x...."), (("intro",), "x.......x.......")]), 0.48),
        part(rimshot, kit_parts(form, [(band + ("intro",), "....x.......x...")]), 0.28, 0.1, 0.1),
        part(soft_snare, kit_parts(form, [(band, "...g...g.g.....g")]), 0.22, 0.05, 0.12),
        part(soft_hat, kit_parts(form, [(band, "x.o.x.o.x.o.x.o.")]), 0.12, 0.3),
        part(shaker, kit_parts(form, [(band + ("intro",), "xgogxgogxgogxgog")]), 0.14, -0.35),
        part(cowbell, kit_parts(form, [(("hook", "hook2"), "o...o...o...o...")]), 0.1, 0.4, 0.05),
        part(conga, pitched(kit_parts(form, [(band, "x......x..x.....")]), 180.0), 0.32, -0.3, 0.08),
        part(conga, pitched(kit_parts(form, [(band + ("intro",), "..o.ox.o....x.og")]), 260.0), 0.26, 0.3, 0.08),
        part(finger_bass, in_sections(form, band + ("intro",), lambda at, c: finger_line(c, "r--5..r.x.5-o.s.", 33, at))
             + in_sections(form, ("break",), lambda at, c: finger_line(c, "r-----.x5-----s.", 33, at)), 0.6),
        part(e_piano, in_sections(form, ("a", "a2", "b", "intro"), lambda at, c: keys_comp(c, "..x-..x-..x-..x-", 55, at))
             + in_sections(form, ("hook", "hook2", "break"), lambda at, c: keys_comp(c, "x-------..o.x---", 55, at)), 0.34, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, band, lambda at, c: scratch(c, "..x-..x-..x-.-x-", 62, at)), 0.2, 0.35, 0.08),
        part(pop_marimba, bars_at(form, ("a", "a2"), answer)
             + in_sections(form, ("b",), lambda at, c: arps(c, 4, (0, 2, 1, 3), 2, at)), 0.26, -0.35, 0.15),
        part(steel, tune, 0.62, 0.15, 0.25, 0.12),
        part(steel, octave(bars_at(form, ("hook2",), hook), -1), 0.22, -0.25, 0.25),
        part(horn_section, last_bar(form, ("hook2",), "..x..x....x-....", lambda c, r, at: keys_comp(c, r, 62, at)), 0.3, 0.0, 0.2),
    ]
    return render_funk(bpm, bar_count, parts, 0.57, 0.12, -14.1)


def funk_race_two():
    """The Axle Cup, works and foundries: a dorian vamp in E minor led by a
    clavinet riff, slap bass pops and anvil clanks as colour."""
    bpm = 106
    groove = ["Em9", "A9", "Em9", "A9", "Cmaj9", "Bm7", "Am9", "B7sus"]
    lift = ["Cmaj9", "Bm7", "Am9", "B7sus"]
    hook_chords = ["Cmaj9", "D9", "Bm7", "Em9", "Cmaj9", "D9", "Am9", "B7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "G5:2 .:1 E5:1 G5:2 B5:3 A5:1 G5:2 .:4",
        "F#5:2 .:1 D5:1 F#5:2 A5:2 .:8",
        "D6:2 .:1 B5:1 A5:2 F#5:3 E5:1 D5:2 .:4",
        "E5:6 .:6 B4:2 D5:2",
        "G5:2 .:1 E5:1 G5:2 B5:3 A5:1 G5:2 .:4",
        "F#5:2 .:1 D5:1 F#5:2 A5:2 C6:2 B5:2 A5:2 .:2",
        "G5:2 .:1 E5:1 C5:2 E5:3 G5:1 B5:2 .:4",
        "A5:4 F#5:4 .:8",
    )
    riff = bars(
        "E4:1 .:1 G4:1 E4:1 .:1 A4:1 .:1 B4:1 .:2 D5:1 B4:1 .:1 A4:1 G4:1 .:1",
        "A4:1 .:1 C#5:1 A4:1 .:1 E5:1 .:1 G5:1 .:2 F#5:1 E5:1 .:1 C#5:1 A4:1 .:1",
        "E4:1 .:1 G4:1 E4:1 .:1 A4:1 .:1 B4:1 .:2 D5:1 B4:1 .:1 A4:1 G4:1 .:1",
        "A4:1 .:1 C#5:1 A4:1 .:1 E5:1 .:1 G5:1 .:2 F#5:1 E5:1 .:1 C#5:1 A4:1 .:1",
        "E4:1 .:1 G4:1 E4:1 .:1 B4:1 .:1 D5:1 .:2 E5:1 D5:1 .:1 B4:1 G4:1 .:1",
        "D4:1 .:1 F#4:1 D4:1 .:1 A4:1 .:1 B4:1 .:2 D5:1 B4:1 .:1 A4:1 F#4:1 .:1",
        "C4:1 .:1 E4:1 C4:1 .:1 G4:1 .:1 B4:1 .:2 C5:1 B4:1 .:1 G4:1 E4:1 .:1",
        "B3:1 .:1 E4:1 F#4:1 .:1 A4:1 .:1 B4:1 .:2 A4:1 F#4:1 .:1 E4:1 D#4:1 .:1",
    )
    hooks = bars_at(form, ("hook", "hook2"), hook)
    parts = funk_kit(form, ["X.....x...x.....", "X.....x...x..x.."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.45, 0.29, 0.17)) + [
        part(anvil, in_turn(form, ("a", "hook", "a2", "hook2"), [QUIET, "..........o....."], kit_bar), 0.1, 0.4, 0.15),
        part(finger_bass, funk_bass(form, ["r-.xr.7O.x5-x7s.", "r-.x.r5.x.O-7.x."]), 0.6),
        part(slap_bass, in_sections(form, ("hook", "hook2"), lambda at, c: bassline(c, "......o.......o.", 2, at)), 0.22),
        part(clavinet, bars_at(form, ("a",), riff) + bars_at(form, ("intro", "a2"), riff[:4])
             + octave(hooks, -1) + in_sections(form, ("b",), lambda at, c: keys_comp(c, "x.x..x.x..x..x..", 60, at)), 0.42, -0.15, 0.1),
        part(e_piano, comping(form, ("intro", "a", "a2", "hook", "hook2"), "....x-......x-..")
             + comping(form, ("b", "break"), "x-------..o.x---"), 0.34, 0.2, 0.2),
        part(wah_guitar, in_sections(form, ("b", "hook2"), lambda at, c: keys_comp(c, "x.xx..x.x.xx..x.", 52, at)), 0.16, 0.35, 0.08),
        part(horn_section, bars_at(form, ("hook2",), hook) + last_bar(form, ("b",), "......x..X--....", lambda c, r, at: keys_comp(c, r, 62, at)), 0.42, 0.0, 0.2, 0.08),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.0)


def funk_race_three():
    """The Gearbox Cup, woods, snow and dunes: sunny in A major, a whistled
    hook over banjo answers and rolls on the funk band."""
    bpm = 112
    groove = ["Amaj9", "Dmaj9", "C#m7", "F#m9", "Bm9", "E9", "Amaj9", "E7sus"]
    lift = ["Dmaj9", "C#m7", "Bm9", "E7sus"] * 2
    hook_chords = ["Dmaj9", "E9", "C#m7", "F#m9", "Bm9", "E9", "A69", "E7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "A5:2 .:1 F#5:1 A5:2 C#6:2 .:2 B5:2 A5:4",
        "G#5:2 .:1 E5:1 G#5:2 B5:2 .:8",
        "E5:2 .:1 G#5:1 B5:2 E6:3 C#6:1 B5:2 .:4",
        "A5:6 .:6 F#5:2 G#5:2",
        "A5:2 .:1 F#5:1 A5:2 D6:2 .:2 C#6:2 B5:4",
        "G#5:2 .:1 E5:1 G#5:2 B5:2 D6:2 C#6:2 B5:2 .:2",
        "C#6:3 B5:1 A5:2 F#5:2 E5:4 .:4",
        "B4:4 .:8 E5:2 G#5:2",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 C#5:1 E5:1 F#5:1 A5:1 C#6:2 A5:2",
                  ".:16", ".:16", ".:16", ".:8 B4:1 D5:1 E5:1 F#5:1 A5:2 E5:2")
    parts = funk_kit(form, ["X.....x.x.......", "X.....x...x..x.."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.47, 0.3, 0.19)) + [
        part(shaker, kit_parts(form, [(("hook", "hook2", "b"), "ogxgogxgogxgogxg")]), 0.1, -0.35),
        part(finger_bass, funk_bass(form, ["r-.x5.o.r-.x5-s.", "r-.xo.5.x.r-7.s."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2", "b"), "x-.o..x-.o.x-...")
             + comping(form, ("hook", "hook2", "break"), "..x-..o.x-..o.x."), 0.36, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, BAND, lambda at, c: scratch(c, "-.-x-.x.-.-x-.x-", 62, at)), 0.2, 0.35, 0.08),
        part(banjo, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4])
             + in_sections(form, ("b", "hook2"), lambda at, c: arps(c, 4, (0, 2, 4, 1, 3, 2), 2, at)), 0.4, -0.3, 0.12),
        part(pop_whistle, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4]), 0.5, 0.1, 0.25, 0.15),
        part(horn_section, last_bar(form, ("b", "hook"), "......x..X--....", lambda c, r, at: keys_comp(c, r, 62, at)), 0.3, 0.0, 0.2),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.1)


def funk_race_four():
    """The Keystone Cup, launchpad, lava and castle: a dark C minor 9 vamp,
    still laid back, the hook on horns over a choir and timpani."""
    bpm = 101
    groove = ["Cm9", "Cm9", "Fm9", "Fm9", "Cm9", "Cm9", "Abmaj9", "G7sus"]
    lift = ["Abmaj9", "Gm7", "Fm9", "G7sus"]
    hook_chords = ["Abmaj9", "Bb9", "Gm7", "Cm9", "Abmaj9", "Bb9", "Fm9", "G7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "C5:3 Eb5:3 G5:2 .:2 F5:2 Eb5:4",
        "D5:3 F5:3 Ab5:2 .:8",
        "Bb5:3 G5:3 F5:2 .:2 Eb5:2 D5:4",
        "C5:8 .:4 G4:2 Bb4:2",
        "C5:3 Eb5:3 G5:2 .:2 Ab5:2 G5:4",
        "F5:3 Ab5:3 C6:2 .:2 Bb5:2 Ab5:4",
        "G5:3 F5:3 Eb5:2 .:2 C5:2 Ab4:4",
        "G4:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 C5:1 Eb5:1 F5:2 Ab5:2 G5:2",
                  ".:16", ".:16", ".:16", ".:8 F5:2 Eb5:1 D5:1 C5:2 Bb4:2")
    booms = [((start + b) * 16, note_freq(n), 16) for name, start, _c in form if name in ("hook", "hook2")
             for b, n in ((0, "Ab2"), (4, "Ab2"), (7, "G2"))]
    parts = funk_kit(form, ["X.....x...x.....", "X.......x.x....."], ["....X..g.g..X..g", "....X..g.g..X.gg"], loud=(0.47, 0.29, 0.16)) + [
        part(timpani, booms, 0.3, 0.0, 0.2),
        part(finger_bass, funk_bass(form, ["r-.x.r7.x.5-r.s.", "r-.xr.O.x7-.5.x."]), 0.62),
        part(e_piano, comping(form, ("intro", "a", "a2", "b"), "x--.....x-.o....")
             + comping(form, ("hook", "hook2", "break"), "x-------..o.x---"), 0.4, -0.15, 0.22),
        part(choir, comping(form, ("hook", "hook2", "break"), "x---------------"), 0.24, 0.0, 0.3),
        part(scratch_guitar, in_sections(form, ("a", "a2", "hook2"), lambda at, c: scratch(c, "-.-.x.--.-.-x.-.", 62, at)), 0.18, 0.35, 0.08),
        part(wah_guitar, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]), 0.3, -0.3, 0.12, 0.1),
        part(horn_section, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4])
             + last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 60, at)), 0.48, 0.0, 0.22, 0.08),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.14, -14.2)


def funk_race_legends():
    """The Legends Cup, famous circuits: a proud anthem in E flat, a singing
    guitar on the hook with horns, stadium claps on the backbeat."""
    bpm = 108
    groove = ["Ebmaj9", "Bb7sus", "Cm9", "Abmaj9", "Ebmaj9", "Bb7sus", "Ab69", "Bb9"]
    lift = ["Abmaj9", "Gm7", "Fm9", "Bb7sus"]
    hook_chords = ["Abmaj9", "Bb9", "Gm7", "Cm9", "Fm9", "Bb9", "Eb69", "Bb7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "Eb5:2 .:1 Eb5:1 Ab5:4 G5:2 F5:2 Eb5:4",
        "F5:2 .:1 F5:1 Bb5:4 .:8",
        "Bb5:2 .:1 Bb5:1 D6:4 C6:2 Bb5:2 G5:4",
        "G5:8 .:8",
        "Ab5:2 .:1 Ab5:1 C6:4 Bb5:2 Ab5:2 F5:4",
        "Bb5:2 .:1 Bb5:1 D6:4 F6:4 .:4",
        "Eb6:3 D6:3 Bb5:2 G5:3 F5:3 Eb5:2",
        "Eb5:8 .:4 Bb4:2 C5:2",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 Eb4:2 F4:2 G4:2 Ab4:2",
                  ".:16", ".:16", ".:16", ".:8 Bb4:2 C5:2 D5:2 F5:2")
    parts = funk_kit(form, ["X.....x...x.....", "X.....x.x.x....."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.47, 0.27, 0.18)) + [
        part(stadium_clap, kit_parts(form, [(("hook", "hook2"), "....x.......x...")]), 0.2, 0.0, 0.15),
        part(finger_bass, funk_bass(form, ["r-.xr.5.r-.x5-7.", "r-.x.r5.O-.x5.s."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x-.o..x-.o.x-...")
             + comping(form, ("b", "hook", "hook2", "break"), "x-------..o.x---"), 0.38, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, BAND, lambda at, c: scratch(c, "-.-.x.--.-.-x.-.", 62, at)), 0.2, 0.35, 0.08),
        part(anthem_guitar, octave(bars_at(form, ("hook", "hook2"), hook), -1) + bars_at(form, ("a", "a2"), answer)
             + bars_at(form, ("intro",), answer[:4]), 0.42, -0.2, 0.22, 0.12),
        part(horn_section, bars_at(form, ("hook2",), hook) + bars_at(form, ("break",), hook[:4])
             + comping(form, ("hook",), "......x.......x-", 62) + last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 62, at)),
             0.42, 0.15, 0.22, 0.08),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.1)


def funk_race_rally():
    """The Gravel Cup: rockier funk in B minor, driven guitar chugs and tom
    fills into each section, the hook on a wah guitar, still in the pocket."""
    bpm = 114
    groove = ["Bm9", "G9", "Bm9", "A9", "Bm9", "G9", "Em9", "F#7sus"]
    lift = ["Gmaj9", "A9", "F#m7", "Bm9"] * 2
    hook_chords = ["Gmaj9", "A9", "Bm9", "Bm9", "Gmaj9", "A9", "Em9", "F#7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "B4:2 .:1 B4:1 D5:2 F#5:2 .:2 E5:2 D5:4",
        "C#5:2 .:1 C#5:1 E5:2 A5:2 .:8",
        "B5:3 A5:3 F#5:2 .:2 E5:2 D5:4",
        "B4:6 .:6 F#4:2 A4:2",
        "B4:2 .:1 B4:1 D5:2 F#5:2 .:2 G5:2 F#5:4",
        "E5:2 .:1 E5:1 G5:2 B5:2 .:2 A5:2 G5:4",
        "F#5:3 E5:3 D5:2 B4:3 D5:3 E5:2",
        "F#5:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 E5:1 F#5:1 A5:2 B5:2 A5:2",
                  ".:16", ".:16", ".:16", ".:8 A5:2 F#5:1 E5:1 C#5:2 A4:2")
    parts = funk_kit(form, ["X.....x.x.x.....", "X.....x.x..x..x."], ["....X..g.g..X..g", "....X..g.g..X.gX"], loud=(0.41, 0.26, 0.15)) + [
        part(tom, fill_down(form, ("b", "hook", "a2")), 0.18, 0.0, 0.12),
        part(finger_bass, funk_bass(form, ["r-.xr.r.x.5-r.7.", "r-.xr.O.x.5-7.s."]), 0.6),
        part(chug, in_sections(form, ("b", "hook", "hook2"), lambda at, c: bassline(c, "r..r..r...r.r...", 2, at)), 0.2, 0.0, 0.05),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x-.o..x-.o.x-...")
             + comping(form, ("b", "hook", "hook2", "break"), "x-------..o.x---"), 0.34, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, ("intro", "a", "a2"), lambda at, c: scratch(c, "-.-x-.x.-.-x-.x-", 62, at)), 0.22, 0.35, 0.08),
        part(wah_guitar, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4])
             + bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]), 0.42, -0.1, 0.15, 0.1),
        part(horn_section, bars_at(form, ("hook2",), hook) + last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 60, at)), 0.36, 0.1, 0.2, 0.08),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -13.8)


def funk_race_indoor():
    """The Hangar Cup, a neon hall: electro funk in F minor, tight drums,
    plucked synth arps and a robot singing the hook."""
    bpm = 105
    groove = ["Fm9", "Dbmaj9", "Bbm9", "C7sus"] * 2
    lift = ["Dbmaj9", "Eb9", "Cm7", "Fm9"]
    hook_chords = ["Dbmaj9", "Eb9", "Cm7", "Fm9", "Bbm9", "Eb9", "Abmaj9", "C7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "F5:2 .:1 Ab5:1 .:2 C5:2 Db5:2 F5:2 .:4",
        "G5:2 .:1 Bb5:1 .:2 G5:2 F5:2 Eb5:2 .:4",
        "Eb5:2 .:1 G5:1 .:2 Bb5:2 G5:2 Eb5:2 .:4",
        "F5:6 .:6 C5:2 Eb5:2",
        "F5:2 .:1 Ab5:1 .:2 C5:2 Db5:2 F5:2 .:4",
        "G5:2 .:1 Bb5:1 .:2 Bb5:2 Ab5:2 G5:2 .:4",
        "Ab5:3 G5:3 Eb5:2 C5:3 Eb5:3 G5:2",
        "F5:8 .:8",
    )
    tight = "xoxoxoxoxoxoxoxo"
    parts = funk_kit(form, ["X...x.....x.x...", "X...x.....x...x."], ["....X.......X..g", "....X..g....X.g."], tight, loud=(0.4, 0.24, 0.13)) + [
        part(finger_bass, funk_bass(form, ["r.rx..o.r.x.5.7.", "r.rx..o.x.r.7-s."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2", "b"), "..x-..x-..x-..x-")
             + comping(form, ("hook", "hook2", "break"), "x-------..o.x---"), 0.32, -0.2, 0.2),
        part(pop_pluck, in_sections(form, ("intro", "a", "a2", "hook", "hook2"), lambda at, c: arps(c, 4, (0, 2, 1, 3, 4, 2, 1, 3), 1, at)), 0.12, 0.35, 0.12, 0.2),
        part(vocoder_lead, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4]), 0.36, 0.0, 0.2, 0.15),
        part(horn_section, last_bar(form, ("b", "hook2"), "......x..X--....", lambda c, r, at: keys_comp(c, r, 60, at)), 0.3, 0.0, 0.2),
    ]
    return render_funk(bpm, len(chords), parts, 0.58, 0.12, -13.9)


def funk_race_coaster():
    """The Corkscrew Cup: playful funk in C, a fairground organ on the
    offbeats and a steam calliope on the hook, with quick runs up and down."""
    bpm = 111
    groove = ["Cmaj9", "A9", "Dm9", "G9"] * 2
    lift = ["Fmaj9", "Em7", "Dm9", "G7sus"] * 2
    hook_chords = ["Fmaj9", "G9", "Em7", "A9", "Dm9", "G9", "C69", "G7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "A5:2 .:1 C6:1 A5:2 F5:2 .:2 G5:1 A5:1 C6:4",
        "B5:2 .:1 D6:1 B5:2 G5:2 .:8",
        "G5:1 A5:1 B5:1 D6:1 E6:4 D6:2 B5:2 .:4",
        "C#6:6 .:6 A5:2 B5:2",
        "C6:2 .:1 A5:1 C6:2 F6:2 .:2 E6:1 D6:1 C6:4",
        "B5:2 .:1 D6:1 B5:2 G5:2 .:2 F5:1 G5:1 A5:1 B5:1 .:2",
        "C6:1 D6:1 E6:1 G6:1 A6:2 G6:2 E6:2 D6:2 C6:4",
        "C6:8 .:8",
    )
    runs_up = bars(".:16", ".:16", ".:16", ".:8 G5:1 A5:1 B5:1 C6:1 D6:1 E6:1 F6:2",
                   ".:16", ".:16", ".:16", ".:8 F6:1 E6:1 D6:1 C6:1 B5:1 A5:1 G5:2")
    parts = funk_kit(form, ["X.....x...x.....", "X.....x...x..x.."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.46, 0.28, 0.17)) + [
        part(finger_bass, funk_bass(form, ["r-.xr.5.o.x.5-s.", "r-.x3.5.x.o-7.s."]), 0.6),
        part(fair_organ, comping(form, ("intro", "a", "a2", "hook", "hook2"), "..x...x...x...x.", 55)
             + comping(form, ("b", "break"), "x-------x-------", 55), 0.2, -0.2, 0.15),
        part(e_piano, comping(form, ("a", "a2", "b"), "x-.o..x-.o.x-..."), 0.26, 0.2, 0.2),
        part(scratch_guitar, in_sections(form, ("a", "a2", "hook", "hook2"), lambda at, c: scratch(c, "-.-x-.x.-.-x-.x-", 62, at)), 0.18, 0.35, 0.08),
        part(calliope, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4])
             + bars_at(form, ("a", "a2"), runs_up) + bars_at(form, ("intro",), runs_up[:4]), 0.4, 0.1, 0.22, 0.12),
        part(pop_marimba, in_sections(form, ("b",), lambda at, c: arps(c, 4, (0, 2, 1, 3), 2, at)), 0.22, -0.35, 0.15),
        part(horn_section, last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 60, at)), 0.3, 0.0, 0.2),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.3)


def funk_race_alpine():
    """The Alpine Cup: a sunny groove in B flat, an accordion on the offbeats
    and cowbells over the band, the hook yodelled with a leap up in each
    phrase."""
    bpm = 103
    groove = ["Bbmaj9", "Gm9", "Ebmaj9", "F9"] * 2
    lift = ["Ebmaj9", "Dm7", "Cm9", "F7sus"]
    hook_chords = ["Ebmaj9", "F9", "Dm7", "Gm9", "Cm9", "F9", "Bb69", "F7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "Bb4:2 .:1 G5:1 .:2 F5:2 Eb5:2 Bb4:2 .:4",
        "C5:2 .:1 A5:1 .:2 G5:2 F5:2 .:6",
        "A4:2 .:1 F5:1 .:2 E5:2 D5:2 A4:2 .:4",
        "Bb4:6 .:6 F4:2 A4:2",
        "G4:2 .:1 Eb5:1 .:2 D5:2 C5:2 G4:2 .:4",
        "A4:2 .:1 F5:1 .:2 A5:2 G5:2 F5:2 .:4",
        "D5:2 F5:2 Bb5:3 A5:1 G5:2 F5:2 D5:4",
        "Bb4:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 F5:1 G5:1 A5:2 C6:2 A5:2",
                  ".:16", ".:16", ".:16", ".:8 Eb5:2 D5:1 C5:1 A4:2 F4:2")
    parts = funk_kit(form, ["X.....x...x.....", "X.......x.x....."], ["....X..g.g..X..g", "....X..g.g..X.gg"], loud=(0.47, 0.3, 0.18)) + [
        part(cowbell, kit_parts(form, [(("hook", "hook2", "b"), "o...o...o...o...")]), 0.08, 0.4, 0.08),
        part(finger_bass, funk_bass(form, ["r-.x5.r.x.5-o.s.", "r-.xr.5.O-.x5.7."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x-.o..x-.o.x-...")
             + comping(form, ("b", "break"), "x-------..o.x---"), 0.34, -0.15, 0.2),
        part(pop_accordion, comping(form, ("hook", "hook2", "b"), "..x-..x-..x-..x-", 55)
             + bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]), 0.3, 0.25, 0.15),
        part(scratch_guitar, in_sections(form, ("a", "a2", "hook2"), lambda at, c: scratch(c, "-.-.x.--.-.-x.-.", 62, at)), 0.18, -0.35, 0.08),
        part(yodel, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4]), 0.42, 0.0, 0.25, 0.12),
        part(horn_section, last_bar(form, ("b", "hook"), "......x..X--....", lambda c, r, at: keys_comp(c, r, 60, at)), 0.28, 0.0, 0.2),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.2)


def funk_race_canyon():
    """The Canyon Cup: a train beat shuffle on brushes in G, a twangy guitar
    answering and somebody whistling the hook."""
    bpm = 113
    groove = ["G69", "C9", "G69", "D9", "Em9", "C9", "Am9", "D7sus"]
    lift = ["Cmaj9", "Bm7", "Am9", "D7sus"] * 2
    hook_chords = ["C9", "G69", "Am9", "Em9", "C9", "G69", "Am9", "D7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "E5:2 G5:2 .:1 C6:3 Bb5:2 G5:2 .:4",
        "B5:3 A5:1 G5:2 E5:2 D5:4 .:4",
        "E5:2 G5:2 .:1 C6:3 B5:2 A5:2 .:4",
        "G5:6 .:6 E5:2 F#5:2",
        "E5:2 G5:2 .:1 C6:3 Bb5:2 G5:2 .:4",
        "B5:3 A5:1 G5:2 B5:2 D6:4 .:4",
        "C6:3 B5:1 A5:2 G5:2 E5:2 G5:2 A5:4",
        "G5:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 D4:1 E4:1 F#4:2 A4:2 C5:2",
                  ".:16", ".:16", ".:16", ".:8 G4:2 F#4:1 E4:1 D4:2 B3:2")
    train = ["gogoXogogogoXogo", "gogoXogogogoXoXo"]
    parts = funk_kit(form, ["X.....x.x.......", "X.....x...x....."], train, "x.o.x.o.x.o.x.o.", loud=(0.45, 0.3, 0.12), snare=brush) + [
        part(finger_bass, funk_bass(form, ["r-.x5.r.x-5.o.s.", "r-.x3.5.r-.x5.7."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x-.o..x-.o.x-...")
             + comping(form, ("b", "hook", "hook2", "break"), "..x-..o.x-..o.x."), 0.32, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, ("hook", "hook2"), lambda at, c: scratch(c, "-.-x-.x.-.-x-.x-", 62, at)), 0.18, 0.35, 0.08),
        part(pop_twang, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4])
             + in_sections(form, ("b",), lambda at, c: arps(c, 3, (0, 2, 1, 3), 2, at)), 0.34, -0.3, 0.2, 0.15),
        part(pop_whistle, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4]), 0.5, 0.1, 0.25, 0.15),
        part(horn_section, last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 60, at)), 0.28, 0.0, 0.2),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.2)


def funk_race_jungle():
    """The Jungle Cup: a dorian groove in A minor on hand drums, the hook on
    marimba and a wooden flute answering."""
    bpm = 102
    groove = ["Am9", "D9", "Am9", "D9", "Fmaj9", "Em7", "Dm9", "E7sus"]
    lift = ["Fmaj9", "G9", "Em7", "Am9"]
    hook_chords = ["Fmaj9", "G9", "Em7", "Am9", "Dm9", "G9", "Cmaj9", "E7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "A5:2 .:1 C6:1 .:2 A5:1 G5:1 E5:2 .:2 C5:2 E5:2",
        "D5:2 .:1 F5:1 .:2 G5:2 B5:4 .:4",
        "G5:2 .:1 B5:1 .:2 G5:1 E5:1 D5:2 .:2 B4:2 D5:2",
        "E5:6 .:6 C5:2 D5:2",
        "F5:2 .:1 A5:1 .:2 F5:1 E5:1 D5:2 .:2 A4:2 C5:2",
        "D5:2 .:1 F5:1 .:2 A5:2 B5:4 .:4",
        "C6:2 B5:2 G5:2 E5:2 D5:2 E5:2 G5:4",
        "A5:4 .:12",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 F#5:2 A5:2 C6:4",
                  ".:16", ".:16", ".:16", ".:8 E5:2 D5:1 B4:1 A4:4")
    hands = ("intro",) + BAND
    parts = funk_kit(form, ["X.....x...x.....", "X.....x...x..x.."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.42, 0.26, 0.15)) + [
        part(shaker, kit_parts(form, [(BAND, "xgogxgogxgogxgog")]), 0.12, -0.35),
        part(conga, pitched(kit_parts(form, [(BAND, "x......x..x.....")]), 180.0), 0.28, -0.3, 0.08),
        part(conga, pitched(kit_parts(form, [(hands, "..o.ox.o....x.og")]), 260.0), 0.22, 0.3, 0.08),
        part(finger_bass, funk_bass(form, ["r-.x.r5.x.7-r.s.", "r-.xr.O.x.5-7.x."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2", "b"), "x-.o..x-.o.x-...")
             + comping(form, ("hook", "hook2", "break"), "x-------..o.x---"), 0.34, -0.15, 0.2),
        part(scratch_guitar, in_sections(form, ("a", "a2", "hook", "hook2"), lambda at, c: scratch(c, "-.-.x.--.-.-x.-.", 62, at)), 0.18, 0.35, 0.08),
        part(pop_marimba, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4])
             + in_sections(form, ("b",), lambda at, c: arps(c, 4, (0, 2, 1, 3), 2, at)), 0.55, 0.1, 0.18),
        part(wood_flute, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4])
             + bars_at(form, ("hook2",), hook), 0.3, -0.2, 0.25, 0.12),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.1)


def funk_race_city():
    """The City Cup at night: city funk in F sharp minor, wah guitar and
    e_piano under a horn hook."""
    bpm = 107
    groove = ["F#m9", "B9", "F#m9", "B9", "Dmaj9", "C#m7", "Bm9", "C#7sus"]
    lift = ["Dmaj9", "E9", "C#m7", "F#m9"]
    hook_chords = ["Dmaj9", "E9", "C#m7", "F#m9", "Bm9", "E9", "Amaj9", "C#7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "C#6:2 .:1 A5:1 .:2 F#5:2 A5:2 B5:2 C#6:4",
        "B5:2 .:1 G#5:1 .:2 E5:2 F#5:2 G#5:2 .:4",
        "E5:2 .:1 G#5:1 .:2 B5:2 C#6:2 E6:2 .:4",
        "C#6:6 .:6 A5:2 B5:2",
        "C#6:2 .:1 A5:1 .:2 F#5:2 A5:2 B5:2 D6:4",
        "D6:2 .:1 B5:1 .:2 G#5:2 B5:2 C#6:2 .:4",
        "C#6:3 B5:3 A5:2 E5:3 F#5:3 G#5:2",
        "F#5:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 D#5:1 F#5:1 A5:2 C#6:2 B5:2",
                  ".:16", ".:16", ".:16", ".:8 G#5:2 F#5:1 E5:1 C#5:2 B4:2")
    parts = funk_kit(form, ["X.....x...x.....", "X.....x.x..x...."], ["....X..g.g..X..g", "....X..g.g..Xg.g"], loud=(0.45, 0.29, 0.17)) + [
        part(finger_bass, funk_bass(form, ["r-.x.rO.x5-.7.s.", "r-.xr.5.x.O-7.x."]), 0.6),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x-.o..x-.o.x-...")
             + comping(form, ("b", "hook", "hook2", "break"), "x-------..o.x---"), 0.38, -0.15, 0.2),
        part(wah_guitar, in_sections(form, ("a", "a2", "hook", "hook2"), lambda at, c: keys_comp(c, "x.xx..x.x.xx..x.", 52, at)), 0.15, 0.35, 0.08),
        part(e_piano, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]) + bars_at(form, ("break",), hook[:4]), 0.32, 0.1, 0.25, 0.12),
        part(horn_section, bars_at(form, ("hook", "hook2"), hook) + last_bar(form, ("b",), "x..x..x...X-----", lambda c, r, at: keys_comp(c, r, 62, at)), 0.46, 0.0, 0.22, 0.08),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.12, -14.1)


def funk_race_sky():
    """The Sky Cup: airy and floating in D flat, the lightest beat, an open
    pad, an airy flute on the hook and chimes answering."""
    bpm = 100
    groove = ["Dbmaj9", "Gbmaj9", "Dbmaj9", "Gbmaj9", "Bbm9", "Gbmaj9", "Ebm9", "Ab7sus"]
    lift = ["Gbmaj9", "Fm7", "Ebm9", "Ab7sus"]
    hook_chords = ["Gbmaj9", "Ab9", "Fm7", "Bbm9", "Ebm9", "Ab9", "Db69", "Ab7sus"]
    form, chords = funk_form(groove, lift, hook_chords)
    hook = bars(
        "Bb5:4 Ab5:2 F5:2 Db6:6 .:2",
        "C6:4 Bb5:2 Ab5:2 Eb5:6 .:2",
        "Ab5:4 F5:2 Eb5:2 C6:6 .:2",
        "Db6:8 .:4 Ab5:2 Bb5:2",
        "Bb5:4 Gb5:2 F5:2 Db6:6 .:2",
        "C6:4 Eb6:2 Db6:2 Bb5:6 .:2",
        "Ab5:4 F5:2 Eb5:2 Db5:6 .:2",
        "Db5:8 .:8",
    )
    answer = bars(".:16", ".:16", ".:16", ".:8 Bb5:2 Db6:2 F6:4",
                  ".:16", ".:16", ".:16", ".:8 Eb6:2 Db6:2 Ab5:4")
    parts = funk_kit(form, ["x.......x.x.....", "x.......x......."], ["....x.......x...", "....x.......x..g"], "x.o.x.o.x.o.x.o.",
                     loud=(0.54, 0.4, 0.18), snare=rimshot, fill="....x.......oxox") + [
        part(shaker, kit_parts(form, [(("hook", "hook2"), "ogxgogxgogxgogxg")]), 0.08, -0.35),
        part(finger_bass, funk_bass(form, ["r--.x.5-.x7-..s.", "r--.x.o-.x5-..s."], "r-------5-------"), 0.58),
        part(e_piano, comping(form, ("intro", "a", "a2"), "x--.....o-.x----"), 0.36, -0.15, 0.25),
        part(open_pad, comping(form, ("b", "hook", "hook2", "break"), "x---------------", 52), 0.3, 0.0, 0.3),
        part(chime, bars_at(form, ("a", "a2"), answer) + bars_at(form, ("intro",), answer[:4]), 0.3, 0.25, 0.3, 0.2),
        part(air_flute, bars_at(form, ("hook", "hook2"), hook) + bars_at(form, ("break",), hook[:4]), 0.5, -0.1, 0.3, 0.15),
        part(vibes, in_sections(form, ("b", "hook2"), lambda at, c: arps(c, 4, (0, 2, 1, 3), 4, at)), 0.18, 0.3, 0.3),
    ]
    return render_funk(bpm, len(chords), parts, 0.6, 0.16, -14.6)


TUNES = {
    "menu": funk_menu, "race_one": funk_race_one, "race_two": funk_race_two, "race_three": funk_race_three,
    "race_four": funk_race_four, "race_legends": funk_race_legends, "race_rally": funk_race_rally,
    "race_indoor": funk_race_indoor, "race_coaster": funk_race_coaster, "race_beach": funk_race_beach,
    "race_alpine": funk_race_alpine, "race_canyon": funk_race_canyon, "race_jungle": funk_race_jungle,
    "race_city": funk_race_city, "race_sky": funk_race_sky,
}
