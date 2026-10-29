"""Build the static parts of the site from ideas.json.

Writes ideas.js (data for the front page), og/<slug>.jpg (1200x630 share
images) and p/<slug>/index.html (one shareable page per idea).

Usage: python3 tools/build.py
"""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://radical-hr.lillefar.com"


def kpi_class(v):
    if v.startswith("−"):
        return "neg"
    return "pos" if v.startswith("+") or v.endswith("*") else ""


# Share images use the site's fonts and dark palette
FONTS = ROOT / "tools" / "fonts"
BG, CREAM, TEAL, MUSTARD, RED, MUTED = "#132325", "#f3e7cc", "#5fb0ad", "#e8b54c", "#f0614f", "#9fb0aa"


def display(size):
    f = ImageFont.truetype(str(FONTS / "Fraunces.ttf"), size)
    f.set_variation_by_axes([144, 900, 0, 1])  # opsz, wght, soft, wonk
    return f


def mono(size):
    return ImageFont.truetype(str(FONTS / "IBMPlexMono-SemiBold.ttf"), size)


def illustration(slug, size):
    """Load the illustration (full-size original when present), center-cropped to size."""
    src = ROOT / "art" / "propaganda" / f"{slug}.png"
    if not src.exists():
        src = ROOT / "img" / f"{slug}.webp"
    return ImageOps.fit(Image.open(src).convert("RGB"), size, Image.LANCZOS)


def wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and draw.textlength(trial, font=font) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def fit_title(draw, text, width, height, start=52):
    """Largest display size where the wrapped title fits the box."""
    for size in range(start, 20, -2):
        font = display(size)
        lines = wrap(draw, text, font, width)
        if len(lines) * size * 1.08 <= height:
            return font, lines
    return font, lines


def og_idea(idea):
    """1200x630: illustration left, policy title panel right."""
    im = Image.new("RGB", (1200, 630), BG)
    im.paste(illustration(idea["slug"], (840, 630)), (0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((840, 0, 846, 630), fill=TEAL)
    x, w = 884, 280
    d.text((x, 48), "RADICAL HR", font=mono(18), fill=TEAL)
    d.text((x, 76), f"POLICY {idea['code']}", font=mono(18), fill=MUTED)
    font, lines = fit_title(d, idea["title"], w, 360)
    y = 130
    for line in lines:
        d.text((x, y), line, font=font, fill=CREAM)
        y += round(font.size * 1.08)
    stamp = mono(17)
    sw = d.textlength(idea["stamp"], font=stamp)
    d.rectangle((x, 530, x + sw + 24, 566), outline=MUSTARD if idea.get("good") else RED, width=3)
    d.text((x + 12, 536), idea["stamp"], font=stamp, fill=MUSTARD if idea.get("good") else RED)
    im.save(ROOT / "og" / f"{idea['slug']}.jpg", quality=84, optimize=True)


def og_home(ideas):
    """1200x630: wordmark left, 2x2 collage right."""
    im = Image.new("RGB", (1200, 630), BG)
    d = ImageDraw.Draw(im)
    picks = ["parking", "paycut", "christmas", "phones"]
    for i, slug in enumerate(picks):
        x, y = 560 + (i % 2) * 310, 60 + (i // 2) * 262
        d.rectangle((x + 8, y + 8, x + 8 + 290, y + 8 + 244), fill=TEAL)
        im.paste(illustration(slug, (290, 244)), (x, y))
    d.text((60, 60), "THE PEOPLE HANDBOOK", font=mono(20), fill=MUTED)
    d.text((54, 110), "Radical", font=display(124), fill=CREAM)
    d.text((54, 240), "HR", font=display(124), fill=TEAL)
    y = 410
    for line in ["A field guide to dark patterns", "in people management."]:
        d.text((60, y), line, font=display(30), fill=CREAM)
        y += 40
    d.text((60, 530), f"{len(ideas)} POLICIES ON FILE", font=mono(20), fill=MUSTARD)
    im.save(ROOT / "og" / "home.jpg", quality=84, optimize=True)


def icons():
    """Apple touch icon; the favicon itself is a hand-written SVG."""
    im = Image.new("RGB", (180, 180), BG)
    d = ImageDraw.Draw(im)
    d.text((90, 94), "HR", font=display(92), fill=TEAL, anchor="mm")
    im.save(ROOT / "apple-touch-icon.png")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Radical HR</title>
<meta name="description" content="{spin}">
<meta name="theme-color" content="#132325">
<link rel="canonical" href="{url}">
<link rel="icon" href="../../favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../../apple-touch-icon.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Radical HR">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{spin}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/og/{slug}.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Satirical 1950s-style illustration: {title}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{spin}">
<meta name="twitter:image" content="{site}/og/{slug}.jpg">
<meta name="twitter:image:alt" content="Satirical 1950s-style illustration: {title}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700;9..144,900&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../style.css">
</head>
<body>

<div class="wrap">
  <div class="topline">
    <span>The People Handbook · Rev. 2026</span>
    <span>Internal · Do not forward to staff</span>
  </div>

  <div class="crumbs">
    <a href="../../">← All policies</a>
    <span>Policy {code} of {total}</span>
  </div>

  <article class="single">
    <div class="art">
      <img src="../../img/{slug}.webp" width="960" height="720" alt="Illustration: {title}">
      <span class="stamp{good}">{stamp}</span>
    </div>
    <div>
      <div class="meta"><span>Policy {code}</span><span>{dept}</span></div>
      <h1>{title}</h1>
      <p class="spin">{spin}</p>
      <dl class="kpi">
        <div><dt>Productivity</dt><dd class="{prod_class}">{prod}</dd></div>
        <div><dt>Morale</dt><dd class="{morale_class}">{morale}</dd></div>
      </dl>
      <div class="share">
        <span>Forward to your manager</span>
        <button type="button" id="copy">Copy link</button>
        <button type="button" id="native" hidden>Share…</button>
        <a href="https://www.linkedin.com/sharing/share-offsite/?url={url_q}" target="_blank" rel="noopener">LinkedIn</a>
        <a href="https://x.com/intent/post?url={url_q}&amp;text={title_q}" target="_blank" rel="noopener">X</a>
        <a href="https://www.facebook.com/sharer/sharer.php?u={url_q}" target="_blank" rel="noopener">Facebook</a>
        <a href="mailto:?subject={title_q}&amp;body={url_q}">Email</a>
      </div>
    </div>
  </article>

  <nav class="pager" aria-label="More policies">
    <a href="../{prev_slug}/"><small>← Previous policy</small><b>{prev_title}</b></a>
    <a href="../{next_slug}/"><small>Next policy →</small><b>{next_title}</b></a>
  </nav>

  <p class="disclaimer"><b>Disclaimer:</b> These policies are only <em>inspired by</em> the truth. Each one started with something that really happened at work, then got exaggerated until it fit on a poster. No real manager, colleague or HR department is depicted, and none of this is advice. Please don't try it at work.</p>

  <footer>
    <span>Radical HR · radical-hr.lillefar.com</span>
    <span>Satire. Any resemblance to your workplace is entirely your workplace's fault.</span>
  </footer>
</div>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
const url = {url_js};
const toast = document.getElementById('toast');
let toastTimer;
const say = msg => {{
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}};
document.getElementById('copy').addEventListener('click', async () => {{
  try {{ await navigator.clipboard.writeText(url); say('Link copied. HR has been notified.'); }}
  catch {{ say(url); }}
}});
const native = document.getElementById('native');
if (navigator.share) {{
  native.hidden = false;
  native.addEventListener('click', () => navigator.share({{ title: document.title, url }}).catch(() => {{}}));
}}
</script>
</body>
</html>
"""


def main():
    ideas = json.loads((ROOT / "ideas.json").read_text())
    for i, idea in enumerate(ideas):
        idea["code"] = f"RHR-{i + 1:03d}"

    (ROOT / "ideas.js").write_text(
        "// Generated by tools/build.py from ideas.json. Do not edit.\n"
        f"window.IDEAS = {json.dumps(ideas, ensure_ascii=False, indent=2)};\n")

    (ROOT / "og").mkdir(exist_ok=True)
    for i, idea in enumerate(ideas):
        slug = idea["slug"]
        prev, nxt = ideas[i - 1], ideas[(i + 1) % len(ideas)]
        url = f"{SITE}/p/{slug}/"
        page = PAGE.format(
            site=SITE, url=url, url_q=quote(url, safe=""), url_js=json.dumps(url),
            slug=slug, code=idea["code"], total=len(ideas),
            title=escape(idea["title"]), title_q=quote(idea["title"]),
            spin=escape(idea["spin"]), dept=escape(idea["dept"]),
            stamp=escape(idea["stamp"]), good=" good" if idea.get("good") else "",
            prod=idea["prod"], prod_class=kpi_class(idea["prod"]),
            morale=idea["morale"], morale_class=kpi_class(idea["morale"]),
            prev_slug=prev["slug"], prev_title=escape(prev["title"]),
            next_slug=nxt["slug"], next_title=escape(nxt["title"]),
        )
        out = ROOT / "p" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        og_idea(idea)

    og_home(ideas)
    icons()
    print(f"Built {len(ideas)} idea pages, share images and ideas.js")


if __name__ == "__main__":
    main()
