from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from process_tokens import TOKEN_RE, clean_html_to_text, heuristic_lemma, is_good_token


def extract_document_terms(html: str) -> set[str]:
    text = clean_html_to_text(html)
    terms: set[str] = set()
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        if not is_good_token(token):
            continue
        lemma = heuristic_lemma(token)
        if is_good_token(lemma):
            terms.add(lemma)
        else:
            terms.add(token)
    return terms


def build_inverted_index(pages_dir: Path) -> dict[str, list[str]]:
    inverted_index: dict[str, set[str]] = defaultdict(set)

    for path in sorted(pages_dir.glob('*.html')):
        html = path.read_text(encoding='utf-8', errors='ignore')
        for term in extract_document_terms(html):
            inverted_index[term].add(path.name)

    return {term: sorted(documents) for term, documents in sorted(inverted_index.items())}


def write_inverted_index(inverted_index: dict[str, list[str]], output_path: Path) -> None:
    lines = []
    for term, documents in inverted_index.items():
        lines.append(' '.join([term, *documents]))
    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def load_inverted_index(index_path: Path) -> dict[str, list[str]]:
    inverted_index: dict[str, list[str]] = {}
    for line in index_path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        term, *documents = parts
        inverted_index[term] = documents
    return inverted_index


def main() -> None:
    parser = argparse.ArgumentParser(description='Построение инвертированного индекса по HTML-документам.')
    parser.add_argument('--pages-dir', default='pages', help='Папка с HTML-файлами.')
    parser.add_argument('--index-out', default='inverted_index.txt', help='Выходной файл для инвертированного индекса.')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists():
        raise FileNotFoundError(f'Папка не найдена: {pages_dir}')

    inverted_index = build_inverted_index(pages_dir)
    write_inverted_index(inverted_index, Path(args.index_out))

    total_postings = sum(len(documents) for documents in inverted_index.values())
    print(f'Готово: {len(inverted_index)} терминов, {total_postings} вхождений в индекс.')


if __name__ == '__main__':
    main()