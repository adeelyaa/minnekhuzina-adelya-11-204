from __future__ import annotations

import argparse
import re
from pathlib import Path

from build_index import build_inverted_index, load_inverted_index
from process_tokens import heuristic_lemma, is_good_token

OPERATORS = {'AND', 'OR', 'NOT'}
PRECEDENCE = {'NOT': 3, 'AND': 2, 'OR': 1}
ASSOCIATIVITY = {'NOT': 'right', 'AND': 'left', 'OR': 'left'}
TOKEN_PATTERN = re.compile(r'\(|\)|AND|OR|NOT|[A-Za-z]+(?:[\'’-][A-Za-z]+)*', re.IGNORECASE)


def normalize_term(term: str) -> str:
    value = term.lower()
    lemma = heuristic_lemma(value)
    if is_good_token(lemma):
        return lemma
    return value


def tokenize_query(query: str) -> list[str]:
    raw_tokens = TOKEN_PATTERN.findall(query)
    if not raw_tokens:
        raise ValueError('Пустой запрос.')

    tokens: list[str] = []
    for token in raw_tokens:
        upper = token.upper()
        if upper in OPERATORS or token in {'(', ')'}:
            tokens.append(upper if upper in OPERATORS else token)
        else:
            normalized = normalize_term(token)
            if not is_good_token(normalized):
                raise ValueError(f'Некорректный термин в запросе: {token}')
            tokens.append(normalized)
    return tokens


def to_postfix(tokens: list[str]) -> list[str]:
    output: list[str] = []
    operators: list[str] = []

    for token in tokens:
        if token == '(':
            operators.append(token)
        elif token == ')':
            while operators and operators[-1] != '(':
                output.append(operators.pop())
            if not operators:
                raise ValueError('Несогласованные скобки в запросе.')
            operators.pop()
        elif token in OPERATORS:
            while (
                operators
                and operators[-1] in OPERATORS
                and (
                    PRECEDENCE[operators[-1]] > PRECEDENCE[token]
                    or (
                        PRECEDENCE[operators[-1]] == PRECEDENCE[token]
                        and ASSOCIATIVITY[token] == 'left'
                    )
                )
            ):
                output.append(operators.pop())
            operators.append(token)
        else:
            output.append(token)

    while operators:
        op = operators.pop()
        if op in {'(', ')'}:
            raise ValueError('Несогласованные скобки в запросе.')
        output.append(op)

    return output


def evaluate_postfix(postfix: list[str], inverted_index: dict[str, list[str]], all_docs: set[str]) -> list[str]:
    stack: list[set[str]] = []

    for token in postfix:
        if token == 'NOT':
            if not stack:
                raise ValueError('Некорректное использование оператора NOT.')
            operand = stack.pop()
            stack.append(all_docs - operand)
        elif token in {'AND', 'OR'}:
            if len(stack) < 2:
                raise ValueError(f'Некорректное использование оператора {token}.')
            right = stack.pop()
            left = stack.pop()
            if token == 'AND':
                stack.append(left & right)
            else:
                stack.append(left | right)
        else:
            stack.append(set(inverted_index.get(token, [])))

    if len(stack) != 1:
        raise ValueError('Не удалось вычислить запрос.')

    return sorted(stack.pop())


def search(query: str, pages_dir: Path, index_path: Path | None = None) -> tuple[list[str], dict[str, list[str]]]:
    if index_path is not None and index_path.exists():
        inverted_index = load_inverted_index(index_path)
    else:
        inverted_index = build_inverted_index(pages_dir)
    all_docs = {path.name for path in sorted(pages_dir.glob('*.html'))}
    query_tokens = tokenize_query(query)
    postfix = to_postfix(query_tokens)
    results = evaluate_postfix(postfix, inverted_index, all_docs)
    return results, inverted_index


def main() -> None:
    parser = argparse.ArgumentParser(description='Булев поиск по инвертированному индексу.')
    parser.add_argument('--pages-dir', default='pages', help='Папка с HTML-файлами.')
    parser.add_argument('--query', required=True, help='Булев запрос с операторами AND, OR, NOT и круглыми скобками.')
    parser.add_argument('--index-file', default='inverted_index.txt', help='Файл с инвертированным индексом.')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists():
        raise FileNotFoundError(f'Папка не найдена: {pages_dir}')

    index_path = Path(args.index_file)
    results, _ = search(args.query, pages_dir, index_path)

    print(f'Запрос: {args.query}')
    print(f'Найдено документов: {len(results)}')
    for document in results:
        print(document)


if __name__ == '__main__':
    main()