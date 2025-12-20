# StreetFood Telegram Bot

Telegram-бот для заказа стритфуда (Burger, Pizza, Fries, Hot Dog и т.д.)  
Интеграция с Google Sheets для хранения заказов.

## Функции
- Меню с ценами и эмодзи
- Приём заказов
- Запись в Google Sheets
- Деплой через Docker + Helm в Kubernetes

## Технологии
- Python + python-telegram-bot
- Google Sheets API
- Docker
- Helm Chart для Kubernetes

## Как запустить локально
```bash
pip install -r requirements.txt
python bot.py