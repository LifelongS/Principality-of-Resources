# run_game.py

import os
import logging
# Убедимся, что game_service/__init__.py определяет create_app
from game_service import create_app
# Импортируем общую функцию запуска потока RabbitMQ
from shared.rabbitmq import start_consumer_thread
# Импортируем специфичный обработчик сообщений для этого сервиса
from game_service.utils import process_user_created_message

# Настройка базового логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем экземпляр приложения Flask с помощью фабрики
# Предполагается, что create_app() загружает GameConfig по умолчанию
app = create_app()

if __name__ == '__main__':
    # === Запуск консьюмера RabbitMQ ===
    # Запускаем в отдельном потоке, чтобы не блокировать запуск Flask
    # Передаем экземпляр app (может понадобиться для контекста),
    # имя очереди для прослушивания и функцию-обработчик
    logger.info("Initializing RabbitMQ consumer thread for 'user_created' queue...")
    start_consumer_thread(app, 'user_created', process_user_created_message)
    logger.info("RabbitMQ consumer thread started.")

    # === Настройка параметров запуска Flask ===
    # Хост: берем из переменной окружения или используем 0.0.0.0
    # 0.0.0.0 делает сервер доступным со всех сетевых интерфейсов машины
    # (удобно для Docker или доступа с других устройств в локальной сети)
    # Если нужна доступность только с локальной машины, используйте '127.0.0.1'
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')

    # Порт: **Берем из конфигурации приложения (GameConfig)**
    port = app.config.get('PORT') # Ключ 'PORT' должен быть определен в GameConfig
    if port is None:
        logger.warning(f"PORT not defined in GameConfig for {app.name}. Defaulting to 5001.")
        port = 5001
    else:
        # Убедимся, что порт - это целое число
        try:
            port = int(port)
        except (ValueError, TypeError):
            logger.error(f"Invalid PORT value '{port}' in configuration. Defaulting to 5001.")
            port = 5001

    # Режим Debug: берем из конфигурации приложения
    debug = app.config.get('DEBUG', False) # Обычно DEBUG=True для разработки

    logger.info(f"Starting GameService Flask app on http://{host}:{port}/")
    logger.info(f"Debug mode: {'ON' if debug else 'OFF'}")

    # === Обработка перезагрузчика Werkzeug (Flask Debugger) ===
    # Если debug=True, Flask может запускать два процесса (основной и дочерний для перезагрузки).
    # Мы хотим, чтобы наш фоновый поток (RabbitMQ) запускался только один раз.
    # Эта проверка гарантирует, что `app.run` будет использовать перезагрузчик только
    # в основном процессе, а не в дочернем, который создается перезагрузчиком.
    # Это стандартный способ предотвратить двойной запуск фоновых задач.
    use_reloader = debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
    if debug:
        logger.info(f"Werkzeug reloader active: {use_reloader} (Prevents duplicate background tasks)")

    # === Запуск Flask приложения ===
    # use_reloader=False передается явно, когда debug=True,
    # чтобы основной вызов app.run сам управлял перезагрузкой правильно
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)