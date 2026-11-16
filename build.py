#!/usr/bin/env python3
"""Build the ARIS static site.

Reads products.json and content/*.md, writes the finished site to _site/.
No dependencies beyond the Python 3 standard library.

    python3 build.py                 # site served from the domain root
    BASE_PATH=/repo python3 build.py # site served from a sub-path (GitHub project pages)
"""
from __future__ import annotations

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

e = html.escape


def url(path: str) -> str:
    """Site-relative URL that works on a custom domain and on a sub-path."""
    return f"{BASE}/{path.lstrip('/')}"


def abs_url(path: str) -> str:
    return SHOP["url"].rstrip("/") + "/" + path.lstrip("/")


def price(value: float) -> str:
    whole, cents = f"{value:.2f}".split(".")
    return f"{whole},{cents} €"


def img(name: str) -> str:
    return url(f"assets/img/products/{name}")


def wa_link(text: str) -> str:
    return f"https://wa.me/{SHOP['whatsapp']}?text={quote(text)}"


# --------------------------------------------------------------------------- layout

def header(active: str = "") -> str:
    links = [("shop", "Shop all", url("#shop"))] + [
        (slug, name, url(f"?c={slug}#shop")) for slug, name in CATS.items()
    ]
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}" data-cat="{slug}"{current if slug == active else ""}>{e(name)}</a>'
        for slug, name, href in links
    )
    return f"""
<div class="announce">{e(SHOP['announcement'])}</div>
<header class="site-header">
  <button class="menu-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button>
  <nav class="nav-primary" id="site-nav" aria-label="Shop">{nav}</nav>
  <a class="logo" href="{url('')}" aria-label="ARIS home"><img src="{url('assets/img/logo.png')}" alt="ARIS" width="318" height="148"></a>
  <nav class="nav-utility" aria-label="Help">
    <a href="{url('shipping-terms/')}">Shipping &amp; returns</a>
    <a href="{wa_link('Hi ARIS! ')}" target="_blank" rel="noopener" class="wa-mini" aria-label="Chat with us on WhatsApp">{WA_ICON}<span>WhatsApp</span></a>
  </nav>
</header>"""


WA_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M12.04 2a9.9 9.9 0 0 0-8.5 15l-1.4 5 5.2-1.36A9.9 9.9 0 1 0 12.04 2Zm0 18.1a8.2 8.2 0 0 1-4.2-1.15l-.3-.18-3.08.8.82-3-.2-.31a8.2 8.2 0 1 1 6.96 3.84Zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.09-.39-.13-.55.12-.16.25-.63.8-.78.96-.14.17-.29.19-.53.06a6.7 6.7 0 0 1-3.32-2.9c-.25-.43.25-.4.71-1.33.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.41-.55-.42h-.47a.9.9 0 0 0-.65.3 2.73 2.73 0 0 0-.85 2.03c0 1.2.87 2.36 1 2.52.12.17 1.71 2.62 4.15 3.67 1.54.67 2.15.72 2.92.61.47-.07 1.46-.6 1.66-1.17.2-.58.2-1.07.15-1.17-.06-.1-.22-.17-.47-.29Z"/>'
    "</svg>"
)


def footer() -> str:
    return f"""
<footer class="site-footer">
  <div class="footer-grid">
    <section>
      <h2>Order</h2>
      <p>Pick your size, tap <em>Order on WhatsApp</em> and we'll confirm availability, shipping and payment with you personally.</p>
    </section>
    <section>
      <h2>Customer care</h2>
      <ul>
        <li><a href="{url('shipping-terms/')}">Shipping &amp; returns</a></li>
        <li><a href="{url('terminos-y-condiciones/')}">Envíos y devoluciones (ES)</a></li>
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
         lang: str = "en", extra_head: str = "", active: str = "") -> str:
    og_image = abs_url(image) if image else abs_url("assets/img/editorial/aris-prioridad2-color-9-scaled.avif")
    full_title = f"{title} | ARIS" if title != "ARIS" else "ARIS — Aris, we are"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{abs_url(path)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{abs_url(path)}">
<meta name="theme-color" content="#000000">
<link rel="icon" href="{url('assets/img/favicon.png')}">
<link rel="stylesheet" href="{url('assets/style.css')}">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<script src="{url('assets/app.js')}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- pages

def product_card(p: dict) -> str:
    sale = p.get("compare_at")
    price_html = (
        f'<span class="price"><s>{price(sale)}</s> {price(p["price"])}</span>' if sale else
        f'<span class="price">{price(p["price"])}</span>'
    )
    second = p["images"][1] if len(p["images"]) > 1 else p["images"][0]
    return f"""
<li class="card" data-cat="{p['category']}">
  <a href="{url(f"product/{p['slug']}/")}">
    <div class="card-media">
      <img src="{img(p['images'][0])}" alt="{e(p['name'])}, {e(CATS[p['category']].lower())} in {e(p['colour'].lower())}" loading="lazy" width="600" height="900">
      <img class="alt" src="{img(second)}" alt="" loading="lazy" width="600" height="900" aria-hidden="true">
      {'<span class="tag">Sale</span>' if sale else ''}
    </div>
    <div class="card-info">
      <span class="name">{e(p['name'])}</span>
      {price_html}
    </div>
  </a>
</li>"""


def build_home() -> str:
    filters = '<button type="button" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" data-filter="{slug}" aria-pressed="false">{e(name)}</button>'
        for slug, name in CATS.items()
    )
    cards = "".join(product_card(p) for p in PRODUCTS)
    ed = lambda n: url(f"assets/img/editorial/{n}")
    body = f"""
<section class="hero" aria-label="Campaign">
  <div class="hero-media">
    <img src="{ed('aris-prioridad2-color-9-scaled.avif')}" alt="Five women in black ARIS activewear posing together" width="1707" height="2560" fetchpriority="high">
    <img src="{ed('aris-prioridad2-color-6-1-scaled.avif')}" alt="A woman meditating in a black ARIS jumpsuit while hands offer her dice" width="1706" height="2560">
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
    <h2 id="shop-title">The collection <span class="count">{len(PRODUCTS)} pieces</span></h2>
    <div class="filters" role="group" aria-label="Filter by category">{filters}</div>
  </div>
  <ul class="grid">{cards}</ul>
</section>

<section class="editorial" id="fabric" aria-labelledby="fabric-title">
  <figure class="editorial-media"><img src="{ed('aris-prioridad2-color-10-scaled.avif')}" alt="A woman smiling as she sets up a line of dominoes" loading="lazy" width="1707" height="2560"></figure>
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
  <figure class="editorial-media"><img src="{ed('aris-prioridad-3-5-scaled.avif')}" alt="A woman looking over her shoulder in a black ARIS top" loading="lazy" width="1707" height="2560"></figure>
</section>

<section class="how" aria-labelledby="how-title">
  <h2 id="how-title">How to order</h2>
  <ol>
    <li><span>01</span>Choose your piece and size</li>
    <li><span>02</span>Tap “Order on WhatsApp” — your order is written for you</li>
    <li><span>03</span>We confirm availability, shipping and payment in the chat</li>
  </ol>
</section>"""
    return page(title="ARIS", description="ARIS activewear in black: recycled fabric, UPF 50+ sun protection. Order directly on WhatsApp.", body=body, path="")


def build_product(p: dict) -> str:
    cat = CATS[p["category"]]
    sale = p.get("compare_at")
    price_html = (
        f'<p class="pd-price"><s>{price(sale)}</s> <strong>{price(p["price"])}</strong> <span class="tag">−{round(100 - p["price"] / sale * 100)}%</span></p>'
        if sale else f'<p class="pd-price"><strong>{price(p["price"])}</strong></p>'
    )
    eager, lazy = 'fetchpriority="high"', 'loading="lazy"'
    gallery = "".join(
        f'<li><img src="{img(name)}" alt="{e(p["name"])} — view {i + 1}" width="600" height="900" {eager if i == 0 else lazy}></li>'
        for i, name in enumerate(p["images"])
    )
    sizes = "".join(
        f'<label><input type="radio" name="size" value="{s}" required><span>{s}</span></label>' for s in p["sizes"]
    )
    page_url = abs_url(f"product/{p['slug']}/")
    base_msg = f"Hi ARIS! I'd like to order:\n\n*{p['name']}*\nPrice: {price(p['price'])}\n{page_url}"
    others = [o for o in PRODUCTS if o["slug"] != p["slug"]]
    same_cat = [o for o in others if o["category"] == p["category"]]
    related = "".join(product_card(o) for o in (same_cat + [o for o in others if o not in same_cat])[:3])
    ld = {
        "@context": "https://schema.org", "@type": "Product", "name": p["name"],
        "description": p["description"], "image": [abs_url(f"assets/img/products/{n}") for n in p["images"]],
        "brand": {"@type": "Brand", "name": "ARIS"}, "color": p["colour"], "material": SHOP["material"],
        "offers": {"@type": "Offer", "priceCurrency": SHOP["currency"], "price": f"{p['price']:.2f}",
                   "availability": "https://schema.org/InStock" if p["in_stock"] else "https://schema.org/OutOfStock",
                   "url": page_url},
    }
    body = f"""
<nav class="crumbs" aria-label="Breadcrumb"><a href="{url('')}">ARIS</a> / <a href="{url(f'?c={p["category"]}#shop')}">{e(cat)}</a> / <span>{e(p['name'])}</span></nav>
<article class="pd">
  <ul class="pd-gallery">{gallery}</ul>
  <div class="pd-panel">
    <div class="pd-sticky">
      <p class="pd-cat">{e(cat)}</p>
      <h1>{e(p['name'])}</h1>
      {price_html}
      <p class="pd-colour">Colour: {e(p['colour'])}</p>
      <form class="order" novalidate data-message="{e(base_msg)}" data-wa="{SHOP['whatsapp']}">
        <fieldset class="sizes">
          <legend>Size <span class="size-hint" aria-live="polite"></span></legend>
          <div>{sizes}</div>
        </fieldset>
        <button type="submit" class="btn btn-wa">{WA_ICON}<span>Order on WhatsApp</span></button>
        <p class="order-note">Opens WhatsApp with your order written out. Nothing is charged until we confirm with you.</p>
      </form>
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
                active=p["category"])


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
    alt = f'<p class="lang-switch"><a href="{url(meta["alt"] + "/")}">{e(meta["alt_label"])}</a></p>' if "alt" in meta else ""
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
