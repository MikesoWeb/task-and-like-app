from app import app, db



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # app.run() # Не используйте это при развертывании на сервере; используйте Gunicorn или другой WSGI-сервер
