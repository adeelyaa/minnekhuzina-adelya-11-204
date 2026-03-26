import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from bs4 import BeautifulSoup

# A compact built-in stopword list to avoid extra downloads.
STOPWORDS = {
    'a','about','above','after','again','against','all','am','an','and','any','are','as','at',
    'be','because','been','before','being','below','between','both','but','by','can','could',
    'did','do','does','doing','down','during','each','few','for','from','further','had','has',
    'have','having','he','her','here','hers','herself','him','himself','his','how','i','if','in',
    'into','is','it','its','itself','just','me','more','most','my','myself','no','nor','not','now',
    'of','off','on','once','only','or','other','our','ours','ourselves','out','over','own','same',
    'she','should','so','some','such','than','that','the','their','theirs','them','themselves',
    'then','there','these','they','this','those','through','to','too','under','until','up','very',
    'was','we','were','what','when','where','which','while','who','whom','why','will','with','you',
    'your','yours','yourself','yourselves'
}

# Words often coming from HTML/UI noise on Wikipedia pages.
NOISE_WORDS = {
    'edit', 'jump', 'navigation', 'search', 'menu', 'sidebar', 'toggle', 'contents', 'references',
    'external', 'links', 'retrieved', 'archived', 'citation', 'template', 'wikidata', 'commons',
    'isbn', 'doi', 'pmid', 'redirect', 'hide', 'show'
}

TOKEN_RE = re.compile(r"[a-z]+")


def _build_lemmatizer():
    try:
        import nltk
        from nltk.stem import WordNetLemmatizer
        nltk.data.find('corpora/wordnet')
        try:
            nltk.data.find('corpora/omw-1.4')
        except LookupError:
            pass
        return WordNetLemmatizer()
    except Exception:
        return None


_LEMMATIZER = _build_lemmatizer()


IRREGULARS = {
    'men': 'man', 'women': 'woman', 'children': 'child', 'people': 'person',
    'mice': 'mouse', 'geese': 'goose', 'feet': 'foot', 'teeth': 'tooth'
}


def lemmatize_token(token: str) -> str:
    token = token.lower()
    if token in IRREGULARS:
        return IRREGULARS[token]
    if _LEMMATIZER is not None:
        noun = _LEMMATIZER.lemmatize(token, pos='n')
        verb = _LEMMATIZER.lemmatize(noun, pos='v')
        adj = _LEMMATIZER.lemmatize(verb, pos='a')
        return adj
    # Fallback rule-based normalization if NLTK resources are unavailable.
    if len(token) > 4 and token.endswith('ies'):
        return token[:-3] + 'y'
    if len(token) > 4 and token.endswith('ing'):
        return token[:-3]
    if len(token) > 3 and token.endswith('ed'):
        return token[:-2]
    if len(token) > 3 and token.endswith('es'):
        return token[:-2]
    if len(token) > 3 and token.endswith('s'):
        return token[:-1]
    return token



def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'svg', 'table']):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)



def tokenize_text(text: str) -> List[str]:
    raw_tokens = TOKEN_RE.findall(text.lower())
    cleaned: List[str] = []
    for token in raw_tokens:
        if len(token) < 2:
            continue
        if token in STOPWORDS or token in NOISE_WORDS:
            continue
        cleaned.append(token)
    return cleaned



def process_html_file(path: Path) -> List[str]:
    html = path.read_text(encoding='utf-8', errors='ignore')
    text = extract_visible_text(html)
    return tokenize_text(text)



def build_page_lemma_map(tokens: Iterable[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, set[str]] = defaultdict(set)
    for token in tokens:
        lemma = lemmatize_token(token)
        if lemma in STOPWORDS or lemma in NOISE_WORDS:
            continue
        grouped[lemma].add(token)
    return {lemma: sorted(values) for lemma, values in grouped.items()}