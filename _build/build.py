#!/usr/bin/env python3
"""
Builds The Udaisarovar website from the files in content/.

Edit content with Pages CMS (or by hand in content/*.json); this script turns it into
the HTML pages. GitHub Actions runs it on every push to main and publishes the result.

  python3 _build/build.py            -> writes the full site into _site/
  python3 _build/build.py --root     -> also writes the HTML pages into the repo root
"""
import hashlib, html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda name: json.load(open(os.path.join(ROOT, "content", name + ".json"), encoding="utf-8"))
SITE = "https://www.theudaisarovar.com/"


def e(s):
    """Escape text for HTML."""
    return html.escape(str(s if s is not None else ""), quote=True)


def img(p):
    """Pages CMS stores '/assets/x.jpg'; pages use relative 'assets/x.jpg'."""
    p = (p or "").strip()
    return p[1:] if p.startswith("/") else p


def digits(phone):
    d = re.sub(r"\D", "", phone or "")
    return d if len(d) > 10 else "91" + d


def wa(phone, text=""):
    from urllib.parse import quote
    return f"https://wa.me/{digits(phone)}" + (f"?text={quote(text)}" if text else "")


def tel(phone):
    return "tel:+" + digits(phone)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


S = C("site")
CT = S["contact"]
BOOK = CT["booking_link"]

# ------------------------------------------------------------------ style choices
HEAD_FONTS = {
    "Cormorant Garamond": "Cormorant+Garamond:ital,wght@0,500;0,600;1,500",
    "Playfair Display": "Playfair+Display:ital,wght@0,500;0,600;1,500",
    "Cinzel": "Cinzel:wght@500;600",
    "Marcellus": "Marcellus",
    "Libre Baskerville": "Libre+Baskerville:ital,wght@0,400;0,700;1,400",
    "Bodoni Moda": "Bodoni+Moda:ital,wght@0,500;0,600;1,500",
}
BODY_FONTS = {
    "Jost": "Jost:wght@300;400;500",
    "Montserrat": "Montserrat:wght@300;400;500;600",
    "Lato": "Lato:wght@300;400;700",
    "Poppins": "Poppins:wght@300;400;500",
    "Mulish": "Mulish:wght@300;400;500;600",
    "Nunito Sans": "Nunito+Sans:wght@300;400;600",
}
GOLDS = {  # button gradient, text-safe gold for small text, decorative gold, text on buttons
    "JD lotus gold": ("linear-gradient(135deg,#C08A3A 0%,#D7AA60 28%,#F4D390 52%,#D7AA60 74%,#B98536 100%)", "#8A672A", "#B8924A", "#2B1D08"),
    "Rose gold": ("linear-gradient(135deg,#B76E5E 0%,#D69A88 30%,#F2C7B8 52%,#D69A88 74%,#A9604F 100%)", "#8E4E40", "#C08878", "#2E140E"),
    "Antique bronze": ("linear-gradient(135deg,#7E5A2E 0%,#A27A45 30%,#C9A570 52%,#A27A45 74%,#704F27 100%)", "#76552A", "#9C7A4C", "#FFFFFF"),
    "Champagne": ("linear-gradient(135deg,#C9B48A 0%,#DFCDA6 30%,#F4E8CC 52%,#DFCDA6 74%,#BCA77C 100%)", "#7C6A44", "#BFAE86", "#2B2410"),
}
ST = S.get("style", {})
hf = ST.get("heading_font") if ST.get("heading_font") in HEAD_FONTS else "Cormorant Garamond"
bf = ST.get("body_font") if ST.get("body_font") in BODY_FONTS else "Jost"
gold = GOLDS.get(ST.get("gold_style"), GOLDS["JD lotus gold"])
FONT_URL = f"https://fonts.googleapis.com/css2?family={HEAD_FONTS[hf]}&family={BODY_FONTS[bf]}&display=swap"
STYLE_VARS = (f':root{{--serif:"{hf}",Georgia,"Times New Roman",serif;--sans:"{bf}",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;'
              f'--jd-gold:{gold[0]};--brass-d:{gold[1]};--gold:{gold[2]};--jd-ink:{gold[3]}}}')

VER = hashlib.md5(open(os.path.join(ROOT, "assets/css/site.css"), "rb").read() + open(os.path.join(ROOT, "assets/js/site.js"), "rb").read()
                  + json.dumps(ST).encode()).hexdigest()[:8]

NAV_L = [("stay.html", "Stay"), ("dining.html", "Dining"), ("experiences.html", "Experiences"), ("events.html", "Events")]
NAV_R = [("rates.html", "Rates"), ("gallery.html", "Gallery"), ("contact.html", "Contact")]
ICON_MENU = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M3 8h18M3 16h18"/></svg>'
ICON_CLOSE = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19"/></svg>'
PLAY = '<svg width="22" height="22" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>'
RING = '<span class="ring"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>'
B = S["brand"]


# ------------------------------------------------------------------ shared layout
def head(seo, path, image, extra=""):
    url = SITE + path
    title, desc = e(seo["title"]), e(seo["description"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-18311903882"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'AW-18311903882');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta name="geo.region" content="IN-RJ">
<meta name="geo.placename" content="Udaipur">
<meta name="geo.position" content="24.5604582;73.8056938">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{img(image)}">
<meta property="og:locale" content="en_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1E1A14">
<link rel="icon" type="image/png" href="assets/brand/favicon.png">
<link rel="apple-touch-icon" href="assets/brand/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{e(FONT_URL)}" rel="stylesheet">
<link rel="stylesheet" href="assets/css/site.css?v={VER}">
<style>{STYLE_VARS}</style>
{extra}</head>
<body>
<div class="loader" aria-hidden="true"><div class="bloom">{RING}<img src="{e(img(B['lotus_logo']))}" alt=""></div><div class="word">{e(B['loader_title'])}<small>{e(B['loader_subtitle'])}</small></div></div>
"""


def header(active, over=False):
    def links(items):
        return "\n      ".join(f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{l}</a>' for h, l in items)
    off = S.get("offer", {})
    topline = ""
    if off.get("show", True):
        code = f' · code <b>{e(off["code"])}</b>' if off.get("code") else ""
        msg = f"Hi, I'd like to book a stay at The Udaisarovar using code {off.get('code', '')}"
        txt = e(off.get("text", ""))
        short = txt.split(" on ")[0] if " on " in txt else txt
        rest = txt[len(short):]
        topline = (f'<div class="topline">{short}<span class="xl">{rest}</span>{code} '
                   f'<a href="{e(wa(CT["phone"], msg))}">Claim on WhatsApp</a></div>\n')
    drawer = "\n    ".join(f'<a href="{h}">{l}</a>' for h, l in [("index.html", "Home")] + NAV_L + NAV_R)
    lotus = e(img(B["lotus_logo"]))
    return f"""{topline}<header class="{'site-head over' if over else 'site-head'}">
  <div class="bar">
    <button class="menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{ICON_MENU}</button>
    <nav class="nav-l" aria-label="Primary">
      {links(NAV_L)}
    </nav>
    <a class="brand" href="index.html" aria-label="{e(B['name'])} {e(B['tagline'])}, home"><img class="lotus" src="{lotus}" alt="JD Stays &amp; Hospitality"><span class="n">{e(B['name'])}</span><span class="t">{e(B['tagline'])}</span></a>
    <nav class="nav-r" aria-label="Secondary">
      {links(NAV_R)}
      <a class="btn btn-dark" href="{e(BOOK)}">Book Now</a>
    </nav>
    <a class="m-book" href="{e(BOOK)}">Book</a>
  </div>
</header>
<div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="Menu">
  <div class="top"><span class="brand" style="align-items:flex-start;color:#FBF8F2"><img class="lotus" src="{lotus}" alt=""><span class="n" style="font-size:1.3rem">{e(B['name'])}</span></span><button class="close" type="button" aria-label="Close menu">{ICON_CLOSE}</button></div>
  <nav aria-label="Menu">
    {drawer}
  </nav>
  <div class="meta">
    <a href="{e(BOOK)}">Book online</a> · <a href="{e(wa(CT['phone']))}">WhatsApp {e(CT['phone'])}</a><br>
    {e(short_address())} · <a href="{e(CT['guest_app_link'])}">Guest App</a>
  </div>
</div>
"""


def short_address():
    parts = [p.strip() for p in CT["address"].split(",")]
    pin = re.findall(r"\d{6}", CT["address"])
    return (", ".join(parts[-3:-1]) + (" " + pin[0] if pin else "")) if len(parts) >= 3 else CT["address"]


def footer():
    addr = e(CT["address"]).replace(", Lakadwas", ",<br>Lakadwas")
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="top">
      <div>
        <img class="jd-logo" src="{e(img(B['footer_logo']))}" alt="JD Stays &amp; Hospitality by JD Group" width="240">
        <div class="logo" style="margin-top:30px"><div><b>{e(B['name'])}</b><span>{e(B['short_line'])}</span></div></div>
        <p style="margin-top:22px;max-width:34ch">{e(S['footer_about'])}</p>
        <p style="margin-top:14px">Managed by <a href="{e(CT['jd_group_link'])}">JD Stays &amp; Hospitality</a>, a JD Group company.</p>
      </div>
      <div>
        <h4>Reservations</h4>
        <ul>
          <li><a href="{e(wa(CT['phone']))}">WhatsApp {e(CT['phone'])}</a></li>
          <li><a href="{tel(CT['phone'])}">Call {e(CT['phone'])}</a></li>
          <li><a href="{e(BOOK)}">Book online</a></li>
          <li><a href="{e(CT['guest_app_link'])}">Guest App</a></li>
        </ul>
      </div>
      <div>
        <h4>Explore</h4>
        <ul>
          <li><a href="stay.html">Stay</a></li>
          <li><a href="dining.html">Dining</a></li>
          <li><a href="experiences.html">Experiences</a></li>
          <li><a href="events.html">Weddings &amp; Events</a></li>
          <li><a href="rates.html">Rates &amp; Packages</a></li>
          <li><a href="gallery.html">Gallery</a></li>
        </ul>
      </div>
      <div>
        <h4>Find us</h4>
        <ul>
          <li><a href="{e(CT['maps_link'])}" target="_blank" rel="noopener">{addr}</a></li>
          <li style="margin-top:10px"><a href="{e(CT['instagram'])}" target="_blank" rel="noopener">Instagram</a> · <a href="{e(CT['youtube'])}" target="_blank" rel="noopener">YouTube</a></li>
          <li><a href="contact.html#partners">Travel partners</a></li>
        </ul>
      </div>
    </div>
    <div class="base">
      <span>© 2026 {e(B['name'].title())} · JD Stays &amp; Hospitality, JD Group of Companies</span>
      <span><a href="rates.html#terms">Booking terms</a> · <a href="journal/luxury-lakeside-retreat-udaipur.html">Journal</a></span>
    </div>
  </div>
</footer>
<nav class="mbar" aria-label="Quick actions"><a href="{e(wa(CT['phone']))}">WhatsApp</a><a href="{e(BOOK)}">Book a stay</a></nav>
<script src="assets/js/site.js?v={VER}"></script>
</body>
</html>
"""


def page_hero(h):
    return f"""<section class="phero" style="padding:0">
  <img src="{e(img(h['image']))}" alt="{e(h['title'])}" style="object-position:{e(h.get('photo_position') or 'center')}">
  <div class="in"><span class="label">{e(h['label'])}</span><h1>{e(h['title'])}</h1></div>
</section>
"""


def facts(items, count=False):
    out = []
    for f in items:
        n = str(f["number"])
        dc = f' data-count="{re.sub(r"[^0-9]", "", n)}"' if count and re.fullmatch(r"[\d,]+", n) else ""
        out.append(f'<div><b{dc}>{e(n)}</b><span>{e(f["label"])}</span></div>')
    return '<div class="facts rv">\n      ' + "\n      ".join(out) + "\n    </div>"


def notes(cols):
    return '<div class="notes">' + "".join(
        f'\n      <div class="rv"><h3>{e(c["title"])}</h3><ul>' + "".join(f"<li>{e(i)}</li>" for i in c["items"]) + "</ul></div>"
        for c in cols) + "\n    </div>"


def packs(P):
    num = P.get("whatsapp_number") or CT["phone"]
    cards = []
    for p in P["packages"]:
        sig = p.get("highlight")
        lis = "".join(f"<li>{e(i)}</li>" for i in p["includes"])
        link = e(wa(num, f"Hi, I'd like to book the {p['name']} package"))
        cards.append(f'<div class="pack{" sig" if sig else ""}"><span class="label">{e(p["tag"])}</span><h3>{e(p["name"])}</h3>'
                     f'<div class="amt">{e(p["price"])}</div><div class="per">{e(p["per"])}</div><ul>{lis}</ul>'
                     f'<a class="btn {"btn-gold" if sig else "btn-line"}" href="{link}">Book on WhatsApp</a></div>')
    return '<div class="packs rv">\n      ' + "\n      ".join(cards) + "\n    </div>"


def motion(b):
    """Scroll animations: photo unveil, parallax inset, alternating slide-in tiles."""
    b = b.replace('class="media rv"', 'class="media rv-zoom"').replace('class="media tall rv"', 'class="media tall rv-zoom"')
    b = b.replace('<img class="inset"', '<img data-par="-0.10" class="inset"')
    b = b.replace('<div class="ph"><img', '<div class="ph rv-zoom"><img')
    n = [0]

    def side(m):
        n[0] += 1
        return m.group(1) + ("rv-l" if n[0] % 2 else "rv-r")
    b = re.sub(r'(class="tile )rv', side, b)
    b = re.sub(r'(class="trip )rv', side, b)
    return b


# ------------------------------------------------------------------ pages
def home():
    H, P = C("home"), C("packages")
    h = H["hero"]
    reel = "\n    ".join(f'<figure><img src="{e(img(p["image"]))}" alt="{e(p["caption"])}" loading="lazy"><figcaption>{e(p["caption"])}</figcaption></figure>' for p in H["reel"]["photos"])
    room_rows = []
    for r in C("stay")["rooms"]:
        g = next((d["value"] for d in r["details"] if d["label"].lower() == "guests"), "")
        v = next((d["value"] for d in r["details"] if d["label"].lower() in ("view", "beds")), "")
        room_rows.append(f'<a href="stay.html#{slug(r["name"])}" data-t="{e(r["name"])}"><span><span class="nm">{e(r["name"])}</span><span class="ds">{e(" · ".join(x for x in (g, v) if x))}</span></span>'
                         f'<span class="pr"><span class="live-l">from </span><b class="live">{e(r["price"])}</b></span></a>')
    tiles = []
    for t in H["experiences"]["tiles"]:
        pr = f'<span class="pr">{e(t["price"])}</span>' if t.get("price") else ""
        tiles.append(f'<a class="tile rv" href="{e(t.get("link") or "experiences.html")}"><img src="{e(img(t["image"]))}" alt="{e(t["title"])}" loading="lazy"><span class="cap"><h3>{e(t["title"])}</h3><p>{e(t["text"])}</p>{pr}</span></a>')
    stories = "\n      ".join(f'<a class="rv" href="{e(s["link"])}"><img src="{e(img(s["image"]))}" alt="{e(s["title"])}" loading="lazy"><span class="k">{e(s["tag"])}</span><h3>{e(s["title"])}</h3></a>' for s in H["journal"]["stories"])
    ig = "\n      ".join(f'<a href="{e(CT["instagram"])}" target="_blank" rel="noopener"><img src="{e(img(p))}" alt="The Udaisarovar on Instagram" loading="lazy"></a>' for p in H["instagram"]["photos"])
    lotus = e(img(B["lotus_logo"]))
    D, EV, W, ST_ = H["dining"], H["events"], H["welcome"], H["stay"]
    video = f'<video class="hero-video" autoplay muted loop playsinline preload="auto" aria-hidden="true" data-src="{e(img(h["video"]))}"></video>' if h.get("video") else ""
    return f"""
<main id="top">
<section class="hero" style="padding:0">
  <div class="media">
    <picture>
      <source media="(max-width:760px)" srcset="{e(img(h.get('phone_photo') or h['photo']))}">
      <img src="{e(img(h['photo']))}" alt="The Udaisarovar on the shore of Udai Sagar lake, Udaipur" style="object-position:center 55%">
    </picture>
    {video}
  </div>
  <div class="in">
    <h1>{e(h['title'])} <em>{e(h['title_italic'])}</em></h1>
    <p class="sub">{e(h['subtitle'])}</p>
  </div>
  <span class="scroll-cue" aria-hidden="true"></span>
  <div class="vload" aria-hidden="true"><div class="bloom">{RING}<img src="{lotus}" alt=""></div></div>
</section>

<div class="bookbar" id="book-online">
  <form id="jd-book" action="{e(BOOK)}" method="get" aria-label="Check availability">
    <label>Check-in<input type="date" name="in" required></label>
    <label>Check-out<input type="date" name="out" required></label>
    <label>Adults<select name="adults"><option>1</option><option selected>2</option><option>3</option><option>4</option><option>5</option><option>6</option><option>7</option><option>8</option></select></label>
    <div class="fld">Rooms from<span style="font-family:var(--serif);font-size:1.35rem;color:var(--ink);letter-spacing:0;text-transform:none">{e(h['rooms_from'])} <span style="font-family:var(--sans);font-size:.8rem;color:var(--mute)">/ night</span></span></div>
    <button type="submit">Check availability</button>
  </form>
  <div class="after"><span>Best price when you book direct</span><span>Instant confirmation</span><span>No booking fees</span><span>Prefer to talk? <a href="{e(wa(CT['phone'], 'Hello, I would like to book a stay at The Udaisarovar'))}">WhatsApp us</a></span></div>
</div>

<section class="intro">
  <div class="wrap narrow rv">
    <img src="{lotus}" alt="" style="width:74px;margin:0 auto 22px"><span class="label">{e(W['label'])}</span>
    <h2>{e(W['title'])}</h2>
    <p class="lead">{e(W['text'])}</p>
  </div>
  <div class="wrap">
    {facts(H['facts'], count=True)}
  </div>
</section>

<section class="band-sand" style="padding:96px 0 110px" aria-label="{e(H['reel']['label'])}">
  <div class="wrap center rv"><span class="label">{e(H['reel']['label'])}</span><h2>{e(H['reel']['title'])}</h2></div>
  <div class="reel" style="margin-top:56px"><div class="track" data-reel>
    {reel}
  </div></div>
</section>

<section id="stay">
  <div class="wrap">
    <div class="split">
      <div class="media rv">
        <img src="{e(img(ST_['photo']))}" alt="{e(ST_['title'])}" loading="lazy">
        {f'<img class="inset" src="{e(img(ST_["small_photo"]))}" alt="Cottage bedroom" loading="lazy">' if ST_.get('small_photo') else ''}
      </div>
      <div class="text rv">
        <span class="label">{e(ST_['label'])}</span>
        <h2>{e(ST_['title'])}</h2>
        <p class="lead">{e(ST_['text'])}</p>
        <div class="roomlist">
          {chr(10).join(room_rows)}
        </div>
        <p class="small" style="margin-top:14px">Per night with breakfast, before GST.</p>
        <a class="more" href="stay.html">Explore the cottages</a>
      </div>
    </div>
  </div>
</section>

<section class="band-sand" id="experiences">
  <div class="wrap">
    <div class="center rv">
      <span class="label">{e(H['experiences']['label'])}</span>
      <h2>{e(H['experiences']['title'])}</h2>
    </div>
    <div class="tiles">
      {chr(10).join(tiles)}
    </div>
  </div>
</section>

<section id="dining">
  <div class="wrap">
    <div class="split rev">
      <div class="media tall rv">
        <img src="{e(img(D['photo']))}" alt="{e(D['title'])}" loading="lazy">
      </div>
      <div class="text rv">
        <span class="label">{e(D['label'])}</span>
        <h2>{e(D['title'])}</h2>
        <p class="lead">{e(D['text'])}</p>
        <p class="small" style="margin-top:16px">{e(D['hours'])}</p>
        <a class="more" href="dining.html">See the menu</a>
      </div>
    </div>
  </div>
</section>

<section class="feature" style="padding:0" id="events">
  <img src="{e(img(EV['photo']))}" alt="{e(EV['title'])}" loading="lazy">
  <div class="in">
    <div class="card rv">
      <span class="label">{e(EV['label'])}</span>
      <h2>{e(EV['title'])}</h2>
      <p class="lead">{e(EV['text'])}</p>
      <p style="margin-top:18px">{e(EV['price_line'])}</p>
      <div class="btns"><a class="btn btn-dark" href="events.html">Plan your event</a></div>
    </div>
  </div>
</section>

<section id="packages">
  <div class="wrap">
    <div class="center rv">
      <span class="label">{e(P['label'])}</span>
      <h2>{e(P['title'])}</h2>
      <p class="lead">{e(P['text'])}</p>
    </div>
    {packs(P)}
    <p class="center small" style="margin-top:22px">{e(P['note'])} <a href="rates.html">All rates and packages</a></p>
  </div>
</section>

<section class="band-sand" id="journal">
  <div class="wrap">
    <div class="center rv"><span class="label">{e(H['journal']['label'])}</span><h2>{e(H['journal']['title'])}</h2></div>
    <div class="jr">
      {stories}
    </div>
  </div>
</section>

<section id="instagram" class="center">
  <div class="wrap">
    <span class="label">{e(H['instagram']['label'])}</span>
    <h2><a href="{e(CT['instagram'])}" target="_blank" rel="noopener" style="text-decoration:none">{e(CT['instagram_handle'])}</a></h2>
    <div class="strip">
      {ig}
    </div>
  </div>
</section>
</main>
<script>
/* Old one-page links (theudaisarovar.com/#rates etc.) now open the matching page */
(function(){{var m={{stay:'stay.html',dining:'dining.html',experiences:'experiences.html',videos:'experiences.html#videos',sightseeing:'experiences.html#sightseeing',events:'events.html',packages:'rates.html#packages',rates:'rates.html',terms:'rates.html#terms','guest-app':'contact.html#guest-app',contact:'contact.html',partners:'contact.html#partners',why:'index.html'}};var h=location.hash.slice(1);if(m[h])location.replace(m[h]);}})();
</script>
"""


def stay():
    T = C("stay")
    rooms = []
    for r in T["rooms"]:
        dl = "".join(f"<dt>{e(d['label'])}</dt><dd>{e(d['value'])}</dd>" for d in r["details"])
        rooms.append(f"""      <article class="room rv" id="{slug(r['name'])}" data-t="{e(r['name'])}">
        <div class="ph"><img src="{e(img(r['photo']))}" alt="{e(r['name'])} at The Udaisarovar" loading="lazy"></div>
        <div>
          <span class="no">{e(r['count'])}</span>
          <h3>{e(r['name'])}</h3>
          <p>{e(r['text'])}</p>
          <dl>{dl}</dl>
          <div class="price-line"><span class="live-l">From </span><span class="live">{e(r['price'])}</span> <small>/ night + GST</small></div>
          <div class="btns" style="margin-top:22px"><a class="btn btn-dark" href="{e(BOOK)}">Check dates</a></div>
        </div>
      </article>""")
    els = "\n      ".join(f'<div><b>{e(x["name"])}</b><span>{e(x["label"])}</span></div>' for x in T["elements"])
    BO = T["buyout"]
    opts = "".join(f"""
      <div class="rv" style="border-top:1px solid var(--gold);padding-top:30px">
        <h3>{e(o['title'])}</h3>
        <div class="price-line">{e(o['price'])} <small>{e(o['per'])}</small></div>
        <p style="margin-top:14px">{e(o['text'])}</p>
      </div>""" for o in BO["options"])
    return page_hero(T["hero"]) + f"""
<main>
<section class="intro">
  <div class="wrap narrow rv">
    <h2>{e(T['intro']['title'])}</h2>
    <p class="lead">{e(T['intro']['text'])}</p>
  </div>
  <div class="wrap">
    <div class="elements rv">
      {els}
    </div>
    <div class="rooms">
{chr(10).join(rooms)}
    </div>
  </div>
</section>

<section class="band-ink" id="buyout">
  <div class="wrap">
    <div class="center rv">
      <span class="label">{e(BO['label'])}</span>
      <h2>{e(BO['title'])}</h2>
      <p class="lead">{e(BO['text'])}</p>
    </div>
    <div class="cols2" style="margin-top:64px">{opts}
    </div>
    <div class="btns center" style="justify-content:center"><a class="btn btn-gold" href="{e(wa(CT['phone'], 'Hello, I want to book all 5 cottages / a full property buyout'))}">Enquire on WhatsApp</a></div>
  </div>
</section>

<section>
  <div class="wrap">
    {notes(T['notes'])}
    <div class="btns" style="justify-content:center"><a class="btn btn-dark" href="{e(BOOK)}">Book your stay</a><a class="btn btn-line" href="rates.html">Seasonal rates</a></div>
  </div>
</section>
</main>
"""


def dining():
    T = C("dining")
    I = T["intro"]
    menu = "\n          ".join(
        f'<div><span>{e(m["item"])}</span><span{" class=\"req\"" if not re.search(r"\d", m["price"]) else ""}>{e(m["price"])}</span></div>' for m in T["menu"])
    pos = ["center 70%", "center 30%", "center"]
    photos = "\n      ".join(f'<img src="{e(img(p))}" alt="Dining at Lake City Café" loading="lazy" style="object-position:{pos[i % 3]}">' for i, p in enumerate(T["photos"]))
    M = T["meal_plans"]
    return page_hero(T["hero"]) + f"""
<main>
<section>
  <div class="wrap">
    <div class="split rev">
      <div class="media rv">
        <img src="{e(img(I['photo']))}" alt="{e(I['title'])}" loading="lazy" style="aspect-ratio:4/5">
      </div>
      <div class="text rv">
        <span class="label">{e(I['label'])}</span>
        <h2>{e(I['title'])}</h2>
        <p class="lead">{e(I['text'])}</p>
        <div class="menu">
          {menu}
        </div>
        <p class="small" style="margin-top:14px">{e(T['menu_note'])}</p>
      </div>
    </div>
    <div class="row3 rv">
      {photos}
    </div>
  </div>
</section>
<section class="band-sand">
  <div class="wrap narrow center rv">
    <span class="label">{e(M['label'])}</span>
    <h2>{e(M['title'])}</h2>
    <p class="lead">{e(M['text'])}</p>
    <div class="btns"><a class="btn btn-dark" href="{e(BOOK)}">Book a stay</a><a class="btn btn-line" href="rates.html#meals">See all rates</a></div>
  </div>
</section>
</main>
"""


def experiences():
    T = C("experiences")
    rows = []
    for i, x in enumerate(T["experiences"]):
        extra = f'<p class="price-line">{e(x["price"])}</p>' if x.get("price") else ""
        rows.append(f"""
    <div class="split{' rev' if i % 2 else ''}" id="{e(x.get('id') or slug(x['title']))}" style="margin-top:110px">
      <div class="media rv"><img src="{e(img(x['photo']))}" alt="{e(x['title'])}" loading="lazy"></div>
      <div class="text rv"><h2 style="font-size:clamp(2rem,3.4vw,2.9rem)">{e(x['title'])}</h2><p class="lead">{e(x['text'])}</p>{extra}</div>
    </div>""")
    V = T["videos"]
    vids = "\n      ".join(
        f'<figure class="vid rv"><button class="yt" data-id="{e(v["youtube_id"])}" aria-label="Play video: {e(v["title"])}" style="background-image:url(https://i.ytimg.com/vi/{e(v["youtube_id"])}/oar2.jpg)"><span class="play">{PLAY}</span></button><figcaption><b>{e(v["title"])}</b>{e(v["text"])}</figcaption></figure>'
        for v in V["list"])
    SS = T["sightseeing"]
    trips = "\n      ".join(
        f'<div class="trip rv"><img src="{e(img(t["photo"]))}" alt="{e(t["title"])}" loading="lazy"><h3>{e(t["title"])}</h3><span class="pr">{e(t["price"])}</span><p>{e(t["text"])}</p></div>'
        for t in SS["trips"])
    return page_hero(T["hero"]) + f"""
<main>
<section style="padding-top:40px">
  <div class="wrap">{"".join(rows)}
    <div style="margin-top:110px">{notes(T['notes'])}</div>
  </div>
</section>

<section class="band-ink" id="videos">
  <div class="wrap">
    <div class="center rv"><span class="label">{e(V['label'])}</span><h2>{e(V['title'])}</h2></div>
    <div class="vids">
      {vids}
    </div>
    <div class="center"><a class="more" href="{e(CT['youtube'])}?sub_confirmation=1" target="_blank" rel="noopener">More on YouTube</a></div>
  </div>
</section>

<section id="sightseeing">
  <div class="wrap">
    <div class="center rv">
      <span class="label">{e(SS['label'])}</span>
      <h2>{e(SS['title'])}</h2>
      <p class="lead">{e(SS['text'])}</p>
    </div>
    <div class="trips">
      {trips}
    </div>
  </div>
</section>
</main>
"""


def events():
    T = C("events")
    tiles = "\n      ".join(
        f'<div class="tile rv"><img src="{e(img(x["photo"]))}" alt="{e(x["title"])}" loading="lazy"><span class="cap"><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></span></div>'
        for x in T["event_types"])
    BO, V = T["buyout"], T["videos"]
    vids = "\n      ".join(
        f'<figure style="margin:0" class="rv"><video src="{e(img(v["video"]))}" poster="{e(img(v["poster"]))}" controls preload="none" playsinline></video><figcaption class="small" style="margin-top:12px">{e(v["caption"])}</figcaption></figure>'
        for v in V["list"])
    inset = f'<img class="inset" src="{e(img(BO["small_photo"]))}" alt="Wedding stage by the lake" loading="lazy">' if BO.get("small_photo") else ""
    brochure = f'<a class="btn btn-line" href="{e(img(BO["brochure"]))}" target="_blank" rel="noopener">Event brochure (PDF)</a>' if BO.get("brochure") else ""
    return page_hero(T["hero"]) + f"""
<main>
<section class="intro">
  <div class="wrap narrow rv">
    <h2>{e(T['intro']['title'])}</h2>
    <p class="lead">{e(T['intro']['text'])}</p>
  </div>
  <div class="wrap">
    {facts(T['facts'])}
  </div>
</section>

<section class="band-sand" style="padding-top:96px">
  <div class="wrap">
    <div class="tiles" style="margin-top:0">
      {tiles}
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="split">
      <div class="media tall rv">
        <img src="{e(img(BO['photo']))}" alt="{e(BO['title'])}" loading="lazy" style="object-position:center 30%">
        {inset}
      </div>
      <div class="text rv">
        <span class="label">{e(BO['label'])}</span>
        <h2>{e(BO['title'])}</h2>
        <p class="lead">{e(BO['text'])}</p>
        <div class="price-line">{e(BO['price'])} <small>{e(BO['per'])}</small></div>
        <p style="margin-top:18px">{e(BO['rooms_only'])}</p>
        <p class="small" style="margin-top:12px">{e(BO['note'])}</p>
        <div class="btns"><a class="btn btn-dark" href="{e(wa(CT['phone'], 'Hello, I want to plan an event at The Udaisarovar'))}">Plan on WhatsApp</a>{brochure}</div>
      </div>
    </div>
  </div>
</section>

<section class="band-ink">
  <div class="wrap">
    <div class="center rv"><span class="label">{e(V['label'])}</span><h2>{e(V['title'])}</h2></div>
    <div class="evvids">
      {vids}
    </div>
  </div>
</section>
</main>
"""


def rates():
    T, P = C("rates"), C("packages")
    ROOMS = [("lake_view", "Lake View Cottage"), ("pool_view", "Pool View Cottage"), ("family_suite", "Family Suite")]

    def season_table(t):
        rows = []
        for g in t["groups"]:
            for i, (k, name) in enumerate(ROOMS):
                per = f'<td rowspan="3" class="per"><b>{e(g["period"])}</b><span>{e(g["note"])}</span></td>' if i == 0 else ""
                rows.append(f'<tr{" class=\"grp\"" if i == 0 else ""}>{per}<td>{name}</td><td class="n">{e(g[k])}</td></tr>')
        return (f'<table class="rates">\n      <thead><tr><th>{e(t["title"])}</th><th>Room</th><th class="n">Rate / night</th></tr></thead>\n      <tbody>\n'
                + "\n".join(rows) + "\n      </tbody>\n    </table>")

    def night_table(rows):
        out, month = [], None
        for r in rows:
            if r["month"] != month:
                month = r["month"]
                out.append(f'<tr class="mon"><td colspan="4">{e(month)}</td></tr>')
            out.append(f'<tr{" class=\"ms\"" if r.get("min_2_nights") else ""}><td class="dt">{e(r["dates"])}</td><td class="n">{e(r["lake_view"])}</td><td class="n">{e(r["pool_view"])}</td><td class="n">{e(r["family_suite"])}</td></tr>')
        return ('<table class="rates"><thead><tr><th>Dates (nights)</th><th class="n">Lake View</th><th class="n">Pool View</th><th class="n">Family Suite</th></tr></thead><tbody>'
                + "\n".join(out) + "</tbody></table>")

    nights = T["nights"]
    half = (len(nights) + 1) // 2
    seasons = "".join(f'<div class="tbl rv"{" style=\"margin-top:56px\"" if i else ""}>{season_table(t)}</div>' for i, t in enumerate(T["season_tables"]))

    def plan(p):
        a, _, b = p.partition(" – ")
        return f"<b>{e(a)}</b> – {e(b)}" if b else e(p)
    meals = "".join(f'<tr><td>{plan(m["plan"])}</td><td class="n">{e(m["lake_pool"])}</td><td class="n">{e(m["family_suite"])}</td></tr>' for m in T["meal_plans"])
    extras = "".join(f'<tr><td>{e(x["item"])}</td><td class="n">{e(x["rate"])}</td></tr>' for x in T["extras"])
    phones = " · ".join(f'<a href="{tel(p)}">{e(p)}</a>' for p in CT.get("package_phones", []))
    return page_hero(T["hero"]) + f"""
<main>
<section id="packages">
  <div class="wrap">
    <div class="center rv">
      <span class="label">{e(P['label'])}</span>
      <h2>{e(P['title'])}</h2>
      <p class="lead">{e(P['text'])}</p>
    </div>
    {packs(P)}
    <p class="center small" style="margin-top:22px">Package reservations: {phones}. {e(P['note'])}</p>
  </div>
</section>

<section class="band-sand" id="rates">
  <div class="wrap">
    <div class="rv">
      <span class="label">Room rates · with breakfast</span>
      <h2>Seasonal rates</h2>
      <p class="lead">{e(T['seasons_intro'])} For the live price on your dates, <a href="{e(BOOK)}">check online</a>.</p>
    </div>
    {seasons}
    <details class="more-rates">
      <summary>{e(T['nights_title'])}</summary>
      <p class="small" style="margin-bottom:8px">₹ per room per night with breakfast, before GST. Dates marked "min 2 nights" need a stay of at least two nights.</p>
      <div class="cols2"><div class="tbl" style="margin-top:0">{night_table(nights[:half])}</div><div class="tbl" style="margin-top:0">{night_table(nights[half:])}</div></div>
    </details>
  </div>
</section>

<section id="meals">
  <div class="wrap">
    <div class="cols2">
      <div class="rv">
        <h2 style="font-size:clamp(1.9rem,3vw,2.6rem)">Meal plans</h2>
        <div class="tbl"><table class="rates"><thead><tr><th>Meal-plan supplement<small>per room per night, added to CP</small></th><th class="n">Lake / Pool</th><th class="n">Family Suite</th></tr></thead><tbody>{meals}</tbody></table></div>
        <p class="small" style="margin-top:10px">{e(T['meal_note'])}</p>
      </div>
      <div class="rv">
        <h2 style="font-size:clamp(1.9rem,3vw,2.6rem)">Extras &amp; buyouts</h2>
        <div class="tbl"><table class="rates"><thead><tr><th>Extras</th><th class="n">Rate</th></tr></thead><tbody>{extras}</tbody></table></div>
      </div>
    </div>
    <p class="small" style="margin-top:30px">{e(T['gst_note'])}</p>
    <div class="btns"><a class="btn btn-dark" href="{e(BOOK)}">Book now</a><a class="btn btn-line" href="{e(wa(CT['phone']))}">Ask on WhatsApp</a></div>
  </div>
</section>

<section class="band-ink" id="terms">
  <div class="wrap">
    <div class="rv"><span class="label">Booking &amp; payment terms</span><h2>Simple, transparent terms</h2></div>
    {notes(T['terms'])}
  </div>
</section>
</main>
"""


def gallery():
    T = C("gallery")
    nav = " ".join(f'<a href="#{slug(g["title"])}">{e(g["title"])}</a>' for g in T["groups"])
    groups = []
    for g in T["groups"]:
        figs = "\n".join(f'<figure><img src="{e(img(p["image"]))}" alt="{e(p.get("caption") or g["title"])}" loading="lazy"><figcaption>{e(p.get("caption", ""))}</figcaption></figure>' for p in g["photos"])
        groups.append(f'<h2 class="gal-h" id="{slug(g["title"])}">{e(g["title"])}</h2>\n<div class="gal" style="margin-top:28px">\n{figs}\n</div>')
    return f"""<main>
<section style="padding-top:88px">
  <div class="wrap">
    <div class="center">
      <span class="label">Gallery</span>
      <h1 style="font-size:clamp(2.6rem,5vw,4.4rem)">{e(T['title'])}</h1>
      <div class="gal-nav" style="justify-content:center">{nav}</div>
    </div>
    {"".join(groups)}
    <div class="center" style="margin-top:72px"><a class="more" href="{e(CT['instagram'])}" target="_blank" rel="noopener">More on Instagram, {e(CT['instagram_handle'])}</a></div>
  </div>
</section>
</main>
"""


def contact():
    T = C("contact")
    G, PT = T["guest_app"], T["partners"]
    pk = " · ".join(f'<a href="{tel(p)}">{e(p)}</a>' for p in CT.get("package_phones", []))
    feats = "\n          ".join(f"<div><span>{e(f)}</span><span></span></div>" for f in G["features"])
    return page_hero(T["hero"]) + f"""
<main>
<section>
  <div class="wrap">
    <div class="contact-grid">
      <div class="rv">
        <h2>{e(T['title'])}</h2>
        <p class="lead">{e(T['text'])}</p>
        <dl class="clist">
          <div><dt>WhatsApp &amp; calls</dt><dd><a href="{e(wa(CT['phone']))}">{e(CT['phone'])}</a></dd></div>
          {f'<div><dt>Package bookings</dt><dd>{pk}</dd></div>' if pk else ''}
          <div><dt>Book online</dt><dd><a href="{e(BOOK)}">{e(re.sub(r'^https?://|/$', '', BOOK))}</a></dd></div>
          <div><dt>Address</dt><dd><a href="{e(CT['maps_link'])}" target="_blank" rel="noopener">{e(CT['address'])}</a></dd></div>
          <div><dt>Instagram</dt><dd><a href="{e(CT['instagram'])}" target="_blank" rel="noopener">{e(CT['instagram_handle'])}</a></dd></div>
          <div><dt>YouTube</dt><dd><a href="{e(CT['youtube'])}" target="_blank" rel="noopener">Udaisarovar Resort</a></dd></div>
          <div><dt>Managed by</dt><dd><a href="{e(CT['jd_group_link'])}" target="_blank" rel="noopener">JD Stays &amp; Hospitality, JD Group</a></dd></div>
        </dl>
        <div class="btns"><a class="btn btn-dark" href="{e(wa(CT['phone']))}">WhatsApp us</a><a class="btn btn-line" href="{e(CT['maps_link'])}" target="_blank" rel="noopener">Get directions</a></div>
      </div>
      <div class="map rv">
        <iframe title="The Udaisarovar on Google Maps" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen src="https://maps.google.com/maps?q=24.5604582,73.8056938&amp;z=14&amp;hl=en&amp;output=embed"></iframe>
      </div>
    </div>
  </div>
</section>

<section class="band-sand" id="guest-app">
  <div class="wrap">
    <div class="split rev">
      <div class="media rv"><img src="{e(img(G['photo']))}" alt="{e(G['title'])}" loading="lazy" style="aspect-ratio:4/5"></div>
      <div class="text rv">
        <span class="label">{e(G['label'])}</span>
        <h2>{e(G['title'])}</h2>
        <p class="lead">{e(G['text'])}</p>
        <div class="menu">
          {feats}
        </div>
        <p class="small" style="margin-top:14px">{e(G['note'])}</p>
        <div class="btns"><a class="btn btn-dark" href="{e(CT['guest_app_link'])}">Open the Guest App</a></div>
      </div>
    </div>
  </div>
</section>

<section class="band-ink" id="partners" style="padding:88px 0">
  <div class="wrap partner">
    <div><span class="label">{e(PT['label'])}</span><h2>{e(PT['title'])}</h2><p class="lead" style="margin-top:14px">{e(PT['text'])}</p></div>
    <a class="btn btn-gold" href="{e(wa(CT['phone'], 'Hi, I am a travel agent and would like your B2B partner rates'))}">Request B2B rates</a>
  </div>
</section>
</main>
"""


def schema():
    st = C("stay")
    offers = [{"@type": "Offer", "name": r["name"], "priceCurrency": "INR", "price": re.sub(r"\D", "", r["price"])} for r in st["rooms"]]
    offers += [{"@type": "Offer", "name": o["title"], "priceCurrency": "INR", "price": re.sub(r"\D", "", o["price"])} for o in st["buyout"]["options"]]
    data = {
        "@context": "https://schema.org", "@type": ["Hotel", "Resort", "LodgingBusiness"], "name": "The Udaisarovar - Lakeside Paradise",
        "description": S["footer_about"], "url": "https://www.theudaisarovar.com",
        "sameAs": [CT["instagram"], CT["youtube"]], "image": SITE + img(C("home")["hero"]["photo"]),
        "telephone": "+" + digits(CT["phone"]), "priceRange": "₹₹", "currenciesAccepted": "INR",
        "address": {"@type": "PostalAddress", "streetAddress": "Near Udaisagar Lake, Naglaphala, Lakadwas", "addressLocality": "Udaipur",
                    "addressRegion": "Rajasthan", "postalCode": "313003", "addressCountry": "IN"},
        "geo": {"@type": "GeoCoordinates", "latitude": 24.5604582, "longitude": 73.8056938}, "hasMap": CT["maps_link"],
        "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": n, "value": True} for n in
                           ["Lake view", "Infinity pool", "Private cottages", "Full villa buyout", "Lakeside camping", "Free parking", "Restaurant", "Event garden"]],
        "makesOffer": offers,
        "parentOrganization": {"@type": "Organization", "name": "JD Group of Companies", "url": CT["jd_group_link"]},
        "brand": {"@type": "Brand", "name": "JD Stays & Hospitality"},
        "potentialAction": {"@type": "ReserveAction", "target": BOOK},
    }
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False) + "\n</script>\n"


KEYWORDS = '<meta name="keywords" content="best hotel in Udaipur, lakeside hotels in Udaipur, luxury lakeside retreat Udaipur, resort in Udaipur, lake view cottage Udaipur, resort packages Udaipur, villa in Udaipur, camping in Udaipur">\n'


def pages():
    yield "index.html", "", C("home")["seo"], C("home")["hero"]["photo"], home(), True, KEYWORDS + schema()
    for fn, fnc, name, img_key in [("stay.html", stay, "stay", None), ("dining.html", dining, "dining", None),
                                   ("experiences.html", experiences, "experiences", None), ("events.html", events, "events", None),
                                   ("rates.html", rates, "rates", None), ("gallery.html", gallery, "gallery", None),
                                   ("contact.html", contact, "contact", None)]:
        d = C(name)
        image = d.get("hero", {}).get("image") or C("home")["hero"]["photo"]
        yield fn, fn, d["seo"], image, fnc(), False, ""


# ------------------------------------------------------------------ output
COPY = ["assets", "journal", "brochure.pdf", "robots.txt", "sitemap.xml", "CNAME"]


def shrink_images(folder):
    """Big phone photos uploaded through the CMS are resized for the web (only in the published copy)."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed: images published as-is")
        return
    for dp, _, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            p = os.path.join(dp, f)
            if os.path.getsize(p) < 450_000:
                continue
            try:
                im = Image.open(p)
                if im.width > 2000:
                    im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
                if f.lower().endswith((".jpg", ".jpeg")):
                    im.convert("RGB").save(p, quality=82, optimize=True, progressive=True)
                else:
                    im.save(p, optimize=True)
                print("resized", os.path.relpath(p, folder))
            except Exception as ex:
                print("could not resize", f, ex)


def main():
    out = os.path.join(ROOT, "_site")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for item in COPY:
        src = os.path.join(ROOT, item)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(out, item))
        elif os.path.exists(src):
            shutil.copy2(src, out)
    for fn, path, seo, image, body, over, extra in pages():
        page = head(seo, path, image, extra) + header(fn, over) + motion(body) + footer()
        open(os.path.join(out, fn), "w", encoding="utf-8").write(page)
        if "--root" in sys.argv:
            open(os.path.join(ROOT, fn), "w", encoding="utf-8").write(page)
        print("built", fn)
    if "--no-resize" not in sys.argv:
        shrink_images(os.path.join(out, "assets"))


if __name__ == "__main__":
    main()
