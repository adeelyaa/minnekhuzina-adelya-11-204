import argparse
import math
from collections import Counter
from typing import Dict, List, Tuple

from text_processing import build_unique_terms, compute_term_idf, load_documents


def build_document_vectors(documents: Dict[str, List[str]], terms: List[str], idf: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    vectors: Dict[str, Dict[str, float]] = {}
    for doc_name, tokens in documents.items():
        counts = Counter(tokens)
        total = len(tokens) or 1
        vector: Dict[str, float] = {}
        for term in terms:
            tf = counts[term] / total
            weight = tf * idf.get(term, 0.0)
            if weight > 0:
                vector[term] = weight
        vectors[doc_name] = vector
    return vectors



def build_query_vector(query: str, terms: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    query_tokens = [token.lower() for token in query.split() if token.lower().isalpha()]
    counts = Counter(query_tokens)
    total = sum(counts.values()) or 1
    vector: Dict[str, float] = {}
    for term in terms:
        if counts[term] == 0:
            continue
        tf = counts[term] / total
        vector[term] = tf * idf.get(term, 0.0)
    return vector



def cosine_similarity(left: Dict[str, float], right: Dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    common_terms = set(left) & set(right)
    numerator = sum(left[term] * right[term] for term in common_terms)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)



def search(query: str, pages_dir: str, top_k: int) -> List[Tuple[str, float]]:
    documents = load_documents(pages_dir)
    terms = build_unique_terms(documents)
    idf = compute_term_idf(documents, terms)
    doc_vectors = build_document_vectors(documents, terms, idf)
    query_vector = build_query_vector(query, terms, idf)

    results: List[Tuple[str, float]] = []
    for doc_name, doc_vector in doc_vectors.items():
        score = cosine_similarity(query_vector, doc_vector)
        if score > 0:
            results.append((doc_name, score))
    results.sort(key=lambda item: (-item[1], int(item[0].split('_')[1].split('.')[0])))
    return results[:top_k]



def main() -> None:
    parser = argparse.ArgumentParser(description='Векторный поиск по коллекции документов.')
    parser.add_argument('--query', required=True, help='Строка поискового запроса')
    parser.add_argument('--pages-dir', default='pages', help='Папка с HTML-документами')
    parser.add_argument('--top-k', type=int, default=10, help='Сколько результатов показать')
    args = parser.parse_args()

    results = search(args.query, args.pages_dir, args.top_k)

    print(f'Запрос: {args.query}')
    print(f'Найдено результатов: {len(results)}')
    for doc_name, score in results:
        print(f'{doc_name} {score:.6f}')


if __name__ == '__main__':
    main()