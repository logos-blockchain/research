"""Compose the drinking-game version.

Reuses the CSS and script of the layman deck verbatim — only the slide bodies and
the drinker graphics are new.

The chain is a row of people taking a turn to drink, one at a time. Two of them
drink at the same moment; only one reaches the tally, so the alcohol counted comes
up short. A later drinker vouches for the one that was missed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/talk.template.html", encoding="utf-8").read()

OPEN_DECK = '<div class="deck">\n<div class="stage" id="stage">\n\n'
FOOT = '<div class="foot">'
if OPEN_DECK not in src or FOOT not in src:
    sys.exit("split markers moved")

head = src[: src.index(OPEN_DECK)]
tail = src[src.index(FOOT):]

# These two scenes were paced for a slow reveal; halve it. GAP is the random
# gap in seconds between one drinker and the next, and the two trailing beats
# (the vouch arc, then the counted figure) come in proportionally sooner.
tail = tail.replace("var GAP = [1, 3];", "var GAP = [0.5, 1.5];", 1)
tail = tail.replace('"draw .8s ease "', '"draw .6s ease "', 1)
if "[0.5, 1.5]" not in tail:
    sys.exit("pacing hook missed")

head = head.replace("<title>Total Stake Inference</title>",
                    "<title>Total Beer Inference</title>", 1)

EXTRA_CSS = """
/* ─── the warning card ──────────────────────
   Styled like a real bottle warning: heavy rule, shouted lead-in, numbered
   clauses. The joke is the content, not the design. */
.warning{
  border:3px solid var(--warn);padding:calc(4.4*var(--u)) calc(5*var(--u));
  display:flex;flex-direction:column;gap:calc(2*var(--u));max-width:calc(118*var(--u));
}
.warning h2{
  margin:0;font-family:var(--display);font-weight:700;font-size:calc(3.1*var(--u));
  letter-spacing:.16em;text-transform:uppercase;color:var(--warn);
}
.warning .sub{margin:calc(-1.2*var(--u)) 0 0;font-family:var(--mono);color:var(--warn);opacity:.75}
.warning ol{
  margin:calc(.6*var(--u)) 0 0;padding:0;list-style:none;counter-reset:w;
  display:flex;flex-direction:column;gap:calc(1.5*var(--u));
}
.warning li{
  position:relative;padding-left:calc(4.6*var(--u));counter-increment:w;
  font-size:calc(2.4*var(--u));max-width:58ch;
}
.warning li::before{
  content:"(" counter(w) ")";position:absolute;left:0;top:0;
  font-family:var(--mono);font-size:.86em;color:var(--warn);
}
"""
head = head.replace("\n/* ─── the load console", EXTRA_CSS + "\n/* ─── the load console", 1)

SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <symbol id="drinker" viewBox="0 0 48 100" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="22" cy="13" r="8.5"/>
    <path d="M22,22 V58"/>
    <path d="M22,31 L34,19"/>
    <path d="M22,31 L12,44"/>
    <path d="M22,58 L13,90"/>
    <path d="M22,58 L31,90"/>
    <path d="M30,4 h12 l-2,15 h-8 Z"/>
    <path d="M31.3,9.5 h9.4"/>
  </symbol>
</svg>

"""


def person(x, colour, width="2"):
    return ('<use href="#drinker" x="%d" y="55" width="60" height="125" '
            'stroke="%s" stroke-width="%s"/>' % (x, colour, width))


XS = [55, 215, 375, 605, 765]      # the turns that reach the tally
MISSED_X = 445                      # drinks at the same moment as the third

TURNS = "\n".join(
    '      <g class="sc" data-seq="%d">%s</g>' % (i, person(x, "var(--ink)"))
    for i, x in enumerate(XS))

ORPHAN = ('      <g class="s-orphan" data-with="2" data-dim="3">%s</g>'
          % person(MISSED_X, "var(--warn)"))

RESCUE = '''      <path class="s-line" data-after="0.4" pathLength="1" d="M600 40 C556 16 506 16 478 44"
            fill="none" stroke="var(--accent)" stroke-width="2.5"/>
      <g class="s-saved" data-after="0.9">
        %s
        <text x="475" y="208" text-anchor="middle" font-family="var(--mono)" font-size="15"
              fill="var(--accent)">counted</text>
        <text x="638" y="30" font-family="var(--mono)" font-size="15"
              fill="var(--accent)">vouched for</text>
      </g>''' % person(MISSED_X, "var(--accent)", "2.5")

SCENE_TOP = '''    <svg viewBox="0 0 880 220" aria-label="%s">
      <path d="M20 180 H860" stroke="var(--rule)" stroke-width="2" stroke-dasharray="5 6"/>
%s'''


def scene(label, rescue):
    body = TURNS + "\n" + ORPHAN + ("\n" + RESCUE if rescue else "")
    return '  <div class="scene">\n' + (SCENE_TOP % (label, body)) + "\n    </svg>\n  </div>"


SLIDES = open(HERE + "/drinking_slides.html", encoding="utf-8").read()
SLIDES = SLIDES.replace("@@SCENE_DISCARD@@", scene(
    "A row of people taking turns to drink a beer; two drink at the same moment and one of the two "
    "beers is never written on the tally", False))
SLIDES = SLIDES.replace("@@SCENE_RESCUE@@", scene(
    "A later drinker vouches for the beer that missed the tally, and it is counted after all", True))

out = head + OPEN_DECK + SPRITE + SLIDES + tail
open(HERE + "/drinking.template.html", "w", encoding="utf-8").write(out)
print("composed drinking.template.html  (%d slides)" % out.count('<section class="slide'))
