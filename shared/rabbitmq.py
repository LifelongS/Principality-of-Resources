# shared/rabbitmq.py
import pika
import json
import logging
import time
import threading
from flask import current_app # Используем current_app для доступа к config

logger = logging.getLogger(__name__)

# --- Функция для отправки сообщений ---
def send_message(queue_name: str, message_body: dict):
    """
    Отправляет JSON-сообщение в указанную очередь RabbitMQ.

    Args:
        queue_name: Имя очереди.
        message_body: Словарь Python, который будет сериализован в JSON.
    """
    connection = None
    try:
        # Получаем хост из конфигурации текущего Flask-приложения
        # Важно: эта функция должна вызываться из контекста запроса или приложения Flask
        # ИЛИ ей нужно передавать config/app явно, если она вызывается вне контекста.
        # Для простоты предположим, что она вызывается из роутов Flask.
        rmq_host = current_app.config.get('RABBITMQ_HOST', 'localhost')

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rmq_host))
        channel = connection.channel()

        # Объявляем очередь как durable=True для устойчивости
        channel.queue_declare(queue=queue_name, durable=True)

        # Сериализуем сообщение
        body_str = json.dumps(message_body)

        # Публикуем сообщение с delivery_mode=2 для персистентности
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=body_str,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Сделать сообщение постоянным
                content_type='application/json',
            )
        )
        logger.info(f"Sent message to queue '{queue_name}'. Body: {body_str[:100]}...") # Логгируем часть тела
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ at {rmq_host}: {e}")
    except Exception as e:
        logger.error(f"Error sending message to RabbitMQ queue '{queue_name}': {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
            logger.debug(f"RabbitMQ connection closed for sending to '{queue_name}'.")

# --- Функции для запуска консьюмера ---

def _consumer_loop(app, queue_name: str, processing_callback: callable):
    """
    Внутренний цикл консьюмера, обрабатывающий соединение и сообщения.

    Args:
        app: Экземпляр Flask приложения (для доступа к контексту и конфигурации).
        queue_name: Имя очереди для прослушивания.
        processing_callback: Функция, которая будет вызвана для обработки
                             каждого сообщения. Должна принимать один аргумент -
                             десериализованное тело сообщения (словарь).
                             Эта функция будет запущена внутри app_context.
    """
    logger.info(f"Consumer thread for queue '{queue_name}' started. Waiting for app context...")
    time.sleep(2) # Даем приложению время на запуск

    while True:
        connection = None
        try:
            rmq_host = app.config.get('RABBITMQ_HOST', 'localhost')
            logger.info(f"Attempting RabbitMQ connection to {rmq_host} for queue '{queue_name}'...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rmq_host))
            channel = connection.channel()

            # Объявляем очередь здесь тоже (durable=True) на случай, если консьюмер запустился первым
            # Или если отправителя нет. Идемпотентно.
            channel.queue_declare(queue=queue_name, durable=True)

            # Настраиваем prefetch_count=1, чтобы worker брал только одно сообщение за раз.
            # Помогает распределять нагрузку, если будет несколько инстансов консьюмера.
            channel.basic_qos(prefetch_count=1)

            def callback_wrapper(ch, method, properties, body):
                """Обертка для вызова processing_callback внутри app_context и ack/nack."""
                logger.debug(f"Received message from '{queue_name}'. Delivery tag: {method.delivery_tag}")
                message_data = None
                try:
                    message_data = json.loads(body)
                    # Выполняем реальную обработку внутри контекста приложения
                    with app.app_context():
                        processing_callback(message_data)

                    # Подтверждаем успешную обработку сообщения
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.debug(f"Message acked. Delivery tag: {method.delivery_tag}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON message from '{queue_name}': {e}. Body: {body[:100]}...")
                    # Отклоняем сообщение без повторной постановки в очередь (requeue=False)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    logger.error(f"Error processing message from '{queue_name}': {e}. Data: {message_data}")
                    # Отклоняем сообщение, но можно вернуть в очередь (requeue=True), если ошибка временная
                    # Осторожно: может привести к зацикливанию, если ошибка постоянная.
                    # Лучше False, а проблемные сообщения анализировать отдельно (Dead Letter Queue)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    # Можно добавить откат db.session.rollback() здесь, если ошибка была в БД
                    with app.app_context():
                       from flask_sqlalchemy import get_debug_queries # Пример доступа к db
                       # Проверяем, есть ли db в расширениях app
                       if 'sqlalchemy' in app.extensions:
                           db = app.extensions['sqlalchemy'].db
                           db.session.rollback()
                           logger.warning("Database session rolled back due to processing error.")


            # Устанавливаем auto_ack=False для ручного подтверждения
            channel.basic_consume(queue=queue_name, on_message_callback=callback_wrapper, auto_ack=False)

            logger.info(f"[*] Waiting for messages in queue '{queue_name}'. To exit press CTRL+C")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"RabbitMQ connection failed for queue '{queue_name}': {e}. Retrying in 5 seconds...")
            if connection and connection.is_open:
                connection.close()
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info(f"[-] Consumer for queue '{queue_name}' stopped by user.")
            if connection and connection.is_open:
                connection.close()
            break # Выход из цикла while True
        except Exception as e:
            logger.error(f"[!] An unexpected error occurred in the consumer loop for '{queue_name}': {e}")
            if connection and connection.is_open:
                connection.close()
            time.sleep(10) # Ждем дольше при неизвестной ошибке

def start_consumer_thread(app, queue_name: str, processing_callback: callable):
    """
    Запускает консьюмер RabbitMQ для указанной очереди в отдельном демон-потоке.

    Args:
        app: Экземпляр Flask приложения.
        queue_name: Имя очереди для прослушивания.
        processing_callback: Функция для обработки сообщений (принимает словарь).
    """
    consumer_thread = threading.Thread(
        target=_consumer_loop,
        args=(app, queue_name, processing_callback),
        daemon=True # Поток завершится, когда завершится основной процесс
    )
    consumer_thread.start()
    logger.info(f"RabbitMQ consumer thread initiated for queue '{queue_name}'.")
    return consumer_thread