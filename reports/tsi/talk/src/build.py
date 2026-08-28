"""Build both decks from source.

    python3 build.py

Reads the report's own figures from ../../report-figures, downsamples and crops the
handful the decks use, composes the drinking-game deck from the layman one, inlines
every figure as a data URI, and writes the finished HTML into the parent directory.

The decks are single self-contained files on purpose: they are opened from disk with
no server, and the only thing they load from beside themselves is whatever the
presenter drops into ../assets.
"""

import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TALK = os.path.dirname(HERE)                       # reports/tsi/talk
FIGS = os.path.join(os.path.dirname(TALK), "report-figures")
CACHE = os.path.join(HERE, ".figs")                # derived, not committed

try:
    from PIL import Image
except ImportError:
    sys.exit("needs Pillow:  pip install pillow")

# source figure, crop box (or None), target width
JOBS = {
    "fig2":   ("fig2_uncle_recovery.png",       None,                       1300),
    "fig22":  ("fig22_heatmap_window_delay.png", None,                      1300),
    "fig26":  ("fig26_deficit_vs_rho.png",      (1255, 105, 2751, 1338),    1300),
    "fig28":  ("fig28_reorg_depth_vs_delay.png", None,                      1400),
    "fig34":  ("fig34_fine_delay_accuracy.png", None,                       1300),
    # left panel only; the panel's own title overhangs the gutter, so it is cropped
    # away and the slide headline carries it instead
    "fig13L": ("fig13_selfish.png",             (30, 95, 1232, 1120),       1200),
}

DECKS = {
    "tsi-talk.html":          ("talk.template.html",     ["fig2", "fig26", "fig22", "fig34"]),
    "tsi-drinking-game.html": ("drinking.template.html", ["fig2", "fig26", "fig22", "fig34",
                                                          "fig28", "fig13L"]),
}


def prepare_figures():
    """Flatten onto white, crop, downsample, quantise. Palette PNG beats JPEG on line art."""
    os.makedirs(CACHE, exist_ok=True)
    for name, (src, box, width) in JOBS.items():
        path = os.path.join(FIGS, src)
        if not os.path.exists(path):
            sys.exit("missing figure: " + path)
        im = Image.open(path).convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
        im = im.convert("RGB")
        if box:
            im = im.crop(box)
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.convert("P", palette=Image.ADAPTIVE, colors=192).save(
            os.path.join(CACHE, name + ".png"), optimize=True)


def data_uri(name):
    with open(os.path.join(CACHE, name + ".png"), "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


def main():
    prepare_figures()

    # the drinking deck is generated: same CSS and script, different slides
    subprocess.run([sys.executable, os.path.join(HERE, "make_drinking.py")], check=True)

    for out, (template, names) in DECKS.items():
        with open(os.path.join(HERE, template), encoding="utf-8") as fh:
            html = fh.read()
        for name in names:
            token = "%%" + name.upper() + "%%"
            if token not in html:
                sys.exit("%s is missing %s" % (template, token))
            html = html.replace(token, data_uri(name))
        if "%%" in html:
            sys.exit("unsubstituted placeholder left in " + template)
        dst = os.path.join(TALK, out)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(html)
        print("%-24s %6.2f MB" % (out, os.path.getsize(dst) / 1024 / 1024))


if __name__ == "__main__":
    main()
