#!/usr/bin/env python3
"""Extract the finder's site-read facts from a page DOM saved by Cowork's browser (get_dom).

Cowork's local Edge browser cannot run page JavaScript, so the Claude design's paste-in
walkthrough scripts cannot run. When get_dom saves the full page DOM to a workspace file
("Full output saved to: <path>"), this parser reads that file OFFLINE and returns the same
kind of small JSON record per surface (platform, testing tools, what already exists, the
selectors a variation would touch), for walkthrough.json and candidates.json.

Honesty rules built in:
- The saved DOM format is not documented. When the file does not look like HTML markup,
  `formatRecognized` is false, only plain-text heuristics run, and no selector is recorded.
- A static DOM has no computed visibility, layout or JavaScript globals: nothing here claims an
  element is visible or above the fold. `selectors[*].source` is "static-dom", to be confirmed by
  the screenshot look (references/site-validation.md) before a variation is built on it.
- Input values are never read (checkout fields may hold the person's own details); only labels.
- A missing element is null/"absent", which can be a parser miss as often as a missing feature.

Usage:
  python dom_facts.py <saved-dom-file> --surface home|pdp|collection|cart|checkout_entry|policy
                      [--url <page url>] [--into <walkthrough.json>]
Standard library only; no network, no browser, no writes except --into.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SURFACE_KEYS = {'home': 'read_home', 'pdp': 'read_pdp', 'collection': 'read_collection', 'cart': 'read_cart',
                'checkout_entry': 'read_checkout_entry', 'policy': 'read_policy'}
TESTING_TOOLS = [('Optimizely', r'optimizely'), ('VWO', r'_vwo|visualwebsiteoptimizer|vwo_code'), ('AB Tasty', r'abtasty'),
                 ('Kameleoon', r'kameleoon'), ('Convert', r'convertexperiments|convert\.com/js'), ('Dynamic Yield', r'dynamicyield|dy-api'),
                 ('Intelligems', r'intelligems'), ('Shoplift', r'shoplift'), ('Visually', r'visually\.io|visually-'),
                 ('Google Optimize', r'googleoptimize|optimize\.google'), ('Adobe Target', r'adobe.?target|mbox\.js|at\.js')]
PLATFORMS = [('shopify', r'cdn\.shopify\.com|shopify-section|Shopify\.theme|myshopify\.com'), ('bigcommerce', r'bigcommerce|stencil-utils|cdn\d*\.bigcommerce'),
             ('magento', r'Magento_|mage/|data-mage-init'), ('sfcc', r'demandware|dwvar_|on/demandware'), ('woocommerce', r'woocommerce|wc-ajax')]
REVIEW_WIDGETS = [('Judge.me', r'judge\.?me|jdgm'), ('Yotpo', r'yotpo'), ('Okendo', r'okendo'), ('Stamped', r'stamped'), ('Loox', r'loox'), ('Trustpilot', r'trustpilot'), ('Klarna', r'klarna'), ('Afterpay', r'afterpay|clearpay')]
EXPRESS = r'shopify-payment-button|dynamic-checkout|shop-pay|shopify-pay|apple-pay|google-pay|paypal|amazon-pay'
POLICY_RE = re.compile(r'(free (standard |express |ground )?(shipping|delivery)|orders? (over|above|of)|\$\s?\d|£\s?\d|€\s?\d|\d+\s*(business |working )?days?|return(s)? within|refund|restocking|exchange)', re.I)
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
GOOD_CLASS = re.compile(r'^[a-zA-Z][\w-]{2,40}$')
BAD_CLASS = re.compile(r'^(css|sc|jsx|_|is-|has-)-?|[a-f0-9]{6,}|\d{3,}')


class Node:
    __slots__ = ('tag', 'attrs', 'parent', 'children', 'text')

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children, self.text = tag, attrs, parent, [], []

    def cls(self):
        return self.attrs.get('class', '') or ''

    def all_text(self, limit=400, lines=False):
        """Visible-text approximation; lines=True keeps one line per text node so block texts don't merge."""
        out, stack = [], [self]
        while stack and sum(len(x) for x in out) < limit * 2:
            n = stack.pop()
            if n.tag in ('script', 'style', 'noscript', 'template'):
                continue
            out.extend(n.text)
            stack.extend(reversed(n.children))
        if lines:
            return '\n'.join(t for t in (re.sub(r'\s+', ' ', x).strip() for x in out) if t)[:limit]
        return re.sub(r'\s+', ' ', ' '.join(out)).strip()[:limit]

    def walk(self):
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', {}, None)
        self.cur = self.root
        self.tags = 0
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        self.tags += 1
        node = Node(tag, {k: (v or '') for k, v in attrs if k != 'value'}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.tags += 1
        self.cur.children.append(Node(tag, {k: (v or '') for k, v in attrs if k != 'value'}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if self.cur.tag == 'script':
            self.scripts.append(data[:20000])
        if data.strip():
            self.cur.text.append(data)


def selector(n):
    if n is None:
        return None
    ident = n.attrs.get('id', '')
    if ident and re.fullmatch(r'[A-Za-z][\w-]{1,60}', ident) and not re.search(r'\d{3,}|[a-f0-9]{8,}', ident):
        return f'{n.tag}#{ident}'
    classes = [c for c in n.cls().split() if GOOD_CLASS.match(c) and not BAD_CLASS.search(c)][:2]
    sel = n.tag + ''.join('.' + c for c in classes)
    for key in ('name', 'action', 'data-section-type', 'type', 'aria-label'):
        if not classes and n.attrs.get(key) and len(n.attrs[key]) < 60 and '"' not in n.attrs[key]:
            return f'{sel}[{key}="{n.attrs[key]}"]'
    return sel


def record(n):
    if n is None:
        return None
    block = n.parent
    while block is not None and block.parent is not None and block.tag in ('span', 'a', 'label', 'strong', 'em', 'b', 'i', 'button', 'p'):
        block = block.parent
    column = block.parent if block is not None else None
    return {'selector': selector(n), 'block': selector(block) if block and block.tag != '#root' else None,
            'column': selector(column) if column and column.tag != '#root' else None, 'source': 'static-dom'}


def find(root, pred, scope=None):
    for n in (scope or root).walk():
        if n.tag != '#root' and pred(n):
            return n
    return None


def find_all(root, pred, scope=None):
    return [n for n in (scope or root).walk() if n.tag != '#root' and pred(n)]


def has(n, pattern):
    return re.search(pattern, n.cls() + ' ' + n.attrs.get('id', '') + ' ' + n.attrs.get('aria-label', ''), re.I) is not None


def detect(raw, scripts):
    blob = raw if len(raw) < 4_000_000 else raw[:4_000_000]
    platform = next((name for name, pat in PLATFORMS if re.search(pat, blob)), None)
    tools = [name for name, pat in TESTING_TOOLS if re.search(pat, blob, re.I)]
    country = re.search(r'Shopify\.country\s*=\s*"([A-Z]{2})"', blob)
    currency = re.search(r'Shopify\.currency\s*=\s*\{[^}]*"active"\s*:\s*"([A-Z]{3})"', blob)
    return platform, tools, {'shopifyOnlineStoreTheme': bool(re.search(r'Shopify\.theme\s*=', blob)),
                             'country': country.group(1) if country else None, 'currency': currency.group(1) if currency else None}


def sentences(text, pattern, limit=6):
    found = []
    for s in re.split(r'(?<=[.!?])\s+|\s{2,}|\n', text):
        s = s.strip()
        if 8 < len(s) < 240 and pattern.search(s) and s not in found:
            found.append(s)
        if len(found) >= limit:
            break
    return found


def parse(raw, surface, url=None):
    tree = Tree()
    try:
        tree.feed(raw)
        tree.close()
    except Exception as exc:  # html.parser is lenient; a crash means the format is not markup
        tree.tags = 0
        parse_error = f'{type(exc).__name__}: {exc}'
    else:
        parse_error = None
    root = tree.root
    out = {'surface': surface, 'url': url, 'source': 'saved get_dom file', 'formatRecognized': parse_error is None and (tree.tags >= 20 or (tree.tags >= 5 and re.search(r'<(html|body|main|div|section)\b', raw[:200000], re.I) is not None)),
           'notes': [], 'selectors': {}}
    if not out['formatRecognized']:
        text = re.sub(r'[ \t\r\f\v]+', ' ', raw[:200000])
        out['notes'].append('Saved DOM was not recognized as HTML markup' + (f' ({parse_error})' if parse_error else '') + '; plain-text heuristics only, no selectors. Use the screenshot checklist for this surface.')
        out['textHeuristics'] = {'addToCart': bool(re.search(r'add to (cart|bag|basket)', text, re.I)), 'quickAdd': bool(re.search(r'quick (add|shop|view)', text, re.I)),
                                 'freeShipping': sentences(text, re.compile(r'free (shipping|delivery)', re.I), 3), 'checkout': bool(re.search(r'check ?out', text, re.I))}
        return out
    platform, tools, store = detect(raw, tree.scripts)
    out.update(platform=platform, testingTools=tools, storefront=store)
    html_el = find(root, lambda n: n.tag == 'html')
    if html_el is not None and html_el.attrs.get('lang'):
        store['htmlLang'] = html_el.attrs['lang']
    main = find(root, lambda n: n.tag == 'main') or root
    out['notes'].append('Static DOM: visibility, layout and above-the-fold position are not known from this file.')
    if surface == 'home':
        bar = find(root, lambda n: has(n, r'announcement'))
        out['announcementBar'] = bar.all_text(200) if bar else None
        if bar:
            out['selectors']['announcementBar'] = record(bar)
        hero = find(main, lambda n: n.tag in ('h1', 'h2') and n.all_text(5))
        out['hero'] = {'heading': hero.all_text(120) if hero else None}
        links = find_all(root, lambda n: n.tag == 'a' and n.attrs.get('href'))
        footer = find(root, lambda n: n.tag == 'footer') or root
        out['policyLinks'] = [{'text': a.all_text(40), 'href': a.attrs['href']} for a in find_all(root, lambda n: n.tag == 'a' and re.search(r'ship|deliver|return|refund|faq|help', n.attrs.get('href', '') + ' ' + n.all_text(40), re.I), footer)][:8]
        cart = next((a.attrs['href'] for a in links if re.fullmatch(r'(/[a-z]{2}(-[a-z]{2})?)?/(cart|basket|bag)/?', a.attrs['href'].split('?')[0], re.I)), None)
        out['cartUrl'] = cart
        out['productLinks'] = list(dict.fromkeys(a.attrs['href'].split('?')[0] for a in links if '/products/' in a.attrs['href']))[:5]
        out['collectionLinks'] = list(dict.fromkeys(a.attrs['href'].split('?')[0] for a in links if '/collections/' in a.attrs['href']))[:5]
        out['search'] = {'present': find(root, lambda n: n.tag == 'form' and re.search(r'search', n.attrs.get('action', '') + n.cls(), re.I)) is not None}
    elif surface == 'pdp':
        form = find(main, lambda n: n.tag == 'form' and re.search(r'/cart/add|add-to-cart|addtocart|product-form', n.attrs.get('action', '') + ' ' + n.cls(), re.I))
        scope = form.parent.parent if form is not None and form.parent is not None and form.parent.parent is not None else main
        h1 = find(main, lambda n: n.tag == 'h1')
        out['title'] = h1.all_text(100) if h1 else None
        price = find(scope, lambda n: has(n, r'price') and re.search(r'\d', n.all_text(40)) and len(n.all_text(60)) < 60) or find(main, lambda n: has(n, r'price') and re.search(r'\d', n.all_text(40)) and len(n.all_text(60)) < 60)
        out['price'] = price.all_text(60) if price else None
        cta = None
        if form is not None:
            cta = find(form, lambda n: n.tag in ('button', 'input') and (n.attrs.get('name') == 'add' or n.attrs.get('type') == 'submit'))
        cta = cta or find(main, lambda n: n.tag == 'button' and re.search(r'add to (cart|bag|basket)', n.all_text(60) or n.attrs.get('aria-label', ''), re.I))
        out['cta'] = {'text': cta.all_text(60) or cta.attrs.get('aria-label'), 'disabled': 'disabled' in cta.attrs or cta.attrs.get('aria-disabled') == 'true'} if cta else 'absent'
        out['inStock'] = None if not cta else not (out['cta']['disabled'] or re.search(r'sold out|unavailable', out['cta']['text'] or '', re.I))
        out['variantSelector'] = bool(form and find(form, lambda n: n.tag == 'select' or (n.tag == 'input' and n.attrs.get('type') == 'radio')))
        copy = sentences((scope or main).all_text(4000, lines=True), re.compile(r'ship|deliver|return|exchange', re.I), 4)
        out['shippingReturnsCopy'] = copy or 'absent'
        out['expressPayOnPdp'] = sorted({m.group(0).lower() for m in re.finditer(EXPRESS, ' '.join(n.tag + ' ' + n.cls() for n in (scope or main).walk()), re.I)})
        blob = ' '.join(n.tag + ' ' + n.cls() + ' ' + n.attrs.get('id', '') for n in main.walk())
        out['widgets'] = [name for name, pat in REVIEW_WIDGETS if re.search(pat, blob, re.I)]
        for key, node in (('productForm', form), ('cta', cta), ('price', price), ('title', h1)):
            if node is not None:
                out['selectors'][key] = record(node)
    elif surface == 'collection':
        h1 = find(main, lambda n: n.tag == 'h1')
        out['title'] = h1.all_text(60) if h1 else None
        links = find_all(main, lambda n: n.tag == 'a' and '/products/' in n.attrs.get('href', ''))
        handles = list(dict.fromkeys(a.attrs['href'].split('?')[0] for a in links))
        out['cards'] = {'count': len(handles), 'sample': handles[:4]}
        if links:
            card = links[0].parent
            while card is not None and card.parent is not None and card.parent.tag != '#root' and len([x for x in card.parent.children if x.tag == card.tag]) < 2:
                card = card.parent
            out['selectors']['productCard'] = record(card)
        quick = find(main, lambda n: has(n, r'quick[-_ ]?(add|shop|view)') or (n.tag in ('button', 'a') and re.search(r'quick (add|shop|view)|^add to (cart|bag)$', n.all_text(30), re.I)))
        out['quickAdd'] = {'present': quick is not None, 'label': quick.all_text(30) if quick else None}
        if quick is not None:
            out['selectors']['quickAdd'] = record(quick)
        sort = find(main, lambda n: n.tag == 'select' and re.search(r'sort', n.attrs.get('name', '') + n.attrs.get('id', '') + n.cls(), re.I))
        out['sort'] = {'options': [o.all_text(40) for o in find_all(sort, lambda n: n.tag == 'option', sort)][:10]} if sort else None
        out['filters'] = len(find_all(main, lambda n: has(n, r'facet|filter') and n.tag in ('details', 'fieldset', 'li', 'div') and n.parent is not None and not has(n.parent, r'facet|filter')))
        count = re.search(r'\b\d[\d,]*\s+(products?|items?|results?)\b', main.all_text(3000), re.I)
        out['productCountText'] = count.group(0) if count else None
    elif surface == 'cart':
        row_class = re.compile(r'^(cart-item|line-item|cart__item|cart-line)(--[\w-]+)?$')
        is_row = lambda n: n.tag == 'cart-item' or 'data-cart-item' in n.attrs or any(row_class.match(c) for c in n.cls().split())
        rows = [n for n in find_all(main, is_row) if not (n.parent is not None and is_row(n.parent))]
        out['itemCount'] = len(rows)
        text = main.all_text(6000, lines=True)
        out['freeShippingProgress'] = sentences(text, re.compile(r'away from free (shipping|delivery)|free (shipping|delivery)', re.I), 2) or None
        out['shippingMessages'] = sentences(text, re.compile(r'ship|deliver', re.I), 4)
        promo = find(root, lambda n: n.tag == 'input' and re.search(r'discount|coupon|promo|gift', n.attrs.get('name', '') + n.attrs.get('id', '') + n.attrs.get('placeholder', ''), re.I))
        out['promoField'] = {'present': promo is not None}
        checkout = find(root, lambda n: (n.tag in ('button', 'input', 'a') and (n.attrs.get('name') == 'checkout' or '/checkout' in n.attrs.get('href', ''))) or (n.tag == 'button' and re.search(r'check ?out', n.all_text(30), re.I)))
        out['checkoutCta'] = checkout.all_text(40) if checkout else 'absent'
        out['expressPay'] = sorted({m.group(0).lower() for m in re.finditer(EXPRESS, ' '.join(n.tag + ' ' + n.cls() for n in root.walk()), re.I)})
        out['upsells'] = find(main, lambda n: has(n, r'upsell|recommend|cross-sell|complementary')) is not None
        remove = find(root, lambda n: (n.tag in ('a', 'button') and (re.search(r'quantity=0|/cart/change', n.attrs.get('href', '')) or re.search(r'remove|delete', n.attrs.get('aria-label', '') + ' ' + n.all_text(20), re.I))))
        out['removeControl'] = {'present': remove is not None}
        for key, node in (('cartRow', rows[0] if rows else None), ('checkoutCta', checkout), ('removeControl', remove)):
            if node is not None:
                out['selectors'][key] = record(node)
    elif surface == 'checkout_entry':
        text = main.all_text(4000, lines=True)
        out['gate'] = {'guestOption': bool(re.search(r'continue as guest|guest checkout|checkout as guest', text, re.I)),
                       'loginPrompt': bool(re.search(r'\b(log ?in|sign ?in)\b', text, re.I)),
                       'passwordField': find(root, lambda n: n.tag == 'input' and n.attrs.get('type') == 'password') is not None}
        inputs = find_all(main, lambda n: n.tag in ('input', 'select', 'textarea') and n.attrs.get('type') not in ('hidden', 'submit', 'button'))
        out['fieldCount'] = len(inputs)
        out['fieldLabels'] = [l.all_text(40) for l in find_all(main, lambda n: n.tag == 'label')][:12]
        out['expressPay'] = sorted({m.group(0).lower() for m in re.finditer(EXPRESS, ' '.join(n.tag + ' ' + n.cls() for n in root.walk()), re.I)})
        out['notes'].append('Observation only: field values are never read or recorded.')
    elif surface == 'policy':
        out['policySentences'] = sentences(main.all_text(20000, lines=True), POLICY_RE, 8)
        out['notFound'] = bool(re.search(r'\b404\b|page not found', root.all_text(400), re.I))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('dom', type=Path)
    parser.add_argument('--surface', required=True, choices=sorted(SURFACE_KEYS))
    parser.add_argument('--url')
    parser.add_argument('--into', type=Path, help='add the record to this walkthrough.json under read_<surface>')
    args = parser.parse_args(argv)
    raw = args.dom.read_text(encoding='utf-8', errors='replace')
    result = parse(raw, args.surface, args.url)
    if args.into:
        data = json.loads(args.into.read_text(encoding='utf-8')) if args.into.exists() else {}
        key = SURFACE_KEYS[args.surface]
        if key in data:
            key = f'{key}:{args.url or "extra"}'
        data[key] = result
        args.into.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
