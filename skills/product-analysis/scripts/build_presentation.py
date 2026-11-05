"""Build safe Noibu boards for Microsoft 365 Copilot Cowork (widget fragment) or standalone snapshots; no network or writes."""
import argparse
import hashlib
import html
import importlib.util
import json
import math
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

HERE = Path(__file__).resolve().parent.parent
WORKFLOWS = {'store-pulse', 'checkout-analysis', 'product-analysis', 'segment-analysis', 'tech-diagnosis', 'accessibility-audit', 'ab-testing', 'ab-test-opportunity-finder', 'build-business-context', 'querying-noibu-data', 'noibu-setup'}
# 21.1.14: the A/B skill is `ab-testing`; the 21.1.x id stays accepted for older reports, schedules and handoffs.
AB_WORKFLOWS = {'ab-testing', 'ab-test-opportunity-finder'}
ANALYTICS = {'store-pulse', 'checkout-analysis', 'product-analysis', 'segment-analysis'}
SCHEDULABLE = WORKFLOWS - {'noibu-setup', 'build-business-context', 'querying-noibu-data'}
FIELDS = {'host', 'schema', 'reportId', 'workflow', 'domain', 'window', 'generatedAt', 'summary', 'overviewContext', 'overviewNotes', 'kpis', 'funnel', 'funnelContext', 'highlights', 'tables', 'findings', 'caveats', 'timezone', 'capabilities', 'contextHash', 'noibuLinks', 'auditLayout', 'comparison', 'checkout', 'segments', 'funnelBasis', 'abView'}
TONES = {None, 'favorable', 'unfavorable', 'neutral'}
HOSTS = {'cowork', 'copilot-chat'}
# Copilot Chat agents can't run Cowork apps, scheduled prompts or third-party ticket/PR connectors,
# so their boards offer only actions the agent can complete.
CHAT_LABELS = {'Open a Ticket': 'Draft a ticket', 'Prepare draft PR': 'Draft a patch', 'Auto-draft PR': 'Draft patches', 'Auto-create tickets': 'Draft tickets'}
VITALS = {'INP': (200, 500, 'ms'), 'LCP': (2500, 4000, 'ms'), 'CLS': (0.1, 0.25, 'score')}
CSS_BLOCK = re.compile(r'/\*NOIBU-CSS-BEGIN\*/\n(.*?)/\*NOIBU-CSS-END\*/\n', re.S)


def load_assets():
    """Return (board template, stylesheet, controller). The stylesheet lives inside board.html
    because Microsoft 365 Copilot rejects .css skill files."""
    source = (HERE / 'assets/board.html').read_text()
    match = CSS_BLOCK.search(source)
    if not match:
        raise ValueError('Board template is missing its embedded stylesheet')
    return source.replace(match.group(0), '    {{STYLE}}\n', 1), match.group(1), (HERE / 'assets/presentation.js').read_text()


link_spec = importlib.util.spec_from_file_location('noibu_console_links', Path(__file__).with_name('console_links.py'))
links = importlib.util.module_from_spec(link_spec)
link_spec.loader.exec_module(links)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def text(value, maximum=12000):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum

def timestamp(value):
    require(text(value), 'Missing timestamp')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp needs timezone')
    return result

def safe_json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

def escape(value):
    return html.escape(str(value if value is not None else 'Not measured'), quote=True)

def validate_change(item):
    require(item.get('tone') in TONES and ('change' not in item or text(item['change'])), 'Invalid metric change')
    require('changeDirection' not in item or isinstance(item['changeDirection'], str) and item['changeDirection'] in {'up', 'down', 'flat'} and bool(item.get('change')), 'Direction requires a measured change')

def render_change(item):
    if not item.get('change'):
        return ''
    # Direction is explicit evidence metadata, never inferred from formatted prose.
    tone = 'decline' if item.get('changeDirection') == 'down' else item.get('tone') or 'neutral'
    return f'<span class="noibu-delta noibu-{tone}">{escape(item["change"])}</span>'

def validate_links(items, domain_id):
    require(isinstance(items, list) and len(items) <= 8, 'Invalid Noibu links')
    for item in items:
        require(isinstance(item, dict) and set(item) == {'label', 'url', 'source'} and text(item['label'], 100) and text(item['source'], 500), 'Link needs label, URL and evidence source')
        require(domain_id is not None, 'Console links need a resolved domain UUID')
        links.validate_url(item['url'], domain_id)

def validate_performance(value):
    require(isinstance(value, dict) and set(value) <= {'metric', 'value', 'unit', 'percentile', 'page', 'pageGroup', 'device', 'traffic', 'status'}, 'Invalid performance fields')
    require(value.get('metric') in VITALS, 'Unsupported performance metric')
    require(value.get('unit') == VITALS[value['metric']][2] and value.get('percentile') == 'p75', 'Performance cards require p75 and normalized units')
    measured = value.get('value')
    require(measured is None or type(measured) in {int, float} and math.isfinite(measured) and measured >= 0, 'Invalid performance value')
    require(all(key not in value or text(value[key], 1000) for key in ['page', 'pageGroup', 'device', 'status']), 'Invalid performance context')
    if 'traffic' in value:
        traffic = value['traffic']
        require(isinstance(traffic, dict) and set(traffic) == {'count', 'unit'} and traffic['unit'] in {'pageviews', 'visits', 'sessions', 'samples'}, 'Traffic needs its actual population unit')
        require(traffic['count'] is None or type(traffic['count']) is int and traffic['count'] >= 0, 'Invalid performance traffic')

DEFAULT_COMPARISON_FOOTER = 'Snapshot only; comparison scope not supplied'


def _comparison(data):
    value = data.get('comparison') or {}
    return value.get('label') or DEFAULT_COMPARISON_FOOTER


# Checkout has a fixed semantic contract, not a label-substring heuristic. These
# roles may be supplied for localized labels; recognized English labels must agree.
CHECKOUT_ROLES = ('added-to-cart', 'checkout-started', 'payment-submitted', 'order-completed')
CHECKOUT_LABELS = dict(zip(('added to cart', 'started checkout', 'payment submitted', 'completed order'), CHECKOUT_ROLES))


def _pp_change(current, prior):
    delta = round(current - prior, 1)
    return {'change': f'{delta:+.1f} pp', 'changeDirection': 'up' if delta > 0 else 'down' if delta < 0 else 'flat', 'tone': 'favorable' if delta > 0 else 'unfavorable' if delta < 0 else 'neutral'}


def _checkout_rates(data):
    """Only verified raw distinct-session counts determine checkout values/geometry.
    Recompute on every validation, including an already prepared report: never trust
    model-provided display, rate, priorRate, change, direction or denominator metadata.
    Unknown is not zero; missing/zero cart bases cannot produce any stage rate.
    """
    stages = data.get('funnel', [])
    require(isinstance(stages, list), 'Invalid checkout funnel')
    resolved = []
    for stage in stages:
        require(isinstance(stage, dict) and text(stage.get('label')) and 'count' in stage, 'Invalid checkout stage')
        require(all(stage.get(k) is None or type(stage[k]) is int and stage[k] >= 0 for k in ('count', 'prior')), 'Stage counts must be nonnegative integers or null')
        named = CHECKOUT_LABELS.get(' '.join(stage['label'].lower().split()))
        role = stage.get('role', named)
        require(role is None or role in CHECKOUT_ROLES, 'Unsupported checkout stage role')
        require(named is None or role == named, 'Checkout label and role disagree')
        resolved.append(role)
    known = [CHECKOUT_ROLES.index(r) for r in resolved if r is not None]
    require(known == sorted(set(known)), 'Checkout stages must be unique and in cart / checkout / payment / order semantic order')
    require('added-to-cart' not in resolved or resolved[0] == 'added-to-cart', 'Checkout cart baseline must be the first stage')
    cart = stages[0] if stages and resolved[0] == 'added-to-cart' else None
    bases = {k: cart.get(k) if cart else None for k in ('count', 'prior')}
    def coverage(k):
        return 'unidentified cart stage' if cart is None else 'not measured' if bases[k] is None else 'zero cart baseline' if bases[k] == 0 else 'measured'
    for stage, role in zip(stages, resolved):
        for key in ('display', 'change', 'changeDirection', 'tone', 'rate', 'priorRate'):
            stage.pop(key, None)
        # Preserve original raw count/prior fields; a role is never guessed from a substring.
        if role is not None:
            stage['role'] = role
        for key, out in (('count', 'rate'), ('prior', 'priorRate')):
            stage[out] = 100 * stage[key] / bases[key] if role is not None and stage.get(key) is not None and bases[key] is not None and bases[key] > 0 else None
        if stage['count'] is not None:
            stage['display'] = format(stage['count'], ',') if role == 'added-to-cart' else f"{stage['rate']:.1f}%" if stage['rate'] is not None else 'Not measured'
        if role != 'added-to-cart' and stage['rate'] is not None and stage['priorRate'] is not None:
            stage.update(_pp_change(stage['rate'], stage['priorRate']))
    def base_text(k):
        return f"{bases[k]:,} = 100%" if coverage(k) == 'measured' else f"{coverage(k)}; rates Not measured"
    note = 'Bars and later-stage rates: % of sessions that added to cart. Current base ' + base_text('count') + '; prior base ' + base_text('prior') + '. Each period uses its own cart base.'
    if any(role is None for role in resolved):
        note += ' Unidentified stage roles: rates Not measured; exact counts retained.'
    if any(s['count'] is None for s in stages):
        note += ' Missing current stage counts: Not measured, not zero.'
    if any(s.get('prior') is None for s in stages):
        note += ' Missing prior stage counts: no comparison for those stages.'
    if any((s[k] or 0) > 100 for s in stages for k in ('rate', 'priorRate')):
        note += ' Rates above 100% retained: verify cohort/instrumentation coverage; not clamped.'
    data['funnelBasis'] = {'kind': 'added-to-cart-sessions', 'current': bases['count'], 'prior': bases['prior'], 'currentCoverage': coverage('count'), 'priorCoverage': coverage('prior'), 'stageOrder': resolved, 'note': note}
    # Checkout completion is a DIFFERENT denominator: completed / started checkout.
    by_role = {r: s for r, s in zip(resolved, stages) if r is not None}
    started, completed = by_role.get('checkout-started'), by_role.get('order-completed')
    def completion(k):
        return 100 * completed[k] / started[k] if started and completed and started.get(k) is not None and started[k] > 0 and completed.get(k) is not None else None
    current, prior = completion('count'), completion('prior')
    metric = {'label': 'Checkout completion', 'value': f'{current:.1f}%' if current is not None else 'Not measured', 'detail': 'Completed / started checkout sessions; separate from cart-based funnel rates.'}
    if current is not None:
        metric['detail'] += f" Current {completed['count']:,} / {started['count']:,}."
    if prior is not None:
        metric['detail'] += f" Prior {completed['prior']:,} / {started['prior']:,} = {prior:.1f}%."
    if current is not None and prior is not None:
        metric.update(_pp_change(current, prior))
    elif prior is None:
        metric['detail'] += ' Prior completion not measured; no comparison.'
    found = False
    for field in ('kpis', 'highlights'):
        for item in data.get(field, []):
            if str(item.get('label', '')).lower() in {'checkout completion', 'checkout completion rate'}:
                for key in ('value', 'detail', 'change', 'changeDirection', 'tone'):
                    item.pop(key, None)
                item.update({k: v for k, v in metric.items() if k != 'label'})
                found = True
    # Do not overflow the six-highlight/eight-KPI contract or drop any caller metric.
    # When no existing completion metric exists, render it separately in the funnel.
    data['funnelBasis']['checkoutCompletion'] = metric
    data['funnelBasis']['completionInMetrics'] = found


def prepare_report(data):
    """Map verified normalized aggregates, not tool-specific guesses, into every renderer path.
    Source rows are retained in the caller's evidence file; previews are ranked here, not underfetched.
    """
    data = json.loads(safe_json(data))
    if data.get('workflow') == 'checkout-analysis':
        _checkout_rates(data)
    else:
        require('funnelBasis' not in data, 'Cart denominator metadata belongs to checkout only')
    caveats = data.setdefault('caveats', [])
    tables = data.setdefault('tables', [])
    if data.get('checkout') is not None:
        c = data.pop('checkout')
        require(not any(t.get('kind') == 'bars' and any(k in t.get('title', '').lower() for k in ('payment', 'delivery')) for t in tables), 'Ambiguous legacy and normalized checkout method tables')
        require(data['workflow'] == 'checkout-analysis' and isinstance(c, dict) and set(c) <= {'mixes', 'missing'}, 'Invalid checkout mapping')
        for kind, mix in c.get('mixes', {}).items():
            require(kind in {'payment', 'delivery'} and isinstance(mix, dict) and set(mix) == {'rows', 'population', 'coveredCount', 'completedCount', 'currencyScope', 'overlap'}, 'Invalid completed-order mix')
            require(mix['population'] in {'completed-orders', 'completed-purchasing-sessions'}, 'Mix requires completed population')
            require(type(mix['overlap']) is bool and text(mix['currencyScope']), 'Mix needs overlap and currency coverage')
            require(all(type(mix[k]) is int and mix[k] >= 0 for k in ('coveredCount', 'completedCount')) and mix['coveredCount'] <= mix['completedCount'], 'Invalid mix coverage')
            require(isinstance(mix['rows'], list) and len(mix['rows']) <= 50, 'Invalid mix rows')
            for row in mix['rows']:
                require(isinstance(row, dict) and set(row) == {'label', 'count'} and text(row['label']) and type(row['count']) is int and row['count'] >= 0, 'Invalid mix count')
            require(all(r['count'] <= mix['coveredCount'] for r in mix['rows']), 'Mix method count exceeds covered population')
            require(mix['overlap'] or sum(r['count'] for r in mix['rows']) <= mix['coveredCount'], 'Nonoverlapping method counts exceed covered population; reconcile evidence')
            unit = 'orders' if mix['population'] == 'completed-orders' else 'purchasing sessions (order grain unavailable)'
            note = f"Completed {unit} only; field coverage {mix['coveredCount']:,}/{mix['completedCount']:,}; {mix['currencyScope']}; " + ('multi-method overlap: counts not additive' if mix['overlap'] else 'one method per measured population member')
            if not mix['overlap'] and sum(r['count'] for r in mix['rows']) < mix['coveredCount']:
                note += f"; returned categories cover {sum(r['count'] for r in mix['rows']):,}/{mix['coveredCount']:,} populated members; bounded method roster"
            tables.append({'title': kind.title() + ' methods', 'columns': ['Method', 'Completed ' + unit], 'rows': [[r['label'], r['count']] for r in sorted(mix['rows'], key=lambda r: -r['count'])], 'kind': 'bars', 'placement': 'overview', 'note': note})
        for missing in c.get('missing', []):
            require(text(missing), 'Invalid missing mix coverage')
            caveats.append(missing)
    if data.get('segments') is not None:
        seg = data.pop('segments')
        require(all(t.get('placement') == 'supporting' for t in tables), 'Ambiguous legacy overview and normalized segment tables; use supporting for unrelated history')
        require(data['workflow'] == 'segment-analysis' and isinstance(seg, dict) and set(seg) == {'countries', 'channels', 'minSessions', 'countryScope', 'channelScope', 'currencyScope'}, 'Invalid segment mapping')
        require(type(seg['minSessions']) is int and seg['minSessions'] > 0 and text(seg['currencyScope']), 'Invalid segment threshold/currency')
        require(all(seg[k] in {'global-complete', 'bounded'} for k in ('countryScope', 'channelScope')), 'Missing ranking scope')
        def checked(rows):
            require(isinstance(rows, list), 'Invalid aggregate rows')
            for r in rows:
                require(isinstance(r, dict) and set(r) <= {'label', 'sessions', 'purchasingSessions', 'revenuePerSession'} and text(r.get('label')), 'Invalid segment row')
                require(type(r.get('sessions')) is int and type(r.get('purchasingSessions')) is int and 0 <= r['purchasingSessions'] <= r['sessions'], 'Invalid segment population')
                require(r.get('revenuePerSession') is None or text(r['revenuePerSession']), 'Revenue per session requires measured currency display or null')
            return rows
        countries, channels = checked(seg['countries']), checked(seg['channels'])
        unknown = [r for r in countries if r['label'].strip().lower() in {'unknown', '(unknown)', '(none)', 'none', 'null', 'unattributed', '(unattributed)', 'zz', 'xx', '--', '-'}]
        known = [r for r in countries if r not in unknown]
        def rows(group):
            return [[r['label'], r['sessions'], f"{100*r['purchasingSessions']/r['sessions']:.2f}%" if r['sessions'] else 'Not measured', r.get('revenuePerSession')] for r in group[:5]]
        country = sorted(known, key=lambda r: (-r['sessions'], r['label']))
        best = sorted([r for r in channels if r['sessions'] >= seg['minSessions']], key=lambda r: (-r['purchasingSessions']/r['sessions'], -r['sessions'], r['label']))
        visited = sorted(channels, key=lambda r: (-r['sessions'], r['label']))
        for title, group, scope in [('Countries / regions', country, seg['countryScope']), (f"Best converting channels ({seg['minSessions']:,}+ sessions)", best, seg['channelScope']), ('Most visited channels', visited, seg['channelScope'])]:
            bounds = 'global complete aggregate' if scope == 'global-complete' else 'bounded returned aggregate; not a global ranking'
            note = f"Top {min(5,len(group))} supported rows; {bounds}; {seg['currencyScope']}"
            if not group:
                caveats.append(title + ': no supported rows; ' + note)
                continue
            if len(group) < 5:
                note += f'; only {len(group)} eligible known/qualified rows available'
            tables.append({'title': title, 'columns': ['Country / region' if group is country else 'Channel', 'Sessions', 'CVR', 'Rev/session'], 'rows': rows(group), 'placement': 'overview', 'numericColumns': [1, 2, 3], 'note': note})
        if unknown:
            caveats.append('Unknown country separate: ' + f"{sum(r['sessions'] for r in unknown):,} sessions in returned aggregate; not a substitute for known regions.")
        caveats.append('UTM source/medium labels remain distinct; unattributed does not prove Direct or broken tracking. Currency components are not pooled.')
    return data


def validate(data):
    require(isinstance(data, dict) and set(data) <= FIELDS, 'Unsupported presentation fields')
    data = prepare_report(data)
    require(data.get('schema') == 'noibu.presentation/1', 'Unsupported presentation schema')
    require(data.get('workflow') in WORKFLOWS, 'Unsupported workflow')
    require(data.get('host', 'cowork') in HOSTS, 'Unsupported host')
    require('auditLayout' not in data or data['workflow'] == 'accessibility-audit' and data['auditLayout'] in {'summary-actions', 'detailed'}, 'Invalid audit layout')
    ab_view_pending = 'abView' in data
    require(text(data.get('reportId'), 100) and re.fullmatch(r'[a-z0-9][a-z0-9-]*', data['reportId']), 'Invalid report identity')
    domain = data.get('domain', {})
    require(isinstance(domain, dict) and set(domain) <= {'name', 'id'}, 'Invalid domain fields')
    require(text(domain.get('name'), 253) and re.fullmatch(r'[a-zA-Z0-9.-]+', domain['name']), 'Invalid domain name')
    if domain.get('id'):
        UUID(domain['id'])
    timestamp(data.get('generatedAt'))
    if ab_view_pending:
        _validate_ab_view(data, domain)
    window = data.get('window', {})
    require(isinstance(window, dict) and set(window) <= {'start', 'end', 'label'}, 'Invalid window')
    require(timestamp(window.get('start')) < timestamp(window.get('end')), 'Invalid time range')
    require(text(data.get('summary')), 'Missing summary')
    require('overviewContext' not in data or text(data['overviewContext'], 1000), 'Invalid overview context')
    require('overviewNotes' not in data or data['workflow'] == 'segment-analysis' and isinstance(data['overviewNotes'], list) and len(data['overviewNotes']) <= 3 and all(text(note, 1000) for note in data['overviewNotes']), 'Invalid overview notes')
    require(isinstance(data.get('capabilities', {}), dict), 'Invalid capabilities')
    allowed_caps = {'createDraft', 'ignoreIssue', 'draftPr', 'createTicket', 'persistContext'}
    require(set(data.get('capabilities', {})) <= allowed_caps and all(type(x) is bool for x in data.get('capabilities', {}).values()), 'Unknown capability')
    for field, maximum in [('kpis', 8), ('funnel', 12), ('highlights', 6), ('tables', 8), ('findings', 12), ('caveats', 12)]:
        require(isinstance(data.get(field, []), list) and len(data.get(field, [])) <= maximum, f'Invalid {field}')
    for kpi in data.get('kpis', []):
        require(isinstance(kpi, dict) and set(kpi) <= {'label', 'value', 'detail', 'change', 'tone', 'changeDirection'} and text(kpi.get('label')) and text(kpi.get('value')), 'Invalid KPI')
        require('detail' not in kpi or text(kpi['detail']), 'Invalid KPI detail')
        validate_change(kpi)
    for item in data.get('highlights', []):
        require(isinstance(item, dict) and set(item) <= {'label', 'value', 'detail', 'change', 'tone', 'changeDirection'} and text(item.get('label')) and text(item.get('value')), 'Invalid highlight')
        require('detail' not in item or text(item['detail']), 'Invalid highlight detail')
        validate_change(item)
    require('funnelContext' not in data or text(data['funnelContext']), 'Invalid funnel context')
    for stage in data.get('funnel', []):
        require(isinstance(stage, dict) and set(stage) <= ({'label', 'count', 'prior', 'display', 'detail', 'change', 'tone', 'changeDirection'} | ({'role', 'rate', 'priorRate'} if data['workflow'] == 'checkout-analysis' else set())) and text(stage.get('label')) and 'count' in stage, 'Invalid stage')
        validate_change(stage)
        require('changeDirection' not in stage or stage['count'] is not None, 'Unmeasured stage cannot have a change direction')
        require(all(key not in stage or text(stage[key]) for key in ['display', 'detail', 'change']), 'Invalid stage annotation')
        require(stage['count'] is not None or 'display' not in stage, 'Unmeasured stage cannot have a measured display')
        for key in ['count', 'prior']:
            value = stage.get(key)
            require(value is None or (type(value) is int and value >= 0), 'Stage counts must be nonnegative integers or null')
    for table in data.get('tables', []):
        require(isinstance(table, dict) and {'title', 'columns', 'rows'} <= set(table) <= {'title', 'columns', 'rows', 'kind', 'note', 'numericColumns', 'placement', 'barColumn'} and text(table['title']), 'Invalid table')
        require(table.get('placement') in {None, 'overview', 'supporting'}, 'Invalid table placement')
        require(table.get('kind') in {None, 'table', 'bars'}, 'Invalid table kind')
        require('note' not in table or text(table['note']), 'Invalid table note')
        require(isinstance(table['columns'], list) and 0 < len(table['columns']) <= 8 and all(text(x) for x in table['columns']), 'Invalid columns')
        require(isinstance(table['rows'], list) and len(table['rows']) <= 50, 'Table row cap exceeded')
        for row in table['rows']:
            require(isinstance(row, list) and len(row) == len(table['columns']), 'Table width mismatch')
            require(all(x is None or isinstance(x, (str, int, float)) and not isinstance(x, bool) for x in row), 'Invalid table cell')
        require(isinstance(table.get('numericColumns', []), list) and all(type(i) is int and 0 <= i < len(table['columns']) for i in table.get('numericColumns', [])), 'Invalid numeric columns')
        if 'barColumn' in table:
            col = table['barColumn']
            require(table.get('kind') != 'bars' and type(col) is int and 0 < col < len(table['columns']), 'Invalid table bar column')
            require(all(row[col] is None or type(row[col]) is int and row[col] >= 0 for row in table['rows']), 'Table bars require normalized integer counts or null')
        if table.get('kind') == 'bars':
            require(len(table['columns']) == 2 and all(row[1] is None or type(row[1]) in {int, float} and math.isfinite(row[1]) and row[1] >= 0 for row in table['rows']), 'Bars require label and nonnegative numeric value columns')
    seen = set()
    for finding in data.get('findings', []):
        require(isinstance(finding, dict) and set(finding) <= {'id', 'title', 'evidence', 'impact', 'fix', 'issueId', 'category', 'tag', 'performance', 'noibuLinks', 'ownership', 'disposition', 'priorityJustification', 'errorRecency'}, 'Invalid finding fields')
        require(finding.get('ownership') in {None, 'merchant-code', 'merchant-content', 'vendor', 'unknown'}, 'Invalid finding ownership')
        require(all(key not in finding or text(finding[key]) for key in ['impact', 'fix', 'tag']), 'Invalid finding annotation')
        require(text(finding.get('id'), 100) and finding['id'] not in seen, 'Invalid/duplicate finding identity')
        seen.add(finding['id'])
        require(text(finding.get('title')) and text(finding.get('evidence')), 'Finding needs evidence')
        require(finding.get('category') in {None, 'merchant', 'performance', 'vendor', 'accessibility'}, 'Invalid finding category')
        if 'performance' in finding:
            # 21.1.15: the gauge is an OPTIONAL section. An incomplete one is dropped with a visible
            # plain-language note; the finding, its evidence and actions still render. No value is guessed.
            try:
                require(finding.get('category') == 'performance', 'Performance card needs performance category')
                validate_performance(finding['performance'])
            except (ValueError, TypeError, KeyError, AttributeError):
                why = 'this finding is not in the performance category' if finding.get('category') != 'performance' else 'the measurement was incomplete (a gauge needs the p75 LCP or INP in ms, or the p75 CLS score)'
                finding.pop('performance')
                finding['gaugeNote'] = 'Measurement gauge not shown because ' + why + '.'
        validate_links(finding.get('noibuLinks', []), domain.get('id'))
        require(finding.get('disposition') in {None, 'priority', 'monitor'}, 'Invalid finding disposition')
        require('priorityJustification' not in finding or text(finding['priorityJustification']), 'Invalid priority justification')
        if finding.get('errorRecency') is not None:
            er = finding['errorRecency']
            require(isinstance(er, dict) and set(er) == {'events', 'windowDays', 'lastSeenHours'} and type(er['events']) is int and er['events'] >= 0 and er['windowDays'] == 7 and type(er['lastSeenHours']) in {int, float} and er['lastSeenHours'] >= 0, 'Error recency needs seven-day events and actual last-seen hours')
    validate_links(data.get('noibuLinks', []), domain.get('id'))
    require(all(text(x) for x in data.get('caveats', [])), 'Invalid caveats')
    if data.get('contextHash'):
        require(re.fullmatch(r'[a-f0-9]{64}', data['contextHash']), 'Invalid context hash')
    _normalize_comparison(data)
    # Also rejects nonfinite evidence anywhere in the input.
    safe_json(data)
    return data

def action(data, kind, target=None):
    result = {'schema': 'noibu.presentation-action/1', 'kind': kind, 'workflow': data['workflow'], 'reportId': data['reportId'], 'domain': data['domain'], 'window': data['window'], 'generatedAt': data['generatedAt'], 'target': target or {}}
    finding = next((f for f in data.get('findings', []) if f['id'] == (target or {}).get('findingId')), None)
    technical = finding and (data['workflow'] in {'tech-diagnosis', 'accessibility-audit'} or finding.get('category') in {'merchant', 'performance', 'accessibility'})
    batch_ids = (target or {}).get('findingIds')
    if batch_ids is not None:
        require(data['workflow'] == 'accessibility-audit' and kind in {'draft-pr', 'create-ticket'} and isinstance(batch_ids, list) and 0 < len(batch_ids) <= 3 and len(set(batch_ids)) == len(batch_ids), 'Invalid audit batch action')
        require(all(any(f['id'] == identity for f in data.get('findings', [])) for identity in batch_ids), 'Unknown audit finding in batch')
        if kind == 'draft-pr':
            require(all(f.get('ownership') not in {'merchant-content', 'vendor'} and f.get('category') != 'vendor' for f in data.get('findings', []) if f['id'] in batch_ids), 'Batch PR includes a content/vendor handoff')
    if finding and finding.get('category') != 'vendor' and (kind in {'get-fix', 'draft-pr'} or kind == 'investigate' and technical) or batch_ids and kind == 'draft-pr':
        result['execution'] = {'route': 'repository-source', 'legacyRoute': 'github-source', 'providers': ['GitHub', 'Azure DevOps'], 'connection': 'discover-applicable-authenticated-accounts', 'selection': 'zero-ask-connect-one-reuse-multiple-ask', 'deduplicate': 'provider-and-account-not-surfaces', 'capabilities': 'repo-read-pr-ticket-pipeline-separate', 'repository': 'resolve-or-ask', 'mode': 'read-only'}
    elif kind == 'schedule':
        result['execution'] = {'route': 'cowork-scheduled-prompt', 'provider': 'discover-send-capability', 'destination': 'resolve-or-ask', 'completion': 'schedule-saved-or-specific-blocker', 'deliveryVerification': 'separate-from-schedule-creation', 'existing': 'match-including-paused', 'emailRecipientState': 'pending-chat-confirmation', 'emailGate': 'confirm-final-exact-addresses-even-if-supplied-before-schedule-or-send', 'defaultRecipient': None}
    elif kind == 'save-report' and data.get('host') == 'copilot-chat':
        result['execution'] = {'route': 'copilot-pages-handoff', 'completion': 'report-ready-user-opens-pages'}
    elif kind == 'save-report':
        result['execution'] = {'route': 'onedrive-document', 'completion': 'document-saved-or-specific-blocker', 'audience': 'owner-only'}
    elif kind == 'create-ticket' and data.get('host') == 'copilot-chat':
        result['execution'] = {'route': 'ticket-draft-only', 'completion': 'labelled-draft-not-created'}
    elif kind == 'create-ticket':
        result['execution'] = {'route': 'ticket-destination-first', 'chooser': 'chat-question', 'question': 'Where should the ticket go?', 'options': ['Linear', 'Jira', 'GitHub Issues', 'Notion'], 'connection': 'discover-after-selection', 'completion': 'verified-ticket-or-explicit-draft-or-specific-blocker'}
    return result

def candidate_data(data, candidates):
    if candidates is None:
        return []
    require(data['workflow'] in AB_WORKFLOWS, 'Candidates belong to experiment workflow')
    module_path = Path(__file__).with_name('validate_candidates.py')
    require(module_path.is_file(), 'A/B candidates need the local scripts/validate_candidates.py from this release; load the A/B skill and use its own runner')
    spec = importlib.util.spec_from_file_location('noibu_candidates', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_candidates(candidates)
    require(candidates['domain'] == data['domain']['name'] and candidates['domainId'] == data['domain'].get('id'), 'Candidate domain mismatch')
    require(candidates['window']['start'] == data['window']['start'] and candidates['window']['end'] == data['window']['end'], 'Candidate window mismatch')
    result = []
    for item in candidates['tests']:
        digest = hashlib.sha256(json.dumps(item['createInput'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        result.append({'rank': item['rank'], 'title': item['title'], 'what': item['what'], 'hypothesis': item['hypothesis'], 'validation': item['validation']['status'], 'metric': item['createInput']['successMetric']['metric'], 'hash': digest, 'evidence': item['evidence'], 'variations': item['createInput']['variations'], 'guardrails': item['createInput'].get('secondaryMetrics', []), 'devices': item['createInput'].get('deviceTypes', []), 'utm': item['createInput'].get('utmConditions', [])})
        # ab-candidates/3 only: the finder's report fields, verbatim (absent on /2).
        result[-1]['report'] = {k: item[k] for k in ('why', 'surface', 'setup', 'metricVolume', 'overlap', 'fixFirst', 'consoleFollowUps', 'reportFile', 'variationName', 'origin') if item.get(k) is not None}
        result[-1]['report']['handoffVariations'] = item.get('variations', [])
        result[-1]['report']['browser'] = candidates.get('browser')
        result[-1]['report']['candidateTotal'] = len(candidates['tests'])
        result[-1]['report']['outsideGoal'] = candidates.get('outsideGoal', [])
        result[-1]['report']['runCaveats'] = candidates.get('caveats', [])
        result[-1]['report']['goal'] = candidates.get('goal')
    return result

def render_funnel(data):
    """One shared linear count scale; connectors may rise for express checkout."""
    if data['workflow'] == 'checkout-analysis':
        return _render_checkout_funnel(data)
    stages = data.get('funnel', [])
    if not stages:
        return ''
    maximum = max([s.get(k) or 0 for s in stages for k in ['count', 'prior']] + [1])
    width, height = 1000, 220
    step = width / len(stages)
    bar = step * .56
    marks, labels, mobile = [], [], []
    prior_present = any(s.get('prior') is not None for s in stages)
    for n, stage in enumerate(stages):
        count, x = stage['count'], n * step
        y = height - height * (count or 0) / maximum
        if n + 1 < len(stages) and count is not None and stages[n + 1]['count'] is not None:
            next_y = height - height * stages[n + 1]['count'] / maximum
            marks.append(f'<path class="noibu-funnel-link" d="M{x + bar:.3f},{y:.3f} L{x + step:.3f},{next_y:.3f} V{height} H{x + bar:.3f} Z"/>')
        if stage.get('prior') is not None:
            h = height * stage['prior'] / maximum
            marks.append(f'<rect class="noibu-prior-mark" x="{x:.3f}" y="{height-h:.3f}" width="{bar:.3f}" height="{h:.3f}" rx="4"/>')
        if count is not None:
            marks.append(f'<rect class="noibu-current-mark" x="{x:.3f}" y="{y:.3f}" width="{bar:.3f}" height="{height-y:.3f}" rx="4"/>')
        value = stage.get('display', f'{count:,}' if count is not None else 'Not measured')
        change = render_change(stage)
        detail = f'<span class="noibu-secondary">{escape(stage["detail"])}</span>' if stage.get('detail') else ''
        labels.append(f'<div class="noibu-stage"><span class="noibu-label">{escape(stage["label"])}</span><div class="noibu-stage-value tabular-nums">{escape(value)} {change}</div>{detail}</div>')
        track = '' if count is None else f'<div class="noibu-mobile-track"><span style="width:{100*count/maximum:.4f}%"></span></div>'
        mobile.append(f'<li><div>{labels[-1]}</div>{track}</li>')
    accessible = '; '.join(f'{s["label"]}: {s["count"]} sessions' if s['count'] is not None else f'{s["label"]}: Not measured' for s in stages)
    legend = '<span><i class="noibu-key-current"></i>Current sessions</span>' + ('<span><i class="noibu-key-prior"></i>Prior sessions</span>' if prior_present else '')
    context = f'<p class="noibu-secondary">{escape(data["funnelContext"])}</p>' if data.get('funnelContext') else ''
    counts = render_table({'title': 'Exact funnel counts', 'columns': ['Stage', 'Current sessions', 'Prior sessions'], 'rows': [[s['label'], s['count'], s.get('prior')] for s in stages]})
    many = ' noibu-funnel-many' if len(stages) > 6 else ''
    return f'<section class="noibu-funnel{many}"><h3>Purchase funnel</h3>{context}<div class="noibu-funnel-desktop"><div class="noibu-stage-labels" style="grid-template-columns:repeat({len(stages)},minmax(0,1fr))">{"".join(labels)}</div><svg class="noibu-funnel-chart" viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="{escape(accessible)}"><title>Distinct sessions by funnel stage</title>{"".join(marks)}</svg></div><ol class="noibu-funnel-mobile" aria-label="{escape(accessible)}">{"".join(mobile)}</ol><div class="noibu-chart-key">{legend}</div><details class="noibu-counts"><summary>Show exact counts</summary>{counts}</details></section>'

def _render_checkout_funnel(data):
    stages = data.get('funnel', [])
    if not stages:
        return ''
    maximum = max([100] + [s[k] for s in stages for k in ('rate', 'priorRate') if s[k] is not None])
    width, height = 1000, 220
    step = width / len(stages)
    bar = step * .56
    marks, labels, mobile = [], [], []
    for n, stage in enumerate(stages):
        x, rate = n * step, stage['rate']
        if rate is not None and n + 1 < len(stages) and stages[n + 1]['rate'] is not None:
            y, next_y = height - height * rate / maximum, height - height * stages[n + 1]['rate'] / maximum
            marks.append(f'<path class="noibu-funnel-link" d="M{x+bar:.3f},{y:.3f} L{x+step:.3f},{next_y:.3f} V{height} H{x+bar:.3f} Z"/>')
        for key, css in (('priorRate', 'prior'), ('rate', 'current')):
            value = stage[key]
            if value is not None:
                h = height * value / maximum
                marks.append(f'<rect class="noibu-{css}-mark" data-percent="{value:.8f}" x="{x:.3f}" y="{height-h:.3f}" width="{bar:.3f}" height="{h:.3f}" rx="4"/>')
        value = stage.get('display', 'Not measured')
        delta = f'<span class="noibu-delta">{escape(stage["change"])}</span>' if stage.get('change') else ''
        prior = f'Prior {stage["priorRate"]:.1f}%' if stage['priorRate'] is not None else 'Prior Not measured'
        label = f'<div class="noibu-stage"><span class="noibu-label">{escape(stage["label"])}</span><div class="noibu-stage-value tabular-nums">{escape(value)} {delta}</div><span class="noibu-secondary">{escape(prior)}</span></div>'
        labels.append(label)
        track = '' if rate is None else f'<div class="noibu-mobile-track"><span style="width:{100*rate/maximum:.4f}%"></span></div>'
        mobile.append('<li>' + label + track + '</li>')
    counts = render_table({'title': 'Exact funnel counts', 'columns': ['Stage', 'Current sessions', 'Prior sessions'], 'rows': [[s['label'], s['count'], s.get('prior')] for s in stages]})
    title = '% of sessions that added to cart'
    context = '<p class="noibu-secondary">' + escape(data['funnelBasis']['note']) + '</p>'
    if data.get('funnelContext'):
        context += '<details><summary>Source funnel notes — annotations only; calculated denominator above controls</summary><p>' + escape(data['funnelContext']) + '</p></details>'
    if not data['funnelBasis']['completionInMetrics']:
        metric = data['funnelBasis']['checkoutCompletion']
        context += '<p><strong>Checkout completion: ' + escape(metric['value']) + '</strong> ' + escape(metric['detail']) + ' ' + escape(metric.get('change', '')) + '</p>'
    # Numeric geometry uses percentages (including >100), never a count axis with a rate header.
    return f'<section class="noibu-funnel"><h3>Purchase funnel</h3>{context}<p>{title} · linear scale 0–{maximum:g}%</p><div class="noibu-funnel-desktop"><div class="noibu-stage-labels" style="grid-template-columns:repeat({len(stages)},minmax(0,1fr))">{"".join(labels)}</div><svg class="noibu-funnel-chart" viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="{escape(data["funnelBasis"]["note"])}"><title>{title}</title>{"".join(marks)}</svg></div><ol class="noibu-funnel-mobile">{"".join(mobile)}</ol><div class="noibu-chart-key"><span><i class="noibu-key-current"></i>Current % of own cart base</span><span><i class="noibu-key-prior"></i>Prior % of own cart base</span></div><details class="noibu-counts"><summary>Show exact counts</summary>{counts}</details></section>'


def render_table(table, compact=False):
    title = '<h3>' + escape(table['title']) + '</h3>'
    note = '<p class="noibu-secondary">' + escape(table['note']) + '</p>' if table.get('note') else ''
    if table.get('kind') == 'bars':
        maximum = max([row[1] or 0 for row in table['rows']] + [1])
        rows = []
        for label, value in table['rows']:
            fill = '' if value is None else f'<span class="noibu-bar-fill" style="width:{100*value/maximum:.4f}%"></span>'
            rows.append(f'<div class="noibu-bar-row"><span>{escape(label)}</span><div class="noibu-bar-track">{fill}</div><span class="tabular-nums">{escape(value if value is None else format(value, ","))}</span></div>')
        return '<section class="noibu-table-section">' + title + f'<div role="group" aria-label="{escape(table["title"])}">' + ''.join(rows) + '</div>' + note + '</section>'
    numeric = set(_numeric_columns(table))
    # Alignment only: never parse formatted text to compute analytics.
    headings = ''.join(f'<th scope="col" class="{"noibu-numeric" if i in numeric else ""}">{escape(c)}</th>' for i, c in enumerate(table['columns']))
    bar_col = table.get('barColumn') if compact else None
    maximum = max([r[bar_col] or 0 for r in table['rows']] + [1]) if bar_col is not None else 1
    def row_html(row):
        cells = []
        for i, cell in enumerate(row):
            value = format(cell, ',') if compact and type(cell) is int else cell
            display = escape(value)
            if compact and i == 0:
                display = '<span class="noibu-product-name" data-tooltip="' + escape(cell) + '">' + display + '</span>'
            elif bar_col == i and cell is not None:
                display = '<span class="noibu-count-cell"><span class="noibu-count-track" aria-hidden="true"><span style="width:' + f'{100*cell/maximum:.4f}%' + '"></span></span><span>' + display + '</span></span>'
            cells.append(f'<td class="{"noibu-numeric tabular-nums" if i in numeric or i == bar_col else ""}">{display}</td>')
        return '<tr>' + ''.join(cells) + '</tr>'
    def grid(rows):
        return '<div class="table-responsive"><table class="table"><thead><tr>' + headings + '</tr></thead><tbody>' + ''.join(row_html(row) for row in rows) + '</tbody></table></div>'
    content = grid(table['rows'][:5] if compact else table['rows'])
    if compact and len(table['rows']) > 5:
        content += f'<details class="noibu-extra-rows"><summary>Show all {len(table["rows"])} rows</summary>' + grid(table['rows']) + '</details>'
    return '<section class="noibu-table-section">' + title + content + note + '</section>'

def render_links(items):
    return ''.join(f'<a class="btn" href="{escape(item["url"])}" target="_blank" rel="noopener noreferrer">{escape(item["label"])}</a>' for item in items)

def render_performance(value, window):
    metric, measured = value['metric'], value['value']
    good, poor, unit = VITALS[metric]
    fmt = lambda number: f'{number:g}' + (' ms' if unit == 'ms' else '')
    context = [value.get('page'), value.get('pageGroup'), value.get('device'), window.get('label') or window['start'] + ' – ' + window['end']]
    traffic = value.get('traffic')
    if traffic and traffic['count'] is not None:
        context.insert(0, f'{traffic["count"]:,} {traffic["unit"]}')
    if measured is None:
        gauge = '<p>p75 not measured — no threshold marker.</p>'
    else:
        band = 'Good' if measured <= good else 'Needs improvement' if measured <= poor else 'Poor'
        # Shared metric scale across peer cards; values beyond the displayed
        # poor-band extent retain an exact visible value and an overflow notice.
        maximum = poor * 2
        good_at, poor_at = 100 * good / maximum, 100 * poor / maximum
        position = min(100, 100 * measured / maximum)
        description = f'{metric} p75 {fmt(measured)}: {band}. Good at or below {fmt(good)}; poor above {fmt(poor)}.'
        overflow = f'<span class="noibu-secondary">Beyond displayed {escape(fmt(maximum))} scale</span>' if measured > maximum else ''
        gauge = f'''<div class="noibu-vital-reading"><strong class="tabular-nums">{escape(fmt(measured))}</strong><span>p75 · {band}</span></div>
<div class="noibu-vital-gauge" role="img" aria-label="{escape(description)}" data-metric="{metric}" data-value="{measured}" data-band="{band}" data-position="{position:g}">
<div class="noibu-vital-track"><span class="noibu-vital-good" style="width:{good_at:g}%">✓</span><span class="noibu-vital-improve" style="width:{poor_at-good_at:g}%">!</span><span class="noibu-vital-poor" style="width:{100-poor_at:g}%">×</span><i class="noibu-vital-marker" style="left:clamp(2px,{position:g}%,calc(100% - 2px))" aria-hidden="true"></i></div>
<div class="noibu-vital-ticks" aria-hidden="true"><span style="left:{good_at:g}%">{escape(fmt(good))}</span><span style="left:{poor_at:g}%">{escape(fmt(poor))}</span></div></div>{overflow}
<div class="noibu-vital-legend">Good ≤ {escape(fmt(good))} · Needs improvement &gt; {escape(fmt(good))} to {escape(fmt(poor))} · Poor &gt; {escape(fmt(poor))}</div>'''
    return gauge + '<p class="noibu-vital-context">' + escape(' · '.join(x for x in context if x)) + '</p>'

def render(data, candidates=None, standalone=False, embed_controller=True):
    # Render a sanitized COPY; the supplied report/evidence and verified URLs remain unchanged.
    data = _display_copy(validate(data))
    if data['workflow'] == 'tech-diagnosis':
        monitoring = [f for f in data.get('findings', []) if not _tech_priority(f)]
        data['findings'] = [f for f in data.get('findings', []) if _tech_priority(f)]
        data.setdefault('caveats', []).extend('Monitor — ' + f['title'] + ': ' + f['evidence'] + (' Impact: ' + f['impact'] if f.get('impact') else '') + (' Next check: ' + f['fix'] if f.get('fix') else '') for f in monitoring)
    checkout = data['workflow'] == 'checkout-analysis'
    product = data['workflow'] == 'product-analysis'
    segment = data['workflow'] == 'segment-analysis'
    compact_report = product or segment
    outlined = data['workflow'] in ANALYTICS
    actions = []
    chat = data.get('host') == 'copilot-chat'
    def button(label, kind, target=None, primary=False):
        if chat:
            label = CHAT_LABELS.get(label, label)
        index = len(actions)
        actions.append(action(data, kind, target))
        return f'<button type="button" class="btn{ " btn-primary" if primary else ""}" data-noibu-action="{index}">{escape(label)}</button>'
    kpis = ''.join(f'<div class="noibu-stat"><span class="noibu-label">{escape(x["label"])}</span><div class="noibu-stat-value tabular-nums">{escape(x["value"])}</div>{render_change(x)}' + ('<span class="noibu-stat-detail noibu-secondary">' + escape(x['detail']) + '</span>' if x.get('detail') else '') + '</div>' for x in data.get('kpis', []))
    funnel = render_funnel(data)
    tables = ''.join(render_table(t) for t in data.get('tables', []))
    if checkout:
        visible = [t for t in data.get('tables', []) if t.get('placement') == 'overview' and t.get('kind') != 'bars']
        mixes = [t for t in data.get('tables', []) if t.get('kind') == 'bars' and t.get('placement') != 'supporting']
        supporting = [t for t in data.get('tables', []) if t not in visible and t not in mixes]
        tables = ''.join(render_table(t) for t in visible)
        if mixes:
            tables += '<div class="noibu-checkout-mixes">' + ''.join(render_table(t) for t in mixes) + '</div>'
        if supporting:
            tables += '<details class="noibu-supporting"><summary>Supporting data & observed abandonment</summary>' + ''.join(render_table(t) for t in supporting) + '</details>'
    elif compact_report and data.get('tables'):
        limit = 3 if segment else 2
        overview = [t for t in data['tables'] if t.get('placement') == 'overview'][:limit]
        if not overview:
            overview = [t for t in data['tables'] if t.get('placement') != 'supporting'][:limit]
        supporting = [t for t in data['tables'] if t not in overview]
        tables = ''.join(render_table(t, compact=True) for t in overview)
        if supporting:
            tables += '<details class="noibu-supporting"><summary>More supporting data (' + str(len(supporting)) + ')</summary>' + ''.join(render_table(t, compact=True) for t in supporting) + '</details>'
        detail_class = 'noibu-segment-details' if segment else 'noibu-product-details'
        tables = f'<details class="{detail_class}"><summary><span class="noibu-show-more">Show more</span><span class="noibu-show-less">Show less</span></summary>' + tables + '</details>'
    tables += _comparison_html(data)
    highlights = ''.join(f'<div><span class="noibu-label">{escape(x["label"])}</span><p>{escape(x["value"])}</p>{render_change(x)}<span class="noibu-stat-detail noibu-secondary">{escape(x.get("detail", ""))}</span></div>' for x in data.get('highlights', []))
    findings = []
    caps = data.get('capabilities', {})
    for n, item in enumerate(data.get('findings', []), 1):
        target = {'findingId': item['id']}
        performance = item.get('performance')
        controls = '' if performance else button('Investigate ↗', 'investigate', target)
        if data['workflow'] in {'tech-diagnosis', 'accessibility-audit'} or performance:
            controls += button('Get fix ↗' if performance else 'Get fix', 'get-fix', target)
            if performance:
                controls += button('Investigate ↗', 'investigate', target)
            if caps.get('draftPr'):
                controls += button('Prepare draft PR', 'draft-pr', target)
        if data['workflow'] in {'tech-diagnosis', 'accessibility-audit'} or item.get('category') in {'merchant', 'performance', 'accessibility'}:
            controls += button('Open a Ticket', 'create-ticket', target)
        if item.get('issueId') and caps.get('ignoreIssue'):
            controls += button('Ignore issue', 'ignore-issue', {**target, 'issueId': item['issueId']})
        if item.get('category') == 'vendor':
            controls += button('Prepare vendor message', 'share-vendor', target)
        destinations = item.get('noibuLinks', [])
        metric_overview = bool(performance and not destinations and data['domain'].get('id'))
        if metric_overview:
            destinations = [{'label': 'View ' + performance['metric'] + ' in Noibu', 'url': links.console_link(data['domain']['id'], 'performance', performance['metric']), 'source': 'Resolved report domain UUID and documented performance overview route'}]
        controls += render_links(destinations)
        fix = '<p>' + escape(item['fix']) + '</p>' if item.get('fix') else ''
        gauge = '<p class="noibu-secondary">' + escape(item['gaugeNote']) + '</p>' if item.get('gaugeNote') else ''
        impact = f'<span class="noibu-impact">{escape(item["impact"])}</span>' if item.get('impact') else ''
        if performance:
            state = '<span class="noibu-vital-status">' + escape(performance['status']) + '</span>' if performance.get('status') else ''
            navigation_note = '<p class="noibu-vital-legend">Noibu link opens the metric overview; page and date filters are not applied.</p>' if metric_overview else ''
            findings.append(f'<section class="noibu-performance-card"><div class="noibu-performance-header"><span>{performance["metric"]}</span>{state}</div><div class="noibu-performance-body"><h3>{escape(item["title"])}</h3><p>{escape(item["evidence"])}</p>{gauge}{render_performance(performance, data["window"])}{fix}<div class="viz-row">{controls}</div>{navigation_note}</div></section>')
        elif checkout:
            fix = '<p class="noibu-next-check"><strong>Next check</strong> ' + escape(item['fix']) + '</p>' if item.get('fix') else ''
            tag = ' · ' + escape(item['tag']) if item.get('tag') and item['tag'].lower() != f'priority {n}' else ''
            findings.append(f'<section class="noibu-finding noibu-checkout-opportunity"><div class="noibu-finding-heading"><span class="noibu-label">Priority {n}{tag}</span>{impact}</div><div class="noibu-opportunity-body"><h3>{escape(item["title"])}</h3><p>{escape(item["evidence"])}</p>{gauge}{fix}<div class="viz-row">{controls}</div></div></section>')
        elif compact_report:
            next_check = '<details class="noibu-next-check"><summary>Investigation & verification</summary><p>' + escape(item['fix']) + '</p></details>' if item.get('fix') else ''
            card_class = 'noibu-segment-opportunity' if segment else 'noibu-product-opportunity'
            findings.append(f'<section class="noibu-finding {card_class}"><div class="noibu-finding-heading"><span class="noibu-label">{escape(item.get("tag", f"Priority {n}"))}</span>{impact}</div><div class="noibu-opportunity-body"><h3>{escape(item["title"])}</h3><p>{escape(item["evidence"])}</p>{gauge}{next_check}<div class="viz-row">{controls}</div></div></section>')
        else:
            findings.append(f'<section class="noibu-finding"><div class="noibu-finding-heading"><span class="noibu-tag">{escape(item.get("tag", f"Priority {n}"))}</span>{impact}</div><h3>{escape(item["title"])}</h3><p>{escape(item["evidence"])}</p>{gauge}{fix}<div class="viz-row">{controls}</div></section>')
    if data['workflow'] == 'tech-diagnosis':
        grouped = []
        for category, title in [('merchant', 'Merchant issues'), ('performance', 'Performance'), ('vendor', 'Vendor issues'), (None, 'Other findings'), ('accessibility', 'Accessibility')]:
            sections = [section for item, section in zip(data.get('findings', []), findings) if item.get('category') == category]
            if sections:
                grouped.append('<section class="noibu-finding-group"><h2>' + title + '</h2>' + ''.join(sections) + '</section>')
        findings = grouped
    experiments = []
    for item in _display_copy(candidate_data(data, candidates)):
        controls = ''
        if caps.get('createDraft'):
            controls = button('Create A/B draft in Noibu', 'create-draft', {'rank': item['rank'], 'title': item['title'], 'createInputHash': item['hash']}, True)
        evidence = ''.join('<li>' + escape(e['claim']) + ' · ' + escape(json.dumps(e['numbers'], ensure_ascii=False)) + ' · ' + escape(e['source']) + '</li>' for e in item['evidence'])
        variations = ''.join('<tr><td>' + escape(v['name']) + '</td><td>' + ('Control' if v['isControl'] else 'Proposed variation') + '</td><td>' + escape(v['trafficSplit']) + '%</td></tr>' for v in item['variations'])
        setup = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Variation</th><th>Role</th><th>Traffic split</th></tr></thead><tbody>' + variations + '</tbody></table></div>'
        guardrails = ', '.join(g['metric'] for g in item['guardrails']) or 'None selected'
        targeting = 'Devices: ' + (', '.join(item['devices']) or 'All') + '; UTM: ' + (json.dumps(item['utm'], ensure_ascii=False) if item['utm'] else 'No selected restrictions')
        experiments.append(f'<section class="noibu-finding"><span class="text-small">Test {item["rank"]} · {escape(item["validation"])}</span><h3>{escape(item["title"])}</h3><p>{escape(item["what"])}</p><p>{escape(item["hypothesis"])}</p><ul>{evidence}</ul><p>Success metric: {escape(item["metric"])} · Guardrails: {escape(guardrails)}</p>{setup}<p>{escape(targeting)}</p>{controls}</section>')
    if data['workflow'] == 'accessibility-audit' and data.get('findings'):
        if data.get('auditLayout') == 'summary-actions':
            findings = []
        ticket_scope = data['findings'][:3]
        pr_scope = [f for f in data['findings'] if f.get('ownership') not in {'merchant-content', 'vendor'} and f.get('category') != 'vendor'][:3]
        audit_actions = button('Auto-draft PR', 'draft-pr', {'findingIds': [f['id'] for f in pr_scope]}, True) if pr_scope else ''
        audit_actions += button('Auto-create tickets', 'create-ticket', {'findingIds': [f['id'] for f in ticket_scope]})
        scope_text = '<p>Tickets: ' + escape('; '.join(f['title'] for f in ticket_scope)) + '.</p>'
        if pr_scope:
            scope_text += '<p>PR review: ' + escape('; '.join(f['title'] for f in pr_scope)) + '. Source/ownership verification and selected repository-provider connection are required before a draft PR can be created.</p>'
        findings.append('<section class="noibu-finding"><h3>' + ('Draft patches or tickets for these top findings?' if chat else 'Draft PRs or open tickets for these top findings?') + '</h3>' + scope_text + '<div class="viz-row">' + audit_actions + '</div></section>')
    save = ''  # No dashboard action (design/README.md, decision 3).
    controls = ('' if outlined else save) + button('Prepare for Copilot Pages' if chat else 'Save report to OneDrive', 'save-report', primary=data['workflow'] not in ANALYTICS) + button('Download Report', 'export-report')
    controls += render_links(data.get('noibuLinks', []))
    if data['workflow'] in SCHEDULABLE and not chat:
        controls += button('Schedule Insights' if compact_report else 'Schedule report', 'schedule', primary=outlined)
    if data.get('contextHash') and caps.get('persistContext'):
        controls += button('Save approved context to Noibu', 'save-context', {'contextHash': data['contextHash']}, True)
    root = 'noibu-' + data['reportId']
    model = {'actions': actions, 'timezone': data.get('timezone', ''), 'workflow': data['workflow']}
    if chat:
        model['host'] = 'copilot-chat'
    # These assets contain fixed code; model values never become executable source.
    template, stylesheet, controller = load_assets()
    schedule = {'TITLE': '', 'DAILY': '', 'NOTE': ''}
    if data['workflow'] in SCHEDULABLE and not chat:
        schedule_titles = {'checkout-analysis': 'Schedule checkout analysis', 'product-analysis': 'Schedule product analysis', 'segment-analysis': 'Schedule segment analysis', 'store-pulse': 'Schedule Store Pulse', 'tech-diagnosis': 'Schedule technical diagnosis', 'accessibility-audit': 'Schedule accessibility audit', 'ab-testing': 'Schedule A/B opportunities', 'ab-test-opportunity-finder': 'Schedule A/B opportunities'}
        scope_notes = {
            'tech-diagnosis': 'Recurring report only: no automatic source edits, PRs, tickets or issue status changes.',
            'accessibility-audit': 'Recurring scans require verified page-script execution in the scheduled run. Setup does not scan or fix anything; audit mode and coverage must be confirmed.',
            'ab-testing': 'Recurring recommendations only: no automatic Noibu test drafts, browser mutations, implementation or test activation.',
            'ab-test-opportunity-finder': 'Recurring recommendations only: no automatic Noibu test drafts, browser mutations, implementation or test activation.'
        }
        schedule['TITLE'] = schedule_titles[data['workflow']]
        if data['workflow'] in scope_notes:
            schedule['NOTE'] = '<p class="text-small">' + escape(scope_notes[data['workflow']]) + '</p>\n    '
        if data['workflow'] == 'store-pulse':
            schedule['DAILY'] = '<label class="noibu-choice"><input type="radio" name="frequency" value="daily"><span>Daily</span></label>\n      '
    else:
        template = re.sub(r'<!--noibu-schedule-->.*?<!--/noibu-schedule-->\n', '', template, count=1, flags=re.S)
    if outlined:
        template = template.replace('{{KPIS}}', '{{OVERVIEWCONTEXT}}\n      {{KPIS}}', 1)
        if save:
            template = template.replace('{{TABLES}}', '{{TABLES}}\n      <div class="noibu-overview-save">' + save + '</div>', 1)
        template = template.replace('<h3>Save & schedule</h3>', '<h3>Save & download</h3>' if chat else '<h3>Download & schedule</h3>', 1)
    if compact_report:
        if len(findings) > 3:
            more_count = len(findings) - 3
            more_label = ' more opportunity' if more_count == 1 else ' more opportunities'
            findings = findings[:3] + ['<details class="noibu-more-findings"><summary>' + str(more_count) + more_label + '</summary>' + ''.join(findings[3:]) + '</details>']
    if data.get('auditLayout') == 'summary-actions':
        template = re.sub(r'  <section class="noibu-overview">.*?  </section>\n', '', template, count=1, flags=re.S)
    values = {'ROOT': root, 'TITLE': escape(data['workflow'].replace('-', ' ').title()), 'DOMAIN': escape(data['domain']['name']), 'WINDOW': escape(data['window'].get('label', data['window']['start'] + ' – ' + data['window']['end'])), 'GENERATED': escape(data['generatedAt']), 'COMPARISON': escape(_comparison(data)), 'SUMMARY': escape(data['summary']), 'KPIS': '<div class="noibu-kpis">' + kpis + '</div>' if kpis else '', 'HIGHLIGHTS': '<div class="noibu-highlights">' + highlights + '</div>' if highlights else '', 'FUNNEL': funnel, 'TABLES': tables, 'FINDINGS': ''.join(findings), 'EXPERIMENTS': ''.join(experiments), 'CAVEATS': '<details class="noibu-caveats" open><summary>Evidence & coverage</summary><ul>' + ''.join('<li>' + escape(x) + '</li>' for x in data.get('caveats', [])) + '</ul></details>' if data.get('caveats') else '', 'ACTIONS': controls, 'MODEL': safe_json(model), 'CONTROLLER': '', 'SCHEDULETITLE': escape(schedule['TITLE']), 'DAILY': schedule['DAILY'], 'SCHEDULENOTE': schedule['NOTE'], 'STYLE': stylesheet.replace('{{ROOT}}', root)}
    if embed_controller:
        values['CONTROLLER'] = '  <script>\n' + controller + '\n  bindNoibuPresentation(document.getElementById(\'' + root + '\'));\n  </script>'
    if segment and data.get('overviewNotes'):
        values['HIGHLIGHTS'] += '<div class="noibu-overview-notes" role="note" aria-label="Data notes">' + ''.join('<p><strong>Data note:</strong> ' + escape(note) + '</p>' for note in data['overviewNotes']) + '</div>'
    values['OVERVIEWCONTEXT'] = '<p class="noibu-overview-context">' + escape(data['overviewContext']) + '</p>' if data.get('overviewContext') else ''
    if outlined:
        values['TITLE'] = 'Overview'
    fragment = re.sub(r'\{\{([A-Z]+)\}\}', lambda match: values[match.group(1)], template)
    fragment = fragment.replace('class="noibu-board"', f'class="noibu-board" data-noibu-workflow="{data["workflow"]}"', 1)
    require(len(fragment.encode()) < 1000000, 'Presentation exceeds size limit')
    if not standalone:
        return fragment
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{values["TITLE"]} — {values["DOMAIN"]}</title></head><body class="noibu-standalone">{fragment}</body></html>'

# ---------------------------------------------------------------------------
# Adaptive Card (Cowork built-in Adaptive Cards skill), in the Noibu insights design language
# (docs/design/noibu-design-language-skills.md) translated to Adaptive Card elements:
# flat cards with a tinted header strip and uppercase label, monochrome data, colour only on
# deltas/severity, ↑ ↓ arrows, max 3 priority cards, no action bar (design/README.md).
# Report text goes into RichTextBlock/TextRun (never Markdown-parsed), so data can't inject
# links or formatting. Tenant test 2026-10-28: card buttons didn't reach the conversation, so the
# card only carries Noibu link buttons; next steps are the AskUserQuestion after the card.
# Host extensions (charts, gauge, progress bars) carry fallbacks.
CARD_LIMIT = 24000  # bytes; Teams swaps larger cards for a 'too large to display' placeholder


class CardSizeError(ValueError):
    """The generated card exceeds the local budget; compact may be tried before rendering."""


def _run(text, **style):
    return {'type': 'TextRun', 'text': _clean(str(text if text is not None else 'Not measured')), **style}


def _rich(*runs, spacing=None, align=None):
    block = {'type': 'RichTextBlock', 'inlines': [r if isinstance(r, dict) else _run(r) for r in runs]}
    if spacing:
        block['spacing'] = spacing
    if align:
        block['horizontalAlignment'] = align
    return block


_CITATION = re.compile(r'\s*\[(?:Source:\s*)?turn\d+[a-z]+\d+(?:[^\]\n]*)\]|\s*[\(\[]ref:\s*NB-[a-f0-9-]+[\)\]]|[\ue200\ue202]cite[\ue202]turn[^\ue201\n]*[\ue201]', re.I)
_SESSION_TOKEN = re.compile(r'\b(?:session_id|sessionId|session_token)\s*[:=]\s*[a-f0-9-]{16,}\b', re.I)
_ISO_TIME = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?')
_MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
COUNTRIES = {'US': 'United States', 'CA': 'Canada', 'GB': 'United Kingdom', 'UK': 'United Kingdom', 'AU': 'Australia', 'NZ': 'New Zealand', 'IE': 'Ireland', 'FR': 'France', 'DE': 'Germany', 'ES': 'Spain', 'IT': 'Italy', 'NL': 'Netherlands', 'BE': 'Belgium', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland', 'CH': 'Switzerland', 'AT': 'Austria', 'PL': 'Poland', 'PT': 'Portugal', 'MX': 'Mexico', 'BR': 'Brazil', 'AR': 'Argentina', 'CL': 'Chile', 'CO': 'Colombia', 'IN': 'India', 'PK': 'Pakistan', 'CN': 'China', 'JP': 'Japan', 'KR': 'South Korea', 'SG': 'Singapore', 'HK': 'Hong Kong', 'PH': 'Philippines', 'ID': 'Indonesia', 'MY': 'Malaysia', 'TH': 'Thailand', 'VN': 'Vietnam', 'AE': 'United Arab Emirates', 'SA': 'Saudi Arabia', 'IL': 'Israel', 'TR': 'Türkiye', 'ZA': 'South Africa', 'NG': 'Nigeria', 'EG': 'Egypt'}
SOURCES = {'google': 'Google', 'facebook': 'Facebook', 'fb': 'Facebook', 'ig': 'Instagram', 'instagram': 'Instagram', 'tiktok': 'TikTok', 'bing': 'Bing', 'pinterest': 'Pinterest', 'youtube': 'YouTube', 'klaviyo': 'Klaviyo', 'shopify_email': 'Shopify Email', 'sendlane': 'Sendlane', 'attentive': 'Attentive', 'omnisend': 'Omnisend', 'mailchimp': 'Mailchimp', 'newsletter': 'Newsletter', 'email': 'Email', 'reddit': 'Reddit', 'snapchat': 'Snapchat', 'linkedin': 'LinkedIn'}
# Copy budget enforced by the generator (Cowork test 2026-10-28: long fields made cards hard to scan).
# Anything over budget is folded behind a toggle, never dropped.
SUMMARY_CHARS, LINE_CHARS, CHIP_CHARS, CELL_CHARS = 220, 120, 32, 40


def _clean(text):
    # Presentation only: drop host citation tags such as "(ref: NB-f3369fc7-...)" that don't belong in a card.
    if not isinstance(text, str):
        return text
    token_view = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    # Only substitute the normalized view when it actually contains a runtime token.
    token_source = token_view if _CITATION.search(token_view) or _SESSION_TOKEN.search(token_view) else text
    cleaned = _SESSION_TOKEN.sub('[session reference retained in evidence]', _CITATION.sub('', token_source))
    return cleaned.rstrip() if cleaned != text else text


def _when(match):
    _, month, day, hour, minute = (int(g) for g in match.groups())
    return f'{_MONTHS[month - 1]} {day}, {hour % 12 or 12}:{minute:02d} {"am" if hour < 12 else "pm"}'


def _prose(text):
    """Display prose: no citation tags, no "Source: …" provenance sentences (they belong in the
    report file), ISO timestamps as readable times, collapsed whitespace."""
    if not isinstance(text, str):
        return text
    text = _clean(text)
    # Preserve full timestamp precision and timezone in evidence and critical windows.
    return re.sub(r'\s{2,}', ' ', text).strip()


def _split(text, limit):
    """(shown, folded): the first sentence(s) that fit the budget, and the full text when cut."""
    text = _prose(text) or ''
    if len(text) <= limit:
        return text, None
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9(])', text)
    shown = ''
    for sentence in sentences:
        if len(shown) + len(sentence) + 1 > limit:
            break
        shown = (shown + ' ' + sentence).strip()
    if not shown:
        shown = text[:limit].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    return shown, text


def _country(value):
    # Design: country names get a flag prefix (the only emoji used). Unknown codes stay as given.
    if not isinstance(value, str) or not re.fullmatch(r'[A-Z]{2}', value.strip()):
        return value
    code = value.strip()
    flag = ''.join(chr(0x1F1E6 + ord(c) - 65) for c in ('GB' if code == 'UK' else code))
    return f'{flag} {COUNTRIES.get(code, code)}'


def _channel(value):
    # Display only; raw keys remain independent through aggregation and ranking.
    if not isinstance(value, str):
        return value
    parts = re.split(r'\s*(?:/|·)\s*', value, maxsplit=1)
    if len(parts) != 2:
        return value
    source, medium = parts
    missing = lambda v: v.strip().lower() in {'', '(none)', 'none', '(not set)', 'not set', 'null', '(null)'}
    if missing(source) and missing(medium):
        return 'Unattributed (UTM not set)'
    name = SOURCES.get(source.lower(), source[:1].upper() + source[1:])
    if missing(medium):
        return name + ' · Medium not set'
    if missing(source):
        return 'Source not set · ' + medium
    return name + ' · ' + medium


def _name(value):
    """Row names: URL slugs read as words ("cable-flex-bracelet" -> "Cable flex bracelet"), long
    names end in "…", and a "· SKU" style suffix becomes a quiet second line."""
    if not isinstance(value, str):
        return value, None
    main, _, secondary = value.partition(' · ')
    if re.fullmatch(r'/[a-z0-9]+(?:[-_][a-z0-9]+)*/?|[a-z0-9]+(?:[-_][a-z0-9]+)+', main.strip()):
        words = re.sub(r'[-_/]+', ' ', main).strip()
        main = words[:1].upper() + words[1:]
    if len(main) > CELL_CHARS:
        main = main[:CELL_CHARS - 1].rsplit(' ', 1)[0] + '…'
    return main, secondary or None


def _row_kind(table):
    first = table['columns'][0].lower()
    return 'country' if 'country' in first else 'channel' if any(k in first for k in ('source', 'channel', 'medium', 'campaign')) else 'name'


def _display_rows(table, limit):
    kind = _row_kind(table)
    fn = _country if kind == 'country' else _channel if kind == 'channel' else None
    rows = [list(r) for r in table['rows'][:limit]]
    if fn:
        for r in rows:
            r[0] = fn(r[0])
    return rows


def _eyebrow(text, **extra):
    # Small uppercase label (fixed UI copy or a report label rendered as plain text).
    return _rich(_run(str(text).upper(), size='Small', weight='Bolder', isSubtle=True), **extra)


def _delta_run(item):
    """Design: arrows ↑ ↓ (never + −), flat dash; colour only for change. Direction is explicit
    report metadata and is never inferred from the formatted text."""
    change = item.get('change')
    if not change:
        return None
    direction = item.get('changeDirection')
    if direction is None:
        return _run(change, size='Small', isSubtle=True)
    text = re.sub(r'^\s*[+\-−↑↓▲▼]\s*', '', change)
    if direction == 'flat':
        return _run('— ' + text, size='Small', isSubtle=True)
    if direction == 'down':
        return _run('↓ ' + text, size='Small', weight='Bolder', color='Warning')
    return _run('↑ ' + text, size='Small', weight='Bolder', color='Warning' if item.get('tone') == 'unfavorable' else 'Good')


def _toggle(title, target, align=None, spacing='Small'):
    block = {'type': 'ActionSet', 'spacing': spacing, 'actions': [{'type': 'Action.ToggleVisibility', 'title': title, 'targetElements': [target]}]}
    if align:
        block['horizontalAlignment'] = align
    return block


def _folded(target, items):
    return {'type': 'Container', 'id': target, 'isVisible': False, 'spacing': 'Small', 'items': items}


def _cowork_check(card):
    """Execute the exact bundled 21.1.8 validator without a sibling-file dependency.

    The CLI checker remains packaged separately. Keep the validation core identical;
    regression tests compare its source bytes and behavior, including existing limits.
    """
    # BEGIN VENDORED COWORK CARD CHECK (core SHA-256 68fc8f823302a133d764afa9c54a2429b34695861704a30d3c04da0db784649e)
    ELEMENTS = {
        'Container', 'ColumnSet', 'Column', 'TextBlock', 'Image', 'ImageSet', 'CodeBlock', 'RichTextBlock',
        'FactSet', 'Table', 'TableRow', 'TableCell', 'Badge', 'Rating', 'ProgressBar', 'ProgressRing', 'Icon',
        'Carousel', 'CarouselPage', 'Accordion', 'AccordionPage', 'TabSet', 'TabPage', 'Component',
        'Chart.Donut', 'Chart.Pie', 'Chart.VerticalBar', 'Chart.VerticalBar.Grouped', 'Chart.HorizontalBar',
        'Chart.HorizontalBar.Stacked', 'Chart.Line', 'Chart.Gauge',
    }
    INLINE = {'TextRun'}
    ACTIONS = {'Action.OpenUrl', 'Action.ShowCard'}  # usable in selectAction / top-level actions only
    # Children that must live only in their parent's named array.
    NESTED = {'Column': ('ColumnSet', 'columns'), 'TableRow': ('Table', 'rows'), 'TableCell': ('TableRow', 'cells'),
              'CarouselPage': ('Carousel', 'pages'), 'AccordionPage': ('Accordion', 'pages'), 'TabPage': ('TabSet', 'pages')}

    _SPACING = {'None', 'ExtraSmall', 'Small', 'Default', 'Medium', 'Large', 'ExtraLarge', 'Padding'}
    _CHART_COLORS = {'good', 'warning', 'attention', 'neutral'} \
        | {f'categorical{c}' for c in ('Red', 'Purple', 'Lavender', 'Blue', 'LightBlue', 'Teal', 'Green', 'Lime', 'Marigold')} \
        | {f'sequential{n}' for n in range(1, 9)} \
        | {f'sequential{h}{n}' for h in ('Red', 'Green', 'Yellow') for n in range(1, 9)} \
        | {f'diverging{c}' for c in ('Blue', 'LightBlue', 'Cyan', 'Teal', 'Yellow', 'Peach', 'LightRed', 'Red', 'Maroon', 'Gray')}
    ENUMS = {
        'spacing': _SPACING,
        'horizontalAlignment': {'Left', 'Center', 'Right'},
        'verticalContentAlignment': {'Top', 'Center', 'Bottom'},
        'height': {'auto', 'stretch'},
        'colorSet': {'categorical', 'sequential', 'diverging', 'sequentialRed', 'sequentialGreen', 'sequentialYellow'},
        'valueFormat': {'Percentage', 'Fraction'},
        'headerSize': {'Small', 'Medium', 'Large', 'XLarge'},
        'expandIconPosition': {'Start', 'Inline', 'End'},
    }
    TEXT_ENUMS = {'size': {'Small', 'Default', 'Medium', 'Large', 'ExtraLarge'}, 'weight': {'Lighter', 'Default', 'Bolder'},
                  'color': {'Default', 'Dark', 'Light', 'Accent', 'Good', 'Warning', 'Attention'}}
    CONTAINER_STYLE = {'default', 'emphasis', 'accent', 'good', 'attention', 'warning'}
    PROGRESS_COLOR = {'Accent', 'Good', 'Warning', 'Attention'}
    CHARTS_WITH_SERIES = {'Chart.Line', 'Chart.VerticalBar.Grouped'}


    def _eq(value, allowed):
        return isinstance(value, str) and value.lower() in {a.lower() for a in allowed}


    def check(card):
        errors = []
        err = lambda path, msg: errors.append(f'{path}: {msg}')
        if card.get('type') != 'AdaptiveCard':
            err('type', "must be 'AdaptiveCard'")
        if card.get('version') != '1.6':
            err('version', f"render_ui requires '1.6', got {card.get('version')!r}")
        if not isinstance(card.get('body'), list) or not card['body']:
            err('body', 'must be a non-empty array')

        def action(a, path):
            if not isinstance(a, dict) or a.get('type') not in ACTIONS:
                err(path, f"action type {a.get('type') if isinstance(a, dict) else a!r} is not supported (only {sorted(ACTIONS)})")
            elif a['type'] == 'Action.OpenUrl' and not str(a.get('url', '')).startswith(('https://', 'http://')):
                err(path, 'Action.OpenUrl needs an http(s) url')

        def element(el, path, parent=None, slot=None):
            if not isinstance(el, dict):
                return err(path, 'element must be an object')
            t = el.get('type')
            if t in INLINE:
                if parent != 'RichTextBlock':
                    err(path, 'TextRun is only valid inside RichTextBlock.inlines')
            elif t not in ELEMENTS:
                return err(path, f"unknown type {t!r}")
            if t in NESTED and (parent, slot) != NESTED[t]:
                err(path, f'{t} must sit in {NESTED[t][0]}.{NESTED[t][1]}')
            for key, allowed in ENUMS.items():
                if key in el and not _eq(el[key], allowed):
                    err(f'{path}.{key}', f'{el[key]!r} not in {sorted(allowed)}')
            if t in ('TextBlock', 'TextRun'):
                for key, allowed in TEXT_ENUMS.items():
                    if key in el and not _eq(el[key], allowed):
                        err(f'{path}.{key}', f'{el[key]!r} not in {sorted(allowed)}')
            if t in ('Container', 'Column', 'ColumnSet', 'TableCell') and 'style' in el and not _eq(el['style'], CONTAINER_STYLE):
                err(f'{path}.style', f"{el['style']!r} not in {sorted(CONTAINER_STYLE)}")
            if t == 'ProgressBar' and 'color' in el and not _eq(el['color'], PROGRESS_COLOR):
                err(f'{path}.color', f"{el['color']!r} not in {sorted(PROGRESS_COLOR)}")
            if t and t.startswith('Chart.'):
                if 'color' in el and el['color'] not in _CHART_COLORS:
                    err(f'{path}.color', f"{el['color']!r} is not a ChartColor")
                for i, d in enumerate(el.get('data', []) if t != 'Chart.Gauge' else []):
                    if not isinstance(d, dict):
                        err(f'{path}.data[{i}]', 'must be an object'); continue
                    if 'color' in d and d['color'] not in _CHART_COLORS:
                        err(f'{path}.data[{i}].color', f"{d['color']!r} is not a ChartColor")
                    if t in CHARTS_WITH_SERIES and not isinstance(d.get('values'), list):
                        err(f'{path}.data[{i}]', 'needs {legend, values:[{x,y}]}')
                if t == 'Chart.Gauge':
                    for i, seg in enumerate(el.get('segments', [])):
                        bad = set(seg) - {'size', 'legend', 'color'}
                        if bad or not isinstance(seg.get('size'), (int, float)):
                            err(f'{path}.segments[{i}]', f'segments are {{size, legend, color}}; got {sorted(seg)}')
                        if 'color' in seg and seg['color'] not in _CHART_COLORS:
                            err(f'{path}.segments[{i}].color', f"{seg['color']!r} is not a ChartColor")
            if t == 'AccordionPage' and 'title' in el and 'headerTitle' not in el:
                err(path, "AccordionPage takes 'headerTitle', not 'title' (the header renders blank)")
            if 'selectAction' in el:
                action(el['selectAction'], f'{path}.selectAction')
            for slot_name in ('items', 'columns', 'rows', 'cells', 'pages', 'inlines', 'images', 'fallbackCard'):
                children = el.get(slot_name)
                if isinstance(children, list):
                    for i, child in enumerate(children):
                        if slot_name == 'inlines' and isinstance(child, str):
                            continue
                        element(child, f'{path}.{slot_name}[{i}]', t, slot_name)
            if isinstance(el.get('fallback'), dict):
                element(el['fallback'], f'{path}.fallback', parent, slot)

        for i, el in enumerate(card.get('body') or []):
            element(el, f'body[{i}]')
        for i, a in enumerate(card.get('actions') or []):
            action(a, f'actions[{i}]')
        return errors
    # END VENDORED COWORK CARD CHECK
    return check(card)


def _accordionize(node):
    """Cowork's render_ui rejects ActionSet (and so Action.ToggleVisibility). Replace every
    [toggle ActionSet, hidden container with the targeted id] pair with one collapsed Accordion,
    recursively, so the card keeps its progressive disclosure on the Cowork schema."""
    if isinstance(node, dict):
        return {k: _accordionize(v) for k, v in node.items()}
    if not isinstance(node, list):
        return node
    out, i = [], 0
    while i < len(node):
        el = node[i]
        nxt = node[i + 1] if i + 1 < len(node) else None
        acts = el.get('actions') if isinstance(el, dict) and el.get('type') == 'ActionSet' else None
        if acts and len(acts) == 1 and acts[0].get('type') == 'Action.ToggleVisibility' and isinstance(nxt, dict) \
                and nxt.get('id') in acts[0].get('targetElements', []) and nxt.get('isVisible') is False:
            hidden = {k: v for k, v in nxt.items() if k not in ('id', 'isVisible', 'spacing')}
            items = hidden['items'] if hidden.get('type') == 'Container' and set(hidden) <= {'type', 'items'} else [hidden]
            page = {'type': 'AccordionPage', 'headerTitle': acts[0]['title'], 'headerSize': 'Small', 'items': _accordionize(items)}
            out.append({'type': 'Accordion', 'spacing': el.get('spacing', 'Small'), 'pages': [page]})
            i += 2
            continue
        require(not acts, 'unpaired toggle in Adaptive Card; every toggle must precede its hidden container')
        out.append(_accordionize(el))
        i += 1
    return out


def _card(label, body, meta=None, right=None, spacing='Medium'):
    """Base container: tinted header strip (label left, short meta/chip right) over the card body.
    Weighted columns, not "auto", so a long right-hand text can never squeeze the label into a
    one-word-wide column (Cowork screenshot, 2026-10-28). Over-budget meta moves into the body."""
    if isinstance(right, str):
        right = _rich(_run(right, size='Small', weight='Bolder', isSubtle=True), align='Right')
    if meta and len(meta) > 44:
        body = [_rich(_run(meta, size='Small', isSubtle=True), spacing='None')] + body
        meta = None
    head_cols = [{'type': 'Column', 'width': 3, 'verticalContentAlignment': 'Center', 'items': [_eyebrow(label)]}]
    if meta or right:
        head_cols.append({'type': 'Column', 'width': 2, 'verticalContentAlignment': 'Center', 'items': [right or _rich(_run(meta, size='Small', isSubtle=True), align='Right')]})
    return {'type': 'Container', 'style': 'default', 'showBorder': True, 'roundedCorners': True, 'spacing': spacing, 'items': [
        {'type': 'Container', 'style': 'emphasis', 'bleed': True, 'items': [{'type': 'ColumnSet', 'columns': head_cols}]},
        {'type': 'Container', 'items': body}]}


# Standard metric names shortened on crowded tile rows (4+ tiles), as the Claude Store Pulse board does.
SHORT_LABELS = {'average order value': 'AOV', 'revenue per session': 'RPS', 'conversion rate': 'Conversion', 'engagement rate': 'Engagement', 'add to cart rate': 'ATC rate', 'checkout completion rate': 'Checkout completion'}


_MULTI_CURRENCY = re.compile(r'^\s*([A-Z]{3}\s?[\d.,]+[kKmM]?)\s*/\s*[A-Z]{3}\s?[\d.,]')


def _stat_strip(items, tiles=True, details=None, pill=None):
    """KPI tiles (or quiet stat columns): uppercase label, value, arrow delta. No detail text on
    the tile (Claude boards show value + delta only); details go to the card's details toggle.
    Tiles stretch to the row height; short metric names keep labels on one line so values line up.
    (No minHeight: the 21.1.6 card that used it didn't display in Cowork.)"""
    n = len(items)
    per_row = 3 if n in {3, 6} or n > 5 else max(1, n)
    rows = []
    for start in range(0, n, per_row):
        group = items[start:start + per_row]
        crowded = len(group) >= 4
        labels, values, multis = [], [], []
        for item in group:
            label = SHORT_LABELS.get(str(item['label']).lower(), item['label']) if crowded else item['label']
            value = str(item['value']) if item.get('value') is not None else None
            multi = _MULTI_CURRENCY.match(value or '')
            if multi:
                value = multi.group(1)  # first currency on the tile; every currency in details
            money = re.fullmatch(r'([A-Z]{3})\s?([\d.,]+[kKmM]?)', value or '')
            if crowded and money:
                label, value = f'{label} · {money.group(1)}', money.group(2)
            labels.append(label)
            values.append(value)
            multis.append(multi)
        value_size = 'Large' if tiles and all(len(v or '') <= (7 if len(group) >= 5 else 10 if crowded else 16) for v in values) else 'Medium'
        columns = []
        for k, item in enumerate(group):
            value, multi = values[k], multis[k]
            cells = [_eyebrow(labels[k]), _rich(_run(value, size=value_size, weight='Bolder'), spacing='Small')]
            delta = _delta_run(item)
            if delta:
                cells.append(_rich(delta, spacing='None'))
            if pill and pill[0] == start + k:
                cells.append(_rich(_run(pill[1], size='Small', weight='Bolder', color='Warning'), spacing='Small'))
            if details is not None and (item.get('detail') or multi):
                details.append((item['label'], ' · '.join(x for x in [item['value'] if multi else None, _prose(item.get('detail'))] if x)))
            column = {'type': 'Column', 'width': 'stretch', 'items': cells}
            if tiles:
                column.update(style='emphasis', spacing='Small')
            elif k:
                column.update(separator=True, spacing='Medium')
            columns.append(column)
        rows.append({'type': 'ColumnSet', 'columns': columns, 'spacing': 'Medium'})
    return rows


def _cell(i, value, numeric, names=True):
    if i == 0 and names and not numeric:
        main, secondary = _name(value)
        items = [_rich(_run(main))]
        if secondary:
            items.append(_rich(_run(secondary, size='Small', isSubtle=True), spacing='None'))
        return items
    text = format(value, ',') if type(value) is int else value
    return [_rich(_run(text), align='Right' if numeric else None)]


def _numeric_columns(table):
    if 'numericColumns' in table:
        return tuple(table['numericColumns'])
    def numeric(v):
        return v is None or isinstance(v, str) and v.strip().lower() in {'not measured', 'unknown', 'n/a', '—'} or type(v) in {int, float} or isinstance(v, str) and bool(re.fullmatch(r'\s*(?:[A-Z]{3}\s*|[$£€¥])?[-+−]?[\d,]+(?:\.\d+)?(?:%|\s*pp)?\s*', v))
    return tuple(i for i in range(len(table['columns'])) if table['rows'] and any(r[i] is not None for r in table['rows']) and all(numeric(r[i]) for r in table['rows']))


def _card_table(columns, rows, numeric=None, names=True):
    """Actual numeric columns right-align; prose gets width and full selectable text."""
    if numeric is None:
        numeric = _numeric_columns({'columns': columns, 'rows': rows})
    widths = [1 if i in numeric else (2 if i == 0 else 4) for i in range(len(columns))]
    # Pure prose: first column is a short role, second is the actual action, not 3:1.
    if len(columns) == 2 and not numeric:
        widths = [1, 4]
        names = False
    head = {'type': 'ColumnSet', 'columns': [{'type': 'Column', 'width': widths[i], 'items': [_eyebrow(c, align='Right' if i in numeric else 'Left')]} for i, c in enumerate(columns)]}
    body = [{'type': 'ColumnSet', 'separator': True, 'columns': [{'type': 'Column', 'width': widths[i], 'items': _cell(i, v, i in numeric, names)} for i, v in enumerate(row)]} for row in rows]
    return {'type': 'Container', 'items': [head] + body}


def _scaled_track(value, maximum, prior=False):
    if value is None:
        return _rich(_run('Not measured', size='Small', isSubtle=True))
    fraction = value / maximum if maximum else 0
    # Supported theme-aware styles: current accent, prior emphasis, empty default.
    # Explicit labels/legend also distinguish series in monochrome/high contrast.
    empty = {'type': 'Column', 'width': max(0.000001, 1-fraction), 'style': 'default', 'items': [{'type': 'TextBlock', 'text': ' '}]}
    fill = {'type': 'Column', 'width': max(0.000001, fraction), 'style': 'emphasis' if prior else 'accent', 'items': [{'type': 'TextBlock', 'text': ' '}]}
    return {'type': 'ColumnSet', 'columns': [fill, empty] if value else [empty]}


def _mix_bars(table, compact=False):
    """Completed population counts: six rows, scaled tracks remain in compact/fallback."""
    maximum = max([r[1] or 0 for r in table['rows']] + [1])
    rows = []
    for label, value in table['rows'][:6]:
        fallback = _scaled_track(value, maximum)
        bar = fallback if compact or value is None else {'type': 'ProgressBar', 'value': round(100 * value / maximum), 'max': 100, 'fallback': fallback}
        rows.append({'type': 'ColumnSet', 'spacing': 'Small', 'columns': [
            {'type': 'Column', 'width': 2, 'items': [_rich(_run(_name(label)[0], size='Small', isSubtle=True))]},
            {'type': 'Column', 'width': 3, 'verticalContentAlignment': 'Center', 'items': [bar]},
            {'type': 'Column', 'width': 1, 'items': [_rich(_run(format(value, ',') if value is not None else 'Not measured', size='Small'), align='Right')]}]})
    return rows


def _funnel(data, details, compact=False):
    """Stepped-funnel header (label, value, delta, pill on the largest step drop) plus a monochrome
    current-vs-prior bar chart; exact-count table as fallback and on demand. The definition line
    goes to the details toggle when it's over the one-line budget."""
    if data['workflow'] == 'checkout-analysis':
        return _checkout_card_funnel(data, details, compact)
    stages = data['funnel']
    measured = [(i, s['count']) for i, s in enumerate(stages) if s['count'] is not None]
    drops = [(1 - measured[k][1] / measured[k - 1][1], measured[k][0]) for k in range(1, len(measured)) if measured[k - 1][1] and measured[k][1] <= measured[k - 1][1]]
    pill = None
    if drops:
        lost, at = max(drops)
        pill = (at, f'↓ {lost:.0%} step drop')
    steps = [{**s, 'value': s.get('display') or (format(s['count'], ',') if s['count'] is not None else 'Not measured')} for s in stages]
    head = ['Stage', 'Current', 'Prior', 'Rate']
    rows = [[s['label'], s['count'], s.get('prior'), s.get('display') or ''] for s in stages]
    if not any(s.get('display') for s in stages):
        head, rows = head[:3], [r[:3] for r in rows]
    counts = lambda: _card_table(head, rows, numeric=tuple(range(1, len(head))))
    # One hue, two shades: Cowork's render_ui rejects colorSet 'monochrome', so colour each series explicitly.
    series = [{'legend': 'Current sessions', 'color': 'sequential7', 'values': [{'x': s['label'], 'y': s['count']} for s in stages if s['count'] is not None]}]
    if any(s.get('prior') is not None for s in stages):
        series.append({'legend': 'Prior sessions', 'color': 'sequential3', 'values': [{'x': s['label'], 'y': s['prior']} for s in stages if s.get('prior') is not None]})
    out = [{'type': 'Container', 'separator': True, 'spacing': 'Medium', 'items': [_eyebrow('Purchase funnel')]}]
    if data.get('funnelContext'):
        shown, folded = _split(data['funnelContext'], LINE_CHARS)
        if folded:
            details.append(('Funnel', folded))
        else:
            out.append(_rich(_run(shown, size='Small', isSubtle=True), spacing='Small'))
    out += _stat_strip(steps, tiles=False, pill=pill)
    maximum = max([s.get(k) or 0 for s in stages for k in ('count', 'prior')] + [1])
    fallback = {'type': 'Container', 'items': []}
    for stage in stages:
        fallback['items'] += [_rich(_run(stage['label'] + ' · ' + (format(stage['count'], ',') if stage['count'] is not None else 'Not measured'), size='Small')), _scaled_track(stage['count'], maximum)]
        if stage.get('prior') is not None:
            fallback['items'] += [_rich(_run('Prior · ' + format(stage['prior'], ','), size='Small', isSubtle=True)), _scaled_track(stage['prior'], maximum, prior=True)]
    if compact:
        out.append(fallback)
    else:
        out.append({'type': 'Chart.VerticalBar.Grouped', 'title': 'Distinct sessions by funnel stage', 'data': series, 'fallback': fallback})
    out.append(_toggle('Show exact counts', 'noibu-funnel-counts'))
    out.append({**counts(), 'id': 'noibu-funnel-counts', 'isVisible': False})
    return out


def _checkout_card_funnel(data, details, compact=False):
    stages = data['funnel']
    out = [_eyebrow('Purchase funnel', spacing='Medium'), _rich(_run(data['funnelBasis']['note'], size='Small', isSubtle=True), spacing='Small')]
    if data.get('funnelContext'):
        details.append(('Source funnel notes — annotations only; calculated denominator above controls', data['funnelContext']))
    if not data['funnelBasis']['completionInMetrics']:
        out += _stat_strip([data['funnelBasis']['checkoutCompletion']], tiles=False, details=details)
    steps = [{**s, 'value': s.get('display', 'Not measured')} for s in stages]
    # Signed percentage-point differences are derived above, not count changes.
    # Keep the existing generic delta design untouched outside checkout.
    for stage in steps:
        stage.pop('change', None)
    out += _stat_strip(steps, tiles=False)
    maximum = max([100] + [s[k] for s in stages for k in ('rate', 'priorRate') if s[k] is not None])
    series = []
    for key, name, color in (('rate', 'Current % of own cart base', 'sequential7'), ('priorRate', 'Prior % of own cart base', 'sequential3')):
        values = [{'x': s['label'], 'y': s[key]} for s in stages if s[key] is not None]
        if values:
            series.append({'legend': name, 'color': color, 'values': values})
    fallback = {'type': 'Container', 'items': [_rich(_run('Legend: Current — accent fill · Prior — muted fill · Empty — unfilled', size='Small'))]}
    for stage in stages:
        current = f"{stage['rate']:.1f}%" if stage['rate'] is not None else 'Not measured'
        prior = f"{stage['priorRate']:.1f}%" if stage['priorRate'] is not None else 'Not measured'
        delta = stage.get('change', 'No measured delta') if stage.get('role') != 'added-to-cart' else 'Each cart base = 100% when measured'
        fallback['items'] += [_rich(_run(stage['label'] + ' · Current ' + current + ' · Prior ' + prior, size='Small')), _rich(_run(delta, size='Small', weight='Bolder')), _scaled_track(stage['rate'], maximum), _scaled_track(stage['priorRate'], maximum, prior=True)]
    if compact or not series:
        out.append(fallback)
    else:
        out += [_rich(_run(s['label'] + ' · Current ' + (f"{s['rate']:.1f}%" if s['rate'] is not None else 'Not measured') + ' · Prior ' + (f"{s['priorRate']:.1f}%" if s['priorRate'] is not None else 'Not measured') + ' · ' + s.get('change', 'Own cart base'), size='Small')) for s in stages]
        out.append({'type': 'Chart.VerticalBar.Grouped', 'title': '% of sessions that added to cart', 'yAxisTitle': '% of sessions that added to cart', 'yMin': 0, 'yMax': maximum, 'data': series, 'fallback': fallback})
    head = ['Stage', 'Current sessions', 'Prior sessions']
    rows = [[s['label'], s['count'], s.get('prior')] for s in stages]
    out += [_toggle('Show exact counts', 'noibu-funnel-counts'), {**_card_table(head, rows, numeric=(1, 2), names=False), 'id': 'noibu-funnel-counts', 'isVisible': False}]
    return out


def _vital(perf, compact=False):
    """Core Web Vitals: value + banded gauge (good/needs improvement/poor) with labelled cutoffs."""
    good, poor, unit = VITALS[perf['metric']]
    value = perf.get('value')
    fmt = lambda v: f'{v:g}' + (' ms' if unit == 'ms' else '')
    if value is None:
        return [_rich(_run(perf['metric'] + ' p75 not measured — no threshold marker.', isSubtle=True))]
    band = 'Good' if value <= good else 'Needs improvement' if value <= poor else 'Poor'
    reading = _rich(_run(fmt(value), size='Large', weight='Bolder'), _run(f'  p75 · {band}', size='Small', weight='Bolder', color={'Good': 'Good', 'Needs improvement': 'Warning', 'Poor': 'Attention'}[band]))
    top = poor * 2
    # Cowork render_ui schema: segments are sized widths ({size, legend, color}); valueFormat is Percentage|Fraction.
    gauge = {'type': 'Chart.Gauge', 'title': perf['metric'] + ' p75', 'value': min(value, top), 'min': 0, 'max': top, 'valueFormat': 'Fraction',
             'subLabel': 'p75 ' + ('ms' if unit == 'ms' else 'score'), 'showLegend': False,
             'segments': [{'size': good, 'color': 'good', 'legend': 'Good'}, {'size': poor - good, 'color': 'warning', 'legend': 'Needs improvement'}, {'size': top - poor, 'color': 'attention', 'legend': 'Poor'}],
             'fallback': 'drop'}
    legend = _rich(_run(f'Good ≤ {fmt(good)} · Needs improvement to {fmt(poor)} · Poor > {fmt(poor)}' + (f' · beyond the {fmt(top)} scale' if value > top else ''), size='Small', isSubtle=True))
    return [reading, legend] if compact else [reading, gauge, legend]


def _generated(value):
    """Footer time as people read it ("Nov 2, 2026, 9:00 pm UTC"), never an ISO timestamp."""
    made = timestamp(value)
    offset = made.utcoffset()
    zone = 'UTC' if not offset else 'UTC' + ('+' if offset.total_seconds() >= 0 else '−') + f'{abs(int(offset.total_seconds())) // 3600:02d}:{abs(int(offset.total_seconds())) % 3600 // 60:02d}'
    return f'{_MONTHS[made.month - 1]} {made.day}, {made.year}, {made.hour % 12 or 12}:{made.minute:02d} {"am" if made.hour < 12 else "pm"} {zone}'


LINK_BUTTONS = 2  # design/README.md 4.5: at most two Noibu link buttons per card


def _link_buttons(links):
    """Button-styled Noibu links at the foot of the card: verified console links only (validated upstream).
    Built as body elements with selectAction because render_ui receives the card body, not top-level actions."""
    columns = [{'type': 'Column', 'width': 'auto', 'style': 'emphasis', 'selectAction': {'type': 'Action.OpenUrl', 'url': link['url']},
                'items': [_rich(_run(link['label'] + ' ↗', size='Small', weight='Bolder', color='Accent'))]} for link in links[:LINK_BUTTONS]]
    return {'type': 'ColumnSet', 'spacing': 'Medium', 'columns': columns}


def _inline_link(link, spacing='Small'):
    return _rich(_run(link['label'] + ' ↗', size='Small', color='Accent', selectAction={'type': 'Action.OpenUrl', 'url': link['url']}), spacing=spacing)


def _details_block(details, target):
    # One "Label — text" paragraph per folded field, label in bold small caps.
    items = []
    for label, text in details:
        items.append(_eyebrow(label, spacing='Small'))
        items.append(_rich(_run(text, size='Small', isSubtle=True), spacing='None'))
    return _folded(target, items)


def render_adaptive_card(data, candidates=None, compact=False):
    """Adaptive Card 1.6; compact removes host extensions, not required checkout/segment data.
    Choose compact BEFORE the response's single render attempt, never retry after a failed render."""
    data = validate(data)
    if data.get('abView'):
        return _ab_card(data, candidates, compact)
    wf, chat = data['workflow'], data.get('host') == 'copilot-chat'
    outlined = wf in ANALYTICS
    window = data['window'].get('label', data['window']['start'] + ' – ' + data['window']['end'])
    caps = data.get('capabilities', {})

    # 1. Overview card, Claude-board density: one or two sentences, one short context line, value +
    # delta tiles, the funnel, tables. Every definition, KPI detail and long note is folded into
    # one "Details & definitions" toggle, so nothing is lost and the card stays scannable.
    fold_tables = wf in {'product-analysis', 'segment-analysis'}
    details = []
    overview = []
    if wf not in ANALYTICS | {'tech-diagnosis'}:
        # Analytics and technical reports put the summary in chat prose before the card
        # (design/README.md 2.1), so the card doesn't repeat it. Audits keep it in the card.
        summary, more = _split(data['summary'], SUMMARY_CHARS)
        overview.append(_rich(_run(summary), spacing='Small'))
        if more:
            details.append(('Summary', more))
    if data.get('overviewContext'):
        shown, folded = _split(data['overviewContext'], LINE_CHARS)
        if folded:
            details.append(('Window', folded))
        else:
            overview.append(_rich(_run(shown, size='Small', isSubtle=True), spacing='Small'))
    if wf == 'segment-analysis' and data.get('kpis'):
        overview.append(_eyebrow('Conversion rate', spacing='Medium'))
    overview += _stat_strip(data.get('kpis', []), tiles=wf != 'segment-analysis', details=details)
    if data.get('funnel'):
        overview += _funnel(data, details, compact)
    if data.get('highlights'):
        overview.append({'type': 'Container', 'separator': True, 'spacing': 'Medium', 'items': _stat_strip(data['highlights'], tiles=False, details=details)})
    tables = data.get('tables', [])
    if wf == 'tech-diagnosis' and data.get('findings'):
        # Deduplicate ONLY exact repeated next-check actions. Unique prose is retained wide/left.
        fixes = {' '.join(_prose(f.get('fix', '')).split()).casefold() for f in data['findings']}
        unique_tables = []
        for table in tables:
            if 'action' in table['title'].lower() and not _numeric_columns(table):
                rows = [row for row in table['rows'] if ' '.join(_prose(str(row[-1])).split()).casefold() not in fixes]
                if not rows:
                    continue
                table = {**table, 'rows': rows}
            unique_tables.append(table)
        tables = unique_tables
    limit = 3 if wf == 'segment-analysis' else 2
    shown_tables = [t for t in tables if t.get('placement') == 'overview'][:limit] or [t for t in tables if t.get('placement') != 'supporting'][:limit]
    if wf == 'checkout-analysis':
        # Always retain abandonment plus BOTH available method mixes, not the generic two-table cap.
        shown_tables = [t for t in tables if t.get('placement') == 'overview' or t.get('kind') == 'bars' and t.get('placement') != 'supporting']
    if compact and wf not in {'segment-analysis', 'checkout-analysis', 'product-analysis'}:
        shown_tables, tables = shown_tables[:1], shown_tables[:1]
    rows_shown = 5 if wf in {'segment-analysis', 'checkout-analysis', 'product-analysis'} else 3 if compact else 5
    def table_section(table, separator=True):
        # Design: the first column header doubles as the table title (no separate heading).
        if table.get('kind') == 'bars':
            section = [_eyebrow(table['title'])] + _mix_bars({**table, 'rows': _display_rows(table, 6)}, compact)
        else:
            section = [_card_table([table['title']] + table['columns'][1:], _display_rows(table, rows_shown), numeric=_numeric_columns(table), names=_row_kind(table) == 'name' and wf != 'product-analysis')]
        if wf == 'product-analysis' and table.get('kind') != 'bars' and len(table['rows']) > rows_shown:
            # Full original names and every row are available, even beyond the five-row preview.
            key = 'noibu-all-rows-' + str(tables.index(table))
            section += [_toggle(str(len(table['rows']) - rows_shown) + ' remaining rows · full names', key), _folded(key, [_card_table(table['columns'], table['rows'][rows_shown:], numeric=_numeric_columns(table), names=False)])]
        if table.get('note'):
            note, folded = _split(table['note'], LINE_CHARS)
            section.append(_rich(_run(note, size='Small', isSubtle=True), spacing='Small'))
            if folded:
                details.append((table['title'], folded))
        return {'type': 'Container', 'separator': separator, 'spacing': 'Medium', 'items': section}
    def mix_pair(pair):
        # Payment and delivery mixes side by side, as on the Claude checkout board.
        return {'type': 'ColumnSet', 'separator': True, 'spacing': 'Medium', 'columns': [{'type': 'Column', 'width': 'stretch', 'spacing': 'Large' if k else 'None', 'items': [{**table_section(t, separator=False), 'spacing': 'None'}]} for k, t in enumerate(pair)]}
    def sections(group, separator=True):
        bars = [t for t in group if t.get('kind') == 'bars']
        out = [table_section(t, separator) for t in group if t.get('kind') != 'bars']
        for k in range(0, len(bars), 2):
            out.append(mix_pair(bars[k:k + 2]) if len(bars[k:k + 2]) == 2 else table_section(bars[k], separator))
        return out
    supporting = [t for t in tables if t not in shown_tables]
    if fold_tables and shown_tables:
        overview.append(_toggle('Show more', 'noibu-overview-tables', align='Center', spacing='Medium'))
        overview.append(_folded('noibu-overview-tables', sections(shown_tables + supporting)))
    else:
        overview += sections(shown_tables)
        if supporting:
            overview.append(_toggle('Show more', 'noibu-supporting', align='Center'))
            overview.append(_folded('noibu-supporting', sections(supporting, separator=False)))
    for note in data.get('overviewNotes', []):
        shown, folded = _split(note, LINE_CHARS)
        overview.append({'type': 'Container', 'style': 'warning', 'spacing': 'Small', 'items': [_rich(_run(shown, size='Small'))]})
        if folded:
            details.append(('Data note', folded))
    overview += _comparison_card(data, details)
    if details:
        overview.append(_toggle('Details & definitions', 'noibu-details', spacing='Medium'))
        overview.append(_details_block(details, 'noibu-details'))
    body = [_card('Overview' if outlined else wf.replace('-', ' '), overview, meta=data['domain']['name'] + ' · ' + window, spacing='None')]

    # 2. Priority cards: design cap of 3, ranked as supplied. Technical diagnosis keeps the tested
    # baseline's merchant / performance / vendor sections, at most two cards each. Each card shows
    # the title and one evidence line; full evidence and the next check sit behind one toggle.
    findings = data.get('findings', [])
    monitoring = [f for f in findings if not _tech_priority(f)] if wf == 'tech-diagnosis' else []
    if wf == 'tech-diagnosis':
        findings = [f for f in findings if _tech_priority(f)]
        plan = []
        for category, title in [('merchant', 'Merchant issues'), ('performance', 'Performance'), ('vendor', 'Vendor issues'), (None, 'Other findings')]:
            group = [f for f in findings if f.get('category') == category][:2]
            plan += [(title if k == 0 else None, f) for k, f in enumerate(group)]
    else:
        plan = [(None, f) for f in findings[:3]]
    for n, (section, item) in enumerate(plan, 1):
        if section:
            body.append(_eyebrow(section, spacing='Large'))
        label = f'Priority {n}' + (' · ' + item['tag'] if item.get('tag') and item['tag'].lower() != f'priority {n}' else '')
        if item.get('performance'):
            label = item['performance']['metric'] + (' · ' + item['performance']['status'] if item['performance'].get('status') else '')
        impact = _prose(item.get('impact')) or None
        chip = impact if impact and len(impact) <= CHIP_CHARS else None
        evidence, full = _split(item['evidence'], 160)
        content = [_rich(_run(item['title'], size='Medium', weight='Bolder'))]
        if impact and not chip:
            short, _ = _split(impact, 180)
            content.append(_rich(_run(short, size='Small', weight='Bolder', isSubtle=True), spacing='Small'))
        content.append(_rich(_run(evidence, isSubtle=True), spacing='Small'))
        if item.get('performance'):
            content += _vital(item['performance'], compact)
        if item.get('gaugeNote'):
            content.append(_rich(_run(item['gaugeNote'], size='Small', isSubtle=True), spacing='Small'))
        folded = []
        if impact and not chip and len(impact) > 180:
            folded.append(_rich(_run('Impact ', size='Small', weight='Bolder'), _run(impact, size='Small'), spacing='Small'))
        if full:
            folded.append(_rich(_run(full, size='Small', isSubtle=True), spacing='Small'))
        if item.get('fix'):
            folded.append(_rich(_run('Next check ', size='Small', weight='Bolder'), _run(_prose(item['fix']), size='Small'), spacing='Small'))
        if folded:
            title = 'Next check' if item.get('fix') and (wf in {'checkout-analysis', 'tech-diagnosis'} or item.get('performance')) else 'Investigation & verification' if item.get('fix') else 'Full evidence'
            content.append(_toggle(title, f'noibu-finding-{n}'))
            content.append(_folded(f'noibu-finding-{n}', folded))
        if item.get('noibuLinks'):
            # Next steps live in the question after the card; the card only links into Noibu.
            content.append(_inline_link(item['noibuLinks'][0]))
        if compact and wf in {'segment-analysis', 'checkout-analysis'}:
            # Spend compact bytes on required five-row sections and measured evidence, not card chrome.
            if chip:
                content.insert(0, _rich(_run(chip, size='Small', isSubtle=True)))
            body.append({'type': 'Container', 'separator': True, 'spacing': 'Medium', 'items': [_eyebrow(label)] + content})
        else:
            body.append(_card(label, content, right=chip))
    if len(findings) > len(plan):
        extra = len(findings) - len(plan)
        body.append(_rich(_run(f'{extra} more ranked finding{"s are" if extra > 1 else " is"} in the full report.', size='Small', isSubtle=True), spacing='Small'))
    if not findings and wf in ANALYTICS | {'tech-diagnosis'}:
        body.append(_card('No priorities', [_rich(_run('No supported ranked priorities in this report; see comparison scope and coverage.', isSubtle=True))]))

    # A/B candidates as cards: title and one line visible; hypothesis and metric folded.
    for item in candidate_data(data, candidates)[:3]:
        what, _ = _split(item['what'], 160)
        content = [_rich(_run(item['title'], size='Medium', weight='Bolder')), _rich(_run(what, isSubtle=True), spacing='Small'),
                   _toggle('Hypothesis & metric', f'noibu-test-{item["rank"]}'),
                   _folded(f'noibu-test-{item["rank"]}', [_rich(_run('Hypothesis ', size='Small', weight='Bolder'), _run(_prose(item['hypothesis']), size='Small')), _rich(_run('Success metric ', size='Small', weight='Bolder'), _run(_prose(item['metric']), size='Small'), spacing='Small')])]
        body.append(_card(f'Test {item["rank"]}', content, meta=item['validation']))

    # Caveats (progressive disclosure), then the action bar card last.
    if monitoring or data.get('caveats'):
        body.append(_toggle('Evidence & coverage', 'noibu-caveats', spacing='Medium'))
        body.append({'type': 'Container', 'id': 'noibu-caveats', 'isVisible': False, 'items': [_rich(_run('• ' + _prose(c), size='Small', isSubtle=True)) for c in data.get('caveats', [])] + [_rich(_run('Monitor — ' + f['title'] + ': ' + _prose(f['evidence']) + ' Next check: ' + _prose(f.get('fix', 'Recheck if volume or critical impact rises.')), size='Small')) for f in monitoring]})
    # Report-level Noibu links: the first two become the card's buttons, any others stay as inline links.
    report_links = data.get('noibuLinks', [])
    if len(report_links) > LINK_BUTTONS:
        body.append(_eyebrow('More in Noibu', spacing='Medium'))
        body += [_inline_link(link, spacing='None') for link in report_links[LINK_BUTTONS:]]
    # No action bar: download, schedule and save are offered by the next-step question after the card.
    if report_links:
        body.append(_link_buttons(report_links))
    body.append(_rich(_run('Generated ' + _generated(data['generatedAt']) + ' · ' + _comparison(data), size='Small', isSubtle=True), spacing='Medium'))

    # Cowork's render_ui takes {type, version '1.6', body}; no $schema, and ActionSet is folded into Accordions.
    card = {'type': 'AdaptiveCard', 'version': '1.6', 'fallbackText': _prose(data['summary']), 'body': _accordionize(body)}
    if compact and wf == 'checkout-analysis':
        # Compact spends bytes on evidence, comparisons and the exact-count table,
        # not repeated optional typography/chrome. No content/rows are removed.
        def quiet(node):
            if isinstance(node, list):
                return [quiet(v) for v in node]
            if not isinstance(node, dict):
                return node
            return {k: quiet(v) for k, v in node.items() if not (
                k == 'spacing' and v in {'Small', 'None'} or
                k == 'size' and v == 'Small' or
                k == 'weight' and v == 'Bolder' or
                k == 'isSubtle' and v is True or
                                k == 'horizontalAlignment' and v == 'Left' or
                k == 'verticalContentAlignment' and v in {'Top', 'Center'} or
                k in {'showBorder', 'roundedCorners', 'bleed'} and v is True)}
        card = quiet(card)
    problems = _cowork_check(card)
    require(not problems, 'Adaptive Card would be rejected by Cowork render_ui: ' + '; '.join(problems[:5]))
    encoded = json.dumps(card, ensure_ascii=False, separators=(',', ':'))
    if len(encoded.encode()) > CARD_LIMIT:
        raise CardSizeError(f'Adaptive Card is {len(encoded.encode())} bytes; reduce rows/findings (limit {CARD_LIMIT})')
    return card



def _validate_ab_view(data, domain):
    view = data['abView']
    require(data['workflow'] in AB_WORKFLOWS and isinstance(view, dict) and view.get('kind') in {'findings', 'test', 'implement'}, 'abView belongs to the A/B workflow')
    allowed = {'findings': {'kind', 'liveSiteCheck'}, 'test': {'kind', 'rank', 'reportFile'}, 'implement': {'kind', 'rank', 'draftId', 'flagKey', 'state'}}[view['kind']]
    require(set(view) <= allowed, 'Invalid abView fields')
    if view['kind'] != 'findings':
        require(type(view.get('rank')) is int and view['rank'] > 0, 'abView needs a candidate rank')
    if view['kind'] == 'implement':
        require(isinstance(view.get('draftId'), str) and re.fullmatch(r'[0-9]{1,18}', view['draftId']), 'Implement card needs the numeric Noibu test id from the create/list result')
        require(text(view.get('flagKey'), 200) and view.get('state') in {'created', 'existing'}, 'Implement card needs flag key and created/existing state')
        require(domain.get('id'), 'Implement card needs the domain UUID for its console link')
    require('reportFile' not in view or isinstance(view['reportFile'], str) and re.fullmatch(r'[A-Za-z0-9._-]{1,120}\.html', view['reportFile']), 'Invalid report file name')
    require(view.get('liveSiteCheck', 'performed') in {'performed', 'partial', 'not-performed'}, 'Invalid live-site check state')


AB_WHAT_CHARS, AB_WHY_CHARS = 260, 320


def _ab_numbers(numbers):
    parts = []
    for key, value in list(numbers.items())[:4]:
        label = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', str(key)).replace('_', ' ').lower()
        shown = f'{value:,}' if isinstance(value, int) and not isinstance(value, bool) else str(value)
        parts.append(f'{label} {shown}')
    return ' · '.join(parts)


def _ab_text(label, value, limit, key, compact):
    """Eyebrow + one block; text over budget shows its first sentence(s), the rest folded, never dropped."""
    shown, more = _split(value, limit)
    out = [_eyebrow(label, spacing='Small'), _rich(_run(shown), spacing='None')]
    if more:
        out += [_toggle('Full text', key), _folded(key, [_rich(_run(more, size='Small', isSubtle=True))])]
    return out


def _ab_card(data, candidates, compact=False):
    """A/B chat cards (ab-testing skill): findings (one block per test), one test's report, or the
    implement card once a draft exists. Cowork card buttons can't post back to the chat (tenant test
    2026-10-28), so next steps are the AskUserQuestion after the card (design/README.md section 5)."""
    view = data['abView']
    items = candidate_data(data, candidates)
    require(items, 'A/B cards need the validated candidates file')
    n = len(items)
    domain = data['domain']['name']
    window = data['window'].get('label', data['window']['start'] + ' – ' + data['window']['end'])
    by_rank = {item['rank']: item for item in items}
    body = []
    live = view.get('liveSiteCheck') or {'none': 'not-performed', None: 'not-performed'}.get(items[0]['report'].get('browser'), 'performed')
    if view['kind'] == 'findings':
        require(n <= 6, 'The findings card shows at most six tests; rank and trim the list first')
        head = [_rich(_run(domain + ' · ' + window, size='Small', isSubtle=True), spacing='None')]
        goal = items[0]['report'].get('goal')
        if goal:
            head.append(_rich(_run('Goal: ' + goal, size='Small'), spacing='Small'))
        if live == 'not-performed':
            head.append({'type': 'Container', 'style': 'warning', 'spacing': 'Small', 'items': [_rich(_run('Live site not checked: these ideas rest on Noibu data alone; structural claims are inferred.', size='Small'))]})
        body.append(_card('A/B test opportunities', head, spacing='None'))
        for item in items:
            report = item['report']
            content = [_eyebrow('What to change'), _rich(_run(item['title'], size='Medium', weight='Bolder'), spacing='None')]
            what, more = _split(item['what'], AB_WHAT_CHARS)
            content.append(_rich(_run(what, isSubtle=True), spacing='Small'))
            if report.get('why'):
                content += _ab_text('Why this test', report['why'], AB_WHY_CHARS, f'noibu-ab-why-{item["rank"]}', compact)
            if more:
                content += [_toggle('Full change', f'noibu-ab-what-{item["rank"]}'), _folded(f'noibu-ab-what-{item["rank"]}', [_rich(_run(more, size='Small', isSubtle=True))])]
            if compact:
                body.append({'type': 'Container', 'separator': True, 'spacing': 'Medium', 'items': [_eyebrow(f'Test {item["rank"]}')] + content})
            else:
                body.append(_card(f'Test {item["rank"]}', content))
        made = timestamp(data['generatedAt'])
        footer = f'Generated {_MONTHS[made.month - 1]} {made.day}, {made.year} · nothing is created in Noibu until you choose a test'
    elif view['kind'] == 'test':
        require(view['rank'] in by_rank, 'No candidate with that rank')
        item = by_rank[view['rank']]
        report = item['report']
        setup = report.get('setup', {})
        content = [_rich(_run(item['title'], size='Medium', weight='Bolder'), spacing='None')]
        if report.get('surface'):
            content.append(_rich(_run(report['surface'], size='Small', isSubtle=True), spacing='None'))
        content += _ab_text('What to change', item['what'], AB_WHAT_CHARS, 'noibu-ab-what', compact)
        if report.get('why'):
            content += _ab_text('Why this test', report['why'], AB_WHY_CHARS, 'noibu-ab-why', compact)
        variant = next((v for v in report.get('handoffVariations', []) if not v.get('isControl')), {})
        preview = variant.get('preview') or {}
        name = report.get('variationName') or variant.get('name') or 'Variation B'
        if preview.get('before') and preview.get('after'):
            shot = 'Before and after screenshots are in the report file' + (' (captured on desktop; mobile layout inferred).' if preview.get('viewport') != 'narrow-desktop-window' else ' (narrow desktop window, not a phone).')
        elif preview.get('kind') == 'preview-theme':
            shot = 'Shown on an unpublished Shopify preview theme; nothing on the live store changed.'
        else:
            shot = 'No screenshot: ' + (preview.get('note') or 'this session could not change the page to show the variation') + '. The change is described above.'
        content += [_eyebrow('Before and after', spacing='Small'), _rich(_run('B: ' + name, weight='Bolder'), spacing='None'), _rich(_run(shot, size='Small', isSubtle=True), spacing='None')]
        evidence = item['evidence'][:3]
        if evidence:
            content.append(_eyebrow('Evidence', spacing='Small'))
            for e in evidence:
                line = _prose(e['claim']) + ' (' + _ab_numbers(e['numbers']) + ')' + (' · correlational' if e.get('correlational') else '')
                content.append(_rich(_run('• ' + line, size='Small'), spacing='None'))
        rows = [('Title', setup.get('title', item['title'])), ('Hypothesis', setup.get('hypothesis', item['hypothesis'])), ('Success metric', setup.get('successMetric', item['metric'])),
                ('Traffic for this metric', report.get('metricVolume')), ('Secondary metrics', setup.get('secondaryMetrics', 'None')), ('Targeting', setup.get('targeting', 'Everyone (skip this section)')), ('Variations', setup.get('variations'))]
        content.append(_eyebrow('Set it up in Noibu', spacing='Small'))
        content += [_rich(_run(label + ' ', size='Small', weight='Bolder'), _run(_prose(value), size='Small'), spacing='None') for label, value in rows if value]
        if report.get('fixFirst'):
            content.append({'type': 'Container', 'style': 'warning', 'spacing': 'Small', 'items': [_rich(_run('Fix first ', size='Small', weight='Bolder'), _run(_prose(report['fixFirst']), size='Small'))]})
        if report.get('overlap'):
            content.append(_rich(_run('Overlap ', size='Small', weight='Bolder'), _run(_prose(report['overlap']), size='Small'), spacing='Small'))
        folded = []
        if variant.get('devNotes'):
            folded.append(_rich(_run(_prose(variant['devNotes']), size='Small')))
        for step in report.get('consoleFollowUps', []):
            folded.append(_rich(_run('In the Noibu console after creating: ' + _prose(step), size='Small', isSubtle=True), spacing='Small'))
        if folded:
            content += [_toggle('Dev notes', 'noibu-ab-dev'), _folded('noibu-ab-dev', folded)]
        if report.get('outsideGoal') and not compact:
            content += [_toggle('Outside your goal', 'noibu-ab-outside'), _folded('noibu-ab-outside', [_rich(_run('• ' + _prose(x), size='Small')) for x in report['outsideGoal']])]
        notes = report.get('runCaveats', []) + data.get('caveats', [])
        if notes:
            content += [_toggle('Run notes', 'noibu-ab-notes'), _folded('noibu-ab-notes', [_rich(_run('• ' + _prose(x), size='Small', isSubtle=True)) for x in dict.fromkeys(notes)])]
        file_name = view.get('reportFile') or report.get('reportFile')
        if file_name:
            content.append(_rich(_run('Full report file: ' + file_name, size='Small', isSubtle=True), spacing='Small'))
        body.append(_card(f'Test {item["rank"]} of {n} · {domain}', content, spacing='None'))
        footer = 'Recommendation only · previews are approximations · creating a test makes a draft that serves no traffic'
    else:
        require(view['rank'] in by_rank, 'No candidate with that rank')
        item = by_rank[view['rank']]
        url = f"https://console.noibu.com/{data['domain']['id']}/ab-tests/{view['draftId']}"
        validate_links([{'label': 'Open draft in Noibu', 'url': url, 'source': 'noibu_create_ab_test/noibu_list_ab_tests result id'}], data['domain']['id'])
        lead = 'Created in Noibu' if view['state'] == 'created' else 'Already in Noibu'
        content = [_rich(_run(item['title'], size='Medium', weight='Bolder'), spacing='None'),
                   _rich(_run('Draft ' + view['draftId'], color='Accent', selectAction={'type': 'Action.OpenUrl', 'url': url}), _run(' · flag key ' + view['flagKey']), spacing='Small'),
                   _rich(_run("It serves no traffic until it's started, and its variation code has to be live first. I can automate that: write the code with Noibu's snippet in it, open a pull request, and take it all the way to a live test. Nothing goes live without your approval.", isSubtle=True), spacing='Small'),
                   _link_buttons([{'label': 'Open draft in Noibu', 'url': url}])]
        body.append(_card(f'{lead} · Test {item["rank"]}', content, spacing='None'))
        footer = None
    if footer:
        body.append(_rich(_run(footer, size='Small', isSubtle=True), spacing='Small'))
    card = {'type': 'AdaptiveCard', 'version': '1.6', 'fallbackText': _prose(data['summary']), 'body': _accordionize(body)}
    problems = _cowork_check(card)
    require(not problems, 'Adaptive Card would be rejected by Cowork render_ui: ' + '; '.join(problems[:5]))
    encoded = json.dumps(card, ensure_ascii=False, separators=(',', ':'))
    if len(encoded.encode()) > CARD_LIMIT:
        raise CardSizeError(f'Adaptive Card is {len(encoded.encode())} bytes; reduce rows/findings (limit {CARD_LIMIT})')
    return card


COMPARISON_MODES = {'snapshot', 'previous-period', 'within-window', 'mixed'}
COMPARISON_DETAIL_KEYS = ('acquisition', 'currentWindow', 'priorWindow', 'metrics', 'priorUnavailableReason')
COMPARISON_ROW_KEYS = {'metric', 'cohort', 'percentile', 'unit', 'current', 'prior', 'currentCoverage', 'priorCoverage'}


class _ComparisonGap(ValueError):
    """Internal: a structured comparison that cannot be shown. Its text is plain language for the card."""


def _gap(condition, reason):
    if not condition:
        raise _ComparisonGap(reason)


def _normalize_comparison(data):
    """21.1.15: comparison problems NEVER block a card.
    - absent or label-only: render normally; the footer uses the label (or the truthful default);
    - simplified {mode,label,currentWindow?,priorWindow?,metrics?,priorUnavailableReason?} or the
      receipt form {..., acquisition}: when valid, the "Current vs previous period" section renders;
    - malformed/incomplete structured details: ONLY that section is omitted and a short in-card note
      says why, in plain words. Prior values are never invented and validator text is never shown.
    Prior-period acquisition stays a query-guidance requirement (comparison-acquisition.md), not a gate.
    """
    c = data.get('comparison')
    if c is None:
        data.pop('comparison', None)
        return
    base = {}
    if isinstance(c, dict):
        if text(c.get('label'), 1000):
            base['label'] = c['label']
        if c.get('mode') in COMPARISON_MODES:
            base['mode'] = c['mode']
    try:
        _gap(isinstance(c, dict), 'the comparison block was not in a recognised format')
        unknown = set(c) - {'mode', 'label'} - set(COMPARISON_DETAIL_KEYS)
        detailed = any(k in c for k in COMPARISON_DETAIL_KEYS)
        if not detailed and not unknown:
            data['comparison'] = base
            return
        _gap(not unknown, 'the comparison block had fields this release does not recognise')
        _gap('mode' in base, 'the comparison mode was not one of snapshot, previous-period, within-window or mixed')
        if 'acquisition' in c:
            data['comparison'] = {**base, **_receipt_comparison(data, c)}
        else:
            data['comparison'] = {**base, **_simple_comparison(data, c)}
    except _ComparisonGap as gap:
        data['comparison'] = {**base, 'omitted': str(gap)}
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        data['comparison'] = {**base, 'omitted': 'the comparison details were not in a recognised format'}


def _comparison_windows(data, c, required):
    if not required and 'currentWindow' not in c and 'priorWindow' not in c:
        return {}
    current, prior = c.get('currentWindow'), c.get('priorWindow')
    def dates(w):
        _gap(isinstance(w, dict) and {'start', 'end'} <= set(w) <= {'start', 'end', 'label'}, 'the current and prior windows were incomplete')
        try:
            start, end = timestamp(w['start']), timestamp(w['end'])
        except (ValueError, TypeError, AttributeError):
            raise _ComparisonGap('the current and prior windows were not valid dates with a timezone')
        _gap(start < end, 'a comparison window ended before it started')
        return start, end
    cs, ce = dates(current); ps, pe = dates(prior)
    _gap(ce - cs == pe - ps and pe == cs, 'the prior window did not immediately precede an equal-length current window')
    _gap(cs == timestamp(data['window']['start']) and ce == timestamp(data['window']['end']), 'the current comparison window did not match the report window')
    return {'currentWindow': {'start': current['start'], 'end': current['end']}, 'priorWindow': {'start': prior['start'], 'end': prior['end']}}


def _comparison_rows(rows, strict):
    _gap(isinstance(rows, list), 'the comparison metrics were not a list')
    _gap(len(rows) <= 12, 'the comparison listed more than 12 metrics')
    required = COMPARISON_ROW_KEYS if strict else {'metric', 'cohort', 'unit', 'current', 'prior'}
    identities, out = set(), []
    for r in rows:
        _gap(isinstance(r, dict) and required <= set(r) <= COMPARISON_ROW_KEYS, 'a comparison metric was incomplete (each needs metric, cohort, unit, current and prior)')
        _gap(all(text(r[k], 1000) for k in ('metric', 'cohort', 'unit')) and all(k not in r or text(r[k], 1000) for k in ('percentile', 'currentCoverage', 'priorCoverage')), 'a comparison metric was missing its name, cohort, unit or coverage text')
        _gap(all(r[k] is None or type(r[k]) in {int, float} and math.isfinite(r[k]) for k in ('current', 'prior')), 'comparison values must be measured numbers or empty (null)')
        if r['metric'] in VITALS:
            _gap(r.get('percentile') == 'p75' and r['unit'] == VITALS[r['metric']][2], 'Core Web Vitals comparisons need p75 values in ms (LCP, INP) or as a score (CLS)')
        key = tuple(r.get(k) for k in ('metric', 'cohort', 'percentile', 'unit'))
        _gap(key not in identities, 'the same metric and cohort appeared twice')
        identities.add(key)
        out.append(dict(r))
    return out


def _check_performance_values(data, rows):
    """A gauge and its comparison row must not disagree about the CURRENT value."""
    for value in [f['performance'] for f in data.get('findings', []) if f.get('performance')]:
        parts = [value.get('page') or value.get('pageGroup'), value.get('device')]
        matches = [r for r in rows if r['metric'] == value['metric'] and r['unit'] == value['unit'] and r.get('percentile', value['percentile']) == value['percentile'] and all(not v or v in r['cohort'] for v in parts)]
        if len(matches) == 1 and value.get('value') is not None and matches[0]['current'] is not None:
            _gap(matches[0]['current'] == value['value'], 'the current values in the comparison did not match the values shown in the findings')


def _simple_comparison(data, c):
    _gap(c['mode'] != 'snapshot' or not c.get('metrics'), 'a snapshot cannot carry prior-period metrics')
    out = _comparison_windows(data, c, required=False)
    rows = _comparison_rows(c.get('metrics', []), strict=False)
    if 'priorUnavailableReason' in c:
        _gap(text(c['priorUnavailableReason'], 1000), 'the reason the prior period was unavailable was empty')
        out['priorUnavailableReason'] = c['priorUnavailableReason']
    _check_performance_values(data, rows)
    if rows:
        out['metrics'] = rows
    return out


def _receipt_comparison(data, c):
    """The 21.1.13 receipt form, unchanged in meaning, but a failure omits only this section."""
    a = c['acquisition']
    _gap(isinstance(a, dict) and {'requested', 'performed', 'unavailable', 'queries'} <= set(a) <= {'requested', 'performed', 'unavailable', 'queries', 'reason'}, 'the prior-period query record was incomplete')
    _gap(all(type(a[k]) is bool for k in ('requested', 'performed', 'unavailable')) and isinstance(a['queries'], list), 'the prior-period query record was incomplete')
    _gap('priorUnavailableReason' not in c or text(c['priorUnavailableReason'], 1000), 'the reason the prior period was unavailable was empty')
    extra = {'priorUnavailableReason': c['priorUnavailableReason']} if 'priorUnavailableReason' in c else {}
    if c['mode'] == 'snapshot':
        _gap(not a['requested'] and not a['performed'] and not a['unavailable'] and not a['queries'] and text(a.get('reason')) and 'user' in a['reason'].lower() and 'snapshot' in a['reason'].lower(), 'the snapshot exception did not record that a snapshot was explicitly requested')
        _gap(not c.get('metrics'), 'a snapshot cannot carry prior-period metrics')
        return {'acquisition': a, **extra}
    _gap(a['requested'] and a['performed'], 'the record says the prior period was not queried')
    out = _comparison_windows(data, c, required=True)
    rows = _comparison_rows(c.get('metrics', []), strict=True)
    _gap(rows, 'no current and prior metric values were supplied')
    receipts = a['queries']
    for r in rows:
        for period in ('current', 'prior'):
            matches = [q for q in receipts if isinstance(q, dict) and all(q.get(k) == r[k] for k in ('metric', 'cohort', 'percentile', 'unit')) and q.get('period') == period]
            _gap(len(matches) == 1, 'some prior-period query receipts were missing or did not match the metric rows')
            q = matches[0]
            _gap(set(q) <= {'metric', 'cohort', 'percentile', 'unit', 'period', 'window', 'status', 'source', 'reason'} and text(q.get('source')) and q.get('window') == out[period + 'Window'], 'some query receipts lacked a source or used a different window')
            _gap(q.get('status') in {'completed', 'unavailable'}, 'some query receipts had an unknown status')
            _gap((q['status'] == 'completed' and r[period] is not None) or (q['status'] == 'unavailable' and r[period] is None and text(q.get('reason'))), 'a missing value had no recorded reason, or a recorded value had no completed query')
    _gap(len(receipts) == 2 * len(rows), 'there were query receipts that did not match any metric row')
    missing = any(q['status'] == 'unavailable' for q in receipts)
    _gap(a['unavailable'] == missing and (not missing or text(a.get('reason'))), 'an unavailable prior period had no recorded reason')
    _check_performance_values(data, rows)
    return {**out, 'metrics': rows, 'acquisition': a, **extra}


def _display_copy(value, key=None):
    """Display-only recursion: never mutate raw evidence or verified URL targets."""
    if isinstance(value, str):
        return value if key == 'url' else _clean(value)
    if isinstance(value, list):
        return [_display_copy(v) for v in value]
    if isinstance(value, dict):
        return {k: _display_copy(v, k) for k, v in value.items()}
    return value


def _comparison_fmt(row):
    fmt = lambda v: 'Not measured' if v is None else f'{v:g}'
    delta = 'Not measured' if row['current'] is None or row['prior'] is None else f"{row['current']-row['prior']:+g}" + (' pp' if row['unit'] == '%' else ' ' + row['unit'])
    name = row['metric'] + (' ' + row['percentile'] if row.get('percentile') else '')
    return name, fmt(row['current']) + ' ' + row['unit'], fmt(row['prior']) + ' ' + row['unit'], delta


def _comparison_coverage(row):
    parts = [('current ' + row['currentCoverage']) if row.get('currentCoverage') else None, ('prior ' + row['priorCoverage']) if row.get('priorCoverage') else None]
    parts = [p for p in parts if p]
    return row['cohort'] + (' — Coverage: ' + '; '.join(parts) if parts else '')


def _comparison_coverage_html(row):
    parts = [label + row[key] for label, key in (('Current coverage: ', 'currentCoverage'), ('Prior coverage: ', 'priorCoverage')) if row.get(key)]
    return _comparison_fmt(row)[0] + ' · ' + row['cohort'] + (' — ' + '; '.join(parts) if parts else '')


OMITTED_COMPARISON = 'Prior-period details were not shown because {}. Other figures are unaffected; no prior values were filled in.'


def _comparison_html(data):
    """Standalone/widget export carries the SAME normalized comparison, not just footer text."""
    c = data.get('comparison') or {}
    a = c.get('acquisition')
    if c.get('omitted'):
        return '<section class="noibu-table-section noibu-period-comparison"><h3>Comparison coverage</h3><p>' + escape(OMITTED_COMPARISON.format(c['omitted'])) + '</p></section>'
    if not a and not c.get('metrics') and not c.get('priorUnavailableReason'):
        return ''
    title = 'Current vs previous period' if c.get('metrics') or c.get('mode') != 'snapshot' else 'Snapshot scope'
    parts = ['<section class="noibu-table-section noibu-period-comparison"><h3>' + title + '</h3>']
    if a and a.get('reason'):
        parts.append('<p>' + escape(a['reason']) + '</p>')
    if c.get('priorUnavailableReason'):
        parts.append('<p>' + escape('Prior period not available: ' + c['priorUnavailableReason']) + '</p>')
    if c.get('currentWindow'):
        parts.append('<p>Current ' + escape(_reader_window(c['currentWindow'])) + ' · Prior ' + escape(_reader_window(c['priorWindow'])) + '</p>')
    elif c.get('metrics') and c.get('label'):
        parts.append('<p>' + escape(c['label']) + '</p>')
    if c.get('metrics'):
        parts.append(render_table({'title': 'Measured comparison', 'columns': ['Metric', 'Current', 'Prior', 'Delta'], 'rows': [list(_comparison_fmt(r)) for r in c['metrics']], 'numericColumns': [1, 2, 3]}))
        parts.append('<details><summary>Comparison coverage' + (' &amp; exact windows' if c.get('currentWindow') else '') + '</summary><ul>' + ''.join('<li>' + escape(_comparison_coverage_html(r)) + '</li>' for r in c['metrics']) + '</ul>')
        if c.get('currentWindow'):
            parts.append('<p>' + escape('Exact current ' + c['currentWindow']['start'] + ' – ' + c['currentWindow']['end'] + '; exact prior ' + c['priorWindow']['start'] + ' – ' + c['priorWindow']['end']) + '</p>')
    else:
        parts.append('<details><summary>Comparison coverage</summary>')
    if a:
        parts.append('<p>' + escape('Acquisition requested=' + str(a['requested']).lower() + '; performed=' + str(a['performed']).lower() + '; unavailable=' + str(a['unavailable']).lower()) + '</p>')
    parts.append('</details></section>')
    return ''.join(parts)


def _reader_window(window):
    start, end = timestamp(window['start']), timestamp(window['end'])
    def short(value):
        label = _MONTHS[value.month-1] + f' {value.day}, {value.year}'
        if value.hour or value.minute or value.second or value.microsecond:
            label += f' {value.hour:02d}:{value.minute:02d}'
        return label
    zone = lambda value: 'UTC' if value.utcoffset().total_seconds() == 0 else value.strftime('%z')
    zones = zone(start) if zone(start) == zone(end) else zone(start) + ' / ' + zone(end)
    return short(start) + ' – ' + short(end) + ' (' + zones + ')'


def _comparison_card(data, details=None):
    c = data.get('comparison') or {}
    a = c.get('acquisition')
    if c.get('omitted'):
        # Only the structured comparison is dropped; the reason is plain language, never validator text.
        return [_eyebrow('Comparison coverage', spacing='Medium'), _rich(_run(OMITTED_COMPARISON.format(c['omitted']), size='Small', isSubtle=True))]
    if not a and not c.get('metrics') and not c.get('priorUnavailableReason'):
        return []
    out = [_eyebrow('Current vs previous period' if c.get('metrics') or c.get('mode') != 'snapshot' else 'Snapshot scope', spacing='Medium')]
    if a:
        state = 'requested=' + str(a['requested']).lower() + ' · performed=' + str(a['performed']).lower() + ' · unavailable=' + str(a['unavailable']).lower()
        if details is not None:
            details.append(('Acquisition evidence', state))
        else:
            out.append(_rich(_run(state, size='Small', isSubtle=True)))
        if a.get('reason'):
            out.append(_rich(_run(a['reason'], size='Small')))
    if c.get('priorUnavailableReason'):
        out.append(_rich(_run('Prior period not available: ' + c['priorUnavailableReason'], size='Small')))
    if c.get('currentWindow'):
        out.append(_rich(_run('Current ' + _reader_window(c['currentWindow']) + ' · Prior ' + _reader_window(c['priorWindow']), size='Small')))
    elif c.get('metrics') and c.get('label'):
        out.append(_rich(_run(c['label'], size='Small')))
    for r in c.get('metrics', []):
        name, current, prior, delta = _comparison_fmt(r)
        out.append(_rich(_run(name, size='Small', weight='Bolder')))
        out.append(_rich(_run('Current ' + current + ' · Prior ' + prior + ' · Delta ' + delta, size='Small')))
        coverage = _comparison_coverage(r)
        if details is not None:
            details.append((r['metric'] + ' cohort & coverage', coverage))
        else:
            out.append(_rich(_run(coverage, size='Small')))
        if r['current'] is None or r['prior'] is None:
            reason = (r.get('priorCoverage') if r['prior'] is None else r.get('currentCoverage')) or c.get('priorUnavailableReason') or 'no reason was recorded'
            out.append(_rich(_run('Unavailable: ' + reason, size='Small')))
    return out


def _tech_priority(f):
    if f.get('priorityJustification'):
        return True
    if f.get('disposition') == 'monitor':
        return False
    if f.get('category') == 'vendor' and re.search(r'\bmonitor\b|low.volume', f.get('title', '') + ' ' + f.get('tag', ''), re.I):
        return False
    er = f.get('errorRecency')
    if er and (er['events'] <= 10 or er['lastSeenHours'] > 48):
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidates', type=Path)
    parser.add_argument('--standalone', action='store_true')
    parser.add_argument('--format', choices=['html', 'adaptive-card'], default='html', help='adaptive-card writes Adaptive Card JSON for Cowork\'s built-in Adaptive Cards skill')
    parser.add_argument('--compact', action='store_true', help='with --format adaptive-card: smaller retry card (standard elements only) for when the full card does not display')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text())
        candidates = json.loads(args.candidates.read_text()) if args.candidates else None
        output = json.dumps(render_adaptive_card(data, candidates, args.compact), ensure_ascii=False, indent=1) if args.format == 'adaptive-card' else render(data, candidates, args.standalone)
    except (ValueError, TypeError, KeyError) as error:
        parser.exit(1, f'Invalid presentation: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output)
    kind = 'Adaptive Card' if args.format == 'adaptive-card' else 'standalone snapshot' if args.standalone else 'inline board'
    print(f'Created {kind}: {args.output}; no external action executed')

if __name__ == '__main__':
    main()
