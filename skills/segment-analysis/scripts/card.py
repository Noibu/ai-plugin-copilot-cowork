#!/usr/bin/env python3
"""Noibu report card for Copilot Cowork.

Turns a small report data file into one Adaptive Card, shows it, and returns what to ask next.
One file, Python standard library only. Every report skill carries an unchanged copy as
scripts/card.py. Run `python card.py --help` for the report data shape and the run command.
"""
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlsplit
from uuid import UUID

CARD_LIMIT = 24000          # bytes; a larger card is not displayed
MAX_TILES = 5
MAX_TABLES = 2              # two side-by-side half tables count as one
PREVIEW_ROWS = 5
COMPACT_ROWS = 3
MAX_PRIORITIES = 3          # drawn on the card
MAX_OPTIONS = 5             # offered in the next-step question
MAX_LINK_BUTTONS = 2
TITLE_CHARS, SHORT_WORDS, EVIDENCE_CHARS, CELL_CHARS, TAG_CHARS = 60, 5, 160, 40, 32
NOT_MEASURED = 'Not measured'

VITALS = {'LCP': (2500, 4000), 'INP': (200, 500), 'CLS': (0.1, 0.25)}   # good / poor cut-offs (ms, ms, score)
SEVERITIES = {'critical': 'Critical', 'serious': 'Serious', 'moderate': 'Moderate', 'minor': 'Minor'}
STATUSES = {'active': ('Active', 'Attention'), 're-emerging': ('Re-emerging', 'Warning'), 'improving': ('Improving', 'Good')}
KINDS = {'fixable': 'Issues you can fix', 'performance': 'Performance', 'vendor': 'Vendor issues'}
CURRENCY_SYMBOLS = {'USD': '$', 'CAD': 'CA$', 'AUD': 'A$', 'NZD': 'NZ$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
COUNTRIES = {'US': 'United States', 'CA': 'Canada', 'GB': 'United Kingdom', 'UK': 'United Kingdom', 'AU': 'Australia', 'NZ': 'New Zealand', 'IE': 'Ireland', 'FR': 'France', 'DE': 'Germany', 'ES': 'Spain', 'IT': 'Italy', 'NL': 'Netherlands', 'BE': 'Belgium', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland', 'CH': 'Switzerland', 'AT': 'Austria', 'PL': 'Poland', 'PT': 'Portugal', 'MX': 'Mexico', 'BR': 'Brazil', 'AR': 'Argentina', 'CL': 'Chile', 'CO': 'Colombia', 'IN': 'India', 'PK': 'Pakistan', 'CN': 'China', 'JP': 'Japan', 'KR': 'South Korea', 'SG': 'Singapore', 'HK': 'Hong Kong', 'PH': 'Philippines', 'ID': 'Indonesia', 'MY': 'Malaysia', 'TH': 'Thailand', 'VN': 'Vietnam', 'AE': 'United Arab Emirates', 'SA': 'Saudi Arabia', 'IL': 'Israel', 'TR': 'Türkiye', 'ZA': 'South Africa', 'NG': 'Nigeria', 'EG': 'Egypt'}


# ---------------------------------------------------------------------------------------------
# What each skill's card shows. Every label on the card is written here; the report data file
# supplies values only. Value kinds: count, rate (a percentage, 54.2 means 54.2%), money, number,
# text, country.
# ---------------------------------------------------------------------------------------------

def _kpi(key, label, kind, good='up', sub=None):
    return {'key': key, 'label': label, 'kind': kind, 'good': good, 'sub': sub}


def _table(key, columns, top=None, half=False):
    return {'key': key, 'columns': columns, 'top': top, 'half': half}


_CHANNEL_COLUMNS = [('sessions', 'Sessions', 'count'), ('conversionRate', 'CVR', 'rate'), ('revenuePerSession', 'Rev / session', 'money')]
_RANKED_COLUMNS = [('sessions', 'Sessions', 'count'), ('conversionRate', 'Conversion', 'rate'), ('revenuePerSession', 'Rev / session', 'money')]

SKILLS = {
    'checkout-analysis': {
        'title': 'Overview', 'unit': 'sessions',
        'context': [('sessions', 'count', '{} sessions'), ('addedToCartRate', 'rate', '{} added to cart')],
        'tiles': [_kpi('checkoutCompletion', 'Checkout completion', 'rate'), _kpi('mobileConversion', 'Mobile conversion', 'rate'),
                  _kpi('desktopConversion', 'Desktop conversion', 'rate'), _kpi('checkoutErrors', 'Checkout errors', 'count', good='down')],
        'stats': [_kpi('medianOrder', 'Median order', 'money'), _kpi('discounted', 'Discounted', 'rate'), _kpi('itemsPerOrder', 'Items / order', 'number')],
        'funnel': {'stages': [('addedToCart', 'Added to cart'), ('startedCheckout', 'Started checkout'), ('paymentSubmitted', 'Payment submitted'), ('completedOrder', 'Completed order')],
                   'axis': '% of cart', 'first': '{}', 'pill': True},
        'tables': [_table('abandonment', [('source', 'Top source of abandonment', 'text'), ('sessions', 'Abandoned sessions', 'count'), ('cartValue', 'Cart value', 'money')]),
                   _table('paymentMethods', [('method', 'Payment methods', 'text'), ('orders', 'Orders', 'count')], half=True),
                   _table('deliveryMethods', [('method', 'Delivery methods', 'text'), ('orders', 'Orders', 'count')], half=True)],
    },
    'product-analysis': {
        'title': 'Overview', 'unit': 'sessions',
        'context': [('sessions', 'count', '{} sessions'), ('conversionRate', 'rate', '{} conversion rate'), ('medianOrder', 'money', 'Median order {}')],
        'funnel': {'stages': [('viewedProduct', 'Viewed product'), ('addedToCart', 'Added to cart'), ('completedOrder', 'Completed order')],
                   'axis': '% of sessions that viewed a product', 'first': '{}', 'pill': True},
        'tables': [_table('products', [('name', 'Top products by sessions', 'text'), ('sessions', 'Sessions', 'count'), ('addToCartRate', 'Add-to-cart', 'rate'), ('conversionRate', 'Conversion', 'rate')], top=('Top product', ['sessions', 'conversionRate'])),
                   _table('collections', [('name', 'Top collections by sessions', 'text')] + _RANKED_COLUMNS, top=('Top collection', ['sessions', 'conversionRate'])),
                   _table('productTypes', [('name', 'Top product types by sessions', 'text')] + _RANKED_COLUMNS, top=('Top type', ['sessions', 'conversionRate']))],
        'signals': ['Low add-to-cart rate', 'Cart abandonment', 'Low collection conversion', 'Underperforming product type', 'High bounce rate'],
    },
    'segment-analysis': {
        'title': 'Overview', 'unit': 'sessions', 'tilesTitle': 'Conversion rate',
        'tiles': [_kpi('siteWideConversion', 'Site wide', 'rate', sub='siteWideSessions'), _kpi('mobileConversion', 'Mobile', 'rate', sub='mobileSessions'),
                  _kpi('desktopConversion', 'Desktop', 'rate', sub='desktopSessions')],
        'tables': [_table('countries', [('country', 'Country', 'country')] + _CHANNEL_COLUMNS, top=('Top country', ['sessions', 'conversionRate'])),
                   _table('bestChannels', [('channel', 'Best converting channels', 'text')] + _CHANNEL_COLUMNS, top=('Best converting channel', ['conversionRate'])),
                   _table('mostVisitedChannels', [('channel', 'Most visited channels', 'text')] + _CHANNEL_COLUMNS, top=('Most visited channel', ['sessions']))],
        'signals': ['Low mobile conversion', 'High-traffic underperformer', 'Campaign drag', 'Localization gap', 'High-value channel', 'Device gap'],
    },
    'store-pulse': {
        'title': 'Store Pulse', 'unit': 'sessions',
        'tiles': [_kpi('sessions', 'Sessions', 'count'), _kpi('engagement', 'Engagement', 'rate'), _kpi('conversion', 'Conversion', 'rate'),
                  _kpi('aov', 'AOV', 'money'), _kpi('rps', 'RPS', 'money')],
        'funnel': {'stages': [('enterStore', 'Enter store'), ('viewProduct', 'View product'), ('addToCart', 'Add to cart'), ('startCheckout', 'Start checkout'), ('checkoutComplete', 'Checkout complete')],
                   'axis': '% of sessions', 'first': '{} sessions', 'pill': False},
        'tables': [_table('channels', [('channel', 'Channel', 'text'), ('sessions', 'Sessions', 'count'), ('engagement', 'Engagement', 'rate'), ('conversion', 'Conversion', 'rate'), ('rps', 'RPS', 'money')]),
                   _table('paidPlatforms', [('platform', 'Paid Ad Platform', 'text'), ('sessions', 'Sessions', 'count'), ('conversions', 'Conversions', 'count'), ('revenue', 'Revenue', 'money')]),
                   _table('topProducts', [('name', 'Top Products by Traffic', 'text'), ('sessions', 'Sessions', 'count'), ('addToCartRate', 'Add to Cart', 'rate')])],
    },
    'tech-diagnosis': {
        'title': 'Tech findings', 'unit': 'sessions',
    },
    'ab-testing': {
        'title': 'A/B test opportunities', 'unit': 'sessions', 'items': 'tests', 'itemLabel': 'Test',
        'drawn': 5, 'emptyLabel': 'No test opportunities', 'ask': 'show test {n}',
    },
    'accessibility-audit': {
        'title': 'Accessibility audit', 'unit': 'pageviews',
        'context': [('pagesScanned', 'count', '{} pages scanned'), ('pageviews', 'count', '{} pageviews'), ('violationInstances', 'count', '{} violation instances'), ('uniqueFixes', 'count', '{} unique fixes')],
        'tiles': [_kpi('critical', 'Critical', 'count', good='down'), _kpi('serious', 'Serious', 'count', good='down'),
                  _kpi('moderate', 'Moderate', 'count', good='down'), _kpi('minor', 'Minor', 'count', good='down')],
        'tables': [_table('pagesScanned', [('page', 'Pages scanned', 'text'), ('pageviews', '30-day pageviews', 'count'), ('instances', 'Violation instances', 'count')]),
                   _table('keyFindings', [('finding', 'Key findings', 'text'), ('wcag', 'WCAG', 'text'), ('severity', 'Severity', 'text')])],
    },
}

TOP_SUFFIX = {'sessions': '{} sessions', 'conversionRate': '{} CVR'}
WHY_CHARS = 240
TEST_FIELDS = {'title', 'shortTitle', 'change', 'why'}
PRIORITY_FIELDS = {'title', 'shortTitle', 'evidence', 'affected', 'link'}
PRIORITY_EXTRA = {
    'product-analysis': {'signal'}, 'segment-analysis': {'signal'},
    'tech-diagnosis': {'kind', 'status', 'errorType', 'vendor', 'occurrences', 'lastSeen', 'where', 'vital'},
    'accessibility-audit': {'severity', 'wcag', 'pages'},
}
REPORT_FIELDS = {'skill', 'store', 'window', 'currency', 'kpis', 'funnel', 'tables', 'priorities', 'tests', 'noPrioritiesReason', 'links', 'reportPages'}


class ReportError(ValueError):
    """The report data file has a field the builder can't use. The message names the field."""


class CardSizeError(ValueError):
    """The card is over the size limit even in compact form."""


def _bad(path, must, got=None):
    shown = '' if got is None else f' (got {json.dumps(got, ensure_ascii=False, default=str)[:60]})'
    raise ReportError(f'{path} must be {must}{shown}')


# ---------------------------------------------------------------------------------------------
# Reading the report data: forgiving about predictable variants, exact about everything else.
# ---------------------------------------------------------------------------------------------

_CITATION = re.compile(r'\s*\[(?:Source:\s*)?turn\d+[a-z]+\d+(?:[^\]\n]*)\]|\s*[\(\[]ref:\s*NB-[a-f0-9-]+[\)\]]|[]cite[]turn[^\n]*[]', re.I)
_ISO_TIME = re.compile(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?')
_TRAILING = {'on', 'in', 'at', 'for', 'of', 'the', 'a', 'an', 'and', 'to', 'with', 'by', 'from', 'vs', 'after', 'before', 'than', 'as', 'per', 'into', 'is', 'are', 'was', 'were', '·', '-', '–'}


def _timestamp(value, path):
    """A timezone-aware datetime. Accepts "Z", a missing offset (read as UTC) and a bare date."""
    if not isinstance(value, str) or not value.strip():
        _bad(path, 'a timestamp such as "2026-10-03T00:00:00Z"', value)
    text = value.strip().replace('Z', '+00:00').replace('z', '+00:00')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        text += 'T00:00:00+00:00'
    try:
        made = datetime.fromisoformat(text)
    except ValueError:
        _bad(path, 'a timestamp such as "2026-10-03T00:00:00Z"', value)
    return made if made.tzinfo else made.replace(tzinfo=timezone.utc)


def _zone(moment):
    offset = int(moment.utcoffset().total_seconds())
    if not offset:
        return 'UTC'
    return 'UTC' + ('+' if offset > 0 else '−') + f'{abs(offset) // 3600}' + (f':{abs(offset) % 3600 // 60:02d}' if abs(offset) % 3600 else '')


def _clock(moment):
    return f'{MONTHS[moment.month - 1]} {moment.day}, {moment.hour % 12 or 12}:{moment.minute:02d} {"am" if moment.hour < 12 else "pm"}'


def _day(moment, exclusive_end=False):
    # An end exactly at midnight is exclusive, so the day shown is the one before.
    if exclusive_end and (moment.hour, moment.minute, moment.second) == (0, 0, 0):
        moment -= timedelta(days=1)
    return f'{MONTHS[moment.month - 1]} {moment.day}'


def _window_names(start, end):
    """(header text, current period name, previous period name), all written for people."""
    length = end - start
    zone = _zone(end)
    if length <= timedelta(hours=36):
        hours = max(1, round(length.total_seconds() / 3600))
        unit = 'hour' if hours == 1 else 'hours'
        return f'Last {hours} {unit} to {_clock(end)} ({zone})', f'Last {hours} {unit}', f'Previous {hours} {unit}'
    span = lambda a, b: f'{_day(a)} – {_day(b, True)}'
    current, previous = span(start, end), span(start - length, start)
    if timedelta(days=6, hours=12) <= length <= timedelta(days=7, hours=12):
        return f'{current} ({zone})', 'Current week', 'Previous week'
    return f'{current} ({zone})', current, previous


def _clean(text):
    """Display text: no citation tags, timestamps as people read them, single spaces."""
    text = _CITATION.sub('', text)
    def human(match):
        try:
            moment = _timestamp(match.group(0), 'text')
        except ReportError:
            return match.group(0)
        return f'{_clock(moment)} ({_zone(moment)})'
    return re.sub(r'\s+', ' ', _ISO_TIME.sub(human, text)).strip()


def _text(value, path, required=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            _bad(path, 'a non-empty string', value)
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str):
        _bad(path, 'a string', value)
    return _clean(value)


def _trim(text, limit):
    if text is None or len(text) <= limit:
        return text
    return text[:limit - 1].rsplit(' ', 1)[0].rstrip(' ,;:·-–') + '…'


def _sentence(text, limit):
    """The first sentence, cut to the limit."""
    first = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9(])', text)[0]
    return _trim(first, limit)


def _short_title(given, title):
    words = re.sub(r'[.:;,]+$', '', given or title).split()[:SHORT_WORDS]
    while not given and len(words) > 1 and words[-1].lower().strip('.,:;') in _TRAILING:
        words.pop()
    return ' '.join(words).rstrip('.,:;…')


def _number(value, path, kind):
    """A number or None. Accepts a number sent as a string ("1,234", "54.2%", "$82.40")."""
    if value is None:
        return None
    wanted = 'a whole number of 0 or more, or null' if kind == 'count' else 'a number or null'
    if isinstance(value, bool):
        _bad(path, wanted, value)
    if isinstance(value, str):
        stripped = re.sub(r'[,\s%$£€¥]|\b[A-Z]{3}\b', '', value)
        if stripped.lower() in {'', 'null', 'none', 'n/a', 'notmeasured', '—', '-'}:
            return None
        try:
            value = float(stripped)
        except ValueError:
            _bad(path, wanted, value)
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        _bad(path, wanted, value)
    if kind == 'count':
        if value < 0 or value != int(value):
            _bad(path, wanted, value)
        return int(value)
    if kind in {'rate', 'money'} and value < 0:
        _bad(path, 'a number of 0 or more, or null', value)
    return value


def _pair(value, path, kind):
    """(current, prior). Accepts a bare value or {"current": …, "prior": …}."""
    if isinstance(value, dict):
        unknown = set(value) - {'current', 'prior'}
        if unknown or 'current' not in value:
            _bad(path, 'a value, or an object with "current" and optionally "prior"', value)
        return _number(value['current'], path + '.current', kind), _number(value.get('prior'), path + '.prior', kind)
    return _number(value, path, kind), None


def _match(value, choices, path):
    """Match a label or key against a list, ignoring case, spaces and punctuation."""
    squash = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())
    for choice in choices:
        if squash(choice) == squash(value):
            return choice
    _bad(path, 'one of: ' + ', '.join(choices), value)


def validate_url(url, path='link', domain_id=None):
    """A console.noibu.com page for this store. Syntax only: it can't prove the page exists."""
    must = 'an https://console.noibu.com/<store id>/… URL returned by a Noibu tool'
    if not isinstance(url, str) or len(url) > 2048 or re.search(r'[\s\\\x00-\x1f]', url):
        _bad(path, must, url)
    parsed = urlsplit(url)
    segments = parsed.path.split('/')
    if parsed.scheme != 'https' or parsed.netloc != 'console.noibu.com' or parsed.fragment \
            or len(segments) < 3 or not segments[2] or any(part in {'.', '..'} for part in segments):
        _bad(path, must, url)
    try:
        store = str(UUID(segments[1]))
    except ValueError:
        _bad(path, must, url)
    if domain_id and store != domain_id:
        _bad(path, 'a link for this store, not another one', url)
    if any(re.search(r'token|secret|password|authorization', key, re.I) for key, _ in parse_qsl(parsed.query)):
        _bad(path, 'a link without credentials in it', url)
    return url


def _link_label(url):
    parts = [p for p in urlsplit(url).path.split('/') if p][1:]
    route, rest = parts[0], parts[1:]
    if route == 'issues':
        return 'View issue in Noibu' if rest else 'View issues in Noibu'
    if route == 'sessions':
        return 'Watch session in Noibu' if rest[:1] == ['player'] else 'View sessions in Noibu'
    return {'performance': 'View performance in Noibu', 'pages': 'View pages in Noibu'}.get(route, 'Open in Noibu')


def read_report(report):
    """Validate the report data and return the model the card is drawn from."""
    if not isinstance(report, dict):
        _bad('report', 'a JSON object', report)
    skill = report.get('skill')
    if skill not in SKILLS:
        _bad('skill', 'one of: ' + ', '.join(SKILLS), skill)
    spec = SKILLS[skill]
    unknown = sorted(set(report) - REPORT_FIELDS)
    if unknown:
        _bad(unknown[0], 'left out; the report fields are: ' + ', '.join(sorted(REPORT_FIELDS)))

    store = report.get('store')
    if isinstance(store, str):
        store = {'name': store}
    if not isinstance(store, dict) or set(store) - {'name', 'id'}:
        _bad('store', 'an object with "name" and optionally "id"', store)
    name = _text(store.get('name'), 'store.name', required=True)
    store_id = None
    if store.get('id') is not None:
        try:
            store_id = str(UUID(str(store['id'])))
        except ValueError:
            _bad('store.id', "the store's Noibu domain UUID", store['id'])

    window = report.get('window')
    if not isinstance(window, dict) or set(window) != {'start', 'end'}:
        _bad('window', 'an object with "start" and "end" timestamps', window)
    start, end = _timestamp(window['start'], 'window.start'), _timestamp(window['end'], 'window.end')
    if end <= start:
        _bad('window.end', 'later than window.start', window['end'])
    header, current_name, prior_name = _window_names(start, end)

    currency = report.get('currency')
    if currency is not None and not (isinstance(currency, str) and re.fullmatch(r'[A-Za-z]{3}', currency.strip())):
        _bad('currency', 'a three-letter currency code such as "USD"', currency)
    model = {'skill': skill, 'spec': spec, 'store': name, 'window': header, 'periods': (current_name, prior_name),
             'currency': currency.strip().upper() if currency else None, 'money': False}

    def need_currency(kind, value, path):
        if kind == 'money' and value is not None:
            model['money'] = True
            if not model['currency']:
                _bad('currency', f'given (for example "USD") because {path} is a money value')

    # KPIs: an absent key is left off the card; null shows as "Not measured".
    kinds = {key: kind for key, kind, _ in spec.get('context', [])}
    for item in spec.get('tiles', []) + spec.get('stats', []):
        kinds[item['key']] = item['kind']
        if item['sub']:
            kinds[item['sub']] = 'count'
    kpis = report.get('kpis') or {}
    if not isinstance(kpis, dict):
        _bad('kpis', 'an object', kpis)
    model['kpis'] = {}
    for key, value in kpis.items():
        if key not in kinds:
            _bad(f'kpis.{key}', 'left out; this skill takes: ' + (', '.join(kinds) or 'no kpis'))
        model['kpis'][key] = _pair(value, f'kpis.{key}', kinds[key])
        need_currency(kinds[key], model['kpis'][key][0], f'kpis.{key}')

    # Funnel: stages in the skill's order; an absent stage is left out, null is "Not measured".
    funnel = report.get('funnel') or {}
    stages = spec.get('funnel', {}).get('stages', [])
    if not isinstance(funnel, dict):
        _bad('funnel', 'an object', funnel)
    for key in funnel:
        if key not in dict(stages):
            _bad(f'funnel.{key}', 'left out; this skill takes: ' + (', '.join(k for k, _ in stages) or 'no funnel'))
    model['funnel'] = [(label,) + _pair(funnel[key], f'funnel.{key}', 'count') for key, label in stages if key in funnel]

    # Tables: rows are objects keyed by column, or arrays in column order.
    tables = report.get('tables') or {}
    table_specs = {t['key']: t for t in spec.get('tables', [])}
    if not isinstance(tables, dict):
        _bad('tables', 'an object', tables)
    model['tables'] = {}
    for key, rows in tables.items():
        if key not in table_specs:
            _bad(f'tables.{key}', 'left out; this skill takes: ' + (', '.join(table_specs) or 'no tables'))
        columns = table_specs[key]['columns']
        if not isinstance(rows, list):
            _bad(f'tables.{key}', 'a list of rows', rows)
        parsed = []
        for i, row in enumerate(rows):
            path = f'tables.{key}[{i}]'
            if isinstance(row, (list, tuple)) and len(row) == len(columns):
                row = {column[0]: cell for column, cell in zip(columns, row)}
            if not isinstance(row, dict) or set(row) - {c[0] for c in columns}:
                _bad(path, 'an object with: ' + ', '.join(c[0] for c in columns), row)
            cells = []
            for column, _, kind in columns:
                if kind in {'text', 'country'}:
                    cells.append(_trim(_text(row.get(column), f'{path}.{column}', required=(column == columns[0][0])), CELL_CHARS))
                else:
                    cells.append(_number(row.get(column), f'{path}.{column}', kind))
                    need_currency(kind, cells[-1], f'{path}.{column}')
            parsed.append(cells)
        if parsed:
            model['tables'][key] = parsed

    # Priorities (or, for A/B testing, tests), in rank order.
    listed = spec.get('items', 'priorities')
    other = 'tests' if listed == 'priorities' else 'priorities'
    if report.get(other):
        _bad(other, f'left out; this skill lists its findings under "{listed}"')
    priorities = report.get(listed) or []
    if not isinstance(priorities, list):
        _bad(listed, 'a list', priorities)
    allowed = TEST_FIELDS if listed == 'tests' else PRIORITY_FIELDS | PRIORITY_EXTRA.get(skill, set())
    model['priorities'] = []
    for i, item in enumerate(priorities):
        path = f'{listed}[{i}]'
        if not isinstance(item, dict):
            _bad(path, 'an object', item)
        for key in item:
            if key not in allowed:
                _bad(f'{path}.{key}', f'left out; an entry in {listed} takes: ' + ', '.join(sorted(allowed)))
        title = _trim(_text(item.get('title'), f'{path}.title', required=True), TITLE_CHARS)
        if listed == 'tests':
            model['priorities'].append({
                'title': title, 'short': _short_title(_text(item.get('shortTitle'), f'{path}.shortTitle'), title),
                'change': _sentence(_text(item.get('change'), f'{path}.change', required=True), EVIDENCE_CHARS),
                'why': _trim(_text(item.get('why'), f'{path}.why', required=True), WHY_CHARS),
                'affected': None})
            continue
        entry = {'title': title, 'short': _short_title(_text(item.get('shortTitle'), f'{path}.shortTitle'), title),
                 'evidence': _sentence(_text(item.get('evidence'), f'{path}.evidence', required=True), EVIDENCE_CHARS),
                 'affected': _number(item.get('affected'), f'{path}.affected', 'count'),
                 'link': validate_url(item['link'], f'{path}.link', store_id) if item.get('link') else None,
                 'tag': None, 'chip': None, 'facts': [], 'vital': None}
        if 'signals' in spec:
            if item.get('signal') is None:
                _bad(f'{path}.signal', 'one of: ' + ', '.join(spec['signals']))
            entry['tag'] = _match(item['signal'], spec['signals'], f'{path}.signal')
        if skill == 'accessibility-audit':
            if item.get('severity') is None:
                _bad(f'{path}.severity', 'one of: ' + ', '.join(SEVERITIES))
            entry['tag'] = SEVERITIES[_match(item['severity'], list(SEVERITIES), f'{path}.severity')]
            wcag = _trim(_text(item.get('wcag'), f'{path}.wcag'), CELL_CHARS)
            pages = _number(item.get('pages'), f'{path}.pages', 'count')
            entry['facts'] = [x for x in [f'WCAG {wcag}' if wcag else None, f'{pages:,} {"page" if pages == 1 else "pages"} affected' if pages is not None else None] if x]
        if skill == 'tech-diagnosis':
            if item.get('kind') is None:
                _bad(f'{path}.kind', 'one of: ' + ', '.join(KINDS))
            kind = _match(item['kind'], list(KINDS), f'{path}.kind')
            entry['tag'] = KINDS[kind]
            if item.get('status') is not None:
                entry['chip'] = STATUSES[_match(item['status'], list(STATUSES), f'{path}.status')]
            occurrences = _number(item.get('occurrences'), f'{path}.occurrences', 'count')
            seen = _timestamp(item['lastSeen'], f'{path}.lastSeen') if item.get('lastSeen') else None
            entry['facts'] = [x for x in [
                _trim(_text(item.get('vendor'), f'{path}.vendor'), TAG_CHARS), _trim(_text(item.get('errorType'), f'{path}.errorType'), TAG_CHARS),
                f'{occurrences:,} {"occurrence" if occurrences == 1 else "occurrences"}' if occurrences is not None else None,
                f'last seen {_clock(seen)} ({_zone(seen)})' if seen else None,
                _trim(_text(item.get('where'), f'{path}.where'), TITLE_CHARS),
                f'~{entry["affected"]:,} sessions affected' if entry['affected'] is not None and entry['chip'] else None] if x]
            vital = item.get('vital')
            if vital is not None:
                if not isinstance(vital, dict) or set(vital) - {'metric', 'value'} or 'metric' not in vital:
                    _bad(f'{path}.vital', 'an object with "metric" and "value"', vital)
                metric = _match(vital['metric'], list(VITALS), f'{path}.vital.metric')
                entry['vital'] = (metric, _number(vital.get('value'), f'{path}.vital.value', 'rate'))
            elif kind == 'performance':
                _bad(f'{path}.vital', 'given for a performance priority: {"metric": "LCP", "value": 4200}')
        model['priorities'].append(entry)

    reason = _text(report.get('noPrioritiesReason'), 'noPrioritiesReason')
    model['reason'] = _sentence(reason, EVIDENCE_CHARS) if reason else None

    pages = report.get('reportPages')
    if pages is not None and (not isinstance(pages, bool) or skill != 'ab-testing'):
        _bad('reportPages', 'true or false, for ab-testing only', pages)
    model['report_pages'] = bool(pages)

    links = report.get('links') or []
    if isinstance(links, str):
        links = [links]
    if not isinstance(links, list):
        _bad('links', 'a list of console.noibu.com URLs', links)
    model['links'] = []
    for i, url in enumerate(links):
        if isinstance(url, dict) and 'url' in url:
            url = url['url']
        url = validate_url(url, f'links[{i}]', store_id)
        if url.rstrip('/') not in {u.rstrip('/') for u in model['links']}:    # one link per Noibu page
            model['links'].append(url)
    return model


# ---------------------------------------------------------------------------------------------
# Formatting values.
# ---------------------------------------------------------------------------------------------

def _percent(value):
    text = f'{value:.2f}' if abs(value) < 1 else f'{value:.1f}'
    return (text.rstrip('0').rstrip('.') if '.' in text else text) + '%'


def _format(value, kind, currency=None):
    if value is None:
        return NOT_MEASURED
    if kind == 'count':
        return f'{value:,}'
    if kind == 'rate':
        return f'{value:.2f}%' if abs(value) < 1 else f'{value:.1f}%'
    if kind == 'money':
        amount = f'{value:,.0f}' if abs(value) >= 1000 else f'{value:,.2f}'
        symbol = CURRENCY_SYMBOLS.get(currency)
        return symbol + amount if symbol else f'{currency} {amount}'
    if kind == 'country':
        code = value.strip().upper()
        if re.fullmatch(r'[A-Z]{2}', code):
            flag = ''.join(chr(0x1F1E6 + ord(c) - 65) for c in ('GB' if code == 'UK' else code))
            return f'{flag} {COUNTRIES.get(code, code)}'
        return value
    if kind == 'number':
        return f'{value:,.1f}'.rstrip('0').rstrip('.') if value != int(value) else f'{int(value):,}'
    return str(value)


def _change(current, prior, kind):
    """(direction, text) or None. For a rate it is the difference between the two rates, in
    percentage points ("pp"); for counts and money it is the relative change, in "%". No prior
    value, no change."""
    if current is None or prior is None:
        return None
    if kind == 'rate':
        delta = current - prior
        text = _percent(abs(delta))[:-1] + 'pp'
    elif prior == 0:
        return None
    else:
        delta = (current - prior) / abs(prior) * 100
        text = _percent(abs(delta))
    if text in ('0%', '0pp'):
        return 'flat', text
    return ('up' if delta > 0 else 'down'), text


# ---------------------------------------------------------------------------------------------
# Drawing the card.
# ---------------------------------------------------------------------------------------------

def _run(text, **style):
    return {'type': 'TextRun', 'text': str(text), **style}


def _rich(*runs, spacing=None, align=None):
    block = {'type': 'RichTextBlock', 'inlines': [r if isinstance(r, dict) else _run(r) for r in runs]}
    if spacing:
        block['spacing'] = spacing
    if align:
        block['horizontalAlignment'] = align
    return block


def _eyebrow(text, **extra):
    return _rich(_run(str(text).upper(), size='Small', weight='Bolder', isSubtle=True), **extra)


def _quiet(text, **extra):
    return _rich(_run(text, size='Small', isSubtle=True), **extra)


def _delta(change, good='up'):
    """An arrow with the colour, never colour alone."""
    if not change:
        return None
    direction, text = change
    if direction == 'flat':
        return _run('— ' + text, size='Small', isSubtle=True)
    favourable = direction == good
    return _run(('↑ ' if direction == 'up' else '↓ ') + text, size='Small', weight='Bolder', color='Good' if favourable else 'Warning')


def _section(element):
    element.update(separator=True, spacing='Medium')
    return element


def _tiles(model):
    spec, kpis = model['spec'], model['kpis']
    shown = [t for t in spec.get('tiles', []) if t['key'] in kpis][:MAX_TILES]
    if not shown:
        return []
    columns = []
    for tile in shown:
        current, prior = kpis[tile['key']]
        size = 'Large' if len(shown) <= 4 else 'Medium'
        items = [_eyebrow(tile['label']), _rich(_run(_format(current, tile['kind'], model['currency']), size=size, weight='Bolder'), spacing='Small')]
        delta = _delta(_change(current, prior, tile['kind']), tile['good'])
        if delta:
            items.append(_rich(delta, spacing='None'))
        if tile['sub'] and kpis.get(tile['sub'], (None,))[0] is not None:
            items.append(_quiet(f'{kpis[tile["sub"]][0]:,} sessions', spacing='None'))
        columns.append({'type': 'Column', 'width': 'stretch', 'style': 'emphasis', 'spacing': 'Small', 'items': items})
    out = [_eyebrow(spec['tilesTitle'], spacing='Medium')] if spec.get('tilesTitle') else []
    return out + [{'type': 'ColumnSet', 'spacing': 'Small' if out else 'Medium', 'columns': columns}]


def _context(model):
    parts = []
    for key, kind, template in model['spec'].get('context', []):
        value = model['kpis'].get(key, (None,))[0]
        if value is not None:
            parts.append(template.format(_format(value, kind, model['currency'])))
    return [_quiet(' · '.join(parts), spacing='Small')] if parts else []


def _stats(model):
    runs = []
    for stat in model['spec'].get('stats', []):
        if stat['key'] in model['kpis']:
            value = _format(model['kpis'][stat['key']][0], stat['kind'], model['currency'])
            runs += [_run(('   ' if runs else '') + stat['label'] + ' ', size='Small', isSubtle=True), _run(value, size='Small', weight='Bolder')]
    return [_rich(*runs, spacing='Small')] if runs else []


def _grid(headers, rows, numeric):
    """A plain table: uppercase header row, divided rows, right-aligned numbers."""
    widths = [1 if i in numeric else 3 if i == 0 else 2 for i in range(len(headers))]
    align = lambda i: 'Right' if i in numeric else None
    head = {'type': 'ColumnSet', 'columns': [{'type': 'Column', 'width': widths[i], 'items': [_eyebrow(h, align=align(i))]} for i, h in enumerate(headers)]}
    body = [{'type': 'ColumnSet', 'separator': True, 'spacing': 'Small', 'columns': [
        {'type': 'Column', 'width': widths[i], 'items': [_rich(_run(cell, size='Small'), align=align(i))]} for i, cell in enumerate(row)]} for row in rows]
    return {'type': 'Container', 'items': [head] + body}


def _funnel(model, compact):
    stages = model['funnel']
    if not stages:
        return []
    spec = model['spec']['funnel']
    base, prior_base = stages[0][1], stages[0][2]
    rate = lambda count, of: 100 * count / of if count is not None and of else None
    rows = []
    for i, (label, current, prior) in enumerate(stages):
        if i == 0:
            rows.append({'label': label, 'value': spec['first'].format(_format(current, 'count')), 'rate': 100.0 if current else None, 'priorRate': 100.0 if prior else None,
                         'priorValue': _format(prior, 'count') if prior is not None else '', 'change': _change(current, prior, 'count')})
        else:
            now, before = rate(current, base), rate(prior, prior_base)
            rows.append({'label': label, 'value': _format(now, 'rate'), 'rate': now, 'priorRate': before,
                         'priorValue': _format(before, 'rate') if before is not None else '', 'change': _change(now, before, 'rate')})
    # The largest step drop, marked on the step where it lands.
    pill = None
    if spec['pill']:
        drops = [(1 - stages[i][1] / stages[i - 1][1], i) for i in range(1, len(stages))
                 if stages[i][1] is not None and stages[i - 1][1] and stages[i][1] <= stages[i - 1][1]]
        if drops and max(drops)[0] > 0:
            pill = (max(drops)[1], f'↓{max(drops)[0]:.0%} step drop')
    current_name, prior_name = model['periods']
    has_prior = any(r['priorRate'] is not None for r in rows)
    arrow = lambda c: '' if not c else ('— ' if c[0] == 'flat' else '↑ ' if c[0] == 'up' else '↓ ') + c[1]
    headers = ['Stage', current_name] + ([prior_name, 'Change'] if has_prior else [])
    table = _grid(headers, [[r['label'], r['value']] + ([r['priorValue'], arrow(r['change'])] if has_prior else []) for r in rows], numeric=set(range(1, len(headers))))
    series = [{'legend': name, 'color': color, 'values': [{'x': r['label'], 'y': round(r[key], 2 if r[key] < 1 else 1)} for r in rows if r[key] is not None]}
              for key, name, color in (('rate', current_name, 'sequential7'), ('priorRate', prior_name, 'sequential3'))]
    series = [s for s in series if s['values']]
    if compact or not series:
        return [_section(table)]
    columns = []
    for i, r in enumerate(rows):
        items = [_eyebrow(r['label']), _rich(_run(r['value'], weight='Bolder'), spacing='Small')]
        delta = _delta(r['change'])
        if delta:
            items.append(_rich(delta, spacing='None'))
        if pill and pill[0] == i:
            items.append(_rich(_run(pill[1], size='Small', weight='Bolder', color='Attention'), spacing='None'))
        column = {'type': 'Column', 'width': 'stretch', 'items': items}
        if i:
            column.update(separator=True, spacing='Small')
        columns.append(column)
    top = max([100.0] + [v['y'] for s in series for v in s['values']])
    chart = {'type': 'Chart.VerticalBar.Grouped', 'title': spec['axis'], 'yAxisTitle': spec['axis'], 'yMin': 0, 'yMax': top, 'data': series, 'fallback': table}
    return [_section({'type': 'ColumnSet', 'columns': columns}), chart]


def _table_block(model, table, rows_shown):
    columns = table['columns']
    numeric = {i for i, c in enumerate(columns) if c[2] not in {'text', 'country'}}
    rows = [[_format(cell, columns[i][2], model['currency']) for i, cell in enumerate(row)] for row in model['tables'][table['key']][:rows_shown]]
    return _grid([c[1] for c in columns], rows, numeric)


def _tables(model, compact):
    """Up to MAX_TABLES tables in the skill's order. Any table past that is one line naming its top row."""
    populated = [t for t in model['spec'].get('tables', []) if t['key'] in model['tables']]
    rows_shown = COMPACT_ROWS if compact else PREVIEW_ROWS
    out, slots, i = [], 0, 0
    while i < len(populated) and slots < MAX_TABLES:
        table = populated[i]
        partner = populated[i + 1] if table['half'] and i + 1 < len(populated) and populated[i + 1]['half'] else None
        if partner:
            out.append(_section({'type': 'ColumnSet', 'columns': [
                {'type': 'Column', 'width': 1, 'items': [_table_block(model, t, rows_shown)]} for t in (table, partner)]}))
        else:
            out.append(_section(_table_block(model, table, rows_shown)))
        slots, i = slots + 1, i + (2 if partner else 1)
    tops = []
    for table in populated[i:]:
        if not table['top']:
            continue
        label, keys = table['top']
        row = dict(zip([c[0] for c in table['columns']], model['tables'][table['key']][0]))
        kinds = {c[0]: c[2] for c in table['columns']}
        name_key = table['columns'][0][0]
        facts = [TOP_SUFFIX[k].format(_format(row[k], kinds[k], model['currency'])) for k in keys if row.get(k) is not None]
        tops.append(_rich(_run(label.upper() + '  ', size='Small', weight='Bolder', isSubtle=True),
                          _run(' · '.join([_format(row[name_key], kinds[name_key])] + facts), size='Small'), spacing='Small'))
    if tops:
        tops[0].update(separator=True, spacing='Medium')
    return out + tops


def _vital_runs(vital):
    metric, value = vital
    if value is None:
        return [_run(f'{metric} p75 ', size='Small', isSubtle=True), _run(NOT_MEASURED, size='Small', weight='Bolder')]
    good, poor = VITALS[metric]
    band, colour = ('Good', 'Good') if value <= good else ('Needs improvement', 'Warning') if value <= poor else ('Poor', 'Attention')
    shown = f'{value:g}' if metric == 'CLS' else f'{value / 1000:.1f} s' if metric == 'LCP' else f'{value:,.0f} ms'
    return [_run(f'{metric} p75 ', size='Small', isSubtle=True), _run(shown, weight='Bolder'), _run(f'  {band}', size='Small', weight='Bolder', color=colour)]


def _tests(model):
    """A/B testing: one block per test, with what to change and why."""
    out = []
    for n, test in enumerate(model['priorities'][:model['spec']['drawn']], 1):
        out.append(_section(_eyebrow(f'Test {n}')))
        out.append(_quiet('WHAT TO CHANGE', spacing='Small'))
        out.append(_rich(_run(test['title'], weight='Bolder'), spacing='None'))
        out.append(_rich(_run(test['change'], size='Small'), spacing='Small'))
        out.append(_quiet('WHY THIS TEST', spacing='Small'))
        out.append(_rich(_run(test['why'], size='Small'), spacing='None'))
    return out


def _priorities(model):
    unit = model['spec']['unit']
    if not model['priorities']:
        out = [_section(_eyebrow(model['spec'].get('emptyLabel', 'No priorities')))]
        if model['reason']:
            out.append(_rich(_run(model['reason'], size='Small'), spacing='Small'))
        return out
    if model['spec'].get('items') == 'tests':
        return _tests(model)
    out = []
    for n, p in enumerate(model['priorities'][:MAX_PRIORITIES], 1):
        label = f'Priority {n}' + (f' · {p["tag"]}' if p['tag'] else '')
        if p['chip']:
            right = _rich(_run(p['chip'][0], size='Small', weight='Bolder', color=p['chip'][1]), align='Right')
        elif p['affected'] is not None:
            right = _rich(_run(f'~{p["affected"]:,} {unit} affected', size='Small', weight='Bolder', isSubtle=True), align='Right')
        else:
            right = None
        head = [{'type': 'Column', 'width': 3, 'items': [_eyebrow(label)]}]
        if right:
            head.append({'type': 'Column', 'width': 2, 'items': [right]})
        out.append(_section({'type': 'ColumnSet', 'columns': head}))
        out.append(_rich(_run(p['title'], weight='Bolder'), spacing='Small'))
        out.append(_rich(_run(p['evidence'], size='Small'), spacing='Small'))
        if p['vital']:
            out.append(_rich(*_vital_runs(p['vital']), spacing='Small'))
        if p['facts']:
            out.append(_quiet(' · '.join(p['facts']), spacing='Small'))
        if p['link']:
            out.append(_rich(_run(_link_label(p['link']) + ' ↗', size='Small', color='Accent', selectAction={'type': 'Action.OpenUrl', 'url': p['link']}), spacing='Small'))
    return out


def _link_buttons(model):
    links = model['links'][:MAX_LINK_BUTTONS]
    if not links:
        return []
    # Body elements with selectAction: the host receives the card body, not top-level actions.
    columns = [{'type': 'Column', 'width': 'auto', 'style': 'emphasis', 'selectAction': {'type': 'Action.OpenUrl', 'url': url},
                'items': [_rich(_run(_link_label(url) + ' ↗', size='Small', weight='Bolder', color='Accent'))]} for url in links]
    return [_section({'type': 'ColumnSet', 'columns': columns})]


def draw(model, compact=False):
    """Header, context line, KPI tiles, funnel, tables, priorities, link buttons. Empty sections are left out."""
    header = {'type': 'Container', 'style': 'emphasis', 'bleed': True, 'items': [
        _eyebrow(model['spec']['title']), _quiet(f'{model["store"]} · {model["window"]}', spacing='None')]}
    body = [header] + _context(model) + _tiles(model) + _stats(model) + _funnel(model, compact) \
        + _tables(model, compact) + _priorities(model) + _link_buttons(model)
    return {'type': 'AdaptiveCard', '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json', 'version': '1.6', 'body': body}


# ---------------------------------------------------------------------------------------------
# Checking the card before it is shown.
# ---------------------------------------------------------------------------------------------

_ELEMENTS = {'Container', 'ColumnSet', 'Column', 'TextBlock', 'RichTextBlock', 'FactSet', 'Table', 'TableRow', 'TableCell', 'Badge',
             'ProgressBar', 'Icon', 'Chart.Donut', 'Chart.Pie', 'Chart.VerticalBar', 'Chart.VerticalBar.Grouped', 'Chart.HorizontalBar',
             'Chart.HorizontalBar.Stacked', 'Chart.Line', 'Chart.Gauge'}
_NESTED = {'Column': ('ColumnSet', 'columns'), 'TableRow': ('Table', 'rows'), 'TableCell': ('TableRow', 'cells')}
_CHART_COLORS = {'good', 'warning', 'attention', 'neutral'} \
    | {f'categorical{c}' for c in ('Red', 'Purple', 'Lavender', 'Blue', 'LightBlue', 'Teal', 'Green', 'Lime', 'Marigold')} \
    | {f'sequential{n}' for n in range(1, 9)}
_ENUMS = {'spacing': {'None', 'ExtraSmall', 'Small', 'Default', 'Medium', 'Large', 'ExtraLarge', 'Padding'},
          'horizontalAlignment': {'Left', 'Center', 'Right'}, 'verticalContentAlignment': {'Top', 'Center', 'Bottom'}}
_TEXT_ENUMS = {'size': {'Small', 'Default', 'Medium', 'Large', 'ExtraLarge'}, 'weight': {'Lighter', 'Default', 'Bolder'},
               'color': {'Default', 'Dark', 'Light', 'Accent', 'Good', 'Warning', 'Attention'}}
_STYLES = {'default', 'emphasis', 'accent', 'good', 'attention', 'warning'}
_HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')


def check(card):
    """Problems that would stop the host showing this card: Adaptive Card 1.6, allowed elements only,
    link actions only, at most two link buttons, host colour names, console.noibu.com links only."""
    errors = []
    err = lambda path, message: errors.append(f'{path}: {message}')
    buttons = []
    if card.get('type') != 'AdaptiveCard':
        err('type', "must be 'AdaptiveCard'")
    if card.get('version') != '1.6':
        err('version', "must be '1.6'")
    if not isinstance(card.get('body'), list) or not card['body']:
        err('body', 'must be a non-empty list')
    if card.get('actions'):
        err('actions', 'top-level actions are not shown; use link buttons in the body')

    def action(a, path):
        if not isinstance(a, dict) or a.get('type') != 'Action.OpenUrl':
            return err(path, 'only Action.OpenUrl is allowed')
        try:
            validate_url(a.get('url'), path)
        except ReportError as exc:
            err(path, str(exc))

    def element(el, path, parent=None, slot=None):
        if not isinstance(el, dict):
            return err(path, 'must be an object')
        kind = el.get('type')
        if kind == 'TextRun':
            if parent != 'RichTextBlock':
                err(path, 'TextRun belongs in RichTextBlock.inlines')
        elif kind not in _ELEMENTS:
            return err(path, f'{kind!r} is not an allowed element')
        if kind in _NESTED and (parent, slot) != _NESTED[kind]:
            err(path, f'{kind} must sit in {_NESTED[kind][0]}.{_NESTED[kind][1]}')
        for key, allowed in _ENUMS.items():
            if key in el and el[key] not in allowed:
                err(f'{path}.{key}', f'{el[key]!r} is not allowed')
        if kind in {'TextBlock', 'TextRun'}:
            for key, allowed in _TEXT_ENUMS.items():
                if key in el and el[key] not in allowed:
                    err(f'{path}.{key}', f'{el[key]!r} is not a host name')
        if 'style' in el and el['style'] not in _STYLES:
            err(f'{path}.style', f'{el["style"]!r} is not a host style')
        for key in ('color', 'style', 'backgroundColor', 'borderColor'):
            if isinstance(el.get(key), str) and _HEX.search(el[key]):
                err(f'{path}.{key}', 'hex colours are not allowed; use a host colour name')
        if kind and kind.startswith('Chart.'):
            for i, series in enumerate(el.get('data', [])):
                if not isinstance(series, dict) or series.get('color', 'good') not in _CHART_COLORS:
                    err(f'{path}.data[{i}]', 'needs a host chart colour')
                elif kind == 'Chart.VerticalBar.Grouped' and not isinstance(series.get('values'), list):
                    err(f'{path}.data[{i}]', 'needs legend and values')
        if 'selectAction' in el:
            action(el['selectAction'], f'{path}.selectAction')
            if kind != 'TextRun':
                buttons.append(path)
        for name in ('items', 'columns', 'rows', 'cells', 'inlines'):
            for i, child in enumerate(el.get(name) or []):
                element(child, f'{path}.{name}[{i}]', kind, name)
        if isinstance(el.get('fallback'), dict):
            element(el['fallback'], f'{path}.fallback', parent, slot)

    for i, el in enumerate(card.get('body') or []):
        element(el, f'body[{i}]')
    if len(buttons) > MAX_LINK_BUTTONS:
        err('body', f'{len(buttons)} link buttons; at most {MAX_LINK_BUTTONS}')
    return errors


def card_bytes(card):
    return len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def build(report, compact=False, limit=CARD_LIMIT):
    """(card, variant, model). Switches to the compact card when the full one is over the limit."""
    model = read_report(report)
    for variant in (['compact'] if compact else ['full', 'compact']):
        card = draw(model, compact=(variant == 'compact'))
        problems = check(card)
        if problems:
            raise ValueError('the card did not pass its own check (' + '; '.join(problems[:3]) + ')')
        size = card_bytes(card)
        if size <= limit:
            return card, variant, model
    raise CardSizeError(f'it is larger than the {limit:,}-byte card limit even in compact form ({size:,} bytes)')


def next_step(model):
    """The next-step question's options (the priorities in card order; fixed routes for A/B testing) and the line to use if it is skipped."""
    spec = model['spec']
    unit, options, seen = spec['unit'], [], set()
    if spec.get('items') == 'tests':    # a fixed set of routes; the test itself is picked in a second question
        count = len(model['priorities'])
        if count and model.get('report_pages'):
            options.append({'label': 'View full reports', 'description': 'Open the full report page for each test.' if count > 1 else 'Open the test\'s full report page.'})
        if count:
            options.append({'label': 'Implement one of the tests', 'description': 'Pick a test to create in Noibu and build.'} if count > 1
                           else {'label': 'Implement this test', 'description': 'Create the test in Noibu and build it.'})
        options += [{'label': 'Look for tests on a different goal', 'description': 'Run the analysis again for another goal.'},
                    {'label': 'Create a specific A/B test', 'description': 'Describe the change you want to test and I\'ll build it.'}]
        return options, f'To go deeper, ask: "{spec["ask"].format(n=1)} for {model["store"]}".' if count else f'To go deeper, ask about any part of this report for {model["store"]}.'
    for n, p in enumerate(model['priorities'][:MAX_OPTIONS], 1):
        label = p['short']
        if label.casefold() in seen:
            label = ' '.join(label.split()[:SHORT_WORDS - 1]) + f' #{n}'
        seen.add(label.casefold())
        options.append({'label': label, 'description': f'{spec.get("itemLabel", "Priority")} {n}' + (f' · ~{p["affected"]:,} {unit}' if p['affected'] is not None else '')})
    if options and spec.get('ask'):
        recovery = f'To go deeper, ask: "{spec["ask"].format(n=1)} for {model["store"]}".'
    elif options:
        recovery = f'To go deeper, ask: "investigate {options[0]["label"]} for {model["store"]}".'
    else:
        recovery = f'To go deeper, ask about any part of this report for {model["store"]}.'
    return options, recovery


# ---------------------------------------------------------------------------------------------
# Showing the card in Cowork, and the command line.
# ---------------------------------------------------------------------------------------------

def _acknowledged(result):
    """'shown', 'failed', 'declined' or 'unconfirmed', from the host's reply to the one render call."""
    status = getattr(result, 'status', None)
    if status in {'denied', 'refused'}:
        return 'declined'
    bodies = []
    for raw in (getattr(result, 'payload', None), getattr(result, 'data', None), getattr(result, 'text', None)):
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                continue
        if isinstance(raw, dict) and set(raw) == {'status', 'data'} and raw['status'] in {'complete', 'ok'}:
            raw = raw['data']
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except ValueError:
                    continue
        if isinstance(raw, dict):
            bodies.append(raw)
    if any(b.get('status') in {'denied', 'refused'} for b in bodies):
        return 'declined'
    if getattr(result, 'is_error', False) or status in {'failed', 'error'} or any(b.get('status') in {'failed', 'error'} or b.get('is_error') is True for b in bodies):
        return 'failed'
    return 'shown' if any(b.get('status') == 'rendered' for b in bodies) else 'unconfirmed'


def _why(exc):
    return ' '.join(str(exc).split())[:300].rstrip('.') or type(exc).__name__


def _load(source):
    if isinstance(source, dict):
        return source
    with open(source, encoding='utf-8') as handle:
        return json.load(handle)


def run_in_cowork():
    """Build the card, show it with exactly one render call, and return one small result."""
    from aether_tools import ToolDenied, ToolError, ToolRefused, args, set_result, tools
    given = args() or {}
    result = {'shown': False, 'options': [], 'recovery': ''}
    try:
        if given.get('report') is None:
            raise ReportError('args.report must be the path to the report data file')
        card, variant, model = build(_load(given['report']), compact=given.get('compact') is True)
    except Exception as exc:
        reason = 'the report data could not be used: ' if isinstance(exc, ReportError) else ''
        result['error'] = f'The card could not be built because {reason}{_why(exc)}.'
        try:
            result['options'], result['recovery'] = next_step(read_report(_load(given.get('report'))))
        except Exception:
            pass
        set_result(result)
        return
    result['options'], result['recovery'] = next_step(model)
    result['variant'] = variant
    try:
        reply = tools.core.render_ui(type=card['type'], version=card['version'], body=card['body'])
        outcome = _acknowledged(reply)
    except (ToolDenied, ToolRefused):
        raise    # the host's own decision; never retried or routed around
    except ToolError as exc:
        result['error'] = f'The card could not be shown because {_why(exc)}.'
        set_result(result)
        return
    except Exception:
        outcome = 'unconfirmed'
    if outcome == 'failed':
        result['error'] = 'The card could not be shown because the host rejected it.'
    elif outcome == 'declined':
        result['error'] = 'The card was not shown because the host declined it. Do not try again.'
    else:
        result['shown'] = True
        if outcome == 'unconfirmed':
            result['note'] = 'The host did not confirm the card. Do not send it again or repeat its data.'
    set_result(result)


RUN_COMMAND = ('copy scripts/card.py to .aether/scripts/card.py, then RunScript card.py with '
               'the arg report set to the path of the report data file')


def _help():
    lines = [
        'Noibu report card for Copilot Cowork',
        '',
        'In Cowork (shows the card):',
        f'  {RUN_COMMAND}',
        '  Optional arg "compact": true draws the compact card.',
        '  Returns {"shown", "variant", "options", "recovery"} and, on failure, "error":',
        '    options   the next-step question, in order: [{"label", "description"}]',
        '    recovery  the line to reply with if the question is skipped',
        '    error     one sentence saying why the card was not built or shown',
        '',
        'On the command line (builds only):',
        '  python card.py report.json [--compact] [--out card.json]',
        '  python card.py --example <skill>      print a complete report data file',
        '  python card.py --help',
        '',
        'Report data file (JSON). Supply values; the builder writes every label and format.',
        '  skill        one of: ' + ', '.join(SKILLS),
        '  store        {"name": "www.example.com", "id": "<Noibu domain UUID, optional>"}',
        '  window       {"start": "2026-10-03T00:00:00Z", "end": "2026-11-02T00:00:00Z"}; the previous',
        '               period is the same length, immediately before',
        '  currency     three-letter code, required when any money value is given; one currency per report',
        '  kpis         {key: value}, keys per skill below',
        '  funnel       {stage: value}, stages per skill below, as distinct session counts',
        '  tables       {table: [row, …]}, a row is an object keyed by column',
        '  priorities   ranked list, most affected first; the card draws 3, the question offers 5',
        '  tests        ab-testing only, in place of priorities: ranked list of tests; the card draws 5',
        '  noPrioritiesReason   one sentence, used only when priorities is empty',
        '  reportPages  ab-testing only: true when the tests\' report pages were published; the question then',
        '               starts with an option that opens the pages. For ab-testing the question offers',
        '               routes (view the reports, implement a test, another goal, a specific test), not tests',
        '  links        up to 2 console.noibu.com URLs returned by a Noibu tool',
        '',
        'Values',
        '  A kpi or funnel value is a number, null, or {"current": n, "prior": n}. The builder writes the',
        '  change from current and prior; never send a formatted change.',
        '  null means not measured and shows as "Not measured". Never send 0 for an unmeasured value.',
        '  Leave a key out to leave it off the card.',
        '  rate   a percentage: 54.2 means 54.2%        count  a whole number',
        '  money  an amount in the report currency       text   up to 40 characters in a table cell',
        '',
        'Priority fields (all skills)',
        '  title       names the metric and the move, 60 characters or fewer',
        '  shortTitle  5 words or fewer; the option label in the next-step question',
        '  evidence    one sentence with its number and comparison, 160 characters or fewer',
        '  affected    how many were affected (sessions; pageviews for accessibility-audit), or null',
        '  link        a console.noibu.com URL for this priority, optional',
    ]
    for skill, spec in SKILLS.items():
        lines += ['', skill]
        kpis = [(k, kind) for k, kind, _ in spec.get('context', [])] + [(t['key'], t['kind']) for t in spec.get('tiles', []) + spec.get('stats', [])] \
            + [(t['sub'], 'count') for t in spec.get('tiles', []) if t['sub']]
        if kpis:
            lines.append('  kpis      ' + ', '.join(f'{k} ({kind})' for k, kind in kpis))
        if spec.get('funnel'):
            lines.append('  funnel    ' + ', '.join(k for k, _ in spec['funnel']['stages']))
        for table in spec.get('tables', []):
            lines.append(f'  tables.{table["key"]}    ' + ', '.join(f'{c[0]} ({c[2]})' for c in table['columns']))
        if spec.get('signals'):
            lines.append('  priority  signal: ' + ' | '.join(spec['signals']))
        if skill == 'tech-diagnosis':
            lines += ['  priority  kind: ' + ' | '.join(KINDS) + '; status: ' + ' | '.join(s[0] for s in STATUSES.values()),
                      '            errorType, vendor, where (text); occurrences (count); lastSeen (timestamp)',
                      '            vital: {"metric": "LCP" | "INP" | "CLS", "value": p75 in ms (CLS as a score)}, required for kind performance']
        if skill == 'ab-testing':
            lines += ['  tests     title (the change in a few words, 60 characters or fewer); shortTitle (5 words or fewer)',
                      '            change (one sentence on the proposed change, 160 characters or fewer)',
                      '            why (the measured problem behind it, 240 characters or fewer)']
        if skill == 'accessibility-audit':
            lines.append('  priority  severity: ' + ' | '.join(SEVERITIES) + '; wcag (text); pages (count)')
    return '\n'.join(lines)


_STORE = {'name': 'www.example.com', 'id': '00000000-0000-4000-8000-000000000000'}
_MONTH = {'start': '2026-10-03T00:00:00Z', 'end': '2026-11-02T00:00:00Z'}
_ISSUES = 'https://console.noibu.com/00000000-0000-4000-8000-000000000000/issues'
EXAMPLES = {
    'checkout-analysis': {
        'skill': 'checkout-analysis', 'store': _STORE, 'window': _MONTH, 'currency': 'USD',
        'kpis': {'sessions': 53212, 'addedToCartRate': 43.0, 'checkoutCompletion': {'current': 54.0, 'prior': 57.5},
                 'mobileConversion': {'current': 1.4, 'prior': 1.9}, 'desktopConversion': {'current': 3.1, 'prior': 3.0},
                 'checkoutErrors': {'current': 212, 'prior': 140}, 'medianOrder': 82.4, 'discounted': 18.0, 'itemsPerOrder': 2.1},
        'funnel': {'addedToCart': {'current': 22866, 'prior': 21900}, 'startedCheckout': {'current': 9695, 'prior': 9800},
                   'paymentSubmitted': {'current': 5465, 'prior': 5900}, 'completedOrder': {'current': 5236, 'prior': 5640}},
        'tables': {'abandonment': [{'source': 'Dropped at payment step', 'sessions': 2140, 'cartValue': 176300},
                                   {'source': 'Left checkout without any action', 'sessions': 1310, 'cartValue': 98200},
                                   {'source': 'Experienced technical issues', 'sessions': 420, 'cartValue': None}],
                   'paymentMethods': [{'method': 'Shop Pay', 'orders': 2890}, {'method': 'Credit card', 'orders': 1630}, {'method': 'PayPal', 'orders': 716}],
                   'deliveryMethods': [{'method': 'Standard', 'orders': 4020}, {'method': 'Express', 'orders': 1216}]},
        'priorities': [
            {'title': 'Checkout completion fell on mobile', 'shortTitle': 'Mobile checkout completion drop', 'affected': 4200,
             'evidence': 'Mobile completion dropped to 1.4% from 1.9% against the previous 30 days.'},
            {'title': 'Payment submission fell after checkout start', 'shortTitle': 'Payment submission drop', 'affected': 1900,
             'evidence': 'Payment was submitted in 23.9% of cart sessions, down from 26.9%.'},
            {'title': 'Card form error blocks payment on Safari', 'shortTitle': 'Safari card form error', 'affected': 610,
             'evidence': 'The error fired 212 times and was last seen on the payment step.', 'link': _ISSUES + '/11111111-1111-4111-8111-111111111111'}],
        'links': [_ISSUES],
    },
    'product-analysis': {
        'skill': 'product-analysis', 'store': _STORE, 'window': _MONTH, 'currency': 'USD',
        'kpis': {'sessions': 53212, 'conversionRate': 2.4, 'medianOrder': 82.4},
        'funnel': {'viewedProduct': 38100, 'addedToCart': 9200, 'completedOrder': 1290},
        'tables': {'products': [{'name': 'Cable flex bracelet', 'sessions': 5200, 'addToCartRate': 2.1, 'conversionRate': 0.6},
                                {'name': 'Pearl drop earrings', 'sessions': 4100, 'addToCartRate': 7.9, 'conversionRate': 2.8}],
                   'collections': [{'name': 'Bracelets', 'sessions': 9100, 'conversionRate': 1.9, 'revenuePerSession': 1.42},
                                   {'name': 'Earrings', 'sessions': 7400, 'conversionRate': 3.1, 'revenuePerSession': 2.2}],
                   'productTypes': [{'name': 'Jewelry', 'sessions': 21000, 'conversionRate': 2.6, 'revenuePerSession': 1.9}]},
        'priorities': [
            {'signal': 'Low add-to-cart rate', 'title': 'Cable flex bracelet', 'affected': 5200,
             'evidence': 'It adds to cart at 2.1% against 6.1% across the store on 5,200 product views.'},
            {'signal': 'Low collection conversion', 'title': 'Bracelets', 'affected': 9100,
             'evidence': 'The collection converts at 1.9% against 2.4% site wide.'}],
    },
    'segment-analysis': {
        'skill': 'segment-analysis', 'store': _STORE, 'window': _MONTH, 'currency': 'USD',
        'kpis': {'siteWideConversion': 2.4, 'siteWideSessions': 53212, 'mobileConversion': 1.4, 'mobileSessions': 36100,
                 'desktopConversion': 3.1, 'desktopSessions': 17112},
        'tables': {'countries': [{'country': 'US', 'sessions': 39000, 'conversionRate': 2.7, 'revenuePerSession': 2.1},
                                 {'country': 'CA', 'sessions': 6100, 'conversionRate': 1.8, 'revenuePerSession': 1.3}],
                   'bestChannels': [{'channel': 'Klaviyo Email', 'sessions': 2000, 'conversionRate': 5.2, 'revenuePerSession': 4.4},
                                    {'channel': 'Google Ads', 'sessions': 12000, 'conversionRate': 2.9, 'revenuePerSession': 2.3}],
                   'mostVisitedChannels': [{'channel': 'Google Ads', 'sessions': 12000, 'conversionRate': 2.9, 'revenuePerSession': 2.3}]},
        'priorities': [
            {'signal': 'Device gap', 'title': 'Mobile', 'affected': 36100,
             'evidence': 'Mobile converts at 1.4% against 3.1% on desktop across 36,100 sessions.'},
            {'signal': 'Campaign drag', 'title': 'Facebook Ads', 'affected': 8300,
             'evidence': 'Facebook Ads converts at 0.4% against 2.4% site wide.'},
            {'signal': 'Localization gap', 'title': 'Canada', 'affected': 6100,
             'evidence': 'Canada converts at 1.8% against 2.7% in the United States.'}],
    },
    'store-pulse': {
        'skill': 'store-pulse', 'store': _STORE, 'window': {'start': '2026-11-01T21:00:00Z', 'end': '2026-11-02T21:00:00Z'}, 'currency': 'USD',
        'kpis': {'sessions': {'current': 12400, 'prior': 11400}, 'engagement': {'current': 61.2, 'prior': 63.0},
                 'conversion': {'current': 0.25, 'prior': 0.29}, 'aov': {'current': 96.1, 'prior': 91.4}, 'rps': {'current': 0.24, 'prior': 0.27}},
        'funnel': {'enterStore': {'current': 12400, 'prior': 11400}, 'viewProduct': {'current': 6110, 'prior': 5900},
                   'addToCart': {'current': 520, 'prior': 500}, 'startCheckout': {'current': 190, 'prior': 205}, 'checkoutComplete': {'current': 31, 'prior': 33}},
        'priorities': [
            {'title': 'Conversion fell on more traffic', 'shortTitle': 'Conversion fell', 'affected': 12400,
             'evidence': 'Conversion was 0.25% against 0.29% in the previous 24 hours on 12,400 sessions.'},
            {'title': 'Fewer sessions started checkout', 'shortTitle': 'Checkout starts fell', 'affected': 520,
             'evidence': 'Checkout was started in 1.5% of sessions, down from 1.8%.'}],
    },
    'tech-diagnosis': {
        'skill': 'tech-diagnosis', 'store': _STORE, 'window': _MONTH,
        'priorities': [
            {'kind': 'fixable', 'status': 'Active', 'title': 'Add to cart fails on product pages', 'shortTitle': 'Add to cart failure', 'affected': 610,
             'evidence': 'A script error stops the add-to-cart button responding on product pages.', 'errorType': 'JavaScript error',
             'occurrences': 1840, 'lastSeen': '2026-11-01T17:44:00Z', 'where': 'Product pages · Safari on iOS', 'link': _ISSUES + '/11111111-1111-4111-8111-111111111111'},
            {'kind': 'performance', 'status': 'Active', 'title': 'Collection pages load slowly on mobile', 'shortTitle': 'Slow collection pages', 'affected': 12000,
             'evidence': 'The largest element takes 4.2 seconds to appear for three in four visits.', 'vital': {'metric': 'LCP', 'value': 4200}, 'where': 'Collection pages · mobile'},
            {'kind': 'vendor', 'title': 'Reviews app fails to load', 'shortTitle': 'Reviews app error', 'affected': 240,
             'evidence': 'The reviews app returns an error on product pages.', 'vendor': 'Reviews app', 'errorType': 'HTTP error', 'occurrences': 310}],
        'links': [_ISSUES],
    },
    'ab-testing': {
        'skill': 'ab-testing', 'store': _STORE, 'window': _MONTH, 'reportPages': True,
        'tests': [
            {'title': 'Quick add on collection cards', 'shortTitle': 'Quick add on cards',
             'change': 'Add an Add to cart button to each product card on collection pages.',
             'why': 'Collection pages reach 29% of sessions, but only 5.8% of those sessions add to cart, against 11.2% for sessions that open a product page.'},
            {'title': 'Shipping reassurance in the cart drawer', 'shortTitle': 'Cart shipping reassurance',
             'change': 'Show the free-shipping threshold and delivery estimate above the checkout button in the cart drawer.',
             'why': '42% of sessions that open the cart leave without starting checkout, and the shipping cost first appears on the shipping step.'}],
    },
    'accessibility-audit': {
        'skill': 'accessibility-audit', 'store': _STORE, 'window': _MONTH,
        'kpis': {'pagesScanned': 10, 'pageviews': 95120, 'violationInstances': 271, 'uniqueFixes': 27, 'critical': 0, 'serious': 24, 'moderate': 2, 'minor': 1},
        'tables': {'pagesScanned': [{'page': 'Homepage', 'pageviews': 31200, 'instances': 42}, {'page': 'Bracelets collection', 'pageviews': 12800, 'instances': 37}],
                   'keyFindings': [{'finding': 'Text contrast is too low', 'wcag': '1.4.3 Contrast (Minimum)', 'severity': 'Serious'},
                                   {'finding': 'Images are missing alt text', 'wcag': '1.1.1 Non-text Content', 'severity': 'Serious'}]},
        'priorities': [
            {'severity': 'serious', 'title': 'Text contrast is too low', 'shortTitle': 'Low text contrast', 'affected': 95120,
             'evidence': 'Body text fails the 4.5:1 contrast ratio on all 10 scanned pages.', 'wcag': '1.4.3 Contrast (Minimum)', 'pages': 10},
            {'severity': 'serious', 'title': 'Images are missing alt text', 'shortTitle': 'Missing alt text', 'affected': 44000,
             'evidence': 'Product images have no text alternative on 4 scanned pages.', 'wcag': '1.1.1 Non-text Content', 'pages': 4}],
    },
}


def run_command_line(argv):
    if not argv or argv[0] in {'-h', '--help'}:
        print(_help())
        return 0
    if argv[0] == '--example':
        if len(argv) != 2 or argv[1] not in EXAMPLES:
            print('--example takes one of: ' + ', '.join(EXAMPLES), file=sys.stderr)
            return 2
        print(json.dumps(EXAMPLES[argv[1]], indent=1, ensure_ascii=False))
        return 0
    compact, out, source, rest = False, None, None, list(argv)
    while rest:
        arg = rest.pop(0)
        if arg == '--compact':
            compact = True
        elif arg == '--out' and rest:
            out = rest.pop(0)
        elif not arg.startswith('-') and source is None:
            source = arg
        else:
            print('usage: python card.py report.json [--compact] [--out card.json]', file=sys.stderr)
            return 2
    if source is None:
        print('usage: python card.py report.json [--compact] [--out card.json]', file=sys.stderr)
        return 2
    try:
        card, variant, model = build(_load(source), compact=compact)
    except Exception as exc:
        reason = 'the report data could not be used: ' if isinstance(exc, ReportError) else ''
        print(json.dumps({'built': False, 'error': f'The card could not be built because {reason}{_why(exc)}.'}, ensure_ascii=False))
        return 1
    if out:
        with open(out, 'w', encoding='utf-8') as handle:
            json.dump(card, handle, ensure_ascii=False, indent=1)
    options, recovery = next_step(model)
    print(json.dumps({'built': True, 'variant': variant, 'bytes': card_bytes(card), 'options': options, 'recovery': recovery}, ensure_ascii=False, indent=1))
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
