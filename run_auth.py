# run_auth.py
from auth_service import create_app, db

app = create_app()

if __name__ == '__main__':
    # Контекст приложения нужен для db.create_all(), если оставляем его в create_app
    # Если используем миграции, эту часть можно убрать отсюда
    with app.app_context():
        # Если db.create_all() вызывается внутри create_app, здесь он не нужен
        # db.create_all() # Возможно, лишний вызов, проверьте create_app
        pass # Оставляем with для других возможных операций в контексте

    # Получаем порт из конфигурации приложения
    port = app.config.get('PORT')
    if port is None:
        print("Warning: PORT not found in app config, defaulting to 5000")
        port = 5000

    app.run(host='0.0.0.0', port=port, debug=True) # Используем 0.0.0.0 для доступности извне (если нужно)
