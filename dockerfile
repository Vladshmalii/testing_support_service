FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/


# Отладочные команды для диагностики структуры проекта
RUN echo "=== Структура проекта ===" && \
    find . -type f -name "*.py" | head -20 && \
    echo "=== Содержимое src (если есть) ===" && \
    ls -la src/ 2>/dev/null || echo "Папка src не найдена" && \
    echo "=== Содержимое корня ===" && \
    ls -la *.py 2>/dev/null || echo "Python файлы в корне не найдены" && \
    echo "=== Проверка main.py ===" && \
    ls -la main.py 2>/dev/null || ls -la src/main.py 2>/dev/null || echo "main.py не найден"

# Создаем src/__init__.py если его нет
RUN mkdir -p src && touch src/__init__.py

# Копируем и настраиваем entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["app"]