"""Validate the Noibu A/B handoff without network calls or Noibu mutations.

Accepts `noibu.ab-candidates/2` (unchanged 21.1.x rules) and `noibu.ab-candidates/3`, the
ab-testing skill's chat-scoped handoff: every /2 rule plus the finder fields the build half
reads (surfaces, readiness incl. splitCheckout, killed, existingTests, selectors, siteFacts,
consoleFollowUps, overlap/fixFirst ...). The createInput hash (sorted keys, compact separators,
UTF-8, Unicode preserved) is the same for both versions.
"""
import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

PRIMARY = {'ADD_TO_CART_RATE', 'CHECKOUT_CONVERSION_RATE', 'PAGE_VIEW_TO_URL_RATE'}
GUARDRAILS = PRIMARY | {'AVERAGE_ORDER_VALUE'}
PAGE_SCOPED = {'PAGE_VIEW_TO_URL_RATE'}
CONSOLE_EXCLUDED = {'REVENUE_PER_SESSION'}  # accepted by the MCP, absent from the console create screen
CREATE_FIELDS = {'title', 'hypothesis', 'successMetric', 'secondaryMetrics', 'deviceTypes', 'utmConditions', 'variations'}
ROOT_V2 = {'schema', 'generatedAt', 'domain', 'domainId', 'goal', 'window', 'tests', 'caveats'}
ROOT_V3 = ROOT_V2 | {'successMetricLabel', 'dataLine', 'captureLine', 'platform', 'testingTools', 'storefront', 'surfaces',
                     'cartState', 'couldNotComplete', 'outsideGoal', 'killed', 'companyId', 'siblings', 'market', 'readiness',
                     'existingTests', 'browser', 'previewBrowsers', 'reportFiles', 'catalogue', 'liveSiteCheck'}
TEST_V3_REQUIRED = {'rank', 'title', 'what', 'why', 'hypothesis', 'createInput', 'validation', 'evidence', 'setup', 'variations', 'overlap', 'fixFirst'}
TEST_V3 = TEST_V3_REQUIRED | {'surface', 'surfaceTemplate', 'successMetric', 'metricVolume', 'siteFacts', 'consoleFollowUps', 'reportFile', 'origin', 'variationName'}
BROWSERS = {'edge', 'none', 'built-in', 'chrome'}
TEMPLATES = {None, 'home', 'collection', 'product', 'cart', 'checkout', 'search', 'landing', 'other'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def timestamp(value):
    require(text(value), 'Timestamp must be a nonempty string')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp must include a timezone')
    return result


def create_hash(create_input):
    """SHA-256 of canonical createInput JSON: sorted keys, compact separators, UTF-8, Unicode preserved."""
    return hashlib.sha256(json.dumps(create_input, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def catalogue_sets(value=None):
    """The metric catalogue read from the noibu_create_ab_test schema at run time, or the last-known one."""
    if value is None:
        return PRIMARY, GUARDRAILS, PAGE_SCOPED
    require(isinstance(value, dict) and set(value) <= {'primary', 'secondary', 'pageScoped', 'maxSecondary', 'source'}, 'Invalid catalogue')
    sets = []
    for key in ('primary', 'secondary', 'pageScoped'):
        items = value.get(key, [])
        require(isinstance(items, list) and all(isinstance(x, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{2,60}', x) for x in items), 'Invalid catalogue codes')
        sets.append(set(items) - CONSOLE_EXCLUDED)
    require(sets[0], 'Catalogue has no primary metric')
    return sets[0], sets[1] | sets[0] if not sets[1] else sets[1], sets[2] or PAGE_SCOPED


def metric(value, allowed, page_scoped=PAGE_SCOPED):
    require(isinstance(value, dict), 'Metric must be an object')
    require(set(value) <= {'metric', 'pageUrl', 'pageGroup'}, 'Unsupported metric field')
    require(value.get('metric') in allowed, 'Unsupported metric')
    url, group = value.get('pageUrl'), value.get('pageGroup')
    if value['metric'] in page_scoped and ('pageUrl' in value or 'pageGroup' in value or value['metric'] == 'PAGE_VIEW_TO_URL_RATE'):
        require(('pageUrl' in value) != ('pageGroup' in value), 'Page-view metric needs exactly one pageUrl/pageGroup field')
        require(text(url) != text(group), 'Page-view metric needs a nonempty pageUrl/pageGroup')
        if url is not None:
            require(text(url) and (url.startswith('/') or url.startswith(('https://', 'http://'))), 'Invalid metric page URL')
    else:
        require(url is None and group is None, 'Only a page-view metric accepts page scope')


def validate_create(value, catalogue=None):
    primary, guardrails, page_scoped = catalogue_sets(catalogue)
    maximum = (catalogue or {}).get('maxSecondary', 3)
    require(type(maximum) is int and 0 <= maximum <= 3, 'Invalid secondary metric cap')
    require(isinstance(value, dict), 'createInput must be an object')
    require(set(value) <= CREATE_FIELDS, 'Unsupported createInput field; lifecycle and opaque targeting are excluded')
    require(text(value.get('title')), 'Missing title')
    if 'hypothesis' in value:
        require(text(value['hypothesis']), 'Hypothesis must be nonempty')
    metric(value.get('successMetric'), primary, page_scoped)
    secondary = value.get('secondaryMetrics', [])
    require(isinstance(secondary, list) and len(secondary) <= maximum, 'At most three guardrails')
    for item in secondary:
        metric(item, guardrails, page_scoped)
    variations = value.get('variations')
    require(isinstance(variations, list) and len(variations) >= 2, 'At least two variations required')
    names, splits, controls = [], [], 0
    for item in variations:
        require(isinstance(item, dict) and set(item) == {'name', 'isControl', 'trafficSplit'}, 'Invalid variation fields')
        require(text(item['name']), 'Missing variation name')
        require(type(item['isControl']) is bool, 'isControl must be boolean')
        require(finite(item['trafficSplit']) and 0 <= item['trafficSplit'] <= 100, 'Invalid traffic split')
        names.append(item['name'].strip())
        splits.append(item['trafficSplit'])
        controls += int(item['isControl'])
    require(len(set(names)) == len(names), 'Variation names must be unique')
    require(controls == 1, 'Exactly one control required')
    require(math.isclose(sum(splits), 100, abs_tol=1e-9), 'Traffic splits must total 100')
    if 'deviceTypes' in value:
        devices = value['deviceTypes']
        require(isinstance(devices, list) and devices and all(x in {'mobile', 'other'} for x in devices), 'Invalid device targeting')
        require(len(set(devices)) == len(devices), 'Duplicate device targeting')
    if 'utmConditions' in value:
        conditions = value['utmConditions']
        require(isinstance(conditions, list), 'UTM conditions must be a list')
        params = []
        for condition in conditions:
            require(isinstance(condition, dict) and set(condition) == {'parameter', 'values'}, 'Invalid UTM condition')
            require(condition['parameter'] in {'utm_campaign', 'utm_medium', 'utm_source', 'utm_term', 'utm_content'}, 'Invalid UTM parameter')
            require(isinstance(condition['values'], list) and condition['values'] and all(text(x) for x in condition['values']), 'Invalid UTM values')
            params.append(condition['parameter'])
        require(len(set(params)) == len(params), 'Combine duplicate UTM parameters into one condition')
    return value


def no_nonfinite(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'Nonfinite evidence number')
    if isinstance(value, dict):
        for item in value.values():
            no_nonfinite(item)
    if isinstance(value, list):
        for item in value:
            no_nonfinite(item)


def _checkout_test(test):
    metric_value = test['createInput']['successMetric']
    group = str(metric_value.get('pageGroup', '')).strip().lower()
    url = str(metric_value.get('pageUrl', '')).lower()
    return metric_value['metric'] == 'CHECKOUT_CONVERSION_RATE' or group == 'checkout' or '/checkout' in url or test.get('surfaceTemplate') == 'checkout'


def _validate_v3_test(test, catalogue):
    require(set(test) <= TEST_V3 and TEST_V3_REQUIRED <= set(test), 'Invalid ab-candidates/3 test fields')
    require(text(test['why']), 'Missing why')
    require(test.get('origin', 'finder') in {'finder', 'user-requested'}, 'Invalid test origin')
    require(test.get('surfaceTemplate') in TEMPLATES, 'Invalid surface template')
    setup = test['setup']
    require(isinstance(setup, dict) and {'title', 'hypothesis', 'successMetric', 'variations'} <= set(setup) <= {'title', 'hypothesis', 'successMetric', 'secondaryMetrics', 'targeting', 'variations'} and all(text(v) for v in setup.values()), 'Invalid setup block')
    require(setup['title'] == test['title'] and setup['hypothesis'] == test['hypothesis'], 'Setup must say what createInput says')
    for key in ('overlap', 'fixFirst', 'metricVolume', 'surface'):
        require(test.get(key) is None or text(test[key]), f'Invalid {key}')
    create_variations = test['createInput']['variations']
    variations = test['variations']
    require(isinstance(variations, list) and len(variations) == len(create_variations), 'Handoff variations must mirror createInput')
    selectors_claimed = False
    for item, base in zip(variations, create_variations):
        require(isinstance(item, dict) and {k: item.get(k) for k in ('name', 'isControl', 'trafficSplit')} == base, 'Handoff variation differs from createInput')
        require(set(item) <= {'name', 'isControl', 'trafficSplit', 'devNotes', 'selectors', 'preview'}, 'Invalid handoff variation field')
        require(item.get('devNotes') is None or text(item['devNotes']), 'Invalid dev notes')
        if item.get('selectors'):
            require(isinstance(item['selectors'], dict), 'Selectors must be an object')
            selectors_claimed = True
        preview = item.get('preview')
        if preview is not None:
            require(isinstance(preview, dict) and set(preview) <= {'before', 'after', 'viewport', 'note', 'kind'}, 'Invalid preview record')
            require(preview.get('viewport', 'desktop') in {'desktop', 'mobile-inferred', 'narrow-desktop-window'}, 'Mobile capture is not available in Cowork; use mobile-inferred')
            require(preview.get('kind', 'capture') in {'capture', 'preview-theme', 'description'}, 'Invalid preview kind')
    if test['validation']['status'] == 'unvalidated':
        require(not selectors_claimed and not test.get('siteFacts'), 'Unvalidated candidates cannot claim verified selectors or site facts')
    if test.get('siteFacts') is not None:
        require(isinstance(test['siteFacts'], list), 'siteFacts must be a list')
    follow = test.get('consoleFollowUps', [])
    require(isinstance(follow, list) and all(text(x) for x in follow), 'Invalid console follow-ups')
    if 'successMetric' in test:
        require(test['successMetric'] == test['createInput']['successMetric'], 'successMetric must mirror createInput')
    if 'reportFile' in test:
        require(text(test['reportFile']) and re.fullmatch(r'[A-Za-z0-9._-]+\.html', test['reportFile']), 'Invalid report file name')


def validate_candidates(value):
    require(isinstance(value, dict) and value.get('schema') in {'noibu.ab-candidates/2', 'noibu.ab-candidates/3'}, 'Unsupported handoff schema')
    v3 = value['schema'] == 'noibu.ab-candidates/3'
    require(set(value) <= (ROOT_V3 if v3 else ROOT_V2), 'Unsupported root fields')
    UUID(value.get('domainId', ''))
    require(text(value.get('domain')) and text(value.get('goal')), 'Missing domain/goal')
    timestamp(value.get('generatedAt'))
    window = value.get('window', {})
    require(isinstance(window, dict) and timestamp(window.get('start')) < timestamp(window.get('end')), 'Invalid analysis window')
    catalogue = value.get('catalogue') if v3 else None
    tests = value.get('tests')
    require(isinstance(tests, list), 'tests must be a list')
    require(isinstance(value.get('caveats', []), list), 'caveats must be a list')
    ranks, titles = [], []
    for test in tests:
        require(isinstance(test, dict), 'Invalid candidate')
        require(type(test.get('rank')) is int and test['rank'] > 0, 'Invalid rank')
        require(text(test.get('hypothesis')) and text(test.get('what')), 'Missing hypothesis/change')
        payload = validate_create(test.get('createInput'), catalogue)
        require(test.get('title') == payload['title'], 'Candidate/create title mismatch')
        require(test['hypothesis'] == payload.get('hypothesis'), 'Candidate/create hypothesis mismatch')
        validation = test.get('validation', {})
        require(isinstance(validation, dict) and validation.get('status') in {'verified', 'partial', 'unvalidated'}, 'Missing validation status')
        if validation['status'] == 'unvalidated':
            require(not test.get('selectors'), 'Unvalidated candidates cannot claim verified selectors')
        evidence = test.get('evidence')
        requested = v3 and test.get('origin') == 'user-requested'
        require(isinstance(evidence, list) and (evidence or requested), 'Candidate needs evidence')
        for item in evidence:
            require(isinstance(item, dict) and text(item.get('claim')) and text(item.get('source')) and isinstance(item.get('numbers'), dict) and item['numbers'], 'Invalid evidence')
        if v3:
            _validate_v3_test(test, catalogue)
        ranks.append(test['rank'])
        titles.append(test['title'])
    require(len(set(ranks)) == len(ranks) and len(set(titles)) == len(titles), 'Duplicate rank/title')
    if v3:
        _validate_v3_root(value)
    no_nonfinite(value)
    return value


def _validate_v3_root(value):
    require(value.get('browser', 'none') in BROWSERS, 'Invalid site-read browser')
    require(value.get('liveSiteCheck', 'not-performed' if value.get('browser', 'none') == 'none' else 'performed') in {'performed', 'partial', 'not-performed'}, 'Invalid live-site check state')
    if value.get('browser', 'none') == 'none':
        require(value.get('liveSiteCheck', 'not-performed') == 'not-performed', 'No browser means the live site was not checked')
        require(all(t['validation']['status'] == 'unvalidated' for t in value['tests']), 'Without a site read every test is unvalidated')
    readiness = value.get('readiness', {})
    require(isinstance(readiness, dict), 'Invalid readiness')
    split = readiness.get('splitCheckout')
    if split is not None:
        require(isinstance(split, dict) and text(split.get('checkoutDomain')), 'Invalid split-checkout record')
        if split.get('checkoutDomainId'):
            UUID(split['checkoutDomainId'])
        require(not any(_checkout_test(t) for t in value['tests']), 'Split-checkout store ships no checkout-metric or checkout-page test')
    for item in value.get('killed', []):
        require(isinstance(item, dict) and set(item) == {'idea', 'reason'} and text(item['idea']) and text(item['reason']), 'Invalid killed entry')
    for key in ('outsideGoal', 'caveats', 'couldNotComplete', 'testingTools'):
        require(isinstance(value.get(key, []), list) and all(text(x) for x in value.get(key, [])), f'Invalid {key}')
    require(len(value.get('outsideGoal', [])) <= 2, 'At most two Outside your goal lines')
    require(isinstance(value.get('existingTests', []), list), 'Invalid existingTests')
    files = value.get('reportFiles', {})
    require(isinstance(files, dict) and all(re.fullmatch(r'[1-9][0-9]*', k) and text(v) for k, v in files.items()), 'Invalid report files')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        data = validate_candidates(json.loads(args.input.read_text()))
    except (ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f'Invalid handoff: {exc}\n')
    print(f"Validated {len(data['tests'])} candidates; no Noibu objects were created.")
    for test in data['tests']:
        print(f"Test {test['rank']}: {test['title']} · createInputHash {create_hash(test['createInput'])}")


if __name__ == '__main__':
    main()
