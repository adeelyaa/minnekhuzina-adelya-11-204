from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup, Comment
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Дополняем базовый список стоп-слов словами, которые часто приходят из вики-разметки/навигации
EXTRA_STOPWORDS = {
    'also', 'would', 'could', 'one', 'two', 'three', 'first', 'second', 'new',
    'may', 'many', 'however', 'within', 'without', 'using', 'used', 'use',
    'page', 'pages', 'article', 'articles', 'edit', 'menu', 'search', 'hide',
    'show', 'toggle', 'content', 'contents', 'main', 'sidebar', 'navigation',
    'current', 'events', 'random', 'contact', 'contribute', 'help', 'learn',
    'community', 'recent', 'changes', 'upload', 'file', 'files', 'special',
    'appearance', 'donate', 'create', 'account', 'log', 'personal', 'tools',
    'table', 'english', 'retrieved', 'archived', 'isbn', 'doi', 'pmid',
    'citation', 'citations', 'references', 'external', 'links'
}

STOPWORDS = set(ENGLISH_STOP_WORDS) | EXTRA_STOPWORDS
TOKEN_RE = re.compile(r"[a-z]+(?:['’-][a-z]+)*")
BAD_SUBSTRINGS = {'amp', 'nbsp', 'quot', 'lt', 'gt', 'http', 'https', 'www'}


def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(['script', 'style', 'noscript', 'svg', 'math', 'table']):
        tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    text = soup.get_text(' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()


def is_good_token(token: str) -> bool:
    normalized = token.replace("'", '').replace('’', '').replace('-', '')
    if len(normalized) < 3:
        return False
    if token in STOPWORDS:
        return False
    if any(part.isdigit() for part in re.split(r"['’-]", token)):
        return False
    if any(substr in token for substr in BAD_SUBSTRINGS):
        return False
    parts = re.split(r"['’-]", token)
    if any(len(part) == 1 for part in parts if part):
        return False
    return True


def heuristic_lemma(token: str) -> str:
    """Простой rule-based лемматизатор для английского текста.

    Без внешних моделей он не идеален, но хорошо сводит частотные формы:
    plural -> singular, -ing/-ed формы -> базовая форма, -ies -> y и т.п.
    """
    irregular = {
        'children': 'child', 'men': 'man', 'women': 'woman', 'people': 'person',
        'mice': 'mouse', 'geese': 'goose', 'teeth': 'tooth', 'feet': 'foot',
        'data': 'datum', 'indices': 'index', 'analyses': 'analysis',
        'studies': 'study', 'studying': 'study', 'studied': 'study',
        'running': 'run', 'ran': 'run', 'written': 'write', 'wrote': 'write',
        'seen': 'see', 'saw': 'see', 'made': 'make', 'making': 'make',
        'does': 'do', 'did': 'do', 'done': 'do', 'has': 'have', 'had': 'have',
        'was': 'be', 'were': 'be', 'is': 'be', 'are': 'be', 'been': 'be',
    }
    if token in irregular:
        return irregular[token]

    word = token

    if len(word) > 4 and word.endswith("'s"):
        word = word[:-2]

    if len(word) > 5 and word.endswith('ies'):
        return word[:-3] + 'y'

    if len(word) > 5 and word.endswith('ves'):
        return word[:-3] + 'f'

    if len(word) > 5 and word.endswith('ing'):
        base = word[:-3]
        if len(base) >= 3 and base[-1] == base[-2]:
            base = base[:-1]
        if not base.endswith('e') and len(base) > 3:
            base_e = base + 'e'
            # make -> making, migrate -> migrating
            if base[-1] not in 'aeiouy':
                return base_e
        return base

    if len(word) > 4 and word.endswith('ied'):
        return word[:-3] + 'y'

    if len(word) > 4 and word.endswith('ed'):
        base = word[:-2]
        if len(base) >= 3 and base[-1] == base[-2]:
            base = base[:-1]
        if len(base) > 3 and base[-1] not in 'aeiouy':
            return base + 'e'
        return base

    if len(word) > 4 and word.endswith('es') and not word.endswith(('aes', 'ees', 'oes')):
        if word.endswith(('sses', 'shes', 'ches', 'xes', 'zes')):
            return word[:-2]

    if len(word) > 3 and word.endswith('s') and not word.endswith(('ss', 'us', 'is')):
        return word[:-1]

    return word


def extract_tokens_from_dir(pages_dir: Path) -> list[str]:
    tokens = set()
    for path in sorted(pages_dir.glob('*.html')):
        html = path.read_text(encoding='utf-8', errors='ignore')
        text = clean_html_to_text(html)
        for match in TOKEN_RE.finditer(text):
            token = match.group(0)
            if is_good_token(token):
                tokens.add(token)
    return sorted(tokens)


def build_lemma_map(tokens: list[str]) -> dict[str, list[str]]:
    lemma_map: dict[str, list[str]] = defaultdict(list)
    for token in tokens:
        lemma = heuristic_lemma(token)
        if is_good_token(lemma):
            lemma_map[lemma].append(token)
        else:
            lemma_map[token].append(token)

    return {lemma: sorted(set(group)) for lemma, group in sorted(lemma_map.items())}


def write_tokens(tokens: list[str], output_path: Path) -> None:
    output_path.write_text('\n'.join(tokens) + '\n', encoding='utf-8')


def write_lemmas(lemma_map: dict[str, list[str]], output_path: Path) -> None:
    lines = []
    for lemma, group in lemma_map.items():
        lines.append(' '.join([lemma, *group]))
    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Токенизация и группировка токенов по леммам.')
    parser.add_argument('--pages-dir', default='pages', help='Папка с HTML-файлами.')
    parser.add_argument('--tokens-out', default='tokens.txt', help='Файл для списка токенов.')
    parser.add_argument('--lemmas-out', default='lemmas.txt', help='Файл для лемматизированных токенов.')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists():
        raise FileNotFoundError(f'Папка не найдена: {pages_dir}')

    tokens = extract_tokens_from_dir(pages_dir)
    lemma_map = build_lemma_map(tokens)

    write_tokens(tokens, Path(args.tokens_out))
    write_lemmas(lemma_map, Path(args.lemmas_out))

    print(f'Готово: найдено {len(tokens)} уникальных токенов и {len(lemma_map)} лемм.')


if __name__ == '__main__':
    main()