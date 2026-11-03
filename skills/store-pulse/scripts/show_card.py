"""Build once and request at most one render through documented Cowork ToolResult.
Host acknowledgement is terminal CARD_ONLY, not independent client visibility.
Unknown delivery is not failure and never authorizes data replay or a second render.
"""
import importlib.util
import json
from pathlib import Path
from aether_tools import ToolDenied, ToolError, ToolRefused, args, log, set_result, tools


def normalize_render_result(result):
    """Only documented ToolResult payload/raw data envelope/text JSON, not arbitrary success.
    payload is normally data; data may retain {status,data}; text may be JSON.
    A card_file, ok/complete envelope, success boolean or prose alone is NOT a receipt.
    """
    envelope_status = result.status
    if envelope_status in {'denied', 'refused'}:
        return envelope_status, None, result.text or str(result.payload)
    if envelope_status in {'omitted', 'partial'}:
        return 'unknown', None, result.text or 'Structured render acknowledgement unavailable'
    bodies = []
    def decode(v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v
    for raw in (result.payload, getattr(result, 'data', None), result.text):
        value = decode(raw)
        if not isinstance(value, dict):
            continue
        # One documented raw envelope level only; no recursive search of arbitrary dictionaries.
        if set(value) == {'status', 'data'} and value['status'] in {'complete', 'ok'}:
            value = decode(value['data'])
        if isinstance(value, dict):
            bodies.append(value)
    for b in bodies:
        if b.get('status') in {'denied', 'refused'}:
            return b['status'], None, result.text or json.dumps(b, default=str)
    if result.is_error or envelope_status in {'failed', 'error'}:
        return 'failed', None, result.text or str(result.payload)
    for b in bodies:
        if b.get('status') in {'failed', 'error'} or b.get('is_error') is True:
            return b.get('status', 'failed'), None, result.text or json.dumps(b, default=str)
    for b in bodies:
        if b.get('status') == 'rendered':
            return 'rendered', b, None
    return 'unknown', None, 'No documented render acknowledgement; delivery outcome unknown. Do not retry or replay the report.'


STAGE_WORDS = {'dependencies': 'a packaged report file is missing', 'import': 'the card builder could not be loaded',
               'read report': 'the report file could not be read', 'read candidates': 'the A/B candidates file could not be read',
               'build': 'the report did not pass validation'}
FALLBACK_INSTRUCTIONS = ('Explicit failure: START the reply with fallback_lead verbatim (one plain sentence saying the visual card '
                         'could not be built or displayed, and the actual reason), then a concise measured text fallback that keeps '
                         'the actual error; no render retry.')


def fallback_lead(stage, exc, built=True):
    """One plain sentence for the user: the card could not be built/displayed, and the actual reason."""
    detail = ' '.join(str(exc).split())[:300].rstrip('.') or type(exc).__name__
    if type(exc).__name__ == 'CardSizeError':
        reason = 'it is larger than the 24 KB chat card limit even in compact form (' + detail + ')'
    else:
        reason = STAGE_WORDS.get(stage, 'an error occurred at the ' + stage + ' step') + ' (' + detail + ')'
    return ('The visual card could not be built because ' if built else 'The visual card could not be displayed because ') + reason + '.'


def main():
    a = args()
    errors = []
    outcome = {'status': 'failed', 'stage': 'dependencies', 'variant': None,
               'render_attempted': False, 'display_confirmed': False, 'errors': errors,
               'response_policy': 'HONEST_ERROR_FALLBACK', 'allow_text_fallback': True,
               'consumer_instructions': FALLBACK_INSTRUCTIONS}
    try:
        skill_dir = Path(a['skill_dir']).expanduser().resolve()
        required = [skill_dir / 'scripts' / name for name in ('build_presentation.py', 'console_links.py')]
        if a.get('candidates'):
            required.append(skill_dir / 'scripts/validate_candidates.py')
        outcome['skill_dir'] = str(skill_dir)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError('Missing packaged report component(s): ' + '; '.join(missing) + '. Use the actual loaded report skill directory from this release, not a sibling/root/older-release path. Do not recreate or skip validation.')
        outcome['stage'] = 'import'
        spec = importlib.util.spec_from_file_location('build_presentation', required[0])
        bp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bp)
        outcome['stage'] = 'read report'
        report = json.loads(Path(a['report']).expanduser().read_text(encoding='utf-8'))
        outcome['stage'] = 'read candidates'
        candidates = json.loads(Path(a['candidates']).expanduser().read_text(encoding='utf-8')) if a.get('candidates') else None
        outcome['stage'] = 'build'
        compact = a.get('compact', False)
        if type(compact) is not bool:
            raise ValueError('compact must be a boolean')
        outcome['variant'] = 'compact' if compact else 'full'
        try:
            card = bp.render_adaptive_card(report, candidates, compact)
        except bp.CardSizeError as exc:
            if compact:
                raise
            errors.append(f'full build: {type(exc).__name__}: {exc}')
            outcome['variant'] = 'compact'
            card = bp.render_adaptive_card(report, candidates, True)
    except Exception as exc:
        errors.append(f'{outcome["stage"]}: {type(exc).__name__}: {exc}')
        outcome.update(fallback_lead=fallback_lead(outcome['stage'], exc), consumer_instructions=FALLBACK_INSTRUCTIONS)
        set_result(outcome)
        return
    outcome['bytes'] = len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    if candidates is not None:
        # A/B: bind each displayed rank to its title and createInput hash, so "Create A/B test N"
        # is checked against exactly what this card showed (validate_candidates.py hash semantics).
        try:
            outcome['abReplyMap'] = [{'rank': c['rank'], 'title': c['title'], 'createInputHash': c['hash']} for c in bp.candidate_data(report, candidates)]
        except Exception as exc:
            errors.append(f'reply map: {type(exc).__name__}: {exc}')
    outcome.update(stage='render', render_attempted=True, status='unknown', response_policy='UNKNOWN_NO_REPLAY', allow_text_fallback=False,
                   consumer_instructions='Outcome unknown: do not say display failed, do not replay data, do not render again. A short uncertainty notice is permitted.')
    try:
        result = tools.core.render_ui(type=card['type'], version=card['version'], body=card['body'])
    except (ToolDenied, ToolRefused):
        raise  # Native denial/refusal/suspension semantics; never bypass or retry.
    except ToolError as exc:
        errors.append(f'{outcome["variant"]} render: {type(exc).__name__}: {exc}')
        outcome.update(status='failed', response_policy='HONEST_ERROR_FALLBACK', allow_text_fallback=True,
                       fallback_lead=fallback_lead('render', exc, built=False), consumer_instructions=FALLBACK_INSTRUCTIONS)
        set_result(outcome)
        return
    except Exception as exc:
        errors.append(f'render outcome unknown: {type(exc).__name__}: {exc}')
        set_result(outcome)
        return
    try:
        state, receipt, detail = normalize_render_result(result)
        outcome.update(tool_status=receipt.get('status') if receipt else None, envelope_status=result.status)
    except Exception as exc:
        errors.append(f'acknowledgement normalization: {type(exc).__name__}: {exc}')
        set_result(outcome)
        return
    if state == 'rendered':
        # Commit ack BEFORE optional diagnostics. A logging exception cannot revoke it.
        outcome.update(status='rendered', card_file=receipt.get('card_file'), acknowledgement=receipt,
                       response_policy='CARD_ONLY', allow_text_fallback=False,
                       consumer_instructions='STOP. Host render acknowledged. No preamble, recap, failed-display claim, text fallback, visibility gate or second render. Client visibility remains independently unverified.')
        if a.get('debug') is True:  # Explicit diagnostic use only; default success streams no chat log.
            try:
                log('%s card acknowledged (%d bytes); client visibility unverified', outcome['variant'], outcome['bytes'])
            except Exception as exc:
                outcome['diagnostic_errors'] = [f'post-ack logging: {type(exc).__name__}: {exc}']
    elif state in {'failed', 'error'}:
        outcome.update(status='failed', response_policy='HONEST_ERROR_FALLBACK', allow_text_fallback=True,
                       fallback_lead='The visual card could not be displayed because the chat host rejected it (' + (' '.join(str(detail).split())[:300].rstrip('.') or 'no detail returned') + ').',
                       consumer_instructions=FALLBACK_INSTRUCTIONS)
        errors.append(detail)
    elif state in {'denied', 'refused'}:
        outcome.update(status=state, response_policy='STOP_NO_RETRY', allow_text_fallback=False,
                       consumer_instructions='Respect native denial/refusal; do not retry or use an alternate route.')
        errors.append(detail)
    else:
        errors.append(detail)
    set_result(outcome)


if __name__ == '__main__':
    main()
