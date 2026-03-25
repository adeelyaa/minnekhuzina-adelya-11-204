# Deployment Manual

1. Установить Python 3
2. Установить зависимости:
   `pip install -r requirements.txt`
3. Запустить краулер:
   `python crawler.py`
4. Выполнить токенизацию и лемматизацию:
   `python process_tokens.py`
5. Построить инвертированный индекс:
   `python build_index.py`
6. Выполнить булев поиск:
   `python boolean_search.py --query "(roman AND empire) OR caesar"`