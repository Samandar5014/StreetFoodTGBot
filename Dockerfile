FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install prometheus-client  # <-- Добавь эту строку!

COPY . .

EXPOSE 8000  

ENTRYPOINT ["python3", "bot.py"]