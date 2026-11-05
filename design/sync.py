"""Copy the runtime UX guidelines into every skill, or check that the copies match.

Cowork loads each skill folder on its own, so every skill carries its own copy of
design/ux-runtime.md as references/ux-guidelines.md. Edit the source only, then sync.

    python design/sync.py           # write/refresh the copies
    python design/sync.py --check   # exit 1 if any copy is missing or out of date (for CI)

Skills are read from manifest.json (agentSkills[].folder). Standard library only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'design' / 'ux-runtime.md'
TARGET = Path('references') / 'ux-guidelines.md'


def skill_dirs():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    return [(ROOT / s['folder']).resolve() for s in manifest.get('agentSkills', [])]


def main(argv):
    check = '--check' in argv
    source = SOURCE.read_bytes()
    stale = []
    for skill in skill_dirs():
        if not (skill / 'SKILL.md').is_file():
            print(f'SKIP {skill.relative_to(ROOT)}: no SKILL.md')
            continue
        target = skill / TARGET
        if target.is_file() and target.read_bytes() == source:
            continue
        stale.append(target)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source)
            print(f'WROTE {target.relative_to(ROOT)}')
    if check:
        for target in stale:
            print(f'STALE {target.relative_to(ROOT)}')
        print('OK: every skill has the current UX guidelines' if not stale
              else f'{len(stale)} skill(s) out of date: run python design/sync.py')
        return 1 if stale else 0
    print(f'Synced {len(stale)} file(s)' if stale else 'Already up to date')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
