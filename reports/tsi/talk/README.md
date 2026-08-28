# Total Beer Inference — talks and a pub game

Two presentations of [the TSI report](../README.md), and a drinking game that reproduces its
headline number on a pub table.

Everything here is a **single self-contained HTML file**. Open it from disk — no server, no build
step, no network. The report's own figures are inlined as data URIs.

| file | what it is |
| --- | --- |
| [`tsi-talk.html`](tsi-talk.html) | the talk, in plain English. 16 slides, no prior knowledge assumed. |
| [`tsi-drinking-game.html`](tsi-drinking-game.html) | the same material as a drinking game. 20 slides. |
| [`beer-game-rules.html`](beer-game-rules.html) | one printable page of rules for the game itself. |

## Presenting

`→` `space` next · `←` back · `N` speaker notes · `T` light/dark for the room ·
`F` fullscreen · `P` export a PDF, one 16:9 slide per page · `?` the key map.

Every slide carries speaker notes. The slides are deliberately sparse; the notes hold the numbers,
the caveats and the answers to the questions that get asked.

## Memes and clips

Four slots take your own media. Drop files into [`assets/`](assets) named `1`, `2`, `3`, `4` — any
of `mp4 webm mov m4v gif png jpg jpeg webp avif`, video tried first. **A slot with no file removes
its own slide**, so the decks present cleanly whether you fill none of them or all four.

Meme captions are the `data-top` and `data-bottom` attributes on the media slides; search a deck for
`data-media` to find them. Leave both empty for a plain clip.

## The game

`beer-game-rules.html` holds two games on one page.

The **circle** is the simple one: one die each, one bottle cap each, secret limits, drink when you
roll above yours and pass a cap to your right. The twist is that the caps make everyone drink at
exactly the same rate — over 4 000 simulated rounds, limits 1 through 5 drank 165/165/164/164/164 —
so sips tell you nothing and the tell is who is never holding a cap. That is a bottleneck game, not
an inference one.

The **vouching** variant is the one the talk is about. Six is loud, one is quiet; a quiet sip that
nobody covers costs the Barman a round, and the pile of caps in the middle is their error. With five
at the table the mat comes out at **0.69** of the truth, against the simulator's **0.64–0.74**.
Vouching empties the pile.

## Building

The HTML in this directory is committed and ready to use. Rebuild only if you edit the sources:

```sh
cd src && python3 build.py      # needs Pillow
```

`src/talk.template.html` is the layman deck. `src/drinking_slides.html` holds only the beer deck's
slide bodies; `src/make_drinking.py` grafts them onto the layman deck's CSS and script so the two
never drift apart. `build.py` crops the figures out of `../report-figures`, runs the composer and
inlines everything.

`src/.figs/` and `src/drinking.template.html` are derived and not committed.
