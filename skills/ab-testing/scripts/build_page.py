#!/usr/bin/env python3
"""Build the A/B finder's deliverables for Microsoft 365 Copilot Cowork from one page.json.

Usage:
  python build_page.py page.json <domain-short>
  python build_page.py page.json implement <rank> <draft id> <flag key> <created|existing>

The first form writes, next to page.json:
  <domain-short>-test-<rank>.html   one standalone, static "Recommended test" report per test
                                    (no script, no remote fonts, no buttons; before/after images
                                    are embedded only when real captured image files exist)
  candidates.json                   the handoff, noibu.ab-candidates/3, derived from page.json +
                                    walkthrough.json and validated by validate_candidates.py
  findings-report.json              the presentation input for the findings Adaptive Card
  test-report-<rank>.json           the presentation input for each test's report card
The second form writes implement-report-<rank>.json (the implement card's input) once a draft
exists, and prints the test's console link.

Nothing here calls Noibu, a browser or the host: the cards are rendered by scripts/show_card.py
through RunScript (one render_ui per response), and a report file reaches the user only when the
run publishes it with the host's file tools after a "Preview test N" reply
(references/output-format.md). This port replaces the Claude Artifact runtime: no
`claude.use`, no `sendPrompt`, no MCP button, no side panel.

page.json shape: references/output-format.md ("page.json fields"). Differences from the Claude
design: no `pageUrls`/`server`; `run.window` start/end are timezone-aware ISO timestamps;
`run.browser` is "edge" or "none"; `previewViewport` is "desktop", "mobile-inferred" or
"narrow-desktop-window"; optional per-test `validation`, `origin`, `previewKind`; optional
`run.catalogue` (the metric catalogue read from the noibu_create_ab_test schema).
"""
import base64
import html
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = 'ab-testing'
WORKFLOW = 'ab-testing'
MAX_IMAGE_BYTES = 3_000_000
IMAGE_TYPES = {b'\xff\xd8\xff': 'image/jpeg', b'\x89PNG\r\n\x1a\n': 'image/png', b'GIF87a': 'image/gif', b'GIF89a': 'image/gif'}

CSS = """
:root { --bg:#f6f6f4; --surface:#fff; --ink:#17191c; --muted:#5c6168; --line:#dcdedb;
  --before:#8a8f96; --after:#1f6f4a; --after-bg:#e8f3ec; --note-bg:#fbf4dd; --note-ink:#5b4a12; --warn:#8a5a00; --panel:#f0f0ed; }
@media (prefers-color-scheme: dark) { :root { --bg:#141618; --surface:#1d2023; --ink:#eceef0; --muted:#a2a8b0; --line:#30353a;
  --before:#8a8f96; --after:#6fcf9a; --after-bg:#1c2e25; --note-bg:#2f2a18; --note-ink:#e6d69a; --warn:#e6b45a; --panel:#23272b; color-scheme:dark; } }
body { margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI",system-ui,-apple-system,sans-serif; font-size:15px; line-height:1.5; }
.wrap { max-width:1180px; margin:0 auto; padding:32px 20px 64px; }
h1 { font-size:28px; font-weight:600; margin:0 0 6px; }
header p { margin:0; color:var(--muted); max-width:70ch; }
.meta { display:flex; flex-wrap:wrap; gap:8px 20px; margin-top:14px; font-family:ui-monospace,Consolas,monospace; font-size:12.5px; color:var(--muted); }
.note { margin-top:18px; background:var(--note-bg); color:var(--note-ink); border-radius:6px; padding:10px 14px; font-size:14px; max-width:80ch; }
section.test { margin-top:44px; padding-top:28px; border-top:1px solid var(--line); }
.test h2 { font-size:22px; font-weight:600; margin:0; }
.surface { font-family:ui-monospace,Consolas,monospace; font-size:12.5px; color:var(--muted); margin-top:6px; word-break:break-all; }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:16px; max-width:100ch; } @media (max-width:760px) { .cols { grid-template-columns:1fr; } }
.cols h3, .setup h3, .dev h3 { font-size:12.5px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin:0 0 4px; font-weight:600; }
.cols p { margin:0; }
.variation { margin-top:18px; font-weight:500; }
.pair { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:10px; } @media (max-width:760px) { .pair { grid-template-columns:1fr; } }
figure { margin:0; background:var(--surface); border:1px solid var(--line); border-radius:8px; overflow:hidden; }
figure img { display:block; width:100%; height:auto; }
figcaption { display:flex; align-items:center; gap:10px; padding:9px 12px; font-size:13px; border-top:1px solid var(--line); color:var(--muted); }
.tag { font-family:ui-monospace,Consolas,monospace; font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; padding:2px 8px; border-radius:4px; }
.tag.before { color:var(--before); border:1px solid var(--line); } .tag.after { color:var(--after); background:var(--after-bg); }
.nopreview { margin-top:10px; padding:12px 14px; border:1px dashed var(--line); border-radius:8px; color:var(--muted); font-size:14px; max-width:80ch; }
.setup { margin-top:20px; background:var(--panel); border-radius:8px; padding:14px 16px; max-width:100ch; }
.setup dl { display:grid; grid-template-columns:max-content 1fr; gap:6px 16px; margin:0; font-size:14px; }
.setup dt { color:var(--muted); } .setup dd { margin:0; }
@media (max-width:560px) { .setup dl { grid-template-columns:1fr; gap:2px; } .setup dt { margin-top:8px; } }
.dev { margin-top:16px; max-width:80ch; font-size:14px; } .dev p { margin:0 0 8px; }
.fix { color:var(--warn); }
.next { margin-top:18px; font-size:14px; color:var(--muted); max-width:80ch; } .next strong { color:var(--ink); }
.outside { margin-top:44px; padding-top:24px; border-top:1px solid var(--line); max-width:80ch; } .outside h2 { font-size:17px; margin:0 0 8px; }
footer { margin-top:48px; color:var(--muted); font-size:13px; max-width:80ch; } footer p { margin:4px 0; }
"""


def esc(s):
    return html.escape('' if s is None else str(s), quote=True)


def _load_validator():
    spec = importlib.util.spec_from_file_location('noibu_ab_candidates', HERE / 'validate_candidates.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _image(folder: Path, rel):
    """A real captured image file inside the run folder, as a data URI; None otherwise.
    Cowork's get_screenshot returns the image to the model and is not assumed to save a file,
    so a path is honoured only when that file actually exists and starts like an image."""
    if not rel or not isinstance(rel, str) or rel.startswith(('/', '\\')) or '..' in Path(rel).parts or re.match(r'^[a-z]+:', rel, re.I):
        return None
    path = (folder / rel)
    try:
        path = path.resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file() or path.stat().st_size > MAX_IMAGE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    mime = next((m for sig, m in IMAGE_TYPES.items() if data.startswith(sig)), None)
    if mime is None and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        mime = 'image/webp'
    return f'data:{mime};base64,' + base64.b64encode(data).decode() if mime else None


def _pair(folder: Path, t: dict):
    before, after = _image(folder, t.get('before')), _image(folder, t.get('after'))
    return (before, after) if before and after else (None, None)


def _evidence(items):
    """Evidence lines as the validator wants them: `numbers` is a non-empty object of named figures.
    A model writing page.json often gives the figures as one string ("26% vs 79%") or a list; those
    are kept under a single key rather than failing the whole build."""
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        item = dict(item)
        numbers = item.get('numbers')
        if isinstance(numbers, (str, int, float)) and str(numbers).strip():
            item['numbers'] = {'figures': numbers}
        elif isinstance(numbers, list) and numbers:
            item['numbers'] = {f'figure{i}': n for i, n in enumerate(numbers, 1)}
        elif not isinstance(numbers, dict) or not numbers:
            item['numbers'] = {'figures': item.get('claim') or 'see why'}
        out.append(item)
    return out


def report_file(prefix: str, rank: int) -> str:
    return f'{prefix}-test-{rank}.html'


def build(page: dict, rank: int, folder: Path) -> str:
    """One standalone report: the run's intro, test <rank> in full, then the run-level closing sections."""
    t = page['tests'][rank - 1]
    s = t['setup']
    before, after = _pair(folder, t)
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{esc(page['domain'].replace('www.', ''))} test {rank}: {esc(t['title'])}</title>",
             f'<style>{CSS}</style></head><body><div class="wrap"><header>',
             f"<h1>A/B test recommendation for {esc(page['domain'])}</h1>",
             f"<p>Goal: {esc(page['goal'])}" + (f" (success metric: {esc(page['successMetricLabel'])})" if page.get('successMetricLabel') else '')
             + ('. It is checked against the live site where a browser was available, and shown as it would look where a capture exists.</p>' if (page.get('run') or {}).get('browser', 'none') != 'none'
                else '. The live site was not checked in this run: structural claims are inferred from Noibu data.</p>'),
             '<div class="meta">' + ''.join(f'<span>{esc(x)}</span>' for x in [page.get('dataLine'), page.get('captureLine')] if x) + '</div>',
             '<div class="note">Previews are approximations: nothing on the site was modified, and the developer\'s build may differ in detail. '
             'Creating a test makes a draft that serves no traffic until it is started in the Noibu console.</div></header>']
    parts.append(f'<section class="test" id="test-{rank}"><h2>{esc(t["title"])}</h2>')
    if t.get('surface'):
        parts.append(f'<div class="surface">{esc(t["surface"])}</div>')
    parts.append(f'<div class="cols"><div><h3>What to change</h3><p>{esc(t["what"])}</p></div><div><h3>Why this test</h3><p>{esc(t["why"])}</p></div></div>')
    parts.append(f'<div class="variation">B: {esc(t.get("variationName") or "Variation")}</div>')
    if before and after:
        viewport = t.get('previewViewport') or 'desktop'
        cap = {'desktop': 'desktop capture', 'narrow-desktop-window': 'narrow desktop window, not a phone', 'mobile-inferred': 'desktop capture; mobile layout inferred'}.get(viewport, 'desktop capture')
        parts.append('<div class="pair">'
                     f'<figure><img src="{before}" alt="{esc(t.get("beforeAlt") or "The page as it is today")}"><figcaption><span class="tag before">Original</span> {esc(t.get("beforeCaption") or "A: as it is today")} ({esc(cap)})</figcaption></figure>'
                     f'<figure><img src="{after}" alt="{esc(t.get("afterAlt") or "The page with the variation applied")}"><figcaption><span class="tag after">Variation B</span> {esc(t.get("afterCaption") or t.get("variationName") or "")}</figcaption></figure></div>')
    else:
        parts.append(f'<div class="nopreview">No screenshot for this variation: {esc(_preview_note(t, folder))}. {esc(t.get("what"))}</div>')
    parts.append('<div class="setup"><h3>Set it up in Noibu</h3><dl>'
                 f'<dt>Title</dt><dd>{esc(s["title"])}</dd>'
                 f'<dt>Hypothesis</dt><dd>{esc(s["hypothesis"])}</dd>'
                 f'<dt>Success metric</dt><dd>{esc(s["successMetric"])}</dd>'
                 + (f'<dt>Traffic for this metric</dt><dd>{esc(t["metricVolume"])}</dd>' if t.get('metricVolume') else '')
                 + f'<dt>Secondary metrics</dt><dd>{esc(s.get("secondaryMetrics") or "None")}</dd>'
                 f'<dt>Targeting</dt><dd>{esc(s.get("targeting") or "Everyone (skip this section)")}</dd>'
                 f'<dt>Variations</dt><dd>{esc(s["variations"])}</dd></dl></div>')
    parts.append('<div class="dev">' + (f'<h3>Dev notes</h3><p>{esc(t["devNotes"])}</p>' if t.get('devNotes') else '')
                 + (f'<p class="fix"><strong>Fix first:</strong> {esc(t["fixFirst"])}</p>' if t.get('fixFirst') else '')
                 + (f'<p class="fix"><strong>Overlap:</strong> {esc(t["overlap"])}</p>' if t.get('overlap') else '') + '</div>')
    parts.append(f'<p class="next"><strong>Create it in Noibu:</strong> reply <strong>Create A/B test {rank}</strong> in the Cowork conversation that found this test. '
                 'It creates a draft only; nothing is started or published.</p></section>')
    if page.get('outsideGoal'):
        parts.append('<section class="outside"><h2>Outside your goal</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in page['outsideGoal']) + '</ul></section>')
    parts.append('<footer>' + ''.join(f'<p>{esc(x)}</p>' for x in page.get('caveats', [])) + '</footer></div></body></html>')
    return '\n'.join(parts)


def _preview_note(t: dict, folder: Path) -> str:
    if t.get('before') and t.get('after') and not all(_pair(folder, t)):
        return 'the capture was not saved as an image file in this session'
    return t.get('previewNote') or 'this session could not change the page to show the variation'


# --- candidates.json: the handoff, derived from page.json + walkthrough.json ---

SURFACE_SCRIPT = {'home': 'read_home', 'collection': 'read_collection', 'product': 'read_pdp', 'cart': 'read_cart', 'checkout': 'read_checkout_entry'}


def _surface_template(test: dict):
    h = test.get('handoff') or {}
    if h.get('surfaceTemplate'):
        return h['surfaceTemplate']
    s = (test.get('surface') or '').lower()
    if s.startswith('/collections') or '/collections/' in s:
        return 'collection'
    if '/products' in s:
        return 'product'
    if s.startswith('/cart'):
        return 'cart'
    if 'checkout' in s:
        return 'checkout'
    if s.strip() in ('/', '') or s.startswith('/ '):
        return 'home'
    return None


def _site_facts(wt: dict, template):
    """A few verbatim facts from the site-read record for this surface (no analysis)."""
    rec = wt.get(SURFACE_SCRIPT.get(template or '', ''), {}) or {}
    keep = ['url', 'title', 'price', 'inStock', 'cta', 'shippingReturnsCopy', 'expressPayOnPdp', 'widgets',
            'productCountText', 'sort', 'filters', 'cards', 'quickAdd', 'merchandising', 'announcementBar', 'hero',
            'testingTools', 'storefront', 'sectionsBelowFold', 'surface', 'itemCount', 'shippingMessages',
            'freeShippingProgress', 'promoField', 'shippingEstimator', 'checkoutCta', 'expressPay', 'upsells', 'notes']
    return [{k: rec[k]} for k in keep if k in rec and rec[k] not in (None, [], {}, '')]


def _validation(page: dict, t: dict, wt: dict, template):
    if t.get('validation'):
        return t['validation']
    if (page.get('run') or {}).get('browser', 'none') == 'none':
        return {'status': 'unvalidated', 'notes': 'No browser read the live site in this run; structural claims are inferred.'}
    if wt.get(SURFACE_SCRIPT.get(template or '', '')):
        return {'status': 'verified', 'notes': 'The surface was read in the browser during this run.'}
    return {'status': 'partial', 'notes': 'The homepage was read; this surface itself was not.'}


def candidates(page: dict, wt: dict, prefix: str, folder: Path) -> dict:
    run = page.get('run') or {}
    meta = wt.get('meta') or {}
    home = wt.get('read_home') or {}
    browser = run.get('browser', 'none')
    out = {'schema': 'noibu.ab-candidates/3',
           'generatedAt': run.get('generatedAt') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'domain': page['domain'], 'domainId': page['domainId'], 'goal': page.get('goal'),
           'window': {k: v for k, v in (run.get('window') or {}).items() if k in ('start', 'end', 'days', 'sessions', 'mobileShare', 'label')},
           'browser': browser,
           'liveSiteCheck': run.get('liveSiteCheck') or ('not-performed' if browser == 'none' else 'performed'),
           'caveats': page.get('caveats', []), 'tests': [], 'outsideGoal': page.get('outsideGoal', []), 'killed': run.get('killed', []),
           'couldNotComplete': meta.get('couldNotComplete') or [],
           'testingTools': run.get('testingTools') or home.get('testingTools') or [],
           'reportFiles': {str(i): report_file(prefix, i) for i in range(1, len(page['tests']) + 1)}}
    for key, value in (('successMetricLabel', page.get('successMetricLabel')), ('dataLine', page.get('dataLine')), ('captureLine', page.get('captureLine')),
                       ('platform', run.get('platform') or home.get('platform')), ('storefront', home.get('storefront')),
                       ('surfaces', meta.get('surfaces')), ('cartState', meta.get('cartState'))):
        if value is not None:
            out[key] = value
    for k in ('companyId', 'siblings', 'market', 'readiness', 'existingTests', 'previewBrowsers', 'catalogue'):
        if k in run:
            out[k] = run[k]
    for i, t in enumerate(page['tests'], 1):
        h = t.get('handoff') or {}
        template = _surface_template(t)
        validation = _validation(page, t, wt, template)
        script = SURFACE_SCRIPT.get(template or '')
        rec = (wt.get(script) or {}) if script else {}
        selectors = dict(rec.get('selectors') or {})
        selectors.update(h.get('selectors') or {})
        if validation['status'] == 'unvalidated':
            selectors = {}
        before, after = _pair(folder, t)
        variations = []
        for v in t['createInput']['variations']:
            item = dict(v)
            if not v.get('isControl'):
                item['devNotes'] = t.get('devNotes')
                if selectors:
                    item['selectors'] = selectors
                if before and after:
                    item['preview'] = {'before': t['before'], 'after': t['after'], 'viewport': t.get('previewViewport') or 'desktop', 'kind': t.get('previewKind') or 'capture'}
                else:
                    item['preview'] = {'note': _preview_note(t, folder), 'kind': t.get('previewKind') or 'description', 'viewport': t.get('previewViewport') or 'desktop'}
            variations.append(item)
        facts = h.get('siteFacts') or _site_facts(wt, template)
        test = {'rank': i, 'title': t['title'], 'reportFile': report_file(prefix, i), 'surfaceTemplate': template,
                'what': t.get('what'), 'why': t.get('why'), 'hypothesis': t['createInput'].get('hypothesis'),
                'successMetric': t['createInput']['successMetric'], 'evidence': _evidence(h.get('evidence', [])),
                'validation': validation, 'variations': variations, 'setup': t.get('setup'), 'createInput': t['createInput'],
                'consoleFollowUps': h.get('consoleFollowUps', []), 'overlap': t.get('overlap'), 'fixFirst': t.get('fixFirst')}
        for key, value in (('surface', t.get('surface')), ('metricVolume', h.get('metricVolume') or t.get('metricVolume')),
                           ('variationName', t.get('variationName')), ('origin', t.get('origin'))):
            if value is not None:
                test[key] = value
        if facts and validation['status'] != 'unvalidated':
            test['siteFacts'] = facts
        out['tests'].append(test)
    return out


# --- presentation inputs for the Adaptive Cards (rendered by show_card.py) ---

def _short(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:40] or 'store'


def _label(window: dict) -> str:
    if window.get('label'):
        return window['label']
    start = datetime.fromisoformat(window['start'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(window['end'].replace('Z', '+00:00'))
    return f"{start:%b} {start.day} – {end:%b} {end.day}, {end.year} ({end.tzname() or 'UTC'})"


def presentation(page: dict, cand: dict, view: dict, suffix: str) -> dict:
    window = cand['window']
    stamp = re.sub(r'[^0-9]', '', cand['generatedAt'])[:14]
    report = {'schema': 'noibu.presentation/1', 'host': 'cowork', 'workflow': WORKFLOW,
              'reportId': f"ab-{_short(page['domain'])}-{stamp}-{suffix}"[:100],
              'domain': {'name': page['domain'], 'id': page['domainId']},
              'window': {'start': window['start'], 'end': window['end'], 'label': _label(window)},
              'generatedAt': cand['generatedAt'],
              'summary': f"{len(cand['tests'])} ranked A/B test idea{'s' if len(cand['tests']) != 1 else ''} for {page['domain']}: {page.get('goal') or 'All goals'}.",
              'abView': view}
    if (page.get('run') or {}).get('timezone'):
        report['timezone'] = page['run']['timezone']
    return report


def main(argv):
    src, out = Path(argv[1]), argv[2]
    page = json.loads(src.read_text(encoding='utf-8'))
    folder = src.parent
    validator = _load_validator()
    for t in page['tests']:
        if t['setup'].get('title', t['title']) != t['title'] or t['createInput'].get('title') != t['title']:
            sys.exit(f'test "{t["title"]}": title, setup.title and createInput.title must match (the create screen shows one title)')
        if t['setup'].get('hypothesis') != t['createInput'].get('hypothesis'):
            sys.exit(f'test "{t["title"]}": setup.hypothesis and createInput.hypothesis must match')
    if out == 'implement':
        rank, draft_id, flag_key, state = int(argv[3]), argv[4], argv[5], argv[6]
        if state not in ('created', 'existing'):
            sys.exit("state must be 'created' or 'existing'")
        cand = json.loads((folder / 'candidates.json').read_text(encoding='utf-8'))
        validator.validate_candidates(cand)
        if not any(t['rank'] == rank for t in cand['tests']):
            sys.exit(f'rank {rank} is not a test in this run (1 to {len(cand["tests"])})')
        if not re.fullmatch(r'[0-9]{1,18}', draft_id):
            sys.exit('draft id must be the numeric Noibu test id from the create or list result')
        path = folder / f'implement-report-{rank}.json'
        path.write_text(json.dumps(presentation(page, cand, {'kind': 'implement', 'rank': rank, 'draftId': draft_id, 'flagKey': flag_key, 'state': state}, f'implement-{rank}'), indent=1, ensure_ascii=False))
        print(f'wrote {path}')
        print(f"console https://console.noibu.com/{page['domainId']}/ab-tests/{draft_id}")
        return 0
    prefix = Path(out).name.removesuffix('.html')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,60}', prefix):
        sys.exit('domain-short must be a simple file-name prefix')
    if not 1 <= len(page['tests']) <= 6:
        sys.exit('a run ships 1 to 6 tests (2 when only 2 survive); record the rest in run.killed')
    wt_path = folder / 'walkthrough.json'
    wt = json.loads(wt_path.read_text(encoding='utf-8')) if wt_path.exists() else {}
    cand = candidates(page, wt, prefix, folder)
    validator.validate_candidates(cand)
    reports = []
    for i in range(1, len(page['tests']) + 1):
        path = folder / report_file(prefix, i)
        path.write_text(build(page, i, folder), encoding='utf-8')
        reports.append(path.name)
    (folder / 'candidates.json').write_text(json.dumps(cand, indent=2, ensure_ascii=False), encoding='utf-8')
    (folder / 'findings-report.json').write_text(json.dumps(presentation(page, cand, {'kind': 'findings', 'liveSiteCheck': cand['liveSiteCheck']}, 'findings'), indent=1, ensure_ascii=False), encoding='utf-8')
    for i in range(1, len(page['tests']) + 1):
        (folder / f'test-report-{i}.json').write_text(json.dumps(presentation(page, cand, {'kind': 'test', 'rank': i, 'reportFile': report_file(prefix, i)}, f'test-{i}'), indent=1, ensure_ascii=False), encoding='utf-8')
    images = sum(1 for t in page['tests'] if all(_pair(folder, t)))
    print(f"wrote {len(reports)} reports ({', '.join(reports)}), candidates.json (validated, noibu.ab-candidates/3), findings-report.json and test-report-<rank>.json"
          + f"; {images} of {len(reports)} reports embed real captured images"
          + ('' if wt else ' (no walkthrough.json: selectors and site facts come from page.json only)'))
    for t in cand['tests']:
        print(f"Test {t['rank']}: {t['title']} · createInputHash {validator.create_hash(t['createInput'])}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
