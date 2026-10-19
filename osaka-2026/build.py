#!/usr/bin/env python3
"""Build the static guide from its page, day, style, script and data sources.

Day fragments are authoritative. Default builds synchronize summaries from them.
--preserve-content is the visual-refactor audit mode: extraction only, no data edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'src'
INCLUDE = re.compile(r'<!-- include: ([a-zA-Z0-9_./-]+) -->')
SCRIPT_NAMES = ('disclosures', 'print', 'map', 'router', 'checklist-state', 'checklist')


def json_source(name: str):
    return json.loads((SOURCE / 'data' / name).read_text())


def expand_includes(text: str) -> str:
    def include(match):
        path = (SOURCE / match[1]).resolve()
        if not path.is_relative_to(SOURCE.resolve()):
            raise ValueError('Include escaped source directory')
        return expand_includes(path.read_text().rstrip('\n'))
    return INCLUDE.sub(include, text)


def generate(*, preserve_content: bool = False) -> dict[str, str]:
    document = expand_includes((SOURCE / 'document.html').read_text())
    checklist = json_source('checklist.json')
    map_data = json_source('map.json')
    if not preserve_content:
        from sync import synchronize
        document, map_data, checklist, facts = synchronize(document, map_data, checklist)
    else:
        facts = None
    document = document.replace('__CHECKLIST_JSON__', json.dumps(checklist, ensure_ascii=False).replace('<', '\\u003c'))
    files = {'index.html': document}
    for layer in json_source('style-layers.json'):
        name = layer['name']
        files[f'assets/css/{name}.css'] = (SOURCE / f'styles/{name}.css').read_text()
    for name in SCRIPT_NAMES:
        script = (SOURCE / f'scripts/{name}.js').read_text()
        if name == 'map':
            for key, value in map_data.items():
                script = script.replace('__' + key.upper() + '__', json.dumps(value, ensure_ascii=False))
        files[f'assets/js/{name}.js'] = script
    if facts is not None:
        files['assets/data/itinerary.json'] = json.dumps(facts, ensure_ascii=False, indent=2) + '\n'
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preserve-content', action='store_true')
    parser.add_argument('--check', action='store_true', help='Verify generated files are current without writing')
    parser.add_argument('--mirror', type=Path, help='Also update this deployment directory')
    args = parser.parse_args()
    files = generate(preserve_content=args.preserve_content)
    if args.check:
        stale = [name for name, value in files.items() if not (ROOT / name).exists() or (ROOT / name).read_text() != value]
        if stale:
            raise SystemExit('Outdated generated files: ' + ', '.join(stale))
    else:
        for name, value in files.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        if args.mirror:
            args.mirror.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'index.html', args.mirror / 'index.html')
            shutil.copytree(ROOT / 'assets', args.mirror / 'assets', dirs_exist_ok=True)
    manifest = [{'path': name, 'sha256': hashlib.sha256(value.encode()).hexdigest()} for name, value in files.items()]
    if not args.check:
        (ROOT / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{"Verified" if args.check else "Built"} {len(files)} static artifacts ({"content preserved" if args.preserve_content else "daily itinerary synchronized"}).')


if __name__ == '__main__':
    main()
