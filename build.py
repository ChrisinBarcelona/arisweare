#!/usr/bin/env python3
"""Build the ARIS static site.

Reads products.json and content/*.md, writes the finished site to _site/.
No dependencies beyond the Python 3 standard library.

    python3 build.py                 # site served from the domain root
    BASE_PATH=/repo python3 build.py # site served from a sub-path (GitHub project pages)
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
BASE = os.environ.get("BASE_PATH", "").rstrip("/")

data = json.loads((ROOT / "products.json").read_text(encoding="utf-8"))
SHOP = data["shop"]
CATS = {c["slug"]: c["name"] for c in data["categories"]}
PRODUCTS = data["products"]
EXPERIENCES = data.get("experiences", [])

e = html.escape


def url(path: str) -> str:
    """Site-relative URL that works on a custom domain and on a sub-path."""
    return f"{BASE}/{path.lstrip('/')}"


def abs_url(path: str) -> str:
    return SHOP["url"].rstrip("/") + "/" + path.lstrip("/")


def price(value: float) -> str:
    whole, cents = f"{value:.2f}".split(".")
    return f"{whole},{cents} €"


def asset(path: str) -> str:
    """Asset URL with a content hash, so browsers fetch new CSS/JS after each update."""
    digest = hashlib.sha1((ROOT / path).read_bytes()).hexdigest()[:8]
    return f"{url(path)}?v={digest}"


def img(name: str) -> str:
    return url(f"assets/img/products/{name}")


def wa_link(text: str) -> str:
    return f"https://wa.me/{SHOP['whatsapp']}?text={quote(text)}"


def editorial(name: str, alt: str, *, lazy: bool = True, priority: bool = False) -> str:
    """AVIF photo with a JPEG fallback for browsers that cannot show AVIF."""
    base = url(f"assets/img/editorial/{name}")
    loading = ' loading="lazy"' if lazy else ""
    prio = ' fetchpriority="high"' if priority else ""
    return (f'<picture><source srcset="{base}.avif" type="image/avif">'
            f'<img src="{base}.jpg" alt="{e(alt)}" width="1067" height="1600"{loading}{prio}></picture>')


WA_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M12.04 2a9.9 9.9 0 0 0-8.5 15l-1.4 5 5.2-1.36A9.9 9.9 0 1 0 12.04 2Zm0 18.1a8.2 8.2 0 0 1-4.2-1.15l-.3-.18-3.08.8.82-3-.2-.31a8.2 8.2 0 1 1 6.96 3.84Zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.09-.39-.13-.55.12-.16.25-.63.8-.78.96-.14.17-.29.19-.53.06a6.7 6.7 0 0 1-3.32-2.9c-.25-.43.25-.4.71-1.33.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.41-.55-.42h-.47a.9.9 0 0 0-.65.3 2.73 2.73 0 0 0-.85 2.03c0 1.2.87 2.36 1 2.52.12.17 1.71 2.62 4.15 3.67 1.54.67 2.15.72 2.92.61.47-.07 1.46-.6 1.66-1.17.2-.58.2-1.07.15-1.17-.06-.1-.22-.17-.47-.29Z"/>'
    "</svg>"
)


# --------------------------------------------------------------------------- layout

def header(active: str = "") -> str:
    links = [("shop", "Shop all", url("#shop"))]
    links += [(slug, name, url(f"?c={slug}#shop")) for slug, name in CATS.items()]
    if EXPERIENCES:
        links.append(("experiences", "Experiences", url("#experiences")))
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}" data-cat="{slug}"{current if slug == active else ""}>{e(name)}</a>'
        for slug, name, href in links
    )
    return f"""
<div class="announce">{e(SHOP['announcement'])}</div>
<header class="site-header">
  <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
  <nav class="nav-primary" id="site-nav" aria-label="Shop">{nav}<a class="nav-mobile-only" href="{url('shipping-terms/')}">Shipping &amp; returns</a></nav>
  <a class="logo" href="{url('')}"><img src="{url('assets/img/logo.png')}" alt="ARIS — home" width="318" height="148"></a>
  <nav class="nav-utility" aria-label="Help">
    <a class="nav-shipping" href="{url('shipping-terms/')}">Shipping &amp; returns</a>
    <a href="{wa_link('Hi ARIS! ')}" target="_blank" rel="noopener" class="wa-mini" aria-label="Chat with us on WhatsApp (opens WhatsApp)">{WA_ICON}<span>WhatsApp</span></a>
  </nav>
</header>"""


def footer() -> str:
    return f"""
<footer class="site-footer">
  <div class="footer-grid">
    <section>
      <h2>Order</h2>
      <p>Pick your size, tap <em>Order on WhatsApp</em> and we'll confirm availability, shipping and payment with you in the chat.</p>
    </section>
    <section>
      <h2>Customer care</h2>
      <ul>
        <li><a href="{url('shipping-terms/')}">Shipping &amp; returns</a></li>
        <li><a href="{url('terminos-y-condiciones/')}" hreflang="es" lang="es">Envíos y devoluciones (ES)</a></li>
        <li><a href="{url('privacy-policy/')}">Privacy policy</a></li>
      </ul>
    </section>
    <section>
      <h2>The fabric</h2>
      <ul>{''.join(f'<li>{e(f)}</li>' for f in SHOP['features'])}</ul>
    </section>
    <section>
      <h2>Contact us</h2>
      <p class="label">WhatsApp</p>
      <p><a href="{wa_link('Hi ARIS! ')}" target="_blank" rel="noopener">{e(SHOP['whatsapp_display'])}</a></p>
      <p class="label">Email</p>
      <p><a href="mailto:{e(SHOP['email'])}">{e(SHOP['email'])}</a></p>
    </section>
  </div>
  <p class="copyright">© <span data-year>2026</span> ARIS</p>
</footer>"""


def page(*, title: str, description: str, body: str, path: str, image: str | None = None,
         lang: str = "en", extra_head: str = "", active: str = "", og_type: str = "website") -> str:
    og_image = abs_url(image or "assets/img/og-image.jpg")
    full_title = f"{title} | ARIS" if title != "ARIS" else "ARIS — Aris, we are"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{abs_url(path)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="ARIS">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{abs_url(path)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<link rel="icon" href="{url('assets/img/favicon.png')}">
<link rel="apple-touch-icon" href="{url('assets/img/apple-touch-icon.png')}">
<link rel="stylesheet" href="{asset('assets/style.css')}">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<script src="{asset('assets/app.js')}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- cards

def product_card(p: dict) -> str:
    sale = p.get("compare_at")
    sold_out = not p.get("in_stock", True)
    price_html = (
        f'<span class="price"><s><span class="sr-only">Was </span>{price(sale)}</s> '
        f'<span class="sr-only">now </span>{price(p["price"])}</span>' if sale else
        f'<span class="price">{price(p["price"])}</span>'
    )
    tag = '<span class="tag">Sold out</span>' if sold_out else ('<span class="tag">Sale</span>' if sale else "")
    second = p["images"][1] if len(p["images"]) > 1 else None
    alt_img = (f'<img class="alt" src="{img(second)}" alt="" loading="lazy" width="600" height="900">'
               if second else "")
    return f"""
<li class="card{' is-sold-out' if sold_out else ''}" data-cat="{p['category']}">
  <a href="{url(f"product/{p['slug']}/")}">
    <div class="card-media">
      <img src="{img(p['images'][0])}" alt="" loading="lazy" width="600" height="900">
      {alt_img}
      {tag}
    </div>
    <div class="card-info">
      <span class="name">{e(p['name'])}</span>
      {price_html}
    </div>
  </a>
</li>"""


def experience_card(x: dict) -> str:
    media = (f'<img src="{img(x["image"])}" alt="" loading="lazy" width="600" height="900">' if x.get("image")
             else f'<div class="type-tile" aria-hidden="true"><span class="type-kicker">ARIS experience</span>'
                  f'<span class="type-title">{e(x["name"])}</span><span class="type-date">{e(x["date"])}</span></div>')
    available = x.get("available", True)
    tag = "" if available else '<span class="tag">Fully booked</span>'
    cta = "Book your spot" if available else "See details"
    return f"""
<li class="card card-experience">
  <a href="{url(f"experience/{x['slug']}/")}">
    <div class="card-media">{media}{tag}</div>
    <div class="exp-info">
      <p class="pd-cat">Experience · {e(x['date'])}</p>
      <h3>{e(x['name'])}</h3>
      <p class="exp-desc">{e(x['description'])}</p>
      <p class="exp-price">{price(x['price'])} <span class="muted">per spot</span></p>
      <span class="btn" aria-hidden="true">{cta}</span>
    </div>
  </a>
</li>"""


# --------------------------------------------------------------------------- pages

def build_home() -> str:
    filters = '<button type="button" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" data-filter="{slug}" aria-pressed="false">{e(name)}</button>'
        for slug, name in CATS.items()
    )
    cards = "".join(product_card(p) for p in PRODUCTS)
    exp_section = ""
    if EXPERIENCES:
        exp_cards = "".join(experience_card(x) for x in EXPERIENCES)
        exp_section = f"""
<section class="shop experiences" id="experiences" aria-labelledby="exp-title">
  <div class="shop-bar">
    <h2 id="exp-title">Experiences</h2>
    <p class="bar-note">Move with us. Book your spot on WhatsApp.</p>
  </div>
  <ul class="grid">{exp_cards}</ul>
</section>"""
    body = f"""
<section class="hero" aria-label="Campaign">
  <div class="hero-media">
    {editorial('aris-prioridad2-color-9-scaled', 'Five women in black ARIS activewear posing together', lazy=False, priority=True)}
    {editorial('aris-prioridad2-color-6-1-scaled', 'A woman meditating in a black ARIS jumpsuit while hands offer her dice', lazy=False)}
  </div>
  <div class="hero-copy">
    <h1>Aris, we are</h1>
    <p>Be whatever you want to be</p>
    <div class="hero-actions">
      <a class="btn btn-light" href="#shop">Shop now</a>
      <a class="btn btn-light" href="#fabric">The fabric</a>
    </div>
  </div>
</section>

<section class="shop" id="shop" aria-labelledby="shop-title">
  <div class="shop-bar">
    <h2 id="shop-title">The collection <span class="count" aria-live="polite">{len(PRODUCTS)} pieces</span></h2>
    <div class="filters" role="group" aria-label="Filter by category">{filters}</div>
  </div>
  <ul class="grid">{cards}</ul>
</section>
{exp_section}
<section class="editorial" id="fabric" aria-labelledby="fabric-title">
  <figure class="editorial-media">{editorial('aris-prioridad2-color-10-scaled', 'A woman smiling as she sets up a line of dominoes')}</figure>
  <div class="editorial-copy">
    <h2 id="fabric-title">From gym to city</h2>
    <p>Every ARIS piece is cut in black from a soft, technical fabric made from recycled plastic bottles, with built-in UPF 50+ sun protection.</p>
    <dl class="specs">
      <dt>Fabric</dt><dd>{e(SHOP['material'])}</dd>
      <dt>Protection</dt><dd>UPF 50+</dd>
      <dt>Care</dt><dd>{e(SHOP['care'])}</dd>
    </dl>
    <a class="btn" href="#shop">Shop the collection</a>
  </div>
  <figure class="editorial-media">{editorial('aris-prioridad-3-5-scaled', 'A woman looking over her shoulder in a black ARIS top')}</figure>
</section>

<section class="how" aria-labelledby="how-title">
  <h2 id="how-title">How to order</h2>
  <ol>
    <li><span aria-hidden="true">01</span>Choose your piece and size</li>
    <li><span aria-hidden="true">02</span>Tap “Order on WhatsApp” — your order is written for you</li>
    <li><span aria-hidden="true">03</span>We confirm availability, shipping and payment in the chat</li>
  </ol>
</section>"""
    return page(title="ARIS", description="ARIS activewear in black: recycled fabric, UPF 50+ sun protection. Order directly on WhatsApp.",
                body=body, path="")


def order_form(*, message: str, choice_name: str, choice_label: str, choices: list[str],
               button: str, note: str, preselect: str | None = None) -> str:
    # Used only when JavaScript is off: the form submits straight to WhatsApp
    fallback = message.replace("{choice}", f"{choice_name}: (please tell us)")
    opts = "".join(
        f'<label><input type="radio" name="choice" value="{e(c)}"{" checked" if c == preselect else ""}>'
        f'<span>{e(c)}</span></label>' for c in choices
    )
    return f"""
      <form class="order" novalidate action="https://wa.me/{SHOP['whatsapp']}" method="get" target="_blank"
            data-message="{e(message)}" data-wa="{SHOP['whatsapp']}" data-choice="{e(choice_name)}">
        <input type="hidden" name="text" value="{e(fallback)}">
        <fieldset class="sizes">
          <legend>{e(choice_label)} <span class="size-hint" role="alert"></span></legend>
          <div>{opts}</div>
        </fieldset>
        <button type="submit" class="btn btn-wa">{WA_ICON}<span>{e(button)}</span></button>
        <p class="order-note">{e(note)}</p>
      </form>"""


def build_product(p: dict) -> str:
    cat = CATS[p["category"]]
    sale = p.get("compare_at")
    sold_out = not p.get("in_stock", True)
    price_html = (
        f'<p class="pd-price"><s><span class="sr-only">Was </span>{price(sale)}</s> <strong><span class="sr-only">now </span>{price(p["price"])}</strong> '
        f'<span class="tag">−{round(100 - p["price"] / sale * 100)}%</span></p>'
        if sale else f'<p class="pd-price"><strong>{price(p["price"])}</strong></p>'
    )
    eager, lazy = 'fetchpriority="high"', 'loading="lazy"'
    n = len(p["images"])
    gallery = "".join(
        f'<li><img src="{img(name)}" alt="{e(p["name"])} — photo {i + 1} of {n}" width="600" height="900" {eager if i == 0 else lazy}></li>'
        for i, name in enumerate(p["images"])
    )
    page_url = abs_url(f"product/{p['slug']}/")
    if sold_out:
        restock = wa_link(f"Hi ARIS! Will {p['name']} be back in stock?\n{page_url}")
        order = f"""
      <p class="sold-out-note">Sold out right now.</p>
      <a class="btn btn-wa" href="{restock}" target="_blank" rel="noopener">{WA_ICON}<span>Ask about a restock</span></a>"""
    else:
        order = order_form(
            message=f"Hi ARIS! I'd like to order:\n\n*{p['name']}*\n{{choice}}\nPrice: {price(p['price'])}\n{page_url}",
            choice_name="Size", choice_label="Size", choices=p["sizes"], button="Order on WhatsApp",
            note="Opens WhatsApp with your order written out. Nothing is charged until we confirm it with you.")
    others = [o for o in PRODUCTS if o["slug"] != p["slug"]]
    same_cat = [o for o in others if o["category"] == p["category"]]
    related = "".join(product_card(o) for o in (same_cat + [o for o in others if o not in same_cat])[:3])
    ld = {
        "@context": "https://schema.org", "@type": "Product", "name": p["name"],
        "description": p["description"], "image": [abs_url(f"assets/img/products/{x}") for x in p["images"]],
        "brand": {"@type": "Brand", "name": "ARIS"}, "color": p["colour"], "material": SHOP["material"],
        "offers": {"@type": "Offer", "priceCurrency": SHOP["currency"], "price": f"{p['price']:.2f}",
                   "availability": "https://schema.org/OutOfStock" if sold_out else "https://schema.org/InStock",
                   "url": page_url},
    }
    body = f"""
<nav class="crumbs" aria-label="Breadcrumb"><a href="{url('')}">ARIS</a> <span aria-hidden="true">/</span> <a href="{url(f'?c={p["category"]}#shop')}">{e(cat)}</a> <span aria-hidden="true">/</span> <span aria-current="page">{e(p['name'])}</span></nav>
<article class="pd">
  <ul class="pd-gallery" aria-label="Photos of {e(p['name'])}" tabindex="0">{gallery}</ul>
  <div class="pd-panel">
    <div class="pd-sticky">
      <p class="pd-cat">{e(cat)}</p>
      <h1>{e(p['name'])}</h1>
      {price_html}
      <p class="pd-colour">Colour: {e(p['colour'])}</p>
      {order}
      <details open>
        <summary>Description</summary>
        <p>{e(p['description'])}</p>
        <ul>{''.join(f'<li>{e(f)}</li>' for f in SHOP['features'])}</ul>
      </details>
      <details>
        <summary>Fabric &amp; care</summary>
        <p>{e(SHOP['material'])}<br>{e(SHOP['care'])}</p>
      </details>
      <details>
        <summary>Shipping &amp; returns</summary>
        <p>Shipping costs are confirmed with you before you pay. You can return any piece within 9 days of receiving it. <a href="{url('shipping-terms/')}">Full terms</a></p>
      </details>
    </div>
  </div>
</article>
<section class="related" aria-labelledby="related-title">
  <h2 id="related-title">You may also like</h2>
  <ul class="grid">{related}</ul>
</section>"""
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return page(title=p["name"], description=f"{p['name']} — {p['description'][:140]}", body=body,
                path=f"product/{p['slug']}/", image=f"assets/img/products/{p['images'][0]}", extra_head=head,
                active=p["category"], og_type="product")


def build_experience(x: dict) -> str:
    page_url = abs_url(f"experience/{x['slug']}/")
    media = (f'<img src="{img(x["image"])}" alt="{e(x["name"])}" width="600" height="900">' if x.get("image") else
             f'<div class="type-tile type-tile-lg" aria-hidden="true"><span class="type-kicker">ARIS experience</span>'
             f'<span class="type-title">{e(x["name"])}</span><span class="type-date">{e(x["date"])}</span></div>')
    if x.get("available", True):
        spots = [str(i) for i in range(1, int(x.get("max_spots", 6)) + 1)]
        order = order_form(
            message=f"Hi ARIS! I'd like to book:\n\n*{x['name']}* — {x['date']}\n{{choice}}\nPrice: {price(x['price'])} per spot\n{page_url}",
            choice_name="Spots", choice_label="How many spots?", choices=spots, preselect="1",
            button="Book on WhatsApp",
            note="Opens WhatsApp with your booking written out. We'll confirm your spot and send you the details.")
    else:
        order = '<p class="sold-out-note">This experience is fully booked.</p>'
    body = f"""
<nav class="crumbs" aria-label="Breadcrumb"><a href="{url('')}">ARIS</a> <span aria-hidden="true">/</span> <a href="{url('#experiences')}">Experiences</a> <span aria-hidden="true">/</span> <span aria-current="page">{e(x['name'])}</span></nav>
<article class="pd pd-experience">
  <div class="pd-hero">{media}</div>
  <div class="pd-panel">
    <div class="pd-sticky">
      <p class="pd-cat">Experience</p>
      <h1>{e(x['name'])}</h1>
      <p class="pd-price"><strong>{price(x['price'])}</strong> <span class="muted">per spot</span></p>
      <p class="pd-colour">Date: {e(x['date'])}</p>
      {order}
      <details open>
        <summary>About</summary>
        <p>{e(x['description'])}</p>
      </details>
    </div>
  </div>
</article>"""
    return page(title=f"{x['name']} {x['date']}", description=f"{x['name']} with ARIS — {x['date']}. Book on WhatsApp.",
                body=body, path=f"experience/{x['slug']}/", active="experiences")


def md_to_html(text: str) -> str:
    out, items = [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for block in text.strip().split("\n"):
        line = block.strip()
        if not line:
            flush()
            continue
        inline = e(line)
        inline = re.sub(r"([\w.+-]+@[\w-]+\.[\w.]+)", r'<a href="mailto:\1">\1</a>', inline)
        if line.startswith("## "):
            flush(); out.append(f"<h2>{e(line[3:])}</h2>")
        elif line.startswith("- "):
            items.append(inline[2:])
        else:
            flush(); out.append(f"<p>{inline}</p>")
    flush()
    return "\n".join(out)


def build_content(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    meta, text = {}, raw
    if raw.startswith("---"):
        _, fm, text = raw.split("---", 2)
        for line in fm.strip().splitlines():
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    alt = ""
    if "alt" in meta:
        alt_lang = "es" if meta.get("lang", "en") == "en" else "en"
        alt = f'<p class="lang-switch"><a href="{url(meta["alt"] + "/")}" hreflang="{alt_lang}" lang="{alt_lang}">{e(meta["alt_label"])}</a></p>'
    body = f"""<article class="legal"><h1>{e(meta['title'])}</h1>{alt}{md_to_html(text)}</article>"""
    slug = path.stem
    return slug, page(title=meta["title"], description=f"ARIS — {meta['title']}", body=body,
                      path=f"{slug}/", lang=meta.get("lang", "en"))


# --------------------------------------------------------------------------- write

def write(rel: str, content: str) -> None:
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")

    write("index.html", build_home())
    urls = [""]
    for p in PRODUCTS:
        write(f"product/{p['slug']}/index.html", build_product(p))
        urls.append(f"product/{p['slug']}/")
    for x in EXPERIENCES:
        write(f"experience/{x['slug']}/index.html", build_experience(x))
        urls.append(f"experience/{x['slug']}/")
    for md in sorted((ROOT / "content").glob("*.md")):
        slug, out = build_content(md)
        write(f"{slug}/index.html", out)
        urls.append(f"{slug}/")

    write("404.html", page(title="Page not found", description="Page not found", path="404.html", body=f"""
<section class="notfound"><h1>Page not found</h1><p>This page doesn't exist — the collection does.</p>
<a class="btn" href="{url('')}">Back to the shop</a></section>"""))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{abs_url(u)}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {abs_url('sitemap.xml')}\n")
    write(".nojekyll", "")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    print(f"Built {len(urls) + 1} pages into {OUT.relative_to(ROOT)}/ (base path: '{BASE or '/'}')")


if __name__ == "__main__":
    main()
