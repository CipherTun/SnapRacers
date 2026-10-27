"""SnapRacers' music, written out note by note and played by a little
tracker built on synth.py.

Each tune is bars of sixteen steps. The melody is written by hand as (note,
steps) pairs, and the chords under it are named once for each bar, which the
bass, the arpeggios and the pads are all worked out from. Drums come from
patterns of steps.

Every tune loops. Anything still ringing past the end (the reverb, a long
note) is folded back onto the start, so it goes around without a gap.

The arcade pop tunes further down are written in sections (intro, verse,
pre chorus, chorus, breakdown) and mixed on a bus with a pumping sidechain,
glue compression and a limiter, by render_pop.
"""

import numpy as np

from synth import (
    RATE, adsr, bandpass, blep_saw, blep_square, circular_filter, compress, decay, drive, drive_clean, echo,
    highpass, limit, lowpass, noise, normalise, note_freq, partials, phase_of, plucked, reverb, rng, sine,
    saw, square, supersaw, sweep_lowpass, ramp, seconds, times, triangle, vowel, wah, widen,
)

# Chords by name, as the notes in them from the root up, in semitones.
SHAPES = {
    "": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10], "sus": [0, 5, 7], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9],
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


def clap(_f, _d, v):
    n = seconds(0.25)
    burst = bandpass(noise(n, 3), 900, 5000)
    env = np.zeros(n)
    for at in (0.0, 0.012, 0.024):
        s = seconds(at)
        env[s:] += decay(n - s, 0.012 if at < 0.02 else 0.15)
    return burst * env * 0.5 * v


def hat(_f, d, v):
    n = seconds(max(d, 0.05))
    return highpass(noise(n, 4), 7000) * decay(n, 0.03 if d < 0.1 else 0.18) * 0.5 * v


def bass(f, d, v):
    n = seconds(d)
    tone = saw(f, n, harmonics=30) * 0.7 + square(f / 2.0, n, harmonics=10) * 0.4
    tone = sweep_lowpass(tone, 300 + 1500 * decay(n, 0.15))
    return drive(tone * adsr(n, 0.004, 0.08, 0.7, 0.03), 1.3) * v


def lead(f, d, v):
    n = seconds(d)
    t = times(n)
    wobble = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) * 4.0, 0.0, 1.0)
    tone = square(f * wobble, n, 0.25, harmonics=24) * 0.6 + saw(f * 1.004, n, harmonics=24) * 0.3
    tone = sweep_lowpass(tone, 1200 + 3000 * decay(n, 0.25))
    return tone * adsr(n, 0.008, 0.1, 0.75, 0.04) * v


def bell(f, d, v):
    """A toy xylophone."""
    n = seconds(max(d, 0.6))
    tone = triangle(f, n) + sine(f * 4.0, n) * 0.25 * decay(n, 0.08) + sine(f * 2.0, n) * 0.2
    return tone * decay(n, 0.7) * adsr(n, 0.002, 0.0, 1.0, 0.02) * 0.8 * v


def steel(f, d, v):
    """A steel drum: a bright ringing note with the pan's out of tune
    overtones, hit hard and dying away."""
    n = seconds(max(d, 0.5))
    tone = sine(f, n) + sine(f * 2.0, n) * 0.5 * decay(n, 0.25) + sine(f * 2.98, n) * 0.22 * decay(n, 0.12)
    ping = sine(f * 4.1, n) * decay(n, 0.02) * 0.3
    return (tone + ping) * decay(n, 0.45) * adsr(n, 0.001, 0.0, 1.0, 0.03) * 0.7 * v


def pluck(f, d, v):
    n = seconds(max(d, 0.12))
    tone = square(f, n, 0.5, harmonics=14)
    return lowpass(tone, 3500) * decay(n, 0.12) * 0.5 * v


def pad(f, d, v):
    n = seconds(d + 0.3)
    tone = saw(f, n, harmonics=16) + saw(f * 1.006, n, harmonics=16) + saw(f * 0.995, n, harmonics=16)
    return lowpass(tone, 1600) * adsr(n, 0.08, 0.2, 0.7, 0.3) * 0.18 * v


def accordion(f, d, v):
    """An accordion: two reeds a little out of tune with each other, and the
    bellows swelling a little."""
    n = seconds(d + 0.05)
    t = times(n)
    tone = square(f, n, 0.4, harmonics=18) * 0.5 + saw(f * 1.005, n, harmonics=18) * 0.35 + square(f * 0.997, n, 0.3, harmonics=12) * 0.25
    tone = lowpass(tone, 2800)
    return tone * (0.9 + 0.1 * np.sin(2 * np.pi * 6.0 * t)) * adsr(n, 0.02, 0.1, 0.8, 0.05) * 0.55 * v


def twang(f, d, v):
    """A twangy electric guitar played low: it slides up into the note, rings
    bright and dark again, with a slow tremolo as it holds."""
    n = seconds(d + 0.25)
    t = times(n)
    bend = 1.0 - 0.03 * decay(n, 0.05)
    trem = 1.0 + 0.01 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.12) * 4.0, 0.0, 1.0)
    tone = saw(f * bend * trem, n, harmonics=30) * 0.6 + square(f * bend * trem, n, 0.3, harmonics=20) * 0.35
    tone = sweep_lowpass(tone, 900 + 3500 * decay(n, 0.1))
    return drive(tone * adsr(n, 0.002, 0.25, 0.55, 0.12), 1.4) * 0.6 * v


def strum(f, d, v):
    """A strummed acoustic string, bright at the start and dying away."""
    n = seconds(max(d, 0.25) + 0.1)
    tone = saw(f, n, harmonics=24) * 0.5 + triangle(f * 2.0, n) * 0.3
    return sweep_lowpass(tone, 600 + 4000 * decay(n, 0.05)) * decay(n, 0.35) * 0.5 * v


def whistle(f, d, v):
    """Somebody whistling: a pure note with a wavering vibrato."""
    n = seconds(d + 0.05)
    t = times(n)
    wobble = 1.0 + 0.008 * np.sin(2 * np.pi * 6.0 * t) * np.clip(t * 5.0, 0.0, 1.0)
    breath = bandpass(noise(n, 5), f * 0.9, f * 1.1) * 0.06
    return (sine(f * wobble, n) + breath) * adsr(n, 0.04, 0.05, 0.85, 0.06) * 0.6 * v


def marimba(f, d, v):
    """A marimba: a soft wooden bar hit with a mallet, its fourth harmonic
    ringing for a moment over a round note that dies away."""
    n = seconds(max(d, 0.5))
    tone = sine(f, n) * decay(n, 0.35) + sine(f * 4.0, n) * 0.3 * decay(n, 0.06) + sine(f * 9.8, n) * 0.08 * decay(n, 0.015)
    mallet = bandpass(noise(n, 6), 400, 3000) * decay(n, 0.004) * 0.2
    return (tone + mallet) * adsr(n, 0.002, 0.0, 1.0, 0.03) * 0.8 * v


def hand_drum(f, d, v):
    """A hand drum: a thump that drops a little in pitch, and the slap of the
    hand on the skin."""
    n = seconds(0.35)
    body = sine(np.geomspace(f * 1.4, f, n), n) * decay(n, 0.16)
    slap = bandpass(noise(n, 7), 800, 4000) * decay(n, 0.01) * 0.4
    return drive(body + slap, 1.2) * v


def flute(f, d, v):
    """A wooden flute: a breathy note with a chiff at the start and a gentle
    vibrato as it holds."""
    n = seconds(d + 0.08)
    t = times(n)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.1) * 4.0, 0.0, 1.0)
    tone = sine(f * vib, n) + sine(f * 2.0 * vib, n) * 0.18 + sine(f * 3.0 * vib, n) * 0.05
    breath = bandpass(noise(n, 8), f * 0.8, f * 2.5) * 0.12
    chiff = bandpass(noise(n, 9), 2000, 6000) * decay(n, 0.02) * 0.15
    return (tone + breath + chiff) * adsr(n, 0.03, 0.05, 0.8, 0.08) * 0.55 * v


def keys(f, d, v):
    """An electric piano: a soft sine with a bit of bark and tremolo."""
    n = seconds(d + 0.2)
    t = times(n)
    tone = sine(f, n) + sine(f * 2.0, n) * 0.3 * decay(n, 0.3) + triangle(f * 3.0, n) * 0.05 * decay(n, 0.1)
    return tone * (0.85 + 0.15 * np.sin(2 * np.pi * 4.5 * t)) * adsr(n, 0.005, 0.4, 0.5, 0.2) * 0.35 * v


def night_lead(f, d, v):
    """A soft synth lead for driving at night: two saws a little apart, a
    slow vibrato and a filter that opens as the note starts."""
    n = seconds(d + 0.1)
    t = times(n)
    wobble = 1.0 + 0.004 * np.sin(2 * np.pi * 4.8 * t) * np.clip((t - 0.2) * 3.0, 0.0, 1.0)
    tone = saw(f * wobble, n, harmonics=28) * 0.5 + saw(f * 1.008 * wobble, n, harmonics=28) * 0.4 + square(f / 2.0, n, 0.5, harmonics=10) * 0.15
    tone = sweep_lowpass(tone, 900 + 2600 * (1.0 - decay(n, 0.12)) * decay(n, 0.9))
    return tone * adsr(n, 0.03, 0.2, 0.7, 0.1) * 0.6 * v


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


# Playing a tune.

def render(bpm, bars, parts, wet=0.18):
    """Plays the parts over `bars` bars and folds the tail back onto the
    start so it loops. Each part is (instrument, notes, loudness, pan, reverb
    send), and each note is (step, Hz, steps) or (step, Hz, steps, how hard)."""
    step = 60.0 / bpm / 4.0
    total = seconds(bars * 16 * step)
    spill = seconds(3.0)
    left = np.zeros(total + spill)
    right = np.zeros(total + spill)
    send_l = np.zeros(total + spill)
    send_r = np.zeros(total + spill)
    for instrument, notes, loud, pan, send in parts:
        track = np.zeros(total + spill)
        for note in notes:
            at, f, length = note[0], note[1], note[2]
            v = note[3] if len(note) > 3 else 1.0
            sound = instrument(f, length * step, v)
            s = seconds(at * step)
            end = min(s + len(sound), len(track))
            track[s:end] += sound[: end - s]
        gl = np.cos((pan + 1.0) * np.pi / 4.0) * loud
        gr = np.sin((pan + 1.0) * np.pi / 4.0) * loud
        left += track * gl
        right += track * gr
        send_l += track * gl * send
        send_r += track * gr * send
    left += reverb(send_l, 1.0, 1.0) * wet * 3.0
    right += reverb(send_r, 1.0, 0.93) * wet * 3.0
    # Fold what rings on past the end back onto the start.
    for ch in (left, right):
        ch[:spill] += ch[total:total + spill]
    out = np.stack([left[:total], right[:total]])
    out = np.tanh(out / np.max(np.abs(out)) * 1.6) / np.tanh(1.6)
    return out * 0.85


# The tunes.

def menu_tune():
    """The garage and the menus: laid back, in F, on a toy xylophone."""
    bpm = 100
    chords = ["Fmaj7", "Am7", "Bbmaj7", "C7", "Fmaj7", "Dm7", "Gm7", "C7"] * 2
    tune = melody(16,
        [("A5", 3), ("C6", 3), ("E6", 2), ("D6", 4), ("C6", 4)],
        [("E6", 6), ("C6", 2), ("G5", 4), ("A5", 4)],
        [("D6", 3), ("F6", 3), ("D6", 2), ("C6", 4), ("Bb5", 4)],
        [("C6", 8), (".", 4), ("G5", 2), ("A5", 2)],
        [("A5", 3), ("C6", 3), ("F6", 2), ("E6", 4), ("C6", 4)],
        [("D6", 6), ("F6", 2), ("E6", 4), ("D6", 4)],
        [("Bb5", 4), ("D6", 4), ("F6", 4), ("E6", 2), ("D6", 2)],
        [("E6", 8), (".", 8)],
        [("A5", 3), ("C6", 3), ("E6", 2), ("D6", 4), ("C6", 4)],
        [("E6", 6), ("C6", 2), ("G5", 4), ("A5", 4)],
        [("D6", 3), ("F6", 3), ("D6", 2), ("C6", 4), ("Bb5", 4)],
        [("C6", 8), (".", 4), ("G5", 2), ("A5", 2)],
        [("A5", 3), ("C6", 3), ("A5", 2), ("G5", 4), ("F5", 4)],
        [("F5", 4), ("A5", 4), ("D6", 4), ("C6", 4)],
        [("Bb5", 4), ("A5", 4), ("G5", 4), ("E5", 4)],
        [("F5", 12), (".", 4)],
    )
    parts = [
        (kick, drums("x.....x...x.....", 16), 0.55, 0.0, 0.0),
        (snare, drums("....x.......x...", 16), 0.35, 0.05, 0.15),
        (hat, drums("..o...o...o...oo", 16), 0.3, 0.3, 0.05),
        (bass, bassline(chords, "r--.r.o.r--.5.o.", 2), 0.5, 0.0, 0.0),
        (keys, comp(chords, "..x...x...x..x..", 4), 0.45, -0.3, 0.25),
        (bell, tune, 0.5, 0.2, 0.35),
    ]
    return render(bpm, 16, parts, wet=0.2)


def race_one():
    """The Baseplate Cup: bright and pushing along, in A minor."""
    bpm = 140
    verse = ["Am", "F", "C", "G", "Am", "F", "C", "G"]
    chorus = ["F", "G", "Em", "Am", "Dm", "G", "C", "E"]
    breakdown = ["Am", "F", "C", "G"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("E5", 2), ("A5", 2), ("B5", 2), ("C6", 4), ("B5", 2), ("A5", 2), ("G5", 2)],
        [("A5", 6), ("F5", 2), ("G5", 2), ("A5", 2), ("C6", 4)],
        [("G5", 2), ("E5", 2), ("G5", 2), ("C6", 4), ("D6", 2), ("E6", 4)],
        [("D6", 6), ("B5", 2), ("G5", 4), (".", 4)],
        [("E5", 2), ("A5", 2), ("B5", 2), ("C6", 4), ("B5", 2), ("A5", 2), ("B5", 2)],
        [("C6", 4), ("A5", 4), ("F6", 4), ("E6", 2), ("D6", 2)],
        [("E6", 4), ("D6", 2), ("C6", 2), ("G5", 4), ("C6", 4)],
        [("B5", 8), ("D6", 4), ("B5", 4)],
    ]
    b = [
        [("A5", 3), ("A5", 1), ("C6", 2), ("A5", 2), ("G5", 4), ("F5", 4)],
        [("G5", 3), ("G5", 1), ("B5", 2), ("D6", 2), ("D6", 4), ("C6", 2), ("B5", 2)],
        [("B5", 4), ("G5", 2), ("E5", 2), ("G5", 4), ("B5", 4)],
        [("C6", 8), ("A5", 4), ("E6", 4)],
        [("F6", 4), ("E6", 2), ("D6", 2), ("A5", 4), ("D6", 4)],
        [("D6", 4), ("C6", 2), ("B5", 2), ("G5", 4), ("B5", 4)],
        [("C6", 4), ("E6", 4), ("G6", 4), ("E6", 4)],
        [("G#5", 4), ("B5", 4), ("E6", 6), ("D6", 2)],
    ]
    rest = [[(".", 16)]] * 4
    tune = melody(16, *(a + b + a + rest))
    bars = len(chords)
    parts = [
        (kick, drums("x...x...x...x...", bars), 0.6, 0.0, 0.0),
        (snare, drums("....x.......x..o", bars), 0.4, 0.05, 0.12),
        (clap, drums("....x.......x...", bars), 0.3, -0.05, 0.2),
        (hat, drums("o.x.o.x.o.x.o.xo", bars), 0.28, 0.35, 0.03),
        (bass, bassline(chords, "r-r-o-r-r-r-o-5-", 2), 0.5, 0.0, 0.0),
        (pluck, arps(chords, 4, (0, 1, 2, 3, 2, 1, 0, 2)), 0.3, -0.35, 0.3),
        (pad, held(chords, 3), 0.4, 0.0, 0.3),
        (lead, tune, 0.42, 0.1, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.16)


def race_two():
    """The Axle Cup, around the works and the foundry: chunky and funky, in E
    minor."""
    bpm = 132
    verse = ["Em", "Em", "C", "D", "Em", "Em", "C", "D"]
    chorus = ["G", "D", "Am", "C", "G", "D", "C", "B7"]
    breakdown = ["Em", "C", "D", "B7"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("E5", 2), (".", 2), ("E5", 2), ("G5", 2), ("A5", 2), ("G5", 2), ("E5", 2), ("D5", 2)],
        [("E5", 6), (".", 2), ("B4", 2), ("D5", 2), ("E5", 4)],
        [("G5", 2), (".", 2), ("G5", 2), ("A5", 2), ("B5", 2), ("A5", 2), ("G5", 2), ("E5", 2)],
        [("F#5", 6), ("D5", 2), ("A5", 4), ("F#5", 4)],
        [("E5", 2), (".", 2), ("E5", 2), ("G5", 2), ("A5", 2), ("G5", 2), ("E5", 2), ("D5", 2)],
        [("E5", 4), ("G5", 4), ("B5", 4), ("A5", 4)],
        [("G5", 2), ("E5", 2), ("G5", 2), ("C6", 4), ("B5", 2), ("A5", 2), ("G5", 2)],
        [("A5", 8), ("F#5", 4), ("D5", 4)],
    ]
    b = [
        [("B5", 4), ("D6", 4), ("B5", 2), ("A5", 2), ("G5", 4)],
        [("A5", 6), ("F#5", 2), ("A5", 4), ("D6", 4)],
        [("C6", 4), ("B5", 2), ("A5", 2), ("E5", 4), ("A5", 4)],
        [("G5", 6), ("E5", 2), ("G5", 4), ("C6", 4)],
        [("B5", 4), ("D6", 4), ("G6", 4), ("F#6", 2), ("E6", 2)],
        [("F#6", 6), ("E6", 2), ("D6", 4), ("A5", 4)],
        [("E6", 4), ("D6", 2), ("C6", 2), ("G5", 4), ("E6", 4)],
        [("D#6", 8), ("B5", 4), ("F#5", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x.....x...x.....", bars), 0.6, 0.0, 0.0),
        (snare, drums("....x.......x.o.", bars), 0.45, 0.05, 0.12),
        (hat, drums("x.x.x.x.x.x.x.xo", bars), 0.25, 0.35, 0.03),
        (bass, bassline(chords, "r-.r..r.o-.r.5o.", 2), 0.55, 0.0, 0.0),
        (keys, comp(chords, "..x..x....x..x..", 4), 0.4, -0.35, 0.2),
        (pad, held(chords, 3), 0.3, 0.2, 0.3),
        (lead, tune, 0.42, 0.1, 0.28),
    ]
    return render(bpm, bars, parts, wet=0.15)


def race_three():
    """The Gearbox Cup, through the woods, the snow and the dunes: bouncy and
    sunny, in D."""
    bpm = 124
    verse = ["D", "G", "Bm", "A", "D", "G", "A", "D"]
    chorus = ["G", "A", "F#m", "Bm", "G", "A", "Em", "A7"]
    breakdown = ["D", "G", "A", "D"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("F#5", 2), ("A5", 2), ("D6", 2), ("A5", 2), ("F#5", 2), ("A5", 2), ("B5", 4)],
        [("B5", 4), ("G5", 2), ("B5", 2), ("D6", 4), ("B5", 4)],
        [("D6", 2), ("C#6", 2), ("B5", 2), ("F#5", 2), ("B5", 4), ("D6", 4)],
        [("C#6", 6), ("A5", 2), ("E5", 4), ("A5", 4)],
        [("F#5", 2), ("A5", 2), ("D6", 2), ("F#6", 2), ("E6", 4), ("D6", 4)],
        [("B5", 2), ("D6", 2), ("G6", 4), ("F#6", 2), ("E6", 2), ("D6", 4)],
        [("C#6", 4), ("E6", 4), ("A5", 4), ("C#6", 4)],
        [("D6", 12), (".", 4)],
    ]
    b = [
        [("G5", 3), ("A5", 1), ("B5", 4), ("D6", 4), ("B5", 4)],
        [("A5", 3), ("B5", 1), ("C#6", 4), ("E6", 4), ("C#6", 4)],
        [("F#6", 4), ("E6", 2), ("C#6", 2), ("A5", 4), ("C#6", 4)],
        [("D6", 6), ("C#6", 2), ("B5", 8)],
        [("G5", 2), ("B5", 2), ("D6", 2), ("G6", 2), ("F#6", 4), ("E6", 4)],
        [("E6", 2), ("C#6", 2), ("E6", 2), ("A6", 2), ("G6", 4), ("E6", 4)],
        [("G6", 4), ("F#6", 2), ("E6", 2), ("B5", 4), ("E6", 4)],
        [("C#6", 4), ("E6", 4), ("G6", 4), ("E6", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x.......x.......", bars), 0.55, 0.0, 0.0),
        (snare, drums("....x.......x...", bars), 0.35, 0.05, 0.15),
        (hat, drums("..x...x...x...x.", bars), 0.28, 0.35, 0.05),
        (bass, bassline(chords, "r...5...r...5.o.", 2), 0.5, 0.0, 0.0),
        (pluck, arps(chords, 4, (0, 2, 1, 2), every=2), 0.35, -0.35, 0.3),
        (bell, tune, 0.45, 0.2, 0.3),
        (lead, [(at, f / 2.0, n) for at, f, n in tune], 0.16, -0.1, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.2)


def race_four():
    """The Keystone Cup: the launchpad, the lava and the castle, so it's big
    and dramatic, in C minor."""
    bpm = 150
    verse = ["Cm", "Ab", "Eb", "Bb", "Cm", "Ab", "Eb", "Bb"]
    chorus = ["Fm", "Cm", "Ab", "G", "Fm", "Cm", "Db", "G"]
    breakdown = ["Cm", "Ab", "Bb", "G"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("C5", 2), ("Eb5", 2), ("G5", 2), ("C6", 4), ("Bb5", 2), ("G5", 2), ("Eb5", 2)],
        [("Ab5", 6), ("G5", 2), ("F5", 2), ("Eb5", 2), ("C5", 4)],
        [("Eb5", 2), ("G5", 2), ("Bb5", 2), ("Eb6", 4), ("D6", 2), ("C6", 2), ("Bb5", 2)],
        [("D6", 8), ("Bb5", 4), ("F5", 4)],
        [("C6", 2), ("Bb5", 2), ("G5", 2), ("C6", 4), ("D6", 2), ("Eb6", 4)],
        [("C6", 6), ("Ab5", 2), ("Eb5", 4), ("Ab5", 4)],
        [("G5", 2), ("Bb5", 2), ("Eb6", 2), ("G6", 4), ("F6", 2), ("Eb6", 2), ("D6", 2)],
        [("D6", 4), ("F6", 4), ("Bb5", 8)],
    ]
    b = [
        [("F5", 4), ("Ab5", 4), ("C6", 4), ("F6", 4)],
        [("Eb6", 6), ("D6", 2), ("C6", 4), ("G5", 4)],
        [("Ab5", 4), ("C6", 4), ("Eb6", 4), ("Ab6", 4)],
        [("G6", 8), ("F6", 4), ("D6", 4)],
        [("F6", 4), ("Eb6", 2), ("C6", 2), ("Ab5", 4), ("C6", 4)],
        [("G6", 6), ("F6", 2), ("Eb6", 4), ("C6", 4)],
        [("F6", 4), ("Db6", 4), ("Ab5", 4), ("F6", 4)],
        [("B5", 4), ("D6", 4), ("G6", 6), ("F6", 2)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x...x...x...x.x.", bars), 0.62, 0.0, 0.0),
        (snare, drums("....x.......x...", bars), 0.45, 0.05, 0.15),
        (clap, drums("....x.......x...", bars), 0.3, -0.05, 0.2),
        (hat, drums("xxxxxxxxxxxxxxxx", bars), 0.18, 0.35, 0.03),
        (bass, bassline(chords, "rrrrrrrrrrrrrr5o", 2), 0.45, 0.0, 0.0),
        (pad, held(chords, 3), 0.45, 0.0, 0.35),
        (pluck, arps(chords, 5, (0, 1, 2, 1)), 0.2, -0.4, 0.3),
        (lead, tune, 0.45, 0.1, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.18)


def race_indoor():
    """The indoor cup, under the lights in the kart hall: tight and electronic,
    in F sharp minor."""
    bpm = 146
    verse = ["F#m", "D", "A", "E", "F#m", "D", "A", "E"]
    chorus = ["Bm", "D", "A", "E", "Bm", "D", "C#m", "C#7"]
    breakdown = ["F#m", "D", "A", "E"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("F#5", 2), (".", 2), ("C#6", 2), ("A5", 2), ("F#5", 2), ("A5", 2), ("B5", 4)],
        [("A5", 4), ("F#5", 2), ("A5", 2), ("D6", 4), ("C#6", 4)],
        [("C#6", 2), (".", 2), ("E6", 2), ("C#6", 2), ("A5", 2), ("C#6", 2), ("E6", 4)],
        [("B5", 6), ("G#5", 2), ("E5", 4), (".", 4)],
        [("F#5", 2), (".", 2), ("C#6", 2), ("A5", 2), ("F#5", 2), ("A5", 2), ("C#6", 4)],
        [("D6", 4), ("C#6", 2), ("A5", 2), ("F#6", 4), ("E6", 4)],
        [("E6", 2), ("C#6", 2), ("A5", 2), ("E6", 4), ("C#6", 2), ("B5", 4)],
        [("G#5", 8), ("B5", 4), ("C#6", 4)],
    ]
    b = [
        [("D6", 4), ("F#6", 4), ("E6", 2), ("D6", 2), ("B5", 4)],
        [("A5", 4), ("D6", 4), ("F#6", 4), ("A6", 4)],
        [("E6", 6), ("C#6", 2), ("A5", 4), ("C#6", 4)],
        [("B5", 8), ("G#5", 4), ("E5", 4)],
        [("D6", 4), ("F#6", 4), ("B6", 4), ("A6", 2), ("F#6", 2)],
        [("F#6", 6), ("E6", 2), ("D6", 4), ("A5", 4)],
        [("E6", 4), ("C#6", 4), ("G#5", 4), ("C#6", 4)],
        [("F6", 4), ("G#6", 4), ("C#6", 8)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x...x...x...x...", bars), 0.62, 0.0, 0.0),
        (clap, drums("....x.......x...", bars), 0.35, -0.05, 0.15),
        (hat, drums("..x...x...x...xo", bars), 0.3, 0.35, 0.03),
        (bass, bassline(chords, "r.r.o.r.r.r.o.r.", 2), 0.5, 0.0, 0.0),
        (pluck, arps(chords, 5, (0, 1, 2, 3)), 0.22, -0.4, 0.3),
        (pad, held(chords, 3), 0.35, 0.1, 0.3),
        (lead, tune, 0.42, 0.1, 0.25),
    ]
    return render(bpm, bars, parts, wet=0.14)


def race_rally():
    """The rallycross cup, over the gravel and the jumps: rocky and driving,
    in G."""
    bpm = 138
    verse = ["G", "C", "D", "G", "Em", "C", "D", "D"]
    chorus = ["C", "G", "D", "Em", "C", "G", "Am", "D7"]
    breakdown = ["G", "C", "D", "G"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("D5", 2), ("G5", 2), ("B5", 2), ("D6", 4), ("B5", 2), ("A5", 2), ("G5", 2)],
        [("E5", 4), ("G5", 2), ("C6", 2), ("E6", 4), ("D6", 4)],
        [("D6", 2), ("C6", 2), ("A5", 2), ("F#5", 2), ("A5", 4), ("D6", 4)],
        [("B5", 8), ("G5", 4), ("D5", 4)],
        [("E5", 2), ("G5", 2), ("B5", 2), ("E6", 4), ("D6", 2), ("B5", 2), ("G5", 2)],
        [("C6", 4), ("E6", 4), ("G6", 4), ("E6", 4)],
        [("F#6", 6), ("E6", 2), ("D6", 4), ("A5", 4)],
        [("D6", 8), (".", 4), ("A5", 2), ("B5", 2)],
    ]
    b = [
        [("C6", 4), ("E6", 4), ("G6", 2), ("E6", 2), ("C6", 4)],
        [("B5", 4), ("D6", 4), ("G6", 4), ("D6", 4)],
        [("A5", 4), ("D6", 4), ("F#6", 4), ("A6", 4)],
        [("G6", 6), ("F#6", 2), ("E6", 4), ("B5", 4)],
        [("E6", 4), ("C6", 2), ("E6", 2), ("G6", 4), ("E6", 4)],
        [("D6", 4), ("B5", 2), ("D6", 2), ("G6", 8)],
        [("A6", 4), ("G6", 2), ("E6", 2), ("C6", 4), ("E6", 4)],
        [("F#6", 4), ("D6", 4), ("A5", 4), ("C6", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x..x..x.x..x..x.", bars), 0.6, 0.0, 0.0),
        (snare, drums("....x.......x...", bars), 0.45, 0.05, 0.12),
        (hat, drums("x.x.x.x.x.x.x.x.", bars), 0.25, 0.35, 0.03),
        (bass, bassline(chords, "r.rr.r.rr.rr.5o.", 2), 0.55, 0.0, 0.0),
        (keys, comp(chords, "x..x..x.x..x..x.", 4), 0.35, -0.35, 0.2),
        (lead, tune, 0.45, 0.1, 0.25),
    ]
    return render(bpm, bars, parts, wet=0.14)


def race_coaster():
    """The roller coaster cup: a fairground tune, bouncy and a bit silly, in B
    flat."""
    bpm = 126
    verse = ["Bb", "F", "Bb", "F", "Eb", "Bb", "F", "Bb"]
    chorus = ["Eb", "Bb", "Cm", "F", "Eb", "Bb", "F7", "Bb"]
    breakdown = ["Bb", "Eb", "F", "Bb"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("F5", 2), ("Bb5", 2), ("D6", 2), ("F6", 4), ("D6", 2), ("Bb5", 4)],
        [("A5", 4), ("C6", 2), ("F6", 2), ("A6", 4), ("F6", 4)],
        [("F6", 2), ("D6", 2), ("Bb5", 2), ("D6", 2), ("F6", 4), ("Bb6", 4)],
        [("A6", 6), ("G6", 2), ("F6", 4), ("C6", 4)],
        [("G5", 2), ("Bb5", 2), ("Eb6", 2), ("G6", 4), ("F6", 2), ("Eb6", 4)],
        [("D6", 4), ("F6", 4), ("Bb6", 4), ("F6", 4)],
        [("A6", 4), ("G6", 2), ("F6", 2), ("C6", 4), ("Eb6", 4)],
        [("D6", 8), (".", 4), ("F5", 2), ("A5", 2)],
    ]
    b = [
        [("G6", 4), ("Eb6", 4), ("Bb5", 4), ("G5", 4)],
        [("F6", 6), ("D6", 2), ("Bb5", 8)],
        [("Eb6", 4), ("C6", 2), ("Eb6", 2), ("G6", 4), ("Eb6", 4)],
        [("F6", 4), ("A5", 4), ("C6", 4), ("F6", 4)],
        [("Bb6", 4), ("G6", 2), ("Eb6", 2), ("G6", 4), ("Bb6", 4)],
        [("Bb6", 6), ("A6", 2), ("F6", 4), ("D6", 4)],
        [("Eb6", 4), ("C6", 4), ("A5", 4), ("Eb6", 4)],
        [("D6", 12), (".", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x.......x.......", bars), 0.55, 0.0, 0.0),
        (snare, drums("....x.......x...", bars), 0.35, 0.05, 0.15),
        (hat, drums("..x...x...x...x.", bars), 0.28, 0.35, 0.05),
        (bass, bassline(chords, "r...5...r...5...", 2), 0.5, 0.0, 0.0),
        (keys, comp(chords, "..x...x...x...x.", 4), 0.35, -0.35, 0.25),
        (bell, tune, 0.5, 0.2, 0.3),
        (lead, [(at, f / 2.0, n) for at, f, n in tune], 0.14, -0.1, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.2)


def race_legends():
    """The famous circuits cup: a big, proud anthem, in E flat."""
    bpm = 144
    verse = ["Eb", "Bb", "Cm", "Ab", "Eb", "Bb", "Ab", "Bb"]
    chorus = ["Ab", "Bb", "Gm", "Cm", "Ab", "Bb", "Fm", "Bb7"]
    breakdown = ["Eb", "Ab", "Bb", "Eb"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("Eb5", 4), ("G5", 2), ("Bb5", 2), ("Eb6", 6), ("D6", 2)],
        [("D6", 4), ("Bb5", 4), ("F5", 4), ("Bb5", 4)],
        [("C6", 4), ("Eb6", 2), ("G6", 2), ("C6", 4), ("Bb5", 4)],
        [("Ab5", 6), ("Bb5", 2), ("C6", 4), ("Ab5", 4)],
        [("Bb5", 4), ("Eb6", 4), ("G6", 6), ("F6", 2)],
        [("F6", 4), ("D6", 4), ("Bb5", 4), ("D6", 4)],
        [("Eb6", 4), ("C6", 4), ("Ab5", 4), ("C6", 4)],
        [("Bb5", 12), (".", 4)],
    ]
    b = [
        [("C6", 4), ("Eb6", 4), ("Ab6", 4), ("G6", 2), ("F6", 2)],
        [("F6", 6), ("D6", 2), ("Bb5", 8)],
        [("G6", 4), ("F6", 2), ("D6", 2), ("Bb5", 4), ("D6", 4)],
        [("Eb6", 6), ("D6", 2), ("C6", 4), ("G5", 4)],
        [("Ab6", 4), ("G6", 2), ("Eb6", 2), ("C6", 4), ("Eb6", 4)],
        [("F6", 4), ("Bb6", 4), ("D6", 4), ("F6", 4)],
        [("Ab6", 4), ("F6", 4), ("C6", 4), ("Ab5", 4)],
        [("Bb5", 4), ("D6", 4), ("F6", 4), ("Ab6", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x...x...x...x...", bars), 0.6, 0.0, 0.0),
        (snare, drums("....x.......x..o", bars), 0.45, 0.05, 0.15),
        (hat, drums("x.x.x.x.x.x.x.x.", bars), 0.22, 0.35, 0.03),
        (bass, bassline(chords, "r-r-r-r-o-o-5-5-", 2), 0.5, 0.0, 0.0),
        (pad, held(chords, 3), 0.45, 0.0, 0.35),
        (pluck, arps(chords, 4, (0, 1, 2, 3, 2, 1)), 0.25, -0.35, 0.3),
        (lead, tune, 0.45, 0.1, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.18)


def race_beach():
    """The beach cup: sunny and easy going, steel drums over a calypso beat,
    in F."""
    bpm = 124
    verse = ["F", "Bb", "C", "F", "Dm", "Bb", "C7", "F"]
    chorus = ["Bb", "C", "Am", "Dm", "Bb", "C", "Gm", "C7"]
    breakdown = ["F", "Bb", "C", "F"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("C6", 2), ("A5", 2), ("F5", 2), ("A5", 2), ("C6", 3), ("D6", 1), ("C6", 4)],
        [("D6", 2), ("F6", 2), ("D6", 2), ("Bb5", 2), ("D6", 4), ("F5", 4)],
        [("E6", 3), ("D6", 1), ("C6", 2), ("Bb5", 2), ("G5", 4), ("C6", 4)],
        [("A5", 6), ("C6", 2), ("F6", 6), (".", 2)],
        [("F6", 2), ("E6", 2), ("D6", 2), ("A5", 2), ("D6", 3), ("E6", 1), ("F6", 4)],
        [("D6", 2), ("Bb5", 2), ("F5", 2), ("Bb5", 2), ("D6", 4), ("F6", 4)],
        [("E6", 2), ("G6", 2), ("E6", 2), ("C6", 2), ("Bb5", 4), ("G5", 4)],
        [("F5", 8), (".", 4), ("A5", 2), ("C6", 2)],
    ]
    b = [
        [("D6", 3), ("F6", 1), ("D6", 2), ("Bb5", 2), ("F6", 4), ("D6", 4)],
        [("E6", 3), ("G6", 1), ("E6", 2), ("C6", 2), ("G6", 4), ("E6", 4)],
        [("C6", 2), ("E6", 2), ("A6", 4), ("G6", 2), ("E6", 2), ("C6", 4)],
        [("D6", 6), ("F6", 2), ("A6", 4), ("F6", 4)],
        [("Bb6", 3), ("A6", 1), ("G6", 2), ("F6", 2), ("D6", 4), ("F6", 4)],
        [("G6", 3), ("F6", 1), ("E6", 2), ("C6", 2), ("E6", 4), ("G6", 4)],
        [("D6", 2), ("Bb5", 2), ("G5", 2), ("Bb5", 2), ("D6", 4), ("G6", 4)],
        [("E6", 4), ("C6", 4), ("G5", 4), ("Bb5", 4)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x..x....x..x....", bars), 0.55, 0.0, 0.0),
        (clap, drums("....x.......x...", bars), 0.35, 0.05, 0.15),
        (hat, drums("x.xxx.xxx.xxx.xx", bars), 0.2, 0.35, 0.03),
        (bass, bassline(chords, "r..5..o.r..5..o.", 2), 0.5, 0.0, 0.0),
        (keys, comp(chords, "..x..x.x..x..x.x", 4), 0.3, -0.35, 0.2),
        (steel, tune, 0.5, 0.15, 0.25),
        (steel, [(at, f / 2.0, n) for at, f, n in tune], 0.16, -0.2, 0.25),
    ]
    return render(bpm, bars, parts, wet=0.16)


def race_alpine():
    """The Alpine cup: a quick oom-pah polka on the accordion, with bells on
    top, in G."""
    bpm = 136
    verse = ["G", "D7", "G", "C", "G", "D7", "D7", "G"]
    chorus = ["C", "G", "D7", "G", "C", "G", "D7", "G"]
    breakdown = ["G", "C", "D7", "G"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("B5", 2), ("D6", 2), ("G6", 4), ("F#6", 2), ("E6", 2), ("D6", 4)],
        [("C6", 2), ("A5", 2), ("F#5", 2), ("A5", 2), ("C6", 4), ("D6", 4)],
        [("B5", 2), ("G5", 2), ("B5", 2), ("D6", 2), ("G6", 6), (".", 2)],
        [("E6", 2), ("G6", 2), ("E6", 2), ("C6", 2), ("A5", 4), ("C6", 4)],
        [("B5", 2), ("D6", 2), ("G6", 2), ("D6", 2), ("B5", 4), ("G5", 4)],
        [("A5", 2), ("C6", 2), ("F#6", 2), ("E6", 2), ("D6", 4), ("C6", 4)],
        [("A5", 3), ("B5", 1), ("C6", 2), ("A5", 2), ("F#5", 4), ("A5", 4)],
        [("G5", 8), (".", 4), ("D6", 2), ("D6", 2)],
    ]
    b = [
        [("G5", 2), ("C6", 2), ("E6", 2), ("G6", 2), ("E6", 4), ("C6", 4)],
        [("D6", 2), ("G6", 2), ("B6", 2), ("G6", 2), ("D6", 4), ("B5", 4)],
        [("C6", 2), ("F#6", 2), ("A6", 2), ("F#6", 2), ("D6", 4), ("A5", 4)],
        [("B5", 2), ("D6", 2), ("G6", 4), ("G6", 2), ("A6", 2), ("B6", 4)],
        [("C7", 3), ("B6", 1), ("A6", 2), ("G6", 2), ("E6", 4), ("G6", 4)],
        [("D6", 3), ("E6", 1), ("D6", 2), ("B5", 2), ("G5", 4), ("B5", 4)],
        [("A5", 2), ("D6", 2), ("F#6", 2), ("A6", 2), ("C7", 4), ("F#6", 4)],
        [("G6", 8), (".", 8)],
    ]
    tune = melody(16, *(a + b + a + [[(".", 16)]] * 4))
    bars = len(chords)
    parts = [
        (kick, drums("x.......x.......", bars), 0.5, 0.0, 0.0),
        (snare, drums("....x.......x...", bars), 0.3, 0.05, 0.1),
        (hat, drums("..x...x...x...x.", bars), 0.18, 0.35, 0.03),
        (bass, bassline(chords, "r.......5.......", 2), 0.5, 0.0, 0.0),
        (accordion, comp(chords, "....x.......x...", 4), 0.22, -0.35, 0.15),
        (accordion, comp(chords, "..x...x...x...x.", 4), 0.12, -0.35, 0.15),
        (accordion, tune, 0.42, 0.15, 0.2),
        (bell, [(at, f * 2.0, n) for at, f, n in tune], 0.12, -0.2, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.18)


def race_canyon():
    """The Canyon cup: a galloping cowboy tune on a twangy guitar, with a
    train beat and somebody whistling along, in E minor."""
    bpm = 150
    verse = ["Em", "Em", "Am", "Em", "C", "B7", "Em", "Em"]
    chorus = ["Am", "Am", "Em", "Em", "C", "D", "Em", "B7"]
    breakdown = ["Em", "Em", "B7", "B7"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("E3", 4), ("G3", 2), ("A3", 2), ("B3", 6), (".", 2)],
        [("B3", 2), ("D4", 2), ("B3", 2), ("A3", 2), ("G3", 4), ("E3", 4)],
        [("A3", 4), ("C4", 2), ("E4", 2), ("D4", 4), ("C4", 4)],
        [("B3", 6), ("G3", 2), ("E3", 8)],
        [("C4", 4), ("E4", 2), ("G4", 2), ("E4", 4), ("C4", 4)],
        [("B3", 4), ("D#4", 2), ("F#4", 2), ("A4", 4), ("F#4", 4)],
        [("E4", 4), ("D4", 2), ("B3", 2), ("G3", 2), ("A3", 2), ("B3", 4)],
        [("E3", 12), (".", 4)],
    ]
    b = [
        [("A3", 2), ("C4", 2), ("E4", 4), ("E4", 2), ("D4", 2), ("C4", 4)],
        [("A3", 4), ("E4", 4), ("A4", 8)],
        [("G4", 4), ("F#4", 2), ("E4", 2), ("B3", 4), ("G3", 4)],
        [("E4", 2), ("D4", 2), ("B3", 4), ("G3", 8)],
        [("C4", 2), ("E4", 2), ("G4", 4), ("E4", 2), ("G4", 2), ("C5", 4)],
        [("D5", 4), ("A4", 2), ("F#4", 2), ("D4", 8)],
        [("B3", 2), ("E4", 2), ("G4", 2), ("B4", 2), ("A4", 4), ("G4", 4)],
        [("F#4", 4), ("D#4", 4), ("B3", 8)],
    ]
    rest = [[(".", 16)]]
    tune = melody(16, *(a + b + a + rest * 4))
    whistled = melody(16, *(rest * 8 + b + rest * 12))
    bars = len(chords)
    parts = [
        (kick, drums("x.......x.......", bars), 0.5, 0.0, 0.0),
        (snare, drums("....o.......o..o", bars), 0.28, 0.05, 0.1),
        (hat, drums("x.xxx.xxx.xxx.xx", bars), 0.14, 0.35, 0.03),
        (bass, bassline(chords, "r.......5.......", 2), 0.5, 0.0, 0.0),
        (strum, comp(chords, "....x.x.....x.x.", 3), 0.2, -0.4, 0.15),
        (twang, tune, 0.45, 0.15, 0.3),
        (whistle, [(at, f * 2.0, n) for at, f, n in whistled], 0.16, -0.2, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.22)


def race_jungle():
    """The Jungle cup: marimba over hand drums and a shaker, with a wooden
    flute on the chorus, in A minor."""
    bpm = 128
    verse = ["Am", "Am", "G", "Am", "F", "G", "E7", "Am"]
    chorus = ["F", "G", "Am", "Am", "F", "G", "E7", "E7"]
    breakdown = ["Am", "G", "F", "E7"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("A5", 2), ("C6", 2), ("E6", 2), ("C6", 2), ("A5", 2), ("E5", 2), ("A5", 4)],
        [("G5", 2), ("A5", 2), ("C6", 4), ("D6", 2), ("C6", 2), ("A5", 4)],
        [("B5", 2), ("D6", 2), ("G6", 2), ("D6", 2), ("B5", 4), ("G5", 4)],
        [("A5", 2), ("C6", 2), ("E6", 4), ("D6", 2), ("C6", 2), ("A5", 4)],
        [("F5", 2), ("A5", 2), ("C6", 2), ("F6", 2), ("E6", 2), ("C6", 2), ("A5", 4)],
        [("G5", 2), ("B5", 2), ("D6", 2), ("G6", 2), ("F6", 2), ("D6", 2), ("B5", 4)],
        [("E6", 3), ("D6", 1), ("B5", 2), ("G#5", 2), ("B5", 4), ("D6", 4)],
        [("A5", 8), (".", 4), ("E5", 2), ("G5", 2)],
    ]
    b = [
        [("C6", 4), ("A5", 2), ("C6", 2), ("F6", 4), ("E6", 4)],
        [("D6", 4), ("B5", 2), ("D6", 2), ("G6", 6), (".", 2)],
        [("E6", 3), ("D6", 1), ("C6", 2), ("A5", 2), ("C6", 4), ("E6", 4)],
        [("A6", 8), ("G6", 4), ("E6", 4)],
        [("F6", 3), ("E6", 1), ("C6", 2), ("A5", 2), ("F6", 4), ("A6", 4)],
        [("G6", 3), ("F6", 1), ("D6", 2), ("B5", 2), ("G6", 4), ("B6", 4)],
        [("G#6", 4), ("E6", 2), ("D6", 2), ("B5", 4), ("G#5", 4)],
        [("B5", 2), ("D6", 2), ("E6", 4), (".", 8)],
    ]
    rest = [[(".", 16)]]
    tune = melody(16, *(a + b + a + rest * 4))
    blown = melody(16, *(rest * 8 + b + rest * 12))
    bars = len(chords)
    low = [(at, 110.0, n, v) for at, _f, n, v in drums("..o.....x..o.o..", bars)]
    high = [(at, 196.0, n, v) for at, _f, n, v in drums("x..x..x...x.x...", bars)]
    parts = [
        (kick, drums("x.....x...x.....", bars), 0.5, 0.0, 0.0),
        (hand_drum, low, 0.4, -0.3, 0.1),
        (hand_drum, high, 0.3, 0.3, 0.1),
        (hat, drums("xoxoxoxoxoxoxoxo", bars), 0.12, 0.4, 0.03),
        (bass, bassline(chords, "r..r..5.r..r..o.", 2), 0.45, 0.0, 0.0),
        (marimba, arps(chords, 4, every=2), 0.16, -0.35, 0.15),
        (marimba, tune, 0.45, 0.15, 0.2),
        (flute, [(at, f / 2.0, n) for at, f, n in blown], 0.3, -0.15, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.2)


def race_city():
    """The City cup: driving through the city at night, with a pulsing synth
    bass in eighths, a steady four on the floor, ticking arpeggios and a soft
    synth lead, in F sharp minor."""
    bpm = 112
    verse = ["F#m", "F#m", "D", "D", "A", "A", "E", "E"]
    chorus = ["D", "E", "F#m", "F#m", "D", "E", "C#m", "C#m"]
    breakdown = ["Bm", "D", "E", "E"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("C#5", 4), ("F#5", 2), ("A5", 2), ("G#5", 4), ("F#5", 4)],
        [("E5", 2), ("F#5", 2), ("C#5", 12)],
        [("D5", 4), ("F#5", 2), ("A5", 2), ("B5", 4), ("A5", 4)],
        [("F#5", 4), ("E5", 2), ("D5", 2), ("F#5", 8)],
        [("E5", 4), ("A5", 2), ("C#6", 2), ("B5", 4), ("A5", 4)],
        [("G#5", 2), ("A5", 2), ("E5", 12)],
        [("B5", 4), ("G#5", 2), ("E5", 2), ("F#5", 2), ("G#5", 2), ("B5", 4)],
        [("G#5", 8), (".", 8)],
    ]
    b = [
        [("F#5", 2), ("A5", 2), ("D6", 4), ("C#6", 4), ("A5", 4)],
        [("G#5", 2), ("B5", 2), ("E6", 6), (".", 2), ("C#6", 2), ("B5", 2)],
        [("C#6", 6), ("A5", 2), ("F#5", 4), ("A5", 4)],
        [("C#6", 4), ("E6", 4), ("C#6", 8)],
        [("D6", 4), ("C#6", 2), ("A5", 2), ("F#5", 4), ("A5", 4)],
        [("B5", 4), ("G#5", 2), ("E5", 2), ("B5", 4), ("E6", 4)],
        [("E6", 4), ("C#6", 2), ("G#5", 2), ("E5", 4), ("G#5", 4)],
        [("C#6", 8), (".", 8)],
    ]
    rest = [[(".", 16)]]
    tune = melody(16, *(a + b + a + rest * 4))
    bars = len(chords)
    # The drums drop to the hats and bass for the breakdown at the end.
    full = bars - len(breakdown)
    parts = [
        (kick, drums("x...x...x...x...", full), 0.6, 0.0, 0.0),
        (clap, drums("....x.......x...", full), 0.3, 0.1, 0.15),
        (hat, drums("..x...x...x...x.", bars), 0.16, 0.35, 0.03),
        (hat, drums("o.o.o.o.o.o.o.o.", bars), 0.07, -0.35, 0.02),
        (bass, bassline(chords, "rororororororoo5", 1), 0.5, 0.0, 0.0),
        (pluck, arps(chords, 4, order=(0, 1, 2, 3), every=1), 0.12, -0.4, 0.25),
        (pad, held(chords, 3), 0.35, 0.0, 0.4),
        (night_lead, tune, 0.4, 0.15, 0.3),
    ]
    return render(bpm, bars, parts, wet=0.24)


def race_sky():
    """The Sky cup: floating along above the clouds, with a breezy flute
    over chiming arpeggios, warm pads and a light skipping beat, in D with a
    raised fourth."""
    bpm = 124
    verse = ["D", "E", "Bm", "G", "D", "E", "G", "A"]
    chorus = ["G", "A", "F#m", "Bm", "G", "A", "D", "D"]
    breakdown = ["G", "E", "G", "A"]
    chords = verse + chorus + verse + breakdown
    a = [
        [("F#5", 2), ("A5", 2), ("D6", 4), ("E6", 2), ("D6", 2), ("A5", 4)],
        [("G#5", 2), ("B5", 2), ("E6", 6), (".", 2), ("D6", 2), ("B5", 2)],
        [("D6", 4), ("C#6", 2), ("B5", 2), ("F#5", 4), ("B5", 4)],
        [("D6", 2), ("B5", 2), ("G5", 4), ("A5", 2), ("B5", 2), ("D6", 4)],
        [("A5", 2), ("D6", 2), ("F#6", 4), ("E6", 2), ("D6", 2), ("A5", 4)],
        [("B5", 2), ("G#5", 2), ("E5", 4), ("G#5", 2), ("B5", 2), ("E6", 4)],
        [("D6", 3), ("B5", 1), ("G5", 2), ("B5", 2), ("D6", 4), ("G6", 4)],
        [("E6", 8), (".", 4), ("C#6", 2), ("E6", 2)],
    ]
    b = [
        [("D6", 4), ("B5", 2), ("D6", 2), ("G6", 4), ("F#6", 4)],
        [("E6", 4), ("C#6", 2), ("E6", 2), ("A6", 6), (".", 2)],
        [("F#6", 3), ("E6", 1), ("C#6", 2), ("A5", 2), ("C#6", 4), ("F#6", 4)],
        [("D6", 4), ("F#6", 4), ("B6", 8)],
        [("B6", 3), ("A6", 1), ("G6", 2), ("D6", 2), ("B5", 4), ("D6", 4)],
        [("C#6", 3), ("D6", 1), ("E6", 2), ("A5", 2), ("C#6", 4), ("E6", 4)],
        [("F#6", 4), ("E6", 2), ("D6", 2), ("A5", 4), ("F#5", 4)],
        [("D6", 8), (".", 8)],
    ]
    rest = [[(".", 16)]]
    tune = melody(16, *(a + b + a + rest * 4))
    bars = len(chords)
    full = bars - len(breakdown)
    parts = [
        (kick, drums("x.....x...x.....", full), 0.45, 0.0, 0.0),
        (snare, drums("....o.......o...", full), 0.24, 0.05, 0.15),
        (hat, drums("x.xx.xx.x.xx.xx.", bars), 0.11, 0.35, 0.03),
        (bass, bassline(chords, "r.....5...r...o.", 2), 0.42, 0.0, 0.0),
        (chime, arps(chords, 5, order=(0, 1, 2, 3, 2, 1), every=2), 0.14, -0.4, 0.35),
        (pad, held(chords, 3), 0.42, 0.0, 0.45),
        (flute, [(at, f / 2.0, n) for at, f, n in tune], 0.42, 0.15, 0.35),
        (chime, [(at, f, n) for at, f, n in tune], 0.1, -0.15, 0.4),
    ]
    return render(bpm, bars, parts, wet=0.28)


# Arcade kart pop. One shared palette: a tight punchy kick, a snappy snare
# and clap, ticking hats, a fat synth bass or slap bass, synth brass stabs,
# a bright detuned supersaw lead and pads that pump with the kick. Each cup
# adds its own flavour on top. Instruments here may give back (2, n) stereo.

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


def pop_clap(_f, _d, v):
    """A clap a little wide: each side its own burst of hands."""
    n = seconds(0.35)
    env = np.zeros(n)
    for at in (0.0, 0.008, 0.016, 0.026):
        s = seconds(at)
        env[s:] += decay(n - s, 0.006 if at < 0.02 else 0.18)
    sides = [bandpass(noise(n, seed), 1100, 7000) * env for seed in (24, 124)]
    return np.stack(sides) * 0.6 * v


def tick(_f, _d, v):
    """A closed hat."""
    n = seconds(0.08)
    return highpass(noise(n, 25), 8000, order=4) * decay(n, 0.025) * 0.6 * v


def open_hat(_f, _d, v):
    n = seconds(0.4)
    return highpass(noise(n, 26), 7000, order=4) * decay(n, 0.25) * adsr(n, 0.001, 0.0, 1.0, 0.05) * 0.45 * v


def crash(_f, _d, v):
    n = seconds(2.5)
    metal = sum(blep_square(f, n) for f in (421.0, 563.0, 789.0, 1043.0, 1381.0))
    metal = highpass(metal, 3000) * decay(n, 1.0) * 0.12
    sides = [highpass(noise(n, seed), 4500) * decay(n, 2.2) + metal for seed in (27, 127)]
    return np.stack(sides) * adsr(n, 0.001, 0.0, 1.0, 0.1) * 0.4 * v


def riser(_f, d, v):
    """Noise that rises and brightens over the note, into the next section."""
    n = seconds(d)
    curve = np.linspace(0.0, 1.0, n) ** 2
    sides = []
    for seed in (28, 128):
        x = noise(n, seed)
        sides.append(bandpass(x, 300, 1500) * (1.0 - curve) + highpass(x, 2500) * curve)
    return np.stack(sides) * (0.05 + curve) * adsr(n, 0.0, 0.0, 1.0, 0.02) * 0.35 * v


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


def super_lead(f, d, v):
    """The hook lead: seven detuned saws spread wide, with a square in the
    middle to hold the pitch."""
    n = seconds(d + 0.08)
    t = times(n)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.18) * 4.0, 0.0, 1.0)
    tone = supersaw(f * vib, n, 7, 0.012, seed=int(f) % 97) + blep_square(f * vib, n, 0.5) * 0.35
    return lowpass(tone, 6500) * adsr(n, 0.004, 0.12, 0.8, 0.07) * 0.7 * v


def square_lead(f, d, v):
    """A lighter lead for the verses: a thin pulse with a little vibrato."""
    n = seconds(d + 0.05)
    t = times(n)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) * 4.0, 0.0, 1.0)
    tone = blep_square(f * vib, n, 0.3) * 0.8 + blep_saw(f * 1.003 * vib, n) * 0.25
    return lowpass(tone, 4000) * adsr(n, 0.004, 0.1, 0.75, 0.05) * 0.7 * v


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


# Flavour for each cup, played over the shared palette. Some give back
# (2, n) stereo, like the palette.

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


def tune_at(bar, lines):
    """A hand written melody placed from `bar`."""
    return shift(melody(16, *lines), bar * 16)


def part(instrument, notes, loud, pan=0.0, verb=0.0, echo_send=0.0, duck=0.0):
    """One part of a pop tune. `duck` is how far it drops with each kick."""
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
    """Plays a pop tune's parts and mixes them on a bus: reverb and a dotted
    eighth echo, the tail folded back onto the start, then width, glue
    compression and a limiter, all wrapping around so it loops. `level` is
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


def drum_parts(form, rules):
    """Puts drum patterns into the sections named for them. `rules` is
    (sections, pattern) pairs, and a pattern can be one bar or a bar per
    step of the section."""
    out = []
    for name, start, chords in form:
        for names, pattern in rules:
            if name in names:
                out += drums(pattern, len(chords), start * 16)
    return out


def in_sections(form, names, make):
    """Notes from `make(first step, chords)` for each section named."""
    out = []
    for name, start, chords in form:
        if name in names:
            out += make(start * 16, chords)
    return out


def starts(form, names, bar=0):
    """A one note hit at the start of each section named, or `bar` bars in
    (negative counts from the section's end)."""
    out = []
    for name, start, chords in form:
        if name in names:
            b = start + (bar if bar >= 0 else len(chords) + bar)
            out.append((b * 16, 0.0, 16))
    return out


def pop_menu():
    """The garage and the menus: a relaxed groove in G, toy bells on top of
    slap bass and brass, with the main theme's hook shape in its chorus."""
    bpm = 118
    verse = ["G", "Em", "C", "D"] * 2
    hook_chords = ["Cmaj7", "D", "Bm7", "Em7", "Cmaj7", "D", "G", "G6"]
    form, chords = song(("intro", ["Cmaj7", "D", "G", "G6"]), ("verse", verse), ("hook", hook_chords),
                        ("break", ["Cmaj7", "D", "Bm7", "Em7"]), ("verse2", verse), ("hook2", hook_chords))
    a = bars(
        "D5:2 G5:2 .:2 B5:2 .:2 A5:2 G5:4",
        "E5:2 G5:2 .:2 B5:2 .:2 A5:2 G5:4",
        "E5:2 G5:2 C6:4 B5:2 A5:2 G5:4",
        "F#5:6 .:2 A5:4 F#5:4",
        "D5:2 G5:2 .:2 B5:2 .:2 D6:2 B5:4",
        "E6:2 D6:2 .:2 B5:2 .:2 A5:2 G5:4",
        "A5:3 B5:3 C6:2 E6:4 D6:2 C6:2",
        "A5:8 .:4 F#5:2 A5:2",
    )
    hook = bars(
        "B5:3 A5:3 G5:2 E5:3 G5:3 A5:2",
        "A5:3 G5:3 F#5:2 D5:6 .:2",
        "B5:3 A5:3 G5:2 E5:3 G5:3 B5:2",
        "D6:6 B5:2 A5:4 G5:4",
        "B5:3 A5:3 G5:2 E5:3 G5:3 A5:2",
        "A5:3 G5:3 F#5:2 A5:4 D6:4",
        "B5:3 A5:3 G5:2 D5:3 E5:3 G5:2",
        "G5:8 .:4 D5:2 E5:2",
    )
    bar_count = len(chords)
    groove = ("verse", "hook", "verse2", "hook2")
    kicks = drum_parts(form, [(groove, "x.....x...x....."), (("intro",), "x.......x.......")])
    melody_notes = (in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
                    + in_sections(form, ("hook", "hook2"), lambda at, _c: shift(melody(16, *hook), at))
                    + in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
                    + in_sections(form, ("break",), lambda at, _c: shift(melody(16, *hook[:4]), at)))
    parts = [
        part(punch_kick, kicks, 0.5),
        part(snap_snare, drum_parts(form, [(groove, "....x.......x...")]), 0.3, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("hook", "hook2"), "....x.......x...")]), 0.25, 0.0, 0.15),
        part(tick, drum_parts(form, [(groove + ("intro",), "x.xox.xox.xox.xo")]), 0.22, 0.35),
        part(shaker, drum_parts(form, [(groove + ("break",), "oxoxoxoxoxoxoxox")]), 0.12, -0.35),
        part(crash, starts(form, ("verse", "hook", "verse2", "hook2")), 0.22, 0.0, 0.1),
        part(riser, [(n[0] + 8, 0.0, 8) for n in starts(form, ("break",), -1)], 0.3, 0.0, 0.1),
        part(slap_bass, in_sections(form, groove + ("intro",), lambda at, c: bassline(c, "r..r..o.r.5..o.r", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.5, 0.0, 0.0, 0.0, 0.3),
        part(pump_pad, in_sections(form, ("hook", "hook2", "break", "intro"), lambda at, c: held(c, 3, at)), 0.35, 0.0, 0.3, 0.0, 0.35),
        part(brass, in_sections(form, ("hook2", "verse2"), lambda at, c: comp(c, "..x..x....x.....", 4, at)), 0.22, -0.25, 0.2),
        part(keys, in_sections(form, ("verse", "verse2", "hook"), lambda at, c: comp(c, "..x...x...x...x.", 4, at)), 0.35, -0.35, 0.2),
        part(chime, melody_notes, 0.52, 0.15, 0.3, 0.15),
        part(pop_pluck, octave(melody_notes, -1), 0.18, -0.15, 0.2, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.18, level=-13.7)


def pop_race_one():
    """The Baseplate Cup and the main theme: big and bright in D, a 3 3 2
    hook on the supersaw over a pumping four on the floor."""
    bpm = 150
    verse = ["D", "Bm", "G", "A"] * 2
    pre = ["Em", "F#m", "G", "A"] * 2
    chorus = ["G", "A", "Bm", "D", "G", "A", "D", "Asus"]
    form, chords = song(("intro", ["G", "A", "D", "Asus"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["G", "A", "Bm", "A"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "A5:2 .:2 F#5:2 A5:2 .:2 B5:2 A5:4",
        "F#5:2 .:2 D5:2 F#5:2 .:2 E5:2 D5:4",
        "B5:2 .:2 G5:2 B5:2 D6:2 C#6:2 B5:2 A5:2",
        "A5:6 .:2 E5:2 F#5:2 G5:2 A5:2",
        "A5:2 .:2 F#5:2 A5:2 .:2 D6:2 C#6:4",
        "B5:2 .:2 F#5:2 B5:2 .:2 C#6:2 D6:4",
        "E6:3 D6:3 B5:2 G5:3 A5:3 B5:2",
        "A5:8 .:4 C#6:2 E6:2",
    )
    b = bars(
        "B5:3 B5:3 B5:2 A5:4 G5:4",
        "C#6:3 C#6:3 C#6:2 B5:4 A5:4",
        "D6:3 D6:3 D6:2 C#6:4 B5:4",
        "C#6:4 E6:4 A5:8",
        "B5:3 B5:3 B5:2 E6:4 D6:4",
        "C#6:3 C#6:3 C#6:2 F#6:4 E6:4",
        "D6:4 E6:4 F#6:4 G6:4",
        "A6:8 .:8",
    )
    hook = bars(
        "F#6:3 E6:3 D6:2 B5:3 D6:3 E6:2",
        "E6:3 D6:3 C#6:2 A5:6 .:2",
        "F#6:3 E6:3 D6:2 B5:3 D6:3 F#6:2",
        "A6:6 F#6:2 E6:4 D6:4",
        "F#6:3 E6:3 D6:2 B5:3 D6:3 E6:2",
        "E6:3 D6:3 C#6:2 E6:4 A6:4",
        "F#6:3 E6:3 D6:2 A5:3 B5:3 D6:2",
        "D6:8 .:4 A5:2 C#6:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    roll = "....x.......x...", "x.x.x.x.xxxxXXXX"
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums(roll[0], len(ch) - 1, start * 16) + drums(roll[1], 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "chorus", "chorus2", "intro"):
            snares += drums(roll[0], len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    parts = [
        part(punch_kick, kicks, 0.52),
        part(snap_snare, snares, 0.4, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2", "verse2"), "....x.......x...")]), 0.3, 0.0, 0.15),
        part(tick, drum_parts(form, [(("verse", "pre", "intro"), "x.o.x.o.x.o.x.o."), (("chorus", "chorus2", "verse2"), "xoxoxoxoxoxoxoxo")]), 0.22, 0.35),
        part(open_hat, drum_parts(form, [(full, "..x...x...x...x.")]), 0.2, -0.3),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.25, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.35, 0.0, 0.1),
        part(pop_bass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r.o.r.o.r.o.r.o.", 2, at))
             + in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "r..r..r.r..r.5o.", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.55, 0.0, 0.0, 0.0, 0.45),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.4, 0.0, 0.3, 0.0, 0.5),
        part(pop_pluck, in_sections(form, ("verse", "verse2", "break"), lambda at, c: arps(c, 4, (0, 1, 2, 3, 2, 1, 0, 2), 1, at)), 0.18, -0.4, 0.15, 0.25, 0.4),
        part(brass, in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
             + in_sections(form, ("chorus2", "pre"), lambda at, c: comp(c, "x..x..x.....x...", 4, at)), 0.3, -0.2, 0.2),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.44, 0.1, 0.2, 0.2),
        part(super_lead, hooks, 0.5, 0.0, 0.25, 0.15),
        part(chime, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1)
             + in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("C#6:4 E6:4 A6:8"))), at)), 0.22, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.0)


def pop_race_beach():
    """The Island Cup: a quick soca beat in F, steel drums on the hook with
    congas, cowbell, a shaker and slap bass under the shared pop sound."""
    bpm = 152
    verse = ["F", "C", "Dm", "Bb"] * 2
    pre = ["Gm", "Am", "Bb", "C"] * 2
    chorus = ["Bb", "C", "F", "Dm", "Bb", "C", "F", "F"]
    form, chords = song(("intro", ["Bb", "C", "F", "F"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["Bb", "C", "F", "Dm"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "C6:2 .:1 A5:1 C6:2 F6:2 .:2 E6:2 C6:4",
        "G5:2 .:1 E5:1 G5:2 C6:2 .:2 Bb5:2 G5:4",
        "A5:2 .:1 F5:1 A5:2 D6:2 .:2 C6:2 A5:4",
        "Bb5:3 C6:3 D6:2 F5:8",
        "C6:2 .:1 A5:1 C6:2 F6:2 .:2 G6:2 A6:4",
        "G6:2 .:1 E6:1 C6:2 G5:2 .:2 C6:2 E6:4",
        "F6:3 E6:3 D6:2 A5:3 C6:3 D6:2",
        "D6:6 C6:2 Bb5:4 C6:4",
    )
    b = bars(
        "Bb5:3 Bb5:3 Bb5:2 D6:4 G5:4",
        "C6:3 C6:3 C6:2 E6:4 A5:4",
        "D6:3 D6:3 D6:2 F6:4 D6:4",
        "E6:4 C6:4 G5:8",
        "Bb5:3 Bb5:3 Bb5:2 D6:4 G6:4",
        "A6:3 G6:3 E6:2 C6:4 E6:4",
        "F6:4 D6:4 Bb5:4 D6:4",
        "C6:2 E6:2 G6:4 .:8",
    )
    hook = bars(
        "D6:2 D6:1 F6:3 D6:2 C6:2 Bb5:2 C6:4",
        "E6:2 E6:1 G6:3 E6:2 C6:2 Bb5:2 G5:4",
        "A5:2 C6:2 F6:2 A6:3 G6:3 F6:4",
        "F6:6 E6:2 D6:4 A5:4",
        "D6:2 D6:1 F6:3 D6:2 C6:2 Bb5:2 C6:4",
        "E6:2 E6:1 G6:3 E6:2 G6:2 Bb6:2 G6:4",
        "A6:3 G6:3 F6:2 C6:3 D6:3 F6:2",
        "F6:8 .:4 C6:2 D6:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    snares = []
    for name, start, ch in form:
        if name == "pre":
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
    steel_notes = (in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
                   + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at))
                   + in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
                   + in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
                   + in_sections(form, ("break",), lambda at, _c: shift(melody(16, *hook[:4]), at)))
    congas_low = [(at, 98.0, n, v) for at, _f, n, v in drum_parts(form, [(full + ("break",), "x......x..x.....")])]
    congas_high = [(at, 165.0, n, v) for at, _f, n, v in drum_parts(form, [(full + ("break",), "..x..x.x....x.ox")])]
    parts = [
        part(punch_kick, kicks, 0.5),
        part(snap_snare, snares, 0.35, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("verse", "chorus", "verse2", "chorus2", "intro"), "....x.......x...")]), 0.3, 0.0, 0.15),
        part(tick, drum_parts(form, [(full, "x.o.x.o.x.o.x.o.")]), 0.16, 0.35),
        part(shaker, drum_parts(form, [(full + ("break", "intro"), "oxoxoxoxoxoxoxox")]), 0.18, -0.35),
        part(cowbell, drum_parts(form, [(("chorus", "chorus2"), "x..x..x.x..x..x."), (("verse2",), "x...x...x...x...")]), 0.2, 0.4, 0.05),
        part(hand_drum, congas_low, 0.3, -0.3, 0.08),
        part(hand_drum, congas_high, 0.24, 0.3, 0.08),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.22, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.3, 0.0, 0.1),
        part(slap_bass, in_sections(form, full + ("intro",), lambda at, c: bassline(c, "r..o..r.r..o.5o.", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.35),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.3, 0.0, 0.3, 0.0, 0.5),
        part(marimba, in_sections(form, ("verse", "verse2"), lambda at, c: arps(c, 4, (0, 2, 1, 3), 2, at)), 0.2, -0.35, 0.15),
        part(brass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: comp(c, "..x..x....x..x..", 4, at)), 0.22, -0.2, 0.2),
        part(steel, steel_notes, 0.68, 0.15, 0.25, 0.15),
        part(steel, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), -1), 0.25, -0.25, 0.25, 0.1),
        part(super_lead, octave(in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at)), -1), 0.16, 0.0, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.0)



def pop_race_two():
    """The Axle Cup, works and foundries: a funky groove in E minor, the hook
    on a clavinet over slap bass, with anvil clanks in the drums."""
    bpm = 144
    verse = ["Em7", "A7", "Em7", "A7", "Cmaj7", "Bm7", "Am7", "B7"]
    pre = ["Am7", "Bm7", "Cmaj7", "D"] * 2
    chorus = ["Em7", "C", "D", "Bm7", "Em7", "C", "D", "B7"]
    form, chords = song(("intro", ["Em7", "C", "D", "B7"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["Em7", "C", "D", "B7"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "B4:2 .:1 B4:1 D5:2 E5:2 .:2 D5:1 E5:1 G5:2 E5:2",
        "C#5:2 .:2 E5:2 G5:2 .:2 F#5:2 E5:4",
        "B4:2 .:1 B4:1 D5:2 E5:2 .:2 G5:1 A5:1 B5:2 G5:2",
        "A5:3 G5:3 E5:2 C#5:8",
        "G5:2 .:1 E5:1 G5:2 B5:2 .:2 A5:2 G5:4",
        "F#5:2 .:1 D5:1 F#5:2 A5:2 .:2 B5:2 F#5:4",
        "E5:3 G5:3 A5:2 C6:4 B5:4",
        "D#5:4 F#5:4 A5:4 B5:4",
    )
    b = bars(
        "E5:1 .:1 A5:1 .:1 E5:1 A5:2 C6:2 .:1 B5:2 A5:2 G5:2",
        "F#5:1 .:1 B5:1 .:1 F#5:1 B5:2 D6:2 .:1 B5:2 A5:2 F#5:2",
        "G5:1 .:1 C6:1 .:1 G5:1 C6:2 E6:2 .:1 D6:2 C6:2 B5:2",
        "A5:4 B5:4 C6:4 D6:4",
        "E5:1 .:1 A5:1 .:1 E5:1 A5:2 C6:2 .:1 B5:2 A5:2 G5:2",
        "F#5:1 .:1 B5:1 .:1 F#5:1 B5:2 D6:2 .:1 B5:2 A5:2 F#5:2",
        "G5:1 .:1 C6:1 .:1 G5:1 C6:2 E6:2 .:1 G6:2 E6:2 C6:2",
        "B5:4 C6:4 D6:4 .:4",
    )
    hook = bars(
        "E5:3 G5:3 A5:2 B5:1 .:1 D6:2 B5:2 A5:2",
        "G5:2 A5:1 G5:1 E5:4 .:2 D5:2 E5:4",
        "E5:3 G5:3 A5:2 B5:1 .:1 D6:2 E6:2 G6:2",
        "F#6:3 E6:3 D6:2 B5:8",
        "E5:3 G5:3 A5:2 B5:1 .:1 D6:2 B5:2 A5:2",
        "G5:2 A5:1 G5:1 E5:4 .:2 B5:2 D6:4",
        "E6:3 D6:3 B5:2 A5:3 G5:3 F#5:2",
        "F#5:6 D#5:2 E5:4 .:2 B4:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(("chorus", "chorus2", "pre", "intro"), "x...x...x...x..."),
                              (("verse", "verse2"), "x..x..x...x.x...")])
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums("....x..o....x.o.", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "chorus", "chorus2", "intro"):
            snares += drums("....x..o....x.o.", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.52),
        part(snap_snare, snares, 0.4, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2", "verse2"), "....x.......x...")]), 0.28, 0.0, 0.15),
        part(tick, drum_parts(form, [(("verse", "pre", "intro"), "x.oxx.o.x.oxx.o."), (("chorus", "chorus2", "verse2"), "xoxoxoxoxoxoxoxo")]), 0.2, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2", "pre"), "..x...x...x...x.")]), 0.18, -0.3),
        part(anvil, drum_parts(form, [(("verse", "verse2", "intro"), "..............x."),
                                      (("chorus", "chorus2"), "......x.......x.")]), 0.22, 0.3, 0.15),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.25, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.33, 0.0, 0.1),
        part(slap_bass, in_sections(form, ("verse", "verse2", "intro"), lambda at, c: bassline(c, "r..o.rr.r.o..5o.", 2, at))
             + in_sections(form, ("chorus", "chorus2"), lambda at, c: bassline(c, "r.o.r.oor.o.r.o5", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.55, 0.0, 0.0, 0.0, 0.35),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.32, 0.0, 0.3, 0.0, 0.5),
        part(clavinet, in_sections(form, ("verse", "verse2", "pre", "chorus", "chorus2"), lambda at, c: comp(c, "x.xx..x.x.xx..x.", 4, at)),
             0.2, 0.35, 0.08),
        part(brass, in_sections(form, ("chorus", "chorus2"), lambda at, c: comp(c, "x..x..x.....x...", 4, at)), 0.22, -0.25, 0.2),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.4, 0.1, 0.2, 0.2),
        part(clavinet, hooks + teaser, 0.62, -0.05, 0.12, 0.12),
        part(super_lead, octave(hooks, 1), 0.26, 0.0, 0.25, 0.15),
        part(brass, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), -1), 0.2, 0.2, 0.2),
        part(chime, octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("F#6:4 D#6:4 B5:8"))), at)), 1),
             0.24, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.3)


def pop_race_three():
    """The Gearbox Cup, woods, snow and dunes: bouncy and sunny in A, a banjo
    picking under somebody whistling the hook over the pop beat."""
    bpm = 162
    verse = ["A", "D", "A", "E", "A", "D", "E", "A"]
    pre = ["Bm", "C#m", "D", "E"] * 2
    chorus = ["A", "E", "F#m", "D", "A", "E", "D", "E"]
    form, chords = song(("intro", ["A", "E", "D", "E"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["A", "E", "F#m", "E"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "A4:1 .:1 C#5:1 E5:1 .:1 A5:2 E5:1 C#5:2 E5:2 A5:4",
        "F#5:2 .:1 D5:1 F#5:2 A5:2 .:2 F#5:2 D5:4",
        "E5:2 .:1 C#5:1 E5:2 A5:2 .:2 B5:2 C#6:4",
        "B5:3 A5:3 G#5:2 E5:8",
        "A4:1 .:1 C#5:1 E5:1 .:1 A5:2 E5:1 C#5:2 E5:2 A5:4",
        "F#5:2 .:1 D5:1 F#5:2 A5:2 .:2 F#5:2 D5:4",
        "G#5:2 .:1 E5:1 G#5:2 B5:2 .:2 D6:2 B5:4",
        "C#6:3 B5:3 A5:2 E5:8",
    )
    b = bars(
        "B4:2 D5:2 F#5:2 B5:2 .:2 A5:2 F#5:4",
        "C#5:2 E5:2 G#5:2 C#6:2 .:2 B5:2 G#5:4",
        "D5:2 F#5:2 A5:2 D6:2 .:2 C#6:2 A5:4",
        "E5:2 G#5:2 B5:2 E6:2 .:2 D6:2 B5:4",
        "D6:3 C#6:3 B5:2 F#5:8",
        "E6:3 C#6:3 G#5:2 C#6:8",
        "F#6:3 E6:3 D6:2 A5:4 D6:4",
        "B5:4 D6:4 E6:8",
    )
    hook = bars(
        "E5:3 A5:3 C#6:2 E6:2 C#6:2 A5:2 B5:2",
        "B5:3 G#5:3 E5:2 G#5:2 B5:2 E6:4",
        "F#5:3 A5:3 C#6:2 F#6:2 E6:2 C#6:2 A5:2",
        "D6:6 C#6:2 B5:4 A5:4",
        "E5:3 A5:3 C#6:2 E6:2 C#6:2 A5:2 B5:2",
        "B5:3 G#5:3 E5:2 G#5:2 B5:2 D6:2 E6:2",
        "F#6:2 F#6:1 E6:1 D6:2 F#6:2 .:2 E6:2 D6:2 B5:2",
        "B5:6 G#5:2 E5:4 .:4",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    snares = []
    for name, start, ch in form:
        if name == "pre":
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x...x...x.x.xxxx", 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "verse2", "chorus", "chorus2", "intro"):
            snares += drums("....x.......x..o", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.5),
        part(snap_snare, snares, 0.38, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2", "verse2"), "....x.......x...")]), 0.28, 0.0, 0.15),
        part(tick, drum_parts(form, [(full + ("intro",), "x.o.x.o.x.o.x.o.")]), 0.18, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2"), "..x...x...x...x.")]), 0.2, -0.3),
        part(shaker, drum_parts(form, [(("verse", "verse2", "pre", "break"), "oxoxoxoxoxoxoxox")]), 0.16, -0.35),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.22, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.3, 0.0, 0.1),
        part(pop_bass, in_sections(form, ("verse", "verse2", "intro"), lambda at, c: bassline(c, "r...5...r..r5...", 2, at))
             + in_sections(form, ("chorus", "chorus2"), lambda at, c: bassline(c, "r.o.r.o.r.o.r.o.", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.45),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.3, 0.0, 0.3, 0.0, 0.5),
        part(banjo, in_sections(form, ("verse", "verse2", "chorus", "chorus2", "intro", "pre"), lambda at, c: arps(c, 4, (0, 1, 2, 3, 1, 2, 0, 3), 1, at)),
             0.26, -0.4, 0.12),
        part(brass, in_sections(form, ("chorus2",), lambda at, c: comp(c, "..x...x...x...x.", 4, at)), 0.18, 0.3, 0.2),
        part(banjo, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at)), 0.55, 0.15, 0.15, 0.15),
        part(square_lead, in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.4, 0.1, 0.2, 0.2),
        part(pop_whistle, hooks + teaser, 0.62, 0.05, 0.22, 0.15),
        part(banjo, hooks, 0.3, 0.3, 0.12),
        part(super_lead, octave(hooks, -1), 0.18, 0.0, 0.2),
        part(pop_whistle, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), -1), 0.3, -0.25, 0.25, 0.1),
        part(chime, octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("E6:4 B5:4 G#5:8"))), at)), 1),
             0.22, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.4)


def pop_race_four():
    """The Keystone Cup, launchpads, lava and castles: big and dramatic in C
    minor, the hook on brass with timpani under it and a choir behind."""
    bpm = 140
    verse = ["Cm", "Ab", "Eb", "Bb", "Cm", "Ab", "Fm", "G"]
    pre = ["Fm", "Gm", "Ab", "Bb"] * 2
    chorus = ["Cm", "Ab", "Eb", "Bb", "Cm", "Ab", "Bb", "G"]
    form, chords = song(("intro", ["Cm", "Ab", "Bb", "G"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["Cm", "Ab", "Eb", "G"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "G4:2 .:1 G4:1 C5:2 Eb5:2 .:2 D5:2 C5:4",
        "C5:2 .:1 C5:1 Eb5:2 Ab5:2 .:2 G5:2 Eb5:4",
        "Bb4:2 .:1 Bb4:1 Eb5:2 G5:2 .:2 F5:2 Eb5:4",
        "F5:3 Eb5:3 D5:2 Bb4:8",
        "G5:2 .:1 G5:1 Eb5:2 C5:2 .:2 D5:2 Eb5:4",
        "Ab5:2 .:1 Ab5:1 Eb5:2 C5:2 .:2 Eb5:2 Ab5:4",
        "C6:3 Ab5:3 F5:2 C5:4 F5:4",
        "D5:4 F5:4 G5:4 B4:4",
    )
    b = bars(
        "F5:2 F5:1 Ab5:3 C6:2 .:2 Ab5:2 F5:4",
        "G5:2 G5:1 Bb5:3 D6:2 .:2 Bb5:2 G5:4",
        "Ab5:2 Ab5:1 C6:3 Eb6:2 .:2 C6:2 Ab5:4",
        "Bb5:4 C6:4 D6:4 F6:4",
        "C6:3 Ab5:3 F5:2 C6:4 Ab5:4",
        "D6:3 Bb5:3 G5:2 D6:4 Bb5:4",
        "Eb6:3 C6:3 Ab5:2 Eb6:4 C6:4",
        "Bb5:4 C6:4 D6:8",
    )
    hook = bars(
        "C5:3 G5:3 Eb5:2 C6:4 Bb5:2 G5:2",
        "Ab5:3 G5:3 Eb5:2 C5:6 .:2",
        "Eb5:3 Bb5:3 G5:2 Eb6:4 D6:2 Bb5:2",
        "D6:6 C6:2 Bb5:4 F5:4",
        "C5:3 G5:3 Eb5:2 C6:4 Bb5:2 G5:2",
        "Ab5:3 G5:3 Eb5:2 Ab5:4 C6:4",
        "D6:2 Eb6:2 F6:4 Eb6:2 D6:2 Bb5:4",
        "B5:6 D6:2 .:4 G5:2 B5:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(("chorus", "chorus2", "pre", "intro"), "x...x...x...x..."),
                              (("verse", "verse2"), "x.....x.x.....x.")])
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "chorus", "chorus2", "intro"):
            snares += drums("....x.......x...", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    timps = (in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r-------r-r-----", 2, at))
             + in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "r---------------", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r---------------", 2, at)))
    for name, start, ch in form:
        if name == "pre":
            last = (start + len(ch) - 1) * 16
            root = chord_notes(ch[-1], 2)[0]
            timps += [(last + k, root, 1, 0.4 + 0.04 * k) for k in range(0, 16, 1)]
    parts = [
        part(punch_kick, kicks, 0.52),
        part(snap_snare, snares, 0.4, 0.05, 0.15),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2"), "....x.......x...")]), 0.26, 0.0, 0.2),
        part(tick, drum_parts(form, [(("verse", "pre", "intro"), "x.o.x.o.x.o.x.o."), (("chorus", "chorus2", "verse2"), "xoxoxoxoxoxoxoxo")]), 0.18, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2"), "..x...x...x...x.")]), 0.17, -0.3),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")) + starts(form, ("chorus", "chorus2"), 4), 0.27, 0.0, 0.15),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.33, 0.0, 0.1),
        part(timpani, timps, 0.5, 0.0, 0.25),
        part(pop_bass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r.o.r.o.r.o.r.o.", 2, at))
             + in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "r.rr.rr.r.rr.rr.", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at)), 0.5, 0.0, 0.0, 0.0, 0.45),
        part(choir, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.4, 0.0, 0.35, 0.0, 0.25),
        part(pump_pad, in_sections(form, ("chorus", "chorus2"), lambda at, c: held(c, 3, at)), 0.22, 0.0, 0.3, 0.0, 0.5),
        part(pop_pluck, in_sections(form, ("verse", "verse2", "pre"), lambda at, c: arps(c, 4, (0, 2, 1, 2, 0, 3, 1, 2), 1, at)), 0.18, -0.4, 0.15, 0.25, 0.4),
        part(brass, in_sections(form, ("pre", "chorus", "chorus2"), lambda at, c: comp(c, "x.....x.....x.x.", 3, at)), 0.2, -0.3, 0.2),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.4, 0.1, 0.2, 0.2),
        part(brass, hooks + teaser, 0.48, -0.05, 0.25, 0.12),
        part(super_lead, hooks, 0.3, 0.05, 0.25, 0.15),
        part(choir, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), -1), 0.35, 0.0, 0.3),
        part(chime, in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("D6:4 B5:4 G5:8"))), at)),
             0.26, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.17, level=-12.9)


def pop_race_legends():
    """The Legends Cup, the famous circuits: a proud anthem in E flat, the
    hook on a guitar-ish lead with a stadium clapping along."""
    bpm = 156
    verse = ["Eb", "Bb", "Cm", "Ab", "Eb", "Bb", "Ab", "Bb"]
    pre = ["Ab", "Bb", "Gm", "Cm", "Fm", "Gm", "Ab", "Bb"]
    chorus = ["Eb", "Bb", "Cm", "Ab", "Eb", "Bb", "Ab", "Bb"]
    form, chords = song(("intro", ["Eb", "Bb", "Ab", "Bb"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["Eb", "Bb", "Cm", "Bb"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "G5:2 .:2 G5:2 F5:2 Eb5:2 F5:2 G5:4",
        "F5:2 .:2 F5:2 D5:2 Bb4:2 D5:2 F5:4",
        "G5:2 .:2 G5:2 Bb5:2 C6:2 Bb5:2 G5:4",
        "Ab5:3 G5:3 Eb5:2 C5:8",
        "G5:2 .:2 Bb5:2 G5:2 Eb6:4 D6:2 Bb5:2",
        "F5:2 .:2 Bb5:2 F5:2 D6:4 C6:2 Bb5:2",
        "C6:3 Bb5:3 Ab5:2 Eb5:4 C5:4",
        "D5:4 F5:4 Bb5:8",
    )
    b = bars(
        "C5:2 Eb5:2 Ab5:4 .:2 G5:2 Ab5:4",
        "D5:2 F5:2 Bb5:4 .:2 Ab5:2 Bb5:4",
        "D5:2 G5:2 Bb5:4 .:2 C6:2 D6:4",
        "Eb6:3 D6:3 C6:2 G5:8",
        "C5:2 F5:2 Ab5:4 .:2 G5:2 Ab5:4",
        "Bb5:2 D6:2 G5:4 .:2 F5:2 G5:4",
        "Ab5:3 Bb5:3 C6:2 Eb6:8",
        "D6:4 C6:4 Bb5:4 .:4",
    )
    hook = bars(
        "Bb4:3 Eb5:3 G5:2 Bb5:6 G5:2",
        "Ab5:3 G5:3 F5:2 D5:4 Bb4:4",
        "Bb4:3 Eb5:3 G5:2 C6:6 Bb5:2",
        "Ab5:4 G5:4 Eb5:4 C5:4",
        "Bb4:3 Eb5:3 G5:2 Bb5:6 G5:2",
        "Ab5:3 G5:3 F5:2 Bb5:4 D6:4",
        "Eb6:6 D6:2 C6:4 Ab5:4",
        "Bb5:10 .:2 F5:2 G5:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(("chorus", "chorus2", "pre", "verse2"), "x...x...x...x..."),
                              (("verse", "intro"), "x.x.....x.x.....")])
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("chorus", "chorus2"):
            snares += drums("....x.......x...", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.52),
        part(snap_snare, snares, 0.38, 0.05, 0.12),
        part(stadium_clap, drum_parts(form, [(("intro", "verse", "chorus", "chorus2", "verse2"), "....x.......x...")]), 0.5, 0.0, 0.2),
        part(tick, drum_parts(form, [(("verse", "pre", "intro"), "x.o.x.o.x.o.x.o."), (("chorus", "chorus2", "verse2"), "xoxoxoxoxoxoxoxo")]), 0.18, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2", "pre"), "..x...x...x...x.")]), 0.18, -0.3),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")) + starts(form, ("chorus", "chorus2"), 4), 0.25, 0.0, 0.12),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.33, 0.0, 0.1),
        part(pop_bass, in_sections(form, ("chorus", "chorus2"), lambda at, c: bassline(c, "r.o.r.o.r.o.r.o.", 2, at))
             + in_sections(form, ("verse", "verse2", "intro"), lambda at, c: bassline(c, "r-r-r-r-r-r-r-5-", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "rrrrrrrrrrrrrrrr", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.45),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.36, 0.0, 0.3, 0.0, 0.5),
        part(pop_pluck, in_sections(form, ("verse", "verse2"), lambda at, c: arps(c, 4, (0, 1, 2, 3, 2, 1), 2, at)), 0.18, -0.4, 0.15, 0.25, 0.4),
        part(brass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: comp(c, "x.......x..x....", 4, at))
             + in_sections(form, ("pre",), lambda at, c: comp(c, "x.....x.....x...", 4, at)), 0.24, -0.25, 0.2),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.4, 0.1, 0.2, 0.2),
        part(anthem_guitar, hooks + teaser, 0.6, -0.05, 0.22, 0.18),
        part(super_lead, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1), 0.24, 0.1, 0.25, 0.15),
        part(super_lead, in_sections(form, ("chorus",), lambda at, _c: shift(melody(16, *hook), at)), 0.18, 0.1, 0.2),
        part(chime, octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("Bb5:4 F5:4 D5:8"))), at)), 1),
             0.24, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.3)


def pop_race_rally():
    """The Gravel Cup: rocky and driving in E, power chord chugs under a
    supersaw hook, with tom fills rolling into each section."""
    bpm = 146
    verse = ["E", "D", "A", "E", "E", "D", "A", "B"]
    pre = ["F#m", "G#m", "A", "B"] * 2
    chorus = ["A", "B", "E", "C#m", "A", "B", "E", "E"]
    form, chords = song(("intro", ["A", "B", "E", "E"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["A", "B", "C#m", "B"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "B4:2 .:1 B4:1 E5:2 G#5:2 .:2 F#5:2 E5:4",
        "D5:2 .:1 D5:1 F#5:2 A5:2 .:2 F#5:2 D5:4",
        "C#5:2 .:1 E5:1 A5:2 C#6:2 .:2 B5:2 A5:4",
        "B5:3 G#5:3 E5:2 B4:8",
        "G#5:2 .:1 G#5:1 B5:2 E6:2 .:2 D6:2 B5:4",
        "A5:2 .:1 F#5:1 A5:2 D6:2 .:2 C#6:2 A5:4",
        "C#6:3 B5:3 A5:2 E5:4 C#5:4",
        "D#5:4 F#5:4 A5:4 B5:4",
    )
    b = bars(
        "F#5:2 A5:2 C#6:4 .:2 A5:2 F#5:4",
        "G#5:2 B5:2 D#6:4 .:2 B5:2 G#5:4",
        "A5:2 C#6:2 E6:4 .:2 C#6:2 A5:4",
        "B5:4 C#6:4 D#6:4 F#6:4",
        "C#6:3 A5:3 F#5:2 C#6:4 A5:4",
        "D#6:3 B5:3 G#5:2 D#6:4 B5:4",
        "E6:3 C#6:3 A5:2 E6:4 C#6:4",
        "D#6:4 E6:4 F#6:8",
    )
    hook = bars(
        "E5:3 A5:3 B5:2 C#6:4 B5:2 A5:2",
        "B5:3 A5:3 F#5:2 D#5:4 F#5:4",
        "E5:3 G#5:3 B5:2 E6:4 D#6:2 B5:2",
        "C#6:6 B5:2 G#5:4 E5:4",
        "E5:3 A5:3 B5:2 C#6:4 B5:2 A5:2",
        "B5:3 A5:3 F#5:2 B5:4 D#6:4",
        "E6:3 D#6:3 B5:2 G#5:3 F#5:3 E5:2",
        "E5:8 .:4 B4:2 D#5:2",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(("chorus", "chorus2", "pre", "intro"), "x...x...x...x..."),
                              (("verse", "verse2"), "x..x..x.x.x...x.")])
    snares = []
    toms = []
    for name, start, ch in form:
        last = (start + len(ch) - 1) * 16
        if name == "pre":
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, last)
        elif name in ("verse", "verse2", "chorus"):
            # A roll down the toms over the last half bar.
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("....x...", 1, last)
            toms += [(last + k, f, 1, 0.6 + 0.05 * i) for i, (k, f) in enumerate(
                [(8, 220.0), (9, 220.0), (10, 185.0), (11, 185.0), (12, 147.0), (13, 147.0), (14, 110.0), (15, 110.0)])]
        elif name in ("chorus2", "intro"):
            snares += drums("....x.......x...", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.52),
        part(snap_snare, snares, 0.42, 0.05, 0.12),
        part(tom, toms, 0.45, -0.1, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2"), "....x.......x...")]), 0.24, 0.0, 0.15),
        part(tick, drum_parts(form, [(("verse", "verse2", "pre", "intro"), "x.x.x.x.x.x.x.x.")]), 0.2, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2"), "x.x.x.x.x.x.x.x.")]), 0.15, -0.3),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")) + starts(form, ("chorus", "chorus2"), 4), 0.22, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.33, 0.0, 0.1),
        part(pop_bass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r.r.r.r.r.r.r.o.", 2, at))
             + in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "r.rr.rr.r.rr.r..", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "rrrrrrrrrrrrrrrr", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.35),
        part(chug, in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "rrr.rrr.rrr.r-r-", 3, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-r-r-", 3, at))
             + in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r-----r-r-----r-", 3, at)), 0.42, 0.0, 0.05),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.26, 0.0, 0.3, 0.0, 0.5),
        part(pop_pluck, in_sections(form, ("break",), lambda at, c: arps(c, 4, (0, 1, 2, 3, 2, 1, 0, 2), 1, at)), 0.18, -0.4, 0.15, 0.25, 0.4),
        part(brass, teaser + in_sections(form, ("chorus2",), lambda at, c: comp(c, "x..x..x.....x...", 4, at)), 0.3, -0.2, 0.2),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.4, 0.1, 0.2, 0.2),
        part(super_lead, hooks, 0.5, 0.0, 0.25, 0.15),
        part(super_lead, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1), 0.15, 0.1, 0.25, 0.15),
        part(chime, octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("C#6:4 B5:4 D#6:8"))), at)), 1),
             0.22, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.14, level=-13.0)


def pop_race_indoor():
    """The Hangar Cup, a neon hall: tight and electronic in B minor, a robot
    singing the hook over sixteenth arps, everything pumping with the kick."""
    bpm = 154
    verse = ["Bm", "G", "D", "A"] * 2
    pre = ["Em", "F#m", "G", "A"] * 2
    chorus = ["G", "A", "F#m", "Bm", "G", "A", "Bm", "F#"]
    form, chords = song(("intro", ["G", "A", "Bm", "F#"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["G", "A", "Bm", "A"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "F#5:2 .:1 F#5:1 D5:2 B4:2 .:2 D5:2 F#5:4",
        "G5:2 .:1 G5:1 D5:2 B4:2 .:2 D5:2 G5:4",
        "A5:2 .:1 A5:1 F#5:2 D5:2 .:2 F#5:2 A5:4",
        "G5:3 F#5:3 E5:2 C#5:8",
        "F#5:2 .:1 F#5:1 B5:2 F#5:2 .:2 E5:2 D5:4",
        "D5:2 .:1 D5:1 G5:2 D5:2 .:2 B4:2 D5:4",
        "F#5:3 E5:3 D5:2 A4:4 D5:4",
        "E5:4 C#5:4 E5:4 A5:4",
    )
    b = bars(
        "E5:2 G5:2 B5:4 .:2 G5:2 E5:4",
        "F#5:2 A5:2 C#6:4 .:2 A5:2 F#5:4",
        "G5:2 B5:2 D6:4 .:2 B5:2 G5:4",
        "A5:4 B5:4 C#6:4 E6:4",
        "B5:3 G5:3 E5:2 B5:4 G5:4",
        "C#6:3 A5:3 F#5:2 C#6:4 A5:4",
        "D6:3 B5:3 G5:2 D6:4 B5:4",
        "C#6:4 D6:4 E6:8",
    )
    # The robot's hook stays under C6.
    hook = bars(
        "B4:3 D5:3 G5:2 F#5:2 E5:2 D5:4",
        "C#5:3 E5:3 A5:2 G5:2 F#5:2 E5:4",
        "C#5:3 F#5:3 A5:2 C#5:2 F#5:2 A5:2 B5:2",
        "B5:6 A5:2 F#5:4 D5:4",
        "B4:3 D5:3 G5:2 F#5:2 E5:2 D5:4",
        "C#5:3 E5:3 A5:2 B5:2 A5:2 E5:4",
        "F#5:3 D5:3 B4:2 D5:3 E5:3 F#5:2",
        "F#5:6 E5:2 C#5:4 A#4:4",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("chorus", "chorus2"):
            snares += drums("....x.......x...", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.55),
        part(snap_snare, snares, 0.34, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(full + ("intro",), "....x.......x...")]), 0.32, 0.0, 0.15),
        part(tick, drum_parts(form, [(full + ("intro", "break"), "xoxxxoxxxoxxxoxx")]), 0.14, 0.35),
        part(open_hat, drum_parts(form, [(full, "..x...x...x...x.")]), 0.2, -0.3),
        part(shaker, drum_parts(form, [(("chorus", "chorus2", "break"), "oxoxoxoxoxoxoxox")]), 0.12, -0.4),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.22, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.35, 0.0, 0.1),
        part(pop_bass, in_sections(form, ("chorus", "chorus2", "intro"), lambda at, c: bassline(c, ".rro.rro.rro.rro", 2, at))
             + in_sections(form, ("verse", "verse2"), lambda at, c: bassline(c, "..r...r...r..5r.", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, ".r.r.r.r.r.r.o.o", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.55, 0.0, 0.0, 0.0, 0.8),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break", "verse2"), lambda at, c: held(c, 3, at)), 0.42, 0.0, 0.3, 0.0, 0.85),
        part(pop_pluck, in_sections(form, full + ("intro",), lambda at, c: arps(c, 4, (0, 1, 2, 3, 1, 2, 3, 2), 1, at)), 0.2, -0.4, 0.12, 0.3, 0.7),
        part(pop_pluck, in_sections(form, ("chorus", "chorus2", "break"), lambda at, c: arps(c, 5, (2, 1, 0, 1), 2, at)), 0.12, 0.45, 0.15, 0.3, 0.7),
        part(brass, in_sections(form, ("chorus2",), lambda at, c: comp(c, "x..x..x.....x...", 4, at)), 0.2, -0.2, 0.2, 0.0, 0.4),
        part(square_lead, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at))
             + in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.38, 0.1, 0.2, 0.25),
        part(vocoder_lead, hooks + teaser, 0.6, 0.0, 0.2, 0.15),
        part(super_lead, octave(hooks, -1), 0.16, 0.0, 0.2, 0.0, 0.3),
        part(chime, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1)
             + octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("A5:4 F#5:4 C#5:8"))), at)), 1),
             0.2, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.13, level=-12.5)


def pop_race_coaster():
    """The Corkscrew Cup: a fairground in B flat, a calliope on the hook and a
    band organ oom-pahing over the pop beat, with silly runs up and down."""
    bpm = 165
    verse = ["Bb", "Gm", "Eb", "F"] * 2
    pre = ["Cm", "Dm", "Eb", "F"] * 2
    chorus = ["Eb", "F", "Bb", "Gm", "Eb", "F", "Bb", "F7"]
    form, chords = song(("intro", ["Eb", "F", "Bb", "F7"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["Eb", "F", "Gm", "F"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "F5:2 .:1 D5:1 F5:2 Bb5:2 .:2 A5:2 Bb5:4",
        "D5:2 .:1 Bb4:1 D5:2 G5:2 .:2 F5:2 D5:4",
        "Eb5:2 .:1 G5:1 Bb5:2 Eb6:2 .:2 D6:2 Bb5:4",
        "C6:1 Bb5:1 A5:1 G5:1 F5:4 C5:8",
        "F5:2 .:1 D5:1 F5:2 Bb5:2 .:2 C6:2 D6:4",
        "Bb5:2 .:1 G5:1 Bb5:2 D6:2 .:2 C6:2 Bb5:4",
        "G5:3 Bb5:3 Eb6:2 D6:2 C6:2 Bb5:2 G5:2",
        "A5:2 Bb5:1 B5:1 C6:4 F5:4 A5:4",
    )
    b = bars(
        "C5:2 Eb5:2 G5:4 .:2 Eb5:2 C5:4",
        "D5:2 F5:2 A5:4 .:2 F5:2 D5:4",
        "Eb5:2 G5:2 Bb5:4 .:2 G5:2 Eb5:4",
        "F5:2 G5:2 A5:2 Bb5:2 C6:4 A5:4",
        "G5:3 Eb5:3 C5:2 G5:4 Eb5:4",
        "A5:3 F5:3 D5:2 A5:4 F5:4",
        "Bb5:3 G5:3 Eb5:2 Bb5:4 G5:4",
        "C6:1 D6:1 C6:1 D6:1 C6:1 D6:1 Eb6:1 E6:1 F6:8",
    )
    hook = bars(
        "G5:3 Bb5:3 Eb6:2 D6:1 Eb6:1 D6:1 C6:1 Bb5:4",
        "A5:3 C6:3 F6:2 Eb6:2 C6:2 A5:4",
        "Bb5:3 D6:3 F6:2 D6:2 Bb5:2 F5:4",
        "G5:2 A5:1 Bb5:1 C6:1 D6:1 Eb6:1 E6:1 F6:4 D6:4",
        "G5:3 Bb5:3 Eb6:2 D6:1 Eb6:1 D6:1 C6:1 Bb5:4",
        "A5:3 C6:3 F6:2 G6:2 F6:2 C6:4",
        "D6:3 C6:3 Bb5:2 F5:3 G5:3 A5:2",
        "Bb5:6 .:2 F5:1 E5:1 Eb5:1 D5:1 Db5:1 C5:1 B4:1 Bb4:1",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    snares = []
    for name, start, ch in form:
        if name in ("pre", "verse2"):
            snares += drums("....x.......x...", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "chorus", "chorus2", "intro"):
            snares += drums("....x.......x..o", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.5),
        part(snap_snare, snares, 0.38, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2", "verse2"), "....x.......x...")]), 0.28, 0.0, 0.15),
        part(tick, drum_parts(form, [(full + ("intro",), "x.o.x.o.x.o.x.o.")]), 0.18, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2"), "..x...x...x...x.")]), 0.18, -0.3),
        part(cowbell, drum_parts(form, [(("chorus", "chorus2"), "x.......x.......")]), 0.14, 0.4, 0.05),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.24, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.32, 0.0, 0.1),
        # Oom-pah: the bass on the beats, the organ on the offbeats.
        part(pop_bass, in_sections(form, ("verse", "verse2", "chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r...5...r...5.o.", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.4),
        part(fair_organ, in_sections(form, full + ("intro",), lambda at, c: comp(c, "..x...x...x...x.", 4, at)), 0.2, -0.35, 0.12),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.26, 0.0, 0.3, 0.0, 0.5),
        part(chime, in_sections(form, ("verse", "verse2"), lambda at, c: arps(c, 5, (0, 1, 2, 3, 2, 1), 2, at)), 0.12, 0.4, 0.2, 0.2),
        part(brass, in_sections(form, ("chorus2",), lambda at, c: comp(c, "x..x..x.....x...", 4, at)), 0.18, 0.25, 0.2),
        part(fair_organ, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at)), 0.5, 0.1, 0.18, 0.15),
        part(square_lead, in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.38, 0.1, 0.2, 0.2),
        part(calliope, hooks + teaser, 0.62, 0.0, 0.22, 0.15),
        part(fair_organ, octave(hooks, -1), 0.3, -0.15, 0.15),
        part(super_lead, octave(hooks, -1), 0.14, 0.0, 0.2),
        part(calliope, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1), 0.22, 0.25, 0.25, 0.1),
        part(chime, octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("C6:4 A5:4 F5:8"))), at)), 1),
             0.22, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.6)


def pop_race_alpine():
    """The Alpine Cup: a polka bounce in C, accordion oom-pahs and cowbells,
    and a yodel on the hook leaping up from the chest into a light high
    voice, kept under C6."""
    bpm = 160
    verse = ["C", "G", "G7", "C", "C", "F", "G", "C"]
    pre = ["Dm", "Em", "F", "G"] * 2
    chorus = ["F", "G", "C", "Am", "F", "G", "C", "G"]
    form, chords = song(("intro", ["F", "G", "C", "G"]), ("verse", verse), ("pre", pre), ("chorus", chorus),
                        ("break", ["F", "G", "Am", "G"]), ("verse2", verse), ("chorus2", chorus))
    a = bars(
        "E5:2 G5:2 E5:2 C5:2 E5:2 G5:2 C6:4",
        "B4:2 D5:2 G5:2 D5:2 B4:2 D5:2 G5:4",
        "F5:2 .:1 F5:1 D5:2 B4:2 .:2 D5:2 F5:4",
        "E5:3 D5:3 C5:2 G4:8",
        "E5:2 G5:2 C6:2 G5:2 E5:2 G5:2 C6:4",
        "C6:2 A5:2 F5:2 A5:2 C6:2 D6:2 C6:4",
        "B5:3 A5:3 G5:2 D5:4 B4:4",
        "C5:4 E5:4 G5:4 .:4",
    )
    b = bars(
        "D5:2 F5:2 A5:4 .:2 F5:2 D5:4",
        "E5:2 G5:2 B5:4 .:2 G5:2 E5:4",
        "F5:2 A5:2 C6:4 .:2 A5:2 F5:4",
        "G5:4 A5:4 B5:4 D6:4",
        "A5:3 F5:3 D5:2 A5:4 F5:4",
        "B5:3 G5:3 E5:2 B5:4 G5:4",
        "C6:3 A5:3 F5:2 C6:4 A5:4",
        "B5:4 C6:4 D6:8",
    )
    # Each bar leaps from a low chest note up into the light voice.
    hook = bars(
        "A4:3 F5:3 A5:2 C5:2 A5:2 G5:2 F5:2",
        "G4:3 D5:3 B5:2 G5:4 D5:4",
        "G4:3 E5:3 G5:2 C5:2 E5:2 G5:4",
        "A5:6 G5:2 E5:4 A4:4",
        "A4:3 F5:3 A5:2 C5:2 A5:2 G5:2 F5:2",
        "G4:3 D5:3 B5:2 A5:2 G5:2 D5:4",
        "E5:3 G5:3 C5:2 G4:3 C5:3 E5:2",
        "D5:6 B4:2 G4:4 .:4",
    )
    bar_count = len(chords)
    full = ("verse", "pre", "chorus", "verse2", "chorus2")
    kicks = drum_parts(form, [(full + ("intro",), "x...x...x...x...")])
    snares = []
    for name, start, ch in form:
        if name == "pre":
            snares += drums("..o...o...o...o.", len(ch) - 1, start * 16) + drums("x.x.x.x.xxxxXXXX", 1, (start + len(ch) - 1) * 16)
        elif name in ("verse", "verse2", "chorus", "chorus2", "intro"):
            snares += drums("..o...o...o...o.", len(ch), start * 16)
    hooks = in_sections(form, ("chorus", "chorus2"), lambda at, _c: shift(melody(16, *hook), at))
    teaser = in_sections(form, ("intro",), lambda at, _c: shift(melody(16, *[hook[0], hook[1], hook[6], hook[7]]), at))
    parts = [
        part(punch_kick, kicks, 0.5),
        part(snap_snare, snares, 0.36, 0.05, 0.12),
        part(pop_clap, drum_parts(form, [(("chorus", "chorus2", "verse2"), "....x.......x...")]), 0.28, 0.0, 0.15),
        part(tick, drum_parts(form, [(full + ("intro",), "x.o.x.o.x.o.x.o.")]), 0.16, 0.35),
        part(open_hat, drum_parts(form, [(("chorus", "chorus2"), "..x...x...x...x.")]), 0.16, -0.3),
        part(cowbell, drum_parts(form, [(("chorus", "chorus2"), "x.x.x.x.x.x.x.x."), (("verse", "verse2", "intro"), "x...x...x...x...")]),
             0.17, 0.4, 0.08),
        part(crash, starts(form, ("intro", "verse", "chorus", "verse2", "chorus2")), 0.22, 0.0, 0.1),
        part(riser, [(n[0], 0.0, 32) for n in starts(form, ("break",), -2)]
             + [(n[0], 0.0, 16) for n in starts(form, ("pre",), -1)], 0.3, 0.0, 0.1),
        # Oom-pah: root and fifth on the beats, the accordion on the offbeats.
        part(pop_bass, in_sections(form, ("verse", "verse2", "chorus", "chorus2", "intro"), lambda at, c: bassline(c, "r...5...r...5...", 2, at))
             + in_sections(form, ("pre",), lambda at, c: bassline(c, "r-r-r-r-r-r-o-o-", 2, at))
             + in_sections(form, ("break",), lambda at, c: bassline(c, "r-------5-------", 2, at)), 0.52, 0.0, 0.0, 0.0, 0.35),
        part(pop_accordion, in_sections(form, full + ("intro",), lambda at, c: comp(c, "..x...x...x...x.", 4, at)), 0.23, -0.3, 0.1),
        part(pump_pad, in_sections(form, ("pre", "chorus", "chorus2", "break"), lambda at, c: held(c, 3, at)), 0.26, 0.0, 0.3, 0.0, 0.5),
        part(brass, in_sections(form, ("chorus2",), lambda at, c: comp(c, "x.....x.x.......", 4, at)), 0.18, 0.25, 0.2),
        part(pop_accordion, in_sections(form, ("verse", "verse2"), lambda at, _c: shift(melody(16, *a), at)), 0.6, 0.1, 0.15, 0.12),
        part(square_lead, in_sections(form, ("pre",), lambda at, _c: shift(melody(16, *b), at)), 0.38, 0.1, 0.2, 0.2),
        part(yodel, hooks + teaser, 0.62, 0.0, 0.22, 0.15),
        part(pop_accordion, hooks, 0.3, -0.2, 0.12),
        part(super_lead, octave(hooks, -1), 0.14, 0.0, 0.2),
        part(chime, octave(in_sections(form, ("chorus2",), lambda at, _c: shift(melody(16, *hook), at)), 1)
             + octave(in_sections(form, ("break",), lambda at, _c: shift(melody(16, *(hook[:3] + bars("A5:4 E5:4 G5:8"))), at)), 1),
             0.2, 0.25, 0.35, 0.2),
    ]
    return render_pop(bpm, bar_count, parts, kicks, wet=0.15, level=-13.0)


# The tunes in the new style.
POP = {"menu": pop_menu, "race_one": pop_race_one, "race_beach": pop_race_beach, "race_two": pop_race_two,
       "race_three": pop_race_three, "race_four": pop_race_four, "race_legends": pop_race_legends,
       "race_rally": pop_race_rally, "race_indoor": pop_race_indoor, "race_coaster": pop_race_coaster,
       "race_alpine": pop_race_alpine}


TUNES = {"menu": pop_menu, "race_one": pop_race_one, "race_two": pop_race_two, "race_three": pop_race_three,
         "race_four": pop_race_four, "race_indoor": race_indoor, "race_rally": race_rally, "race_coaster": race_coaster,
         "race_legends": pop_race_legends,
         "race_beach": pop_race_beach, "race_alpine": race_alpine, "race_canyon": race_canyon,
         "race_jungle": race_jungle, "race_city": race_city, "race_sky": race_sky}
