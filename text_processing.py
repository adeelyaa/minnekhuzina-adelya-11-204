from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from bs4 import BeautifulSoup

# Compact built-in stop-word list for English so the project works offline.
STOP_WORDS: Set[str] = {
    'a','about','above','after','again','against','all','am','an','and','any','are','as','at','be','because',
    'been','before','being','below','between','both','but','by','can','could','did','do','does','doing','down',
    'during','each','few','for','from','further','had','has','have','having','he','her','here','hers','herself',
    'him','himself','his','how','i','if','in','into','is','it','its','itself','just','me','more','most','my',
    'myself','no','nor','not','of','off','on','once','only','or','other','our','ours','ourselves','out','over',
    'own','same','she','should','so','some','such','than','that','the','their','theirs','them','themselves',
    'then','there','these','they','this','those','through','to','too','under','until','up','very','was','we',
    'were','what','when','where','which','while','who','whom','why','will','with','you','your','yours','yourself',
    'yourselves','also','would','may','might','must','shall','yet','however','within','without','per','via'
}

TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")

# Suffix-based offline lemmatizer. It is intentionally simple, deterministic,
# and does not require any online corpus downloads.
IRREGULAR_LEMMAS = {
    'men': 'man', 'women': 'woman', 'children': 'child', 'people': 'person',
    'mice': 'mouse', 'geese': 'goose', 'teeth': 'tooth', 'feet': 'foot',
    'went': 'go', 'gone': 'go', 'done': 'do', 'did': 'do', 'does': 'do',
    'was': 'be', 'were': 'be', 'is': 'be', 'are': 'be', 'am': 'be',
    'has': 'have', 'had': 'have', 'having': 'have'
}


def read_html_text(path: Path) -> str:
    html = path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(' ')


def normalize_token(token: str) -> str:
    return token.lower().strip("'_")



def is_valid_token(token: str) -> bool:
    if not token:
        return False
    if token in STOP_WORDS:
        return False
    if not token.isalpha():
        return False
    if len(token) < 2:
        return False
    return True



def simple_lemma(token: str) -> str:
    token = token.lower()
    if token in IRREGULAR_LEMMAS:
        return IRREGULAR_LEMMAS[token]

    if len(token) > 4 and token.endswith('ies'):
        return token[:-3] + 'y'
    if len(token) > 4 and token.endswith('ing'):
        stem = token[:-3]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem
    if len(token) > 3 and token.endswith('ed'):
        stem = token[:-2]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem
    if len(token) > 4 and token.endswith('sses'):
        return token[:-2]
    if len(token) > 3 and token.endswith('es'):
        return token[:-2]
    if len(token) > 3 and token.endswith('s') and not token.endswith('ss'):
        return token[:-1]
    return token



def extract_tokens_from_text(text: str) -> List[str]:
    tokens: List[str] = []
    for match in TOKEN_RE.findall(text.lower()):
        token = normalize_token(match)
        if is_valid_token(token):
            tokens.append(token)
    return tokens



def extract_tokens_from_html(path: Path) -> List[str]:
    return extract_tokens_from_text(read_html_text(path))



def load_documents(pages_dir: str = 'pages') -> Dict[str, List[str]]:
    docs: Dict[str, List[str]] = {}
    for path in sorted(Path(pages_dir).glob('page_*.html'), key=lambda p: int(p.stem.split('_')[1])):
        docs[path.name] = extract_tokens_from_html(path)
    return docs



def build_unique_terms(documents: Dict[str, List[str]]) -> List[str]:
    return sorted({token for tokens in documents.values() for token in tokens})



def build_lemma_mapping(terms: Iterable[str]) -> Dict[str, List[str]]:
    lemma_map: Dict[str, List[str]] = defaultdict(list)
    for token in sorted(set(terms)):
        lemma_map[simple_lemma(token)].append(token)
    return dict(sorted(lemma_map.items()))



def build_inverted_index(documents: Dict[str, List[str]]) -> Dict[str, List[str]]:
    postings: Dict[str, Set[str]] = defaultdict(set)
    for doc_name, tokens in documents.items():
        for token in set(tokens):
            postings[token].add(doc_name)
    return {term: sorted(doc_names, key=lambda n: int(n.split('_')[1].split('.')[0])) for term, doc_names in sorted(postings.items())}



def compute_term_idf(documents: Dict[str, List[str]], terms: Iterable[str]) -> Dict[str, float]:
    total_docs = len(documents)
    doc_sets = {doc_name: set(tokens) for doc_name, tokens in documents.items()}
    idf: Dict[str, float] = {}
    for term in terms:
        df = sum(1 for tokens in doc_sets.values() if term in tokens)
        if df == 0:
            continue
        idf[term] = math.log(total_docs / df)
    return idf



def compute_lemma_idf(documents: Dict[str, List[str]], lemma_map: Dict[str, List[str]]) -> Dict[str, float]:
    total_docs = len(documents)
    doc_sets = {doc_name: set(tokens) for doc_name, tokens in documents.items()}
    idf: Dict[str, float] = {}
    for lemma, lemma_terms in lemma_map.items():
        lemma_term_set = set(lemma_terms)
        df = sum(1 for tokens in doc_sets.values() if tokens & lemma_term_set)
        if df == 0:
            continue
        idf[lemma] = math.log(total_docs / df)
    return idf



def compute_term_tfidf(documents: Dict[str, List[str]], terms: Iterable[str]) -> Dict[str, List[Tuple[str, float, float]]]:
    idf = compute_term_idf(documents, terms)
    result: Dict[str, List[Tuple[str, float, float]]] = {}
    for doc_name, tokens in documents.items():
        counts = Counter(tokens)
        total_terms = len(tokens) or 1
        rows: List[Tuple[str, float, float]] = []
        for term in sorted(terms):
            term_idf = idf.get(term, 0.0)
            tf = counts[term] / total_terms
            tfidf = tf * term_idf
            rows.append((term, term_idf, tfidf))
        result[doc_name] = rows
    return result



def compute_lemma_tfidf(documents: Dict[str, List[str]], lemma_map: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, float, float]]]:
    idf = compute_lemma_idf(documents, lemma_map)
    result: Dict[str, List[Tuple[str, float, float]]] = {}
    for doc_name, tokens in documents.items():
        counts = Counter(tokens)
        total_terms = len(tokens) or 1
        rows: List[Tuple[str, float, float]] = []
        for lemma, lemma_terms in lemma_map.items():
            lemma_tf = sum(counts[term] for term in lemma_terms) / total_terms
            tfidf = lemma_tf * idf.get(lemma, 0.0)
            rows.append((lemma, idf.get(lemma, 0.0), tfidf))
        result[doc_name] = rows
    return result