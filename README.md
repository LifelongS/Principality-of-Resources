# Царство ресурсов
-браузерная онлайн-игра в жанре экономической стратегии

## Установка и запуск
1. Установите Python 3.9+ и RabbitMQ.
2. Склонируйте репозиторий:
   ```bash
   git clone <репозиторий-будет-указан-позже>

   3.Установите зависимости
   pip install -r requirements.txt

   4.Запустите RabbitMQ (стандартные настройки).
   5.В разных терминалах выполните:
   python run_auth.py  # AuthService (порт 5000)
   python run_game.py  # GameService (порт 5001)

   6.Откройте в браузере:
    Регистрация: http://localhost:5000/register
    Игра: http://localhost:5001/game