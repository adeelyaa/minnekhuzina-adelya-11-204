# Задания 1, 2 и 3

## Автор
Миннехузина Аделя, группа 11-204

## Что есть в репозитории
- `crawler.py` — краулер для первого задания
- `pages/` — 100 сохранённых HTML-страниц
- `index.txt` — соответствие номера файла и URL
- `process_tokens.py` — токенизация сохранённых документов и группировка токенов по леммам
- `tokens.txt` — список уникальных токенов
- `lemmas.txt` — список лемм и соответствующих токенов
- `build_index.py` — построение инвертированного индекса
- `boolean_search.py` — булев поиск по инвертированному индексу
- `inverted_index.txt` — файл с инвертированным индексом

## Задание 1
Программа скачивает 100 HTML-страниц с Wikipedia (английский язык) и сохраняет их в папку `pages` без очистки HTML-разметки.

Запуск:

```bash
pip install -r requirements.txt
python crawler.py
```

## Задание 2
Скрипт `process_tokens.py`:
- извлекает текст из сохранённых HTML-документов;
- выделяет отдельные слова;
- удаляет дубликаты, числа, стоп-слова и мусорные токены;
- группирует токены по леммам;
- сохраняет результат в `tokens.txt` и `lemmas.txt`.

Запуск:

```bash
pip install -r requirements.txt
python process_tokens.py
```

## Задание 3
### Построение инвертированного индекса
Скрипт `build_index.py`:
- обходит все HTML-документы в папке `pages/`;
- извлекает термины с той же нормализацией, что и во втором задании;
- лемматизирует термины;
- строит инвертированный индекс вида «термин → список документов»;
- сохраняет результат в `inverted_index.txt`.

Запуск:

```bash
python build_index.py
```

### Булев поиск
Скрипт `boolean_search.py` поддерживает операторы:
- `AND`
- `OR`
- `NOT`
- круглые скобки для сложных запросов

Примеры запуска:

```bash
python boolean_search.py --query "caesar"
python boolean_search.py --query "roman AND empire"
python boolean_search.py --query "(roman AND empire) OR caesar"
python boolean_search.py --query "history AND NOT war"
```

По умолчанию поиск использует файл `inverted_index.txt`. При его отсутствии индекс будет построен заново по папке `pages/`.

## Формат выходных файлов
### `tokens.txt`
Каждая строка содержит один токен:

```text
token
```

### `lemmas.txt`
Каждая строка содержит лемму и все токены, которые к ней отнесены:

```text
<lemma> <token1> <token2> ... <tokenN>
```

### `inverted_index.txt`
Каждая строка содержит термин и список документов, в которых он встречается:

```text
<term> <document1> <document2> ... <documentN>
```
