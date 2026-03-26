import argparse
from pathlib import Path

from text_processing import build_page_lemma_map, process_html_file


def write_page_tokens(page_name: str, tokens: list[str], output_dir: Path) -> None:
    unique_tokens = sorted(set(tokens))
    output_path = output_dir / f"{Path(page_name).stem}_tokens.txt"
    output_path.write_text("\n".join(unique_tokens) + ("\n" if unique_tokens else ""), encoding='utf-8')



def write_page_lemmas(page_name: str, tokens: list[str], output_dir: Path) -> None:
    lemma_map = build_page_lemma_map(tokens)
    lines = [f"{lemma} {' '.join(lemma_map[lemma])}" for lemma in sorted(lemma_map)]
    output_path = output_dir / f"{Path(page_name).stem}_lemmas.txt"
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding='utf-8')



def main() -> None:
    parser = argparse.ArgumentParser(description='Create token and lemma files for each crawled page.')
    parser.add_argument('--pages-dir', default='pages', help='Directory with downloaded HTML pages')
    parser.add_argument('--tokens-dir', default='tokens_by_page', help='Output directory for token files')
    parser.add_argument('--lemmas-dir', default='lemmas_by_page', help='Output directory for lemma files')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    tokens_dir = Path(args.tokens_dir)
    lemmas_dir = Path(args.lemmas_dir)
    tokens_dir.mkdir(parents=True, exist_ok=True)
    lemmas_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(pages_dir.glob('page_*.html'))
    for html_file in html_files:
        tokens = process_html_file(html_file)
        write_page_tokens(html_file.name, tokens, tokens_dir)
        write_page_lemmas(html_file.name, tokens, lemmas_dir)

    print(f'Processed {len(html_files)} documents.')
    print(f'Token files: {tokens_dir}')
    print(f'Lemma files: {lemmas_dir}')


if __name__ == '__main__':
    main()