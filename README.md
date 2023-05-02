# Проект парсинга pep
Парсер собирает данные обо всех PEP документах, сравнивает статусы и записывает их в csv файл.
# Установка

Устанавливаем винтуальное окружение:

```
python -m venv venv
```

Активируем venv:

```
source venv/Scripts/activate
```

Обновляем пакетный менеджер pip:

```
pip install --upgrade pip
```

Устанавливаем зависимости:

```
pip install -r requirements.txt
```

# Примеры команд:

Если вам нужен вывод в командную строку, а не в .csv файл, то замените --output file на --output pretty
Информация о PEP:

```
python main.py pep --output file
```

Обновления в Python:

```
python main.py whats-new --output file
```

Информация о версиях Python:

```
python main.py latest-version --output file
```

Версии Python в архиве .zip:

```
python main.py download
```
