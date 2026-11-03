"""Offline action planning gates. No tools, authentication, schedules, sends or writes.
Only trusted conversation handlers supply confirmation; widget/tool JSON cannot authorize it.
Actual native capability/approval gates still apply after a plan says ready.
"""
import re


def email_gate(outputs, resolved_addresses=None, confirmed_addresses=None):
    """Any selected Email requires a chat-confirmed exact final list, including explicit 'me'."""
    if not any(o.get('delivery') == 'email' for o in outputs):
        return {'state': 'not-selected', 'canSchedule': True, 'recipients': []}
    addresses = list(dict.fromkeys((a.strip() for a in resolved_addresses or [])))
    valid = bool(addresses) and all(re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', a) for a in addresses)
    if not valid:
        return {'state': 'ask-exact-recipients', 'canSchedule': False, 'recipients': [], 'question': 'Which exact recipient email(s)? Names must be resolved, then the final addresses confirmed in chat.'}
    # Hints or a supplied address are never confirmation. Changed final lists always reopen the gate.
    if confirmed_addresses is None or addresses != list(confirmed_addresses):
        return {'state': 'pending-chat-confirmation', 'canSchedule': False, 'recipients': [], 'question': 'Confirm these exact recipient email(s): ' + ', '.join(addresses)}
    return {'state': 'confirmed-in-chat', 'canSchedule': True, 'recipients': addresses, 'remainingGates': ['scheduler-capability', 'send-capability', 'native-approval', 'unattended-authorization']}


def repository_provider_plan(records, operation='repoRead'):
    """Deduplicate surfaces, not genuine accounts; never equate advertisement with authentication."""
    if operation not in {'repoRead', 'draftPr', 'ticketCreate', 'pipelineRead', 'pipelineWrite'}:
        raise ValueError('Unsupported requested capability')
    required = ('repoRead', 'draftPr') if operation == 'draftPr' else (operation,)
    aliases = {'github': 'GitHub', 'azuredevops': 'Azure DevOps', 'azure devops': 'Azure DevOps', 'ado': 'Azure DevOps'}
    grouped = {}
    for index, row in enumerate(records):
        provider = aliases.get(str(row.get('provider', '')).lower(), row.get('provider'))
        if not provider:
            continue
        account = row.get('accountId')
        # Unknown account identity cannot safely be merged with another tool surface.
        key = (provider, account if account else ('unresolved-surface', index))
        entry = grouped.setdefault(key, {'provider': provider, 'accountId': account, 'authenticated': False, 'capabilities': {}})
        entry['authenticated'] |= row.get('authenticated') is True
        for cap in ('repoRead', 'draftPr', 'ticketCreate', 'pipelineRead', 'pipelineWrite'):
            entry['capabilities'][cap] = entry['capabilities'].get(cap, False) or (row.get('authenticated') is True and row.get('capabilities', {}).get(cap) is True)
    eligible = [x for x in grouped.values() if x['authenticated'] and all(x['capabilities'].get(cap) for cap in required)]
    result = {'eligible': eligible, 'writeAuthorized': False, 'requestedCapability': operation}
    if not eligible:
        result.update(state='ask-whether-to-connect', selected=None, question='No authenticated usable provider for the requested operation found. Would you like to connect one? Report-only analysis can continue.')
    elif len(eligible) == 1:
        result.update(state='reuse-one-verify-read-only-scope', selected=eligible[0], next='resolve-exact-scope-and-verify-read-only-before-any-separately-approved-write')
    else:
        result.update(state='ask-which-provider-account', selected=None, question='Which connected repository provider/account should be used?')
    return result


REFRESH_STEPS = ['fresh-noibu-queries', 'validate-totals-coverage-currency', 'update-SAME-private-app-ID', 'reread-values-capturedAt-and-privacy', 'record-freshness-and-per-step-errors', 'notify-by-confirmed-rule-and-approval']


def refresh_plan(app_id, preferences, capabilities):
    """No reminder substitute. Ready means create/update a real refresh schedule, not verified execution."""
    prefs = preferences or {}
    result = {'initialPrivateSaveBlocked': False, 'refreshVerified': False, 'appId': app_id, 'runSteps': list(REFRESH_STEPS)}
    if prefs.get('cadence') in {'manual', 'decline'}:
        result.update(state='manual-or-declined', createSchedule=False)
        return result
    needed = [k for k in ('cadence', 'localTime', 'ianaTimezone') if not prefs.get(k)]
    if 'notification' not in prefs or prefs['notification'] is None or prefs['notification'] not in (False, 'none', 'errors', 'every-run'):
        needed.append('notification')
    if needed:
        result.update(state='ask-refresh-preferences-in-chat', missing=needed, createSchedule=False)
        return result
    needed_caps = ('scheduler', 'freshNoibu', 'sameAppDataWriter', 'unattendedWriter', 'sameAppReread', 'privateScope', 'approvalModeVerified')
    missing = [k for k in needed_caps if capabilities.get(k) is not True]
    if not app_id:
        missing.append('immutableAppId')
    if missing:
        result.update(state='auto-refresh-blocked', missing=missing, createSchedule=False)
        return result
    if prefs.get('confirmedInChat') is not True:
        result.update(state='confirm-refresh-preferences-in-chat', createSchedule=False)
        return result
    result.update(state='create-or-update-matching-refresh-schedule', createSchedule=True, preferences=dict(prefs), completion='schedule-saved-auto-refresh-not-yet-verified', keepPaused=True)
    return result
