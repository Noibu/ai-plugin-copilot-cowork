#!/usr/bin/env python3
"""Noibu A/B test report pages for Copilot Cowork.

Turns a finder run's candidates.json into one report page per test: a self-contained HTML file
that Cowork opens in its browser. One file, Python standard library only, no scripts or outside
requests in the page. Every heading and label on the page is written here; candidates.json
supplies the values. Run `python report.py --help` for the run command.
"""
import html
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

NAME_LIMIT = 48  # characters in a page's file name, before .html
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()

CSS = """
:root { --bg:#f6f6f4; --surface:#fff; --ink:#17191c; --muted:#5c6168; --line:#dcdedb;
  --after:#1f6f4a; --after-bg:#e8f3ec; --note-bg:#fbf4dd; --note-ink:#5b4a12; --warn:#8a5a00; --panel:#f0f0ed; color-scheme:light; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#141618; --surface:#1d2023; --ink:#eceef0; --muted:#a2a8b0; --line:#30353a;
  --after:#6fcf9a; --after-bg:#1c2e25; --note-bg:#2f2a18; --note-ink:#e6d69a; --warn:#e6b45a; --panel:#23272b; color-scheme:dark; } }
:root[data-theme="dark"] { --bg:#141618; --surface:#1d2023; --ink:#eceef0; --muted:#a2a8b0; --line:#30353a;
  --after:#6fcf9a; --after-bg:#1c2e25; --note-bg:#2f2a18; --note-ink:#e6d69a; --warn:#e6b45a; --panel:#23272b; color-scheme:dark; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; font-size:15px; line-height:1.5; }
.mono, .meta, .rank, .surface, .tag { font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
.wrap { max-width:1180px; margin:0 auto; padding:32px 20px 64px; }
h1 { font-size:28px; font-weight:600; letter-spacing:-.01em; margin:0 0 6px; text-wrap:balance; }
header p { margin:0; color:var(--muted); max-width:70ch; }
.meta { display:flex; flex-wrap:wrap; gap:8px 20px; margin-top:14px; font-size:12.5px; color:var(--muted); }
.note { margin-top:18px; background:var(--note-bg); color:var(--note-ink); border-radius:6px; padding:10px 14px; font-size:14px; max-width:80ch; }
section.test { margin-top:44px; padding-top:28px; border-top:1px solid var(--line); }
.rank { font-size:12.5px; color:var(--muted); letter-spacing:.06em; text-transform:uppercase; display:block; margin-bottom:6px; }
.test h2 { font-size:22px; font-weight:600; margin:0; letter-spacing:-.01em; text-wrap:balance; }
.surface { font-size:12.5px; color:var(--muted); margin-top:6px; word-break:break-all; }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:16px; max-width:100ch; }
@media (max-width:760px) { .cols { grid-template-columns:1fr; } }
h3 { font-size:12.5px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin:0 0 4px; font-weight:600; }
.cols p { margin:0; }
.variation { margin-top:18px; font-weight:500; }
.evidence { margin-top:20px; max-width:100ch; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px; }
.evidence ul, .unconfirmed ul, .outside ul { margin:0; padding-left:20px; } .evidence li, .unconfirmed li, .outside li { margin:4px 0; }
.tag { font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; padding:2px 8px; border-radius:4px; color:var(--warn); border:1px solid var(--line); margin-left:6px; white-space:nowrap; }
.unconfirmed { margin-top:10px; padding:12px 14px; border:1px dashed var(--line); border-radius:8px; color:var(--muted); font-size:14px; max-width:80ch; }
.unconfirmed p { margin:6px 0 0; }
.setup { margin-top:20px; background:var(--panel); border-radius:8px; padding:14px 16px; max-width:100ch; }
.setup dl { display:grid; grid-template-columns:max-content 1fr; gap:6px 16px; margin:0; font-size:14px; }
.setup dt { color:var(--muted); } .setup dd { margin:0; }
@media (max-width:560px) { .setup dl { grid-template-columns:1fr; gap:2px; } .setup dt { margin-top:8px; } }
.dev { margin-top:16px; max-width:80ch; font-size:14px; } .dev p { margin:0 0 8px; }
.fix { color:var(--warn); }
a { color:inherit; }
.cta { margin-top:18px; max-width:80ch; font-size:14px; border-left:3px solid var(--after); background:var(--after-bg); border-radius:0 6px 6px 0; padding:10px 14px; }
.cta p { margin:2px 0; } .cta q { font-weight:600; quotes:'"' '"'; }
.outside { margin-top:44px; padding-top:24px; border-top:1px solid var(--line); max-width:80ch; } .outside h2 { font-size:17px; margin:0 0 8px; }
footer { margin-top:48px; color:var(--muted); font-size:13px; max-width:80ch; } footer p { margin:4px 0; }
@media print { body { background:#fff; } .wrap { padding:0; } .setup, .evidence, .cta { break-inside:avoid; } }
"""


class ReportError(ValueError):
    """candidates.json has something the builder can't use. The message names the field."""


def esc(value):
    return html.escape(_s(value), quote=True)


def _s(value):
    """Any value as one line of display text."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, (list, tuple)):
        return ' · '.join(x for x in (_s(v) for v in value) if x)
    if isinstance(value, dict):
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def _lines(value):
    """A field that may be one line or a list of lines, as a list of non-empty lines."""
    if isinstance(value, (list, tuple)):
        return [x for x in (_s(v) for v in value) if x]
    return [_s(value)] if _s(value) else []


_CONSOLE_URL = re.compile(r'https://console\.noibu\.com/[^\s<>"\']*[^\s<>"\'.,;:)\]]')


def rich(value):
    """Escaped text, with any console.noibu.com URL in it turned into a link."""
    return _CONSOLE_URL.sub(lambda m: f'<a href="{m.group(0)}">open in Noibu ↗</a>', esc(value))


def _generated(value):
    try:
        moment = datetime.fromisoformat(_s(value).replace('Z', '+00:00'))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        moment = moment.astimezone(timezone.utc)
    except ValueError:
        moment = datetime.now(timezone.utc)
    return f'{MONTHS[moment.month - 1]} {moment.day}, {moment.year}, {moment.hour % 12 or 12}:{moment.minute:02d} {"am" if moment.hour < 12 else "pm"} (UTC)'


def page_name(title, taken):
    """A file name made from the test's title: plain words joined by hyphens, cut at a word when long, unique in the run."""
    plain = unicodedata.normalize('NFKD', _s(title)).encode('ascii', 'ignore').decode().lower()
    words = re.sub(r'[^a-z0-9]+', ' ', plain.replace("'", '')).split()
    name = ''
    for word in words:
        if name and len(name) + 1 + len(word) > NAME_LIMIT:
            break
        name = f'{name}-{word}' if name else word[:NAME_LIMIT]
    name = name or 'test'
    unique, n = name, 2
    while unique in taken:
        unique, n = f'{name}-{n}', n + 1
    taken.add(unique)
    return unique


def read_run(run):
    """Check the few things a page can't be built without, and return the run's tests with their ranks."""
    if not isinstance(run, dict):
        raise ReportError('candidates.json must be a JSON object')
    if not _s(run.get('domain')):
        raise ReportError('domain must be the store\'s domain name')
    tests = run.get('tests')
    if not isinstance(tests, list) or not tests:
        raise ReportError('tests must be a non-empty list')
    ranked = []
    for i, test in enumerate(tests, 1):
        if not isinstance(test, dict) or not _s(test.get('title')):
            raise ReportError(f'tests[{i - 1}].title must be a non-empty string')
        rank = test.get('rank')
        ranked.append((rank if isinstance(rank, int) and not isinstance(rank, bool) and rank > 0 else i, test))
    if len({rank for rank, _ in ranked}) != len(ranked):
        ranked = [(i, test) for i, (_, test) in enumerate(ranked, 1)]
    return ranked


def _test_section(rank, test):
    setup = test.get('setup') if isinstance(test.get('setup'), dict) else {}
    variations = [v for v in (test.get('variations') or []) if isinstance(v, dict)]
    lettered = [v for v in variations if not v.get('isControl')]
    parts = [f'<section class="test" id="test-{rank}">', f'<span class="rank">Test {rank}</span>', f'<h2>{esc(test["title"])}</h2>']
    if _s(test.get('surface')):
        parts.append(f'<div class="surface">{esc(test["surface"])}</div>')

    cols = [(label, _s(test.get(key))) for label, key in (('What to change', 'what'), ('Why this test', 'why'))]
    if any(text for _, text in cols):
        parts.append('<div class="cols">' + ''.join(f'<div><h3>{label}</h3><p>{esc(text)}</p></div>' for label, text in cols if text) + '</div>')

    names = [_s(v.get('name')) for v in lettered] or ([_s(test.get('variationName'))] if _s(test.get('variationName')) else [])
    for letter, name in zip('BCDEF', [n for n in names if n]):
        parts.append(f'<div class="variation">{letter}: {esc(name)}</div>')

    unconfirmed = _lines(test.get('unconfirmed'))
    if unconfirmed:
        parts.append('<div class="unconfirmed"><h3>Not confirmed on the store</h3><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in unconfirmed)
                     + '</ul><p>These rest on Noibu data alone. They are checked against the store\'s code when the test is built.</p></div>')

    evidence = [e for e in (test.get('evidence') or []) if isinstance(e, dict) and _s(e.get('claim'))]
    if evidence:
        parts.append('<div class="evidence"><h3>Why this test, in numbers</h3><ul>' + ''.join(
            f'<li>{esc(e["claim"])}' + ('<span class="tag">Correlational</span>' if e.get('correlational') is True else '') + '</li>' for e in evidence) + '</ul></div>')

    rows = [('Title', _s(setup.get('title')) or _s(test['title'])), ('Hypothesis', _s(setup.get('hypothesis'))),
            ('Success metric', _s(setup.get('successMetric'))), ('Traffic for this metric', _s(test.get('metricVolume'))),
            ('Secondary metrics', _s(setup.get('secondaryMetrics')) or 'None'),
            ('Targeting', _s(setup.get('targeting')) or 'Everyone (skip this section)'), ('Variations', _s(setup.get('variations')))]
    parts.append('<div class="setup"><h3>Set it up in Noibu</h3><dl>' + ''.join(f'<dt>{label}</dt><dd>{esc(text)}</dd>' for label, text in rows if text) + '</dl></div>')

    notes = [(_s(v.get('name')), _s(v.get('devNotes'))) for v in lettered if _s(v.get('devNotes'))]
    if not notes and _s(test.get('devNotes')):
        notes = [('', _s(test['devNotes']))]
    dev = []
    if notes:
        dev.append('<h3>Dev notes</h3>')
        for name, text in notes:
            lead = f'<strong>{esc(name)}:</strong> ' if name and len(notes) > 1 else ''
            dev.append(f'<p>{lead}{esc(text)}</p>')
    if _s(test.get('fixFirst')):
        dev.append(f'<p class="fix"><strong>Fix first:</strong> {rich(test["fixFirst"])}</p>')
    if _s(test.get('overlap')):
        dev.append(f'<p class="fix"><strong>Overlap:</strong> {rich(test["overlap"])}</p>')
    for line in _lines(test.get('consoleFollowUps')):
        dev.append(f'<p><strong>To set in the Noibu console after creating:</strong> {rich(line)}</p>')
    if dev:
        parts.append('<div class="dev">' + ''.join(dev) + '</div>')

    parts.append('<div class="cta">'
                 f'<p>To create this test as a draft, go back to the chat and ask Cowork: <q>create test {rank} in Noibu</q></p>'
                 f'<p>To have the variation code written as well, ask: <q>build test {rank}</q></p>'
                 '<p>A draft serves no traffic until it is started, and its variation code has to be live first.</p></div>')
    parts.append('</section>')
    return parts


def build(run, rank, test):
    """One report page: the run's intro, one test in full, then what applies to the whole run."""
    domain = _s(run['domain'])
    goal = _s(run.get('goal'))
    metric = _s(run.get('successMetricLabel'))
    lead = (f'Goal: {esc(goal)}' + (f' (success metric: {esc(metric)})' if metric else '') + '. ') if goal else ''
    parts = ['<!doctype html>', '<html lang="en"><head><meta charset="utf-8">', '<meta name="viewport" content="width=device-width,initial-scale=1">',
             f'<title>{esc(test["title"])}</title>', f'<style>{CSS}</style></head><body>', '<div class="wrap"><header>',
             f'<h1>A/B test recommendation for {esc(domain)}</h1>',
             f'<p>{lead}It is built from this store\'s Noibu data.</p>']
    if _s(run.get('dataLine')):
        parts.append(f'<div class="meta"><span>{esc(run["dataLine"])}</span></div>')
    parts.append('<div class="note">The store\'s pages were not opened for this report, so it has no picture of the change. '
                 'Anything it assumes about a page is listed as not confirmed and is checked against the store\'s code when the test is built.</div>')
    parts.append('</header>')
    parts += _test_section(rank, test)
    outside = _lines(run.get('outsideGoal'))
    if outside:
        parts.append('<section class="outside"><h2>Outside your goal</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in outside) + '</ul></section>')
    parts.append('<footer>' + ''.join(f'<p>{rich(x)}</p>' for x in _lines(run.get('caveats')))
                 + f'<p>Generated {esc(_generated(run.get("generatedAt")))} from Noibu data for {esc(domain)}.</p></footer></div>')
    parts.append('</body></html>')
    return '\n'.join(parts)


def write_pages(run, folder):
    """Write one page per test into the folder. Returns [{"rank", "title", "path"}] in rank order."""
    ranked = read_run(run)
    os.makedirs(folder, exist_ok=True)
    pages, taken = [], set()
    for rank, test in ranked:
        path = os.path.join(folder, page_name(test['title'], taken) + '.html')
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(build(run, rank, test))
        pages.append({'rank': rank, 'title': _s(test['title']), 'path': path})
    return pages


def _load(source):
    if isinstance(source, dict):
        return source
    with open(source, encoding='utf-8') as handle:
        return json.load(handle)


def _why(exc):
    return ' '.join(str(exc).split())[:300].rstrip('.') or type(exc).__name__


def run_in_cowork():
    """Build every test's page and return where each one is."""
    from aether_tools import args, set_result
    given = args() or {}
    try:
        source = given.get('candidates')
        if not source:
            raise ReportError('args.candidates must be the path to candidates.json')
        # Scripts can't write to the Cowork output folder, so the pages go beside candidates.json
        # and the skill publishes them from there.
        beside = os.path.dirname(os.path.abspath(source)) if isinstance(source, str) else os.getcwd()
        folder = str(given.get('folder') or os.path.join(beside, 'pages'))
        set_result({'pages': write_pages(_load(source), folder)})
    except Exception as exc:
        set_result({'pages': [], 'error': f'The report pages could not be built because {_why(exc)}.'})


RUN_COMMAND = ('copy scripts/report.py to .aether/scripts/report.py, then RunScript report.py with the arg candidates '
               'set to the path of candidates.json. The pages are written to a pages folder beside it; '
               'publish each one to the Cowork output folder')

HELP = f"""Noibu A/B test report pages for Copilot Cowork

In Cowork (writes one page per test):
  {RUN_COMMAND}
  Returns {{"pages": [{{"rank", "title", "path"}}]}} in rank order and, on failure, "error".
  A page is named after its test's title, in lowercase words joined by hyphens: quick-add-on-collection-cards.html.

On the command line:
  python report.py candidates.json --out <folder>
  python report.py --example            print a sample candidates.json
  python report.py --help

What a page shows, all from candidates.json:
  run     domain, goal, successMetricLabel, dataLine, outsideGoal, caveats, generatedAt
  test    title, surface, what, why, unconfirmed, evidence[].claim (and its correlational flag),
          setup (title, hypothesis, successMetric, secondaryMetrics, targeting, variations), metricVolume,
          variations[].name and devNotes, fixFirst, overlap, consoleFollowUps
  A field that is absent or empty is left off the page. A console.noibu.com URL in fixFirst, overlap,
  consoleFollowUps or a caveat becomes a link."""

EXAMPLE = {
    'schema': 'noibu.ab-candidates/1', 'generatedAt': '2026-10-03T14:20:00Z', 'domain': 'www.example-store.ca',
    'domainId': '00000000-0000-4000-8000-000000000000', 'goal': 'Increase add to cart rate', 'successMetricLabel': 'Add to cart rate',
    'dataLine': 'Noibu, Sep 3 to Oct 3, 2026 (30 days, about 483,000 sessions, 78% on mobile)',
    'caveats': ['The live store was not read, so other testing tools on it could not be detected.', 'Baselines come from session funnel depth; the setup screen\'s figure wins.'],
    'tests': [
        {'rank': 1, 'title': 'Quick add on collection cards', 'surface': '/collections/plush and every other collection page', 'surfaceTemplate': 'collection',
         'variationName': 'Add to cart button on cards',
         'what': 'Add an Add to cart button to each product card on collection pages, so a shopper can add without opening the product page.',
         'why': 'Collection pages reach 29% of sessions, but only 5.8% of those sessions add to cart, against 11.2% for sessions that open a product page.',
         'metricVolume': 'About 6,500 add-to-cart shoppers a week in this targeting. Noibu shows the days to a verdict at setup.',
         'evidence': [{'claim': 'Collection pages reach 29% of sessions (141,000 of 482,560)', 'numbers': {'collectionGroupSessions': 141000, 'allSessions': 482560}, 'source': 'batch1#8, R2', 'correlational': False},
                      {'claim': 'Sessions that open a product page add to cart at 11.2%, against 5.8% for collection sessions', 'numbers': {}, 'source': 'batch1#5', 'correlational': True}],
         'unconfirmed': ['Collection cards have no add-to-cart control'],
         'variations': [{'name': 'Original', 'isControl': True, 'trafficSplit': 50},
                        {'name': 'Add to cart button on cards', 'isControl': False, 'trafficSplit': 50,
                         'devNotes': 'Collection grid: add an Add to cart control under the price on each product card. Products with variants open the existing quick view instead.'}],
         'setup': {'title': 'Quick add on collection cards', 'hypothesis': 'Adding an Add to cart button to collection cards will increase add to cart rate.',
                   'successMetric': 'Add to cart rate (about 5.8%)', 'secondaryMetrics': 'Checkout conversion rate · Average order value',
                   'targeting': 'Everyone (skip this section)', 'variations': 'A: Original (control) · B: Add to cart button on cards, split equally'},
         'consoleFollowUps': [], 'overlap': None,
         'fixFirst': 'Mobile layout shift on /collections/plush is 0.31 at p75, which would add noise to both arms: https://console.noibu.com/00000000-0000-4000-8000-000000000000/issues/11111111-1111-4111-8111-111111111111'},
        {'rank': 2, 'title': 'Shipping reassurance in the cart drawer', 'surface': '/cart', 'surfaceTemplate': 'cart', 'variationName': 'Shipping line above checkout',
         'what': 'Show the free-shipping threshold and delivery estimate above the checkout button in the cart drawer.',
         'why': '42% of sessions that open the cart leave without starting checkout, and the shipping cost first appears on the shipping step.',
         'metricVolume': 'About 2,100 checkout starts a week in this targeting. Noibu shows the days to a verdict at setup.',
         'evidence': [{'claim': '42% of sessions that open the cart leave without starting checkout', 'numbers': {}, 'source': 'batch2#3', 'correlational': False}],
         'variations': [{'name': 'Original', 'isControl': True, 'trafficSplit': 50},
                        {'name': 'Shipping line above checkout', 'isControl': False, 'trafficSplit': 50, 'devNotes': 'Cart drawer: add one line above the checkout button with the free-shipping threshold and the delivery estimate.'}],
         'setup': {'title': 'Shipping reassurance in the cart drawer', 'hypothesis': 'Showing shipping terms in the cart drawer will increase checkout starts.',
                   'successMetric': 'Viewed page: page group Checkout (baseline shown at setup)', 'secondaryMetrics': 'None',
                   'targeting': 'Everyone (skip this section)', 'variations': 'A: Original (control) · B: Shipping line above checkout, split equally'},
         'consoleFollowUps': [], 'overlap': 'Draft "Cart drawer upsell" targets the same cart drawer.', 'fixFirst': None}],
    'outsideGoal': ['Sticky checkout button on the mobile cart page (acts on checkout starts).'],
    'killed': [{'idea': 'Promo code field in the cart', 'reason': 'already present: shoppers clicked "Apply" on /cart 1,240 times in the window'}],
}


def run_command_line(argv):
    if not argv or argv[0] in {'-h', '--help'}:
        print(HELP)
        return 0
    if argv == ['--example']:
        print(json.dumps(EXAMPLE, indent=1, ensure_ascii=False))
        return 0
    if len(argv) != 3 or argv[1] != '--out' or argv[0].startswith('-'):
        print('usage: python report.py candidates.json --out <folder>', file=sys.stderr)
        return 2
    try:
        pages = write_pages(_load(argv[0]), argv[2])
    except Exception as exc:
        print(json.dumps({'pages': [], 'error': f'The report pages could not be built because {_why(exc)}.'}, ensure_ascii=False))
        return 1
    print(json.dumps({'pages': pages}, ensure_ascii=False, indent=1))
    return 0


def main(argv):
    if not argv:
        try:
            import aether_tools  # noqa: F401  (present only inside Cowork)
        except ImportError:
            return run_command_line(argv)
        run_in_cowork()
        return 0
    return run_command_line(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
