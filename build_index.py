import argparse
from pathlib import Path

from text_processing import build_page_lemma_map, process_html_file


def main() -> None:
    parser = argparse.ArgumentParser(description='Build an inverted index based on lemmas.')
    parser.add_argument('--pages-dir', default='pages', help='Directory with downloaded HTML pages')
    parser.add_argument('--index-file', default='inverted_index.txt', help='Output file for the inverted index')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    index: dict[str, list[str]] = {}

    for html_file in sorted(pages_dir.glob('page_*.html')):
        tokens = process_html_file(html_file)
        lemma_map = build_page_lemma_map(tokens)
        for lemma in lemma_map:
            index.setdefault(lemma, []).append(html_file.name)

    lines = [f"{lemma} {' '.join(index[lemma])}" for lemma in sorted(index)]
    Path(args.index_file).write_text("\n".join(lines) + ("\n" if lines else ""), encoding='utf-8')

    print(f'Indexed {len(index)} lemmas.')
    print(f'Output file: {args.index_file}')


if __name__ == '__main__':
    main()