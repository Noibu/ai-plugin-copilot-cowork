#!/usr/bin/env python3
"""Deterministic gates for the ab-testing skill: run modes, the writes each mode may make, the
create-draft plan, reply matching and the AskUserQuestion option cap. No tools, no network, no
writes: the conversation calls this (RunScript or python) to check a step BEFORE making a tool call,
and native approvals still apply after it says "allowed".

    python ab_flow.py modes --shopify-theme
    python ab_flow.py check-write <mode> <write> [--merged] [--live] [--finder] [--scheduled]
    python ab_flow.py plan-create <candidates.json> <rank> <roster.json> [--enums enums.json] [--hash <hex>]
    python ab_flow.py match-mode "<reply text>"
    python ab_flow.py test-options <candidates.json> [<candidates.json> ...]
    python ab_flow.py match-test "<reply text>" <candidates.json> [...]
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

MODES = ('full', 'pr', 'theme', 'preview')  # fixed order: most automated first, "just show me the code" last
LABELS = {'full': 'Launch an end-to-end test', 'pr': 'Prepare a pull request', 'theme': 'Preview on a Shopify theme', 'preview': 'Just show me the code'}
DESCRIPTIONS = {'full': "Open a pull request on my code repository, check preview. Once merged, confirm it's live and start test.",
                'pr': 'Open a pull request on my code repository.',
                'theme': 'Build an unpublished copy of my live theme with the change and check it. Shoppers never see it.',
                'preview': 'Nothing is pushed or published, I show the code here.'}
STAGES = {'full': ['2a', '2b', '2c', '2d', '3', '4-merge-gate', '5'], 'pr': ['2a', '2b', '2c', '2d', '4-follow-up'],
          'theme': ['2a', '2b', '2c', '3', '4-follow-up'], 'preview': ['2a', '2b', '2c', '2e', '4-follow-up']}
# Pre-merge writes each mode promised. Nothing else is ever written before the merge gate.
WRITES = {'full': {'noibu-draft', 'branch', 'branch-fix', 'pull-request', 'preview-theme', 'patch-file', 'draft-hypothesis-update', 'pr-comment'},
          'pr': {'noibu-draft', 'branch', 'pull-request', 'patch-file', 'draft-hypothesis-update'},
          'theme': {'noibu-draft', 'preview-theme', 'patch-file'},
          'preview': {'noibu-draft', 'patch-file'},
          # Follow-up after `pr` ("QA, merge, then start"): the rest of `full`, reusing the existing draft and PR.
          # No new draft, branch or pull request; QA fixes are pushed to the existing PR branch only.
          'qa-merge-start': {'preview-theme', 'pr-comment', 'branch-fix'}}
START_MODES = {'full', 'qa-merge-start'}
NEVER = {'merge', 'publish-theme', 'deploy', 'live-theme-write', 'stop-test', 'delete-unapproved-theme'}
FINDER_EFFECTS = {'cart-round-trip', 'report-file'}
FOLLOW_UP = {'preview': [('full', 'Continue: run it end to end from here'), ('pr', 'Continue: create the pull request from the code you wrote'), ('theme', 'Continue: preview it on a Shopify theme'), ('stop', 'Stop here')],
             'pr': [('qa-merge-start', 'Continue: QA it, then after I merge, start the test'), ('theme', 'Continue: preview it on a Shopify theme'), ('stop', 'Stop here')],
             'theme': [('pr', 'Continue: create the pull request from the code you wrote'), ('full', 'Continue: run it end to end from here'), ('stop', 'Stop here')]}
MODE_PHRASES = [('qa-merge-start', r'\bqa\b.*\b(merge|start)|qa,? merge|qa it'),
                ('full', r'end[- ]to[- ]end|launch|run it|all the way|merge and start'),
                ('pr', r'pull request|merge request|\bpr\b|just the pr'),
                ('theme', r'shopify theme|theme preview|preview theme|preview on a shopify'),
                ('preview', r'show me the code|preview the implementation|just the diff|just show')]


def modes(shopify_theme):
    """Run-mode options in fixed order; theme only on a Shopify Online Store theme (connector or not)."""
    return [{'mode': m, 'label': LABELS[m], 'description': DESCRIPTIONS[m]} for m in MODES if m != 'theme' or shopify_theme]


def follow_up(after, shopify_theme):
    if after not in FOLLOW_UP:
        raise ValueError('Only partial modes end with a follow-up card')
    return [{'next': n, 'phrase': p} for n, p in FOLLOW_UP[after] if n != 'theme' or shopify_theme]


def check_write(mode, write, merged=False, live=False, finder=False, scheduled=False, approved_theme=None, theme_name=None):
    """Raise ValueError unless this write is allowed now. Pure policy; native approvals still apply."""
    if write in NEVER:
        raise ValueError(f'{write} is never done by this skill')
    if finder:
        if write not in FINDER_EFFECTS:
            raise ValueError('The finder writes nothing in Noibu or on the git host: only the cart round trip and report files')
        return True
    if scheduled and write not in FINDER_EFFECTS:
        raise ValueError('A scheduled run never creates drafts, branches, pull requests or preview themes, and never starts tests')
    if write == 'start-test':
        if mode not in START_MODES:
            raise ValueError('Only full mode (or the "QA, merge, then start" follow-up) starts a test')
        if not (merged and live):
            raise ValueError('Start only after the user confirmed the merge AND the code was verified live')
        return True
    if write == 'delete-preview-theme':
        if not approved_theme or approved_theme != theme_name or not str(theme_name).startswith('Noibu preview:'):
            raise ValueError('Delete only the exact Noibu preview theme the user approved in this run')
        return True
    if mode not in WRITES or write not in WRITES[mode]:
        raise ValueError(f'{mode} mode did not promise {write}; offer it on the follow-up card instead')
    return True


def create_hash(create_input):
    return hashlib.sha256(json.dumps(create_input, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def _validator():
    spec = importlib.util.spec_from_file_location('noibu_ab_candidates', Path(__file__).with_name('validate_candidates.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_test(candidates, title=None, rank=None):
    tests = candidates['tests']
    if title:
        hit = [t for t in tests if t['title'] == title] or [t for t in tests if t['title'].casefold() == title.strip().casefold()]
        if hit:
            return hit[0]
    if rank is not None:
        hit = [t for t in tests if t['rank'] == rank]
        if hit:
            return hit[0]
    return None


def plan_create(candidates, rank, roster, enums=None, displayed_hash=None, title=None):
    """What a "Create A/B test N" reply may do: create a DRAFT, adopt an existing draft, or stop.
    roster = noibu_list_ab_tests rows (all statuses); enums = the tool schema's current metric enums."""
    _validator().validate_candidates(candidates)
    test = find_test(candidates, title=title, rank=rank)
    if test is None:
        return {'action': 'ask-which-test', 'reason': 'No test with that rank or title in this chat\'s candidates.json'}
    digest = create_hash(test['createInput'])
    if displayed_hash and displayed_hash != digest:
        return {'action': 'stop-hash-mismatch', 'reason': 'The candidates file changed since the card was shown; rebuild and show the card again', 'rank': test['rank']}
    if enums:
        primary, secondary = set(enums.get('primary', [])), set(enums.get('secondary', []))
        codes = [test['createInput']['successMetric']['metric']]
        bad = [c for c in codes if c not in primary] + [m['metric'] for m in test['createInput'].get('secondaryMetrics', []) if m['metric'] not in secondary]
        if bad:
            return {'action': 'stop-metric-not-accepted', 'reason': 'The create tool no longer accepts: ' + ', '.join(bad), 'rank': test['rank']}
    wanted = test['createInput']['title'].strip().casefold()
    for row in roster or []:
        name = str(row.get('title') or row.get('name') or '').strip().casefold()
        if name != wanted:
            continue
        status = str(row.get('status', '')).upper()
        if status in {'RUNNING', 'STOPPED'}:
            return {'action': 'stop-existing-' + status.lower(), 'reason': f'A {status} test with this title already exists; nothing is created', 'rank': test['rank'], 'testId': row.get('id'), 'key': row.get('key')}
        return {'action': 'adopt-existing-draft', 'state': 'existing', 'rank': test['rank'], 'testId': row.get('id'), 'key': row.get('key')}
    return {'action': 'create-draft', 'state': 'created', 'rank': test['rank'], 'createInputHash': digest,
            'call': {'tool': 'noibu_create_ab_test', 'arguments': dict(test['createInput'], domainId=candidates['domainId'], skill='ab-testing', skillStep='create-test',
                                                                       rationale=f'User replied Create A/B test {test["rank"]} on the findings card for "{test["title"]}"')}}


def test_options(tests, max_words=5):
    """AskUserQuestion options for picking a test (card 4b, split checkout, blast radius).
    tests: [{rank, title, run?}] in display order. Labels are at most `max_words` words plus an
    optional '#rank' / '(run N)' suffix and are guaranteed distinct; the full title goes in the
    description. Truncation keeps the first word that tells colliding titles apart."""
    rows = [{'rank': t['rank'], 'title': t['title'], 'run': t.get('run', 1)} for t in tests]
    words = [r['title'].split() for r in rows]
    labels = [' '.join(w[:max_words]) for w in words]
    def groups():
        seen = {}
        for i, label in enumerate(labels):
            seen.setdefault(label.casefold(), []).append(i)
        return [g for g in seen.values() if len(g) > 1]
    for group in groups():
        for i in group:
            others = set(x.casefold() for j in group if j != i for x in words[j])
            distinct = next((w for w in words[i][max_words - 1:] if w.casefold() not in others), None)
            if distinct is None:
                distinct = next((w for w in words[i] if w.casefold() not in others), None)
            if distinct is not None and distinct not in words[i][:max_words - 1]:
                labels[i] = ' '.join(words[i][:max_words - 1] + [distinct])
    for group in groups():
        same_rank = len({rows[i]['rank'] for i in group}) < len(group)
        for i in group:
            labels[i] = labels[i] + (f" (run {rows[i]['run']})" if same_rank else f" #{rows[i]['rank']}")
    for group in groups():  # identical titles with identical rank and run: last resort, position
        for n, i in enumerate(group, 1):
            labels[i] = labels[i] + f' [{n}]'
    assert len({l.casefold() for l in labels}) == len(labels)
    return [{'label': l, 'description': r['title'], 'rank': r['rank'], 'title': r['title'], 'run': r['run']} for l, r in zip(labels, rows)]


def match_test(reply, options):
    """Match a reply to exactly one option: full title, then unique label, then rank ('test 2',
    '#2', 'the second one'). Anything matching zero or several options is re-asked, never guessed."""
    text = ' '.join(str(reply).replace('Implement the test:', '').split()).strip().casefold()
    for key in ('title', 'label'):
        hits = [o for o in options if o[key].casefold() == text]
        if len(hits) == 1:
            return {'action': 'pick', 'option': hits[0], 'by': key}
        if len(hits) > 1:
            return {'action': 're-ask', 'candidates': hits, 'reason': f'Several tests share that {key}'}
    ordinals = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6}
    m = re.fullmatch(r'(?:test\s*|#|number\s*)?(\d+)|(?:the\s+)?(first|second|third|fourth|fifth|sixth)(?:\s+one)?', text)
    if m:
        rank = int(m.group(1)) if m.group(1) else ordinals[m.group(2)]
        hits = [o for o in options if o['rank'] == rank]
        if len(hits) == 1:
            return {'action': 'pick', 'option': hits[0], 'by': 'rank'}
        return {'action': 're-ask', 'candidates': hits or options, 'reason': 'That number matches no single test'}
    partial = [o for o in options if text and text in o['title'].casefold()]
    return {'action': 're-ask', 'candidates': partial or options, 'reason': 'No single test matched'}


def match_mode(reply):
    text = reply.casefold()
    for mode, pattern in MODE_PHRASES:
        if re.search(pattern, text):
            return mode
    return None


def cap_options(options, limit=5, keep_last=None):
    """AskUserQuestion takes 2-5 options and no catch-all. Keep order; when a fixed last option
    (e.g. "Stop here") exists, it survives the cut. Returns (shown, overflow) so the question text
    can name what was left off (a typed reply still matches it)."""
    options = list(options)
    tail = [o for o in options if keep_last is not None and o == keep_last]
    head = [o for o in options if o not in tail]
    shown = head[:limit - len(tail)] + tail
    overflow = head[limit - len(tail):]
    if len(shown) < 2:
        raise ValueError('AskUserQuestion needs at least two distinct options; ask in one plain line instead')
    return shown, overflow


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('modes'); m.add_argument('--shopify-theme', action='store_true')
    w = sub.add_parser('check-write'); w.add_argument('mode'); w.add_argument('write')
    for flag in ('--merged', '--live', '--finder', '--scheduled'):
        w.add_argument(flag, action='store_true')
    c = sub.add_parser('plan-create'); c.add_argument('candidates', type=Path); c.add_argument('rank', type=int); c.add_argument('roster', type=Path)
    c.add_argument('--enums', type=Path); c.add_argument('--hash')
    r = sub.add_parser('match-mode'); r.add_argument('reply')
    o = sub.add_parser('test-options', help='distinct AskUserQuestion labels for candidates.json files (newest run last)'); o.add_argument('candidates', type=Path, nargs='+')
    t = sub.add_parser('match-test'); t.add_argument('reply'); t.add_argument('candidates', type=Path, nargs='+')
    a = p.parse_args(argv)
    try:
        if a.cmd == 'modes':
            out = modes(a.shopify_theme)
        elif a.cmd == 'check-write':
            out = {'allowed': check_write(a.mode, a.write, a.merged, a.live, a.finder, a.scheduled)}
        elif a.cmd == 'plan-create':
            out = plan_create(json.loads(a.candidates.read_text()), a.rank, json.loads(a.roster.read_text()), json.loads(a.enums.read_text()) if a.enums else None, a.hash)
        elif a.cmd in ('test-options', 'match-test'):
            tests = [dict(t, run=n) for n, f in enumerate(a.candidates, 1) for t in json.loads(f.read_text())['tests']]
            options = test_options(tests)
            out = options if a.cmd == 'test-options' else match_test(a.reply, options)
        else:
            out = {'mode': match_mode(a.reply)}
    except ValueError as exc:
        out = {'allowed': False, 'reason': str(exc)}
        print(json.dumps(out, indent=1))
        return 1
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
