"""Install this authored skill for the selected local coding host."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['codex', 'claude'], required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'skills' / 'ecu-workbench'
    parent = Path.home() / ('.codex' if args.host == 'codex' else '.claude') / 'skills'
    target = parent / source.name
    # Never silently replace a separately maintained skill.
    if target.exists():
        for path in source.rglob('*'):
            if path.is_file() and (not (target / path.relative_to(source)).exists()
                                  or path.read_bytes() != (target / path.relative_to(source)).read_bytes()):
                raise SystemExit('Existing skill differs; review it before replacing')
        print(f'Already installed: {target}')
        return
    parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    print(f'Installed: {target}')


if __name__ == '__main__':
    main()
