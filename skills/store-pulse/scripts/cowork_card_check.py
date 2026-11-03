"""Offline check that an Adaptive Card fits Microsoft 365 Copilot Cowork's render_ui schema.

Mirrors the rules render_ui enforces (element allow-list, strict nesting, enum values, chart data
shapes, version 1.6) so a card can be verified in CI or another editor before it reaches Cowork,
where a rejected card silently degrades the report to Markdown tables. Standard library only.

    python cowork_card_check.py card.json        # exit 0 = passes, 1 = lists every problem
"""
import json
import sys

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


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1].strip()); return 2
    with open(argv[1], encoding='utf-8') as fh:
        errors = check(json.load(fh))
    for e in errors:
        print('FAIL', e)
    print('PASS: card fits Cowork render_ui schema' if not errors else f'{len(errors)} problem(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
