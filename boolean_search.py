import argparse
import re
from pathlib import Path

from text_processing import lemmatize_token

OPERATORS = {'AND', 'OR', 'NOT'}
PRECEDENCE = {'NOT': 3, 'AND': 2, 'OR': 1}
TOKEN_RE = re.compile(r'\(|\)|AND|OR|NOT|[A-Za-z]+', re.IGNORECASE)


def load_index(index_file: Path) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    if not index_file.exists():
        raise FileNotFoundError(f'Index file not found: {index_file}')
    for line in index_file.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts:
            continue
        index[parts[0]] = set(parts[1:])
    return index



def normalize_query(query: str) -> list[str]:
    result: list[str] = []
    for token in TOKEN_RE.findall(query):
        upper = token.upper()
        if upper in OPERATORS or token in {'(', ')'}:
            result.append(upper if upper in OPERATORS else token)
        else:
            result.append(lemmatize_token(token.lower()))
    return result



def to_postfix(tokens: list[str]) -> list[str]:
    output: list[str] = []
    stack: list[str] = []
    for token in tokens:
        if token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError('Mismatched parentheses in query.')
            stack.pop()
        elif token in OPERATORS:
            while stack and stack[-1] in OPERATORS and PRECEDENCE[stack[-1]] >= PRECEDENCE[token]:
                output.append(stack.pop())
            stack.append(token)
        else:
            output.append(token)
    while stack:
        if stack[-1] in {'(', ')'}:
            raise ValueError('Mismatched parentheses in query.')
        output.append(stack.pop())
    return output



def evaluate_postfix(postfix: list[str], index: dict[str, set[str]], all_docs: set[str]) -> set[str]:
    stack: list[set[str]] = []
    for token in postfix:
        if token == 'NOT':
            if not stack:
                raise ValueError('Invalid query: NOT has no operand.')
            operand = stack.pop()
            stack.append(all_docs - operand)
        elif token in {'AND', 'OR'}:
            if len(stack) < 2:
                raise ValueError(f'Invalid query: {token} has too few operands.')
            right = stack.pop()
            left = stack.pop()
            stack.append(left & right if token == 'AND' else left | right)
        else:
            stack.append(index.get(token, set()))
    if len(stack) != 1:
        raise ValueError('Invalid query.')
    return stack[0]



def main() -> None:
    parser = argparse.ArgumentParser(description='Boolean search over a lemma-based inverted index.')
    parser.add_argument('--query', required=True, help='Boolean query string')
    parser.add_argument('--index-file', default='inverted_index.txt', help='Path to inverted index file')
    args = parser.parse_args()

    index = load_index(Path(args.index_file))
    all_docs = set().union(*index.values()) if index else set()
    normalized_tokens = normalize_query(args.query)
    postfix = to_postfix(normalized_tokens)
    result = sorted(evaluate_postfix(postfix, index, all_docs))

    print(f'Original query: {args.query}')
    print(f"Normalized query: {' '.join(normalized_tokens)}")
    print(f'Found documents: {len(result)}')
    for doc in result:
        print(doc)


if __name__ == '__main__':
    main()