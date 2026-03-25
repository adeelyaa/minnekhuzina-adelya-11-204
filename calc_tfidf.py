from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from process_tokens import TOKEN_RE, clean_html_to_text, heuristic_lemma, is_good_token


def load_tokens(tokens_path: Path) -> list[str]:
    return [line.strip() for line in tokens_path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_lemma_map(lemmas_path: Path) -> dict[str, list[str]]:
    lemma_map: dict[str, list[str]] = {}
    for line in lemmas_path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        lemma, *tokens = parts
        lemma_map[lemma] = tokens or [lemma]
    return lemma_map


def extract_document_tokens(html: str) -> list[str]:
    text = clean_html_to_text(html)
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        if is_good_token(token):
            tokens.append(token)
    return tokens


def compute_idf(df: int, total_docs: int) -> float:
    if df <= 0:
        return 0.0
    return math.log(total_docs / df)


def build_document_stats(pages_dir: Path) -> dict[str, Counter[str]]:
    stats: dict[str, Counter[str]] = {}
    for path in sorted(pages_dir.glob('*.html')):
        html = path.read_text(encoding='utf-8', errors='ignore')
        tokens = extract_document_tokens(html)
        stats[path.name] = Counter(tokens)
    return stats


def build_term_document_frequency(doc_counters: dict[str, Counter[str]], vocabulary: list[str]) -> dict[str, int]:
    df: dict[str, int] = {term: 0 for term in vocabulary}
    for counter in doc_counters.values():
        present = set(counter)
        for term in vocabulary:
            if term in present:
                df[term] += 1
    return df


def build_lemma_document_frequency(
    doc_counters: dict[str, Counter[str]], lemma_map: dict[str, list[str]]
) -> dict[str, int]:
    df: dict[str, int] = {lemma: 0 for lemma in lemma_map}
    for counter in doc_counters.values():
        present = set(counter)
        for lemma, terms in lemma_map.items():
            if any(term in present for term in terms):
                df[lemma] += 1
    return df


def write_term_tfidf(
    out_dir: Path,
    vocabulary: list[str],
    doc_counters: dict[str, Counter[str]],
    term_idf: dict[str, float],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for document_name, counter in doc_counters.items():
        total_terms = sum(counter.values())
        lines: list[str] = []
        for term in vocabulary:
            tf = (counter.get(term, 0) / total_terms) if total_terms else 0.0
            tf_idf = tf * term_idf[term]
            lines.append(f'{term} {term_idf[term]:.6f} {tf_idf:.6f}')
        output_path = out_dir / document_name.replace('.html', '.txt')
        output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_lemma_tfidf(
    out_dir: Path,
    lemma_map: dict[str, list[str]],
    doc_counters: dict[str, Counter[str]],
    lemma_idf: dict[str, float],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for document_name, counter in doc_counters.items():
        total_terms = sum(counter.values())
        lines: list[str] = []
        for lemma, terms in lemma_map.items():
            term_count_sum = sum(counter.get(term, 0) for term in terms)
            tf = (term_count_sum / total_terms) if total_terms else 0.0
            tf_idf = tf * lemma_idf[lemma]
            lines.append(f'{lemma} {lemma_idf[lemma]:.6f} {tf_idf:.6f}')
        output_path = out_dir / document_name.replace('.html', '.txt')
        output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Подсчёт TF-IDF для терминов и лемм по HTML-документам.')
    parser.add_argument('--pages-dir', default='pages', help='Папка с HTML-файлами.')
    parser.add_argument('--tokens-file', default='tokens.txt', help='Файл со списком терминов из задания 2.')
    parser.add_argument('--lemmas-file', default='lemmas.txt', help='Файл со списком лемм из задания 2.')
    parser.add_argument('--terms-out-dir', default='term_tfidf', help='Папка для TF-IDF по терминам.')
    parser.add_argument('--lemmas-out-dir', default='lemma_tfidf', help='Папка для TF-IDF по леммам.')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists():
        raise FileNotFoundError(f'Папка не найдена: {pages_dir}')

    vocabulary = load_tokens(Path(args.tokens_file))
    lemma_map = load_lemma_map(Path(args.lemmas_file))
    doc_counters = build_document_stats(pages_dir)
    total_docs = len(doc_counters)
    if total_docs == 0:
        raise ValueError('В папке pages нет HTML-файлов.')

    term_df = build_term_document_frequency(doc_counters, vocabulary)
    term_idf = {term: compute_idf(df, total_docs) for term, df in term_df.items()}

    lemma_df = build_lemma_document_frequency(doc_counters, lemma_map)
    lemma_idf = {lemma: compute_idf(df, total_docs) for lemma, df in lemma_df.items()}

    write_term_tfidf(Path(args.terms_out_dir), vocabulary, doc_counters, term_idf)
    write_lemma_tfidf(Path(args.lemmas_out_dir), lemma_map, doc_counters, lemma_idf)

    print(f'Готово: обработано {total_docs} документов.')
    print(f'TF-IDF по терминам: {args.terms_out_dir}')
    print(f'TF-IDF по леммам: {args.lemmas_out_dir}')


if __name__ == '__main__':
    main()