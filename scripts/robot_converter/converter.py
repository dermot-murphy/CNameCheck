"""CLI entry point: convert ASPICE Markdown test cases to Robot Framework .robot files."""

import argparse
import sys
from pathlib import Path

from .parser import parse_file
from .generator import generate


def convert_file(md_path: Path, output_dir: Path) -> Path:
    content = md_path.read_text(encoding='utf-8')
    suite = parse_file(content)
    robot_text = generate(suite)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / md_path.with_suffix('.robot').name
    out_path.write_text(robot_text, encoding='utf-8')
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Convert ASPICE Markdown test cases to Robot Framework .robot files.'
    )
    parser.add_argument(
        '--input', '-i', required=True,
        help='Path to a .md file or a directory containing .md test case files.',
    )
    parser.add_argument(
        '--output', '-o', required=True,
        help='Output directory for generated .robot files.',
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if input_path.is_file():
        md_files = [input_path]
    elif input_path.is_dir():
        md_files = sorted(input_path.rglob('*.md'))
    else:
        print(f'ERROR: input path does not exist: {input_path}', file=sys.stderr)
        sys.exit(1)

    if not md_files:
        print(f'No .md files found in {input_path}', file=sys.stderr)
        sys.exit(1)

    for md_file in md_files:
        try:
            out = convert_file(md_file, output_dir)
            print(f'  {md_file} → {out}')
        except Exception as exc:
            print(f'ERROR converting {md_file}: {exc}', file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
