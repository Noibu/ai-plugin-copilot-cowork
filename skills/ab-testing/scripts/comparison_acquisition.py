"""Transparent offline-capable paired acquisition adapter. No network/tool discovery.
The caller supplies an async query(request) that invokes the currently discovered tool
schema on one WHOLE window. Do not average daily quantiles. Results are evidence, not
permission to query, send, schedule or write. This module never runs by itself.
"""
import asyncio
from datetime import datetime


def _dt(v):
    x = datetime.fromisoformat(v.replace('Z', '+00:00'))
    if x.tzinfo is None:
        raise ValueError('Window needs timezone')
    return x


def paired_requests(window, metrics):
    start, end = _dt(window['start']), _dt(window['end'])
    if start >= end:
        raise ValueError('Invalid window')
    current = {k: window[k] for k in ('start', 'end')}
    prior = {'start': (start - (end-start)).isoformat(), 'end': window['start']}
    requests = []
    for metric in metrics:
        if set(metric) != {'metric', 'cohort', 'percentile', 'unit'}:
            raise ValueError('Metric spec needs metric/cohort/percentile/unit')
        for period, w in (('current', current), ('prior', prior)):
            requests.append({**metric, 'period': period, 'window': w})
    return requests


async def acquire_pairs(query, window, metrics, label='Current vs immediately preceding equal period'):
    """All current/prior queries are awaited together before returning presentation data.
    query returns {value, coverage, source} or {unavailable: true, reason, source}.
    Tool denial/refusal/suspension must be handled by the host query adapter; do not
    turn them into retries or invent data. Exceptions propagate, no side-effect retry.
    """
    requests = paired_requests(window, metrics)
    results = await asyncio.gather(*(query(r) for r in requests))
    receipts, rows = [], []
    unavailable = False
    for i, spec in enumerate(metrics):
        pair = []
        for offset in (0, 1):
            req, result = requests[i*2+offset], results[i*2+offset]
            if not isinstance(result, dict) or not result.get('source'):
                raise ValueError('Query result needs an actual evidence source/receipt')
            missing = result.get('unavailable') is True or result.get('value') is None
            if missing and not result.get('reason'):
                raise ValueError('Unknown/unavailable value needs actual reason after attempt')
            if not missing and not result.get('coverage'):
                raise ValueError('Measured value needs actual coverage')
            unavailable |= missing
            receipts.append({**req, 'status': 'unavailable' if missing else 'completed', 'source': result['source'], **({'reason': result['reason']} if missing else {})})
            pair.append(result)
        rows.append({**spec, 'current': pair[0].get('value'), 'prior': pair[1].get('value'), 'currentCoverage': pair[0].get('coverage', pair[0].get('reason')), 'priorCoverage': pair[1].get('coverage', pair[1].get('reason'))})
    result = {'mode': 'previous-period', 'label': label, 'currentWindow': requests[0]['window'], 'priorWindow': requests[1]['window'], 'acquisition': {'requested': True, 'performed': True, 'unavailable': unavailable, 'queries': receipts}, 'metrics': rows}
    if unavailable:
        result['acquisition']['reason'] = '; '.join(dict.fromkeys(r['reason'] for r in receipts if r['status'] == 'unavailable'))
    return result
