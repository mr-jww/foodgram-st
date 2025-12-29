# Проект Foodgram

Сайт, на котором пользователи могут публиковать своим рецепты, добавлять чужие в избранное и подписываться на публикации других авторов. Сервис позволяет создавать список продуктов, которые следует купить для приготвления тех или иных блюд. Публикации сопровождаются картинками. 

## Технологии
- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose
- Nginx

## Как локально запустить проект

1. Необходимо клонировать репозиторий:
```bash
git clone https://github.com/mr-jww/foodgram-project.git
```

2. В папке `infra` нужно создать файл `.env` и заполнить его следующей информацией:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=твои_секретный_ключ
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
```
3. Из этой же папки `infra` запускается docker-compose:
```bash
docker compose up -d --build
```

4. Далее выполняются миграции, собирается статистика и загружаются ингредиенты:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --no-input
docker compose exec backend python manage.py load_ingredients
```

5. Создание суперпользователя:
```bash
docker compose exec backend python manage.py createsuperuser
```

6. Проект становится локально доступным по адресу: http://localhost/

### Автор: Руденко Роман