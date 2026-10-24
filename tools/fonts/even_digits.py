"""Makes a copy of Chakra Petch Bold with every digit the same width,
for clocks that don't jiggle. The font has no tnum feature, and the phone's
text server can't use one anyway.

    uv run --with fonttools python tools/fonts/even_digits.py
"""
from pathlib import Path

from fontTools.ttLib import TTFont

FOLDER = Path(__file__).resolve().parents[2] / "art/fonts/chakra_petch"
SOURCE = FOLDER / "ChakraPetch-Bold.ttf"
OUT = FOLDER / "ChakraPetch-Bold-EvenDigits.ttf"

font = TTFont(SOURCE)
cmap = font.getBestCmap()
digits = [cmap[ord(c)] for c in "0123456789"]
hmtx = font["hmtx"]
glyf = font["glyf"]
wide = max(hmtx[name][0] for name in digits)
for name in digits:
    advance, lsb = hmtx[name]
    # Centre the glyph in the wider cell.
    shift = (wide - advance) // 2
    glyph = glyf[name]
    if glyph.numberOfContours > 0:
        glyph.coordinates.translate((shift, 0))
        glyph.recalcBounds(glyf)
    hmtx[name] = (wide, lsb + shift)
# Kerning would undo the even widths. That drops the kerning between letters
# too, which is fine as only the clock uses this copy.
if "GPOS" in font:
    del font["GPOS"]
for record in font["name"].names:
    if record.nameID in (1, 4, 16):
        record.string = record.toUnicode().replace("Chakra Petch", "Chakra Petch Even Digits")
    elif record.nameID in (3, 6):
        record.string = record.toUnicode().replace("ChakraPetch", "ChakraPetchEvenDigits")
font.save(OUT)
print("saved", OUT, "digits", wide, "wide")
