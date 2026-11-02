"""The page shell: <head>, header and footer around every page."""

import json

from register import TODAY

from .styles import theme_colors
from .base import E, EXT, LOGO, NAV, SITE, SPRITE, WORLD, big_number, icon


THEME = theme_colors()  # the page background in each theme, from web/styles/tokens.css


class Shell:
    def page(self, path, title, desc, body, *, section="", og_image=None, jsonld=None, scripts=(), lastmod=None, index=True, write=True):
        full_title = f"{title} · Patent Yard" if title != "Patent Yard" else (f"Patent Yard: expired and lapsed patents to build on, and {big_number(WORLD['n'])} records worldwide" if WORLD else "Patent Yard: free-to-use patents from four patent offices")
        cur = ' aria-current="page"'
        nav = "".join(f'<a href="{href}"{cur if section == href else ""}>{label}</a>' for href, label in NAV)
        og = og_image or self.default_og
        ld_json = json.dumps(jsonld, separators=(",", ":")).replace("</", "<\\/") if jsonld else ""
        ld = f'<script type="application/ld+json">{ld_json}</script>' if jsonld else ""
        js = "".join(f'<script type="module" src="/assets/js/{s}.js"></script>' for s in ("app",) + tuple(scripts))  # unversioned: modules import each other by plain path
        doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script src="/assets/js/theme.js"></script>
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Patent Yard">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{og}">
<meta name="twitter:card" content="summary_large_image">
{'' if index else '<meta name="robots" content="noindex">'}
<meta name="theme-color" content="{THEME["light"]}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{THEME["dark"]}" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/atom+xml" title="New on Patent Yard" href="/feed.xml">
<link rel="preload" href="/assets/fonts/hanken-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{self.css}">
{ld}
</head>
<body>
{SPRITE}
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Patent Yard home"><span class="mark">{LOGO}</span><b>Patent Yard</b></a>
    <nav class="mainnav" id="mainnav" aria-label="Main">{nav}</nav>
    <form class="hsearch" action="/browse/" role="search"><svg class="i" aria-hidden="true"><use href="#i-search"/></svg><label class="sr" for="hq">Search patents</label><input id="hq" name="q" type="search" placeholder="Search patents"><kbd class="hk" aria-hidden="true">/</kbd></form>
    <button class="iconbtn cmdbtn" type="button" id="cmdBtn" aria-label="Search and jump (Ctrl K)" title="Search and jump (⌘K)">{icon("search")}</button>
    <button class="iconbtn" type="button" id="themeBtn" aria-label="Switch between light and dark mode" title="Light or dark mode">{icon("sun").replace('class="i"', 'class="i sun"')}{icon("moon").replace('class="i"', 'class="i moon"')}</button>
    <span class="acct" id="acct"><a class="btn secondary sm" href="/account/" aria-label="Sign in">{icon("user")}<span>Sign in</span></a></span>
    <button class="menu-btn" id="menuBtn" aria-controls="mainnav" aria-expanded="false" aria-label="Menu">{icon("menu")}</button>
  </div>
</header>
<main id="main" class="wrap" tabindex="-1">
{body}
</main>
<footer class="foot">
  <div class="wrap">
    <div><b>Patent Yard</b><p class="about">A free register of expired, lapsed and abandoned patents from the US, Europe, Canada and Australia, traced to patent office records, with tools for developing new inventions from them.</p><p class="num" id="footStat">Recently lapsed US patents are rechecked for reinstatement daily</p></div>
    <nav aria-label="Product"><span class="kicker">Product</span><a href="/browse/">Free to use</a><a href="/all/">All patents</a><a href="/opportunities/">Opportunities</a><a href="/studio/">Invention studio</a><a href="/insights/">Insights</a><a href="/fields/">Fields</a></nav>
    <nav aria-label="Your work"><span class="kicker">Your work</span><a href="/account/">My bench</a><a href="/saved/">Saved patents</a><a href="/settings/">Settings</a><a href="/feed.xml">New patents feed (RSS)</a></nav>
    <nav aria-label="Data sources"><span class="kicker">Data sources</span><a href="https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents" {EXT}>USPTO Official Gazette</a><a href="https://ppubs.uspto.gov/pubwebapp/" {EXT}>USPTO Patent Public Search</a><a href="https://patentcenter.uspto.gov/" {EXT}>USPTO Patent Center</a><a href="https://data.epo.org/linked-data/" {EXT}>EPO linked open data</a><a href="https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en" {EXT}>CIPO</a><a href="https://www.ipaustralia.gov.au/" {EXT}>IP Australia IPGOD</a><a href="https://console.cloud.google.com/marketplace/product/google_patents_public_datasets/google-patents-public-data" {EXT}>Google Patents Public Data</a></nav>
    <nav aria-label="About and legal"><span class="kicker">Patent Yard</span><a href="/about/">About</a><a href="/how-it-works/">How it works</a><a href="/how-it-works/#faq">FAQ</a><a href="/contact/">Contact</a><a href="/legal/terms/">Terms</a><a href="/legal/privacy/">Privacy</a><a href="/legal/disclaimer/">Disclaimer</a><a href="/legal/copyright/">Copyright and takedown</a><a href="/legal/accessibility/">Accessibility</a></nav>
    <p class="fine">Patent data comes from the United States Patent and Trademark Office; the European Patent Office's Linked open EP data, used under <a href="https://creativecommons.org/licenses/by/4.0/" {EXT}>CC BY 4.0</a>; the Canadian Intellectual Property Office, and contains information licensed under the <a href="https://open.canada.ca/en/open-government-licence-canada" {EXT}>Open Government Licence – Canada</a>; and IP Australia's IPGOD, used under <a href="https://creativecommons.org/licenses/by/2.5/au/" {EXT}>CC BY 2.5 AU</a>.{" All patents uses Google Patents Public Data, under CC BY 4.0." if WORLD else ""} Patent Yard is not affiliated with any of these offices and does not give legal advice. Plain-English names, summaries, modern angles and build levels are Patent Yard's notes, drafted with Claude (an AI model) from each patent's text.</p>
  </div>
</footer>
<div id="toast" role="status" aria-live="polite"></div>
<script src="/assets/js/config.js"></script>
{js}
</body>
</html>
"""
        if write:
            out = self.dist / path.strip("/") / "index.html" if path.endswith("/") else self.dist / path.lstrip("/")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(doc)
            if index:
                self.pages.append((path, lastmod or TODAY.isoformat()))
        return doc
