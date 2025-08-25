# API YaMDb

REST API для сбора отзывов пользователей на произведения различных категорий.

## Возможности

- ** Управление пользователями** (регистрация, аутентификация, роли)
- ** Работа с произведениями** (фильмы, книги, музыка)
- ** Система отзывов и оценок** (1-10 баллов)
- ** Комментарии к отзывам**
- ** Поиск и фильтрация** по различным параметрам
- ** Пагинация** и сортировка результатов

## Технологии

- **Python 3.11+**
- **Django 4.2+**
- **Django REST Framework 3.14+**
- **Simple JWT** для аутентификации
- **PostgreSQL** (продакшен) / **SQLite** (разработка)
- **Django Filter** для поиска и фильтрации

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd api-yamdb


2. Создание виртуального окружения
    bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # или
    venv\Scripts\activate     # Windows

3. Установка зависимостей
    bash
    pip install -r requirements.txt

5. Миграции и запуск
    bash
    python manage.py migrate
    python manage.py runserver


 API Endpoints
 Аутентификация
POST /api/v1/auth/signup/ - Регистрация пользователя

POST /api/v1/auth/token/ - Получение JWT токена

 Пользователи
GET /api/v1/users/ - Список пользователей (только admin)

POST /api/v1/users/ - Создание пользователя (admin)

GET /api/v1/users/me/ - Профиль текущего пользователя

 Произведения (Titles)
GET /api/v1/titles/ - Список произведений

POST /api/v1/titles/ - Создание произведения (admin)

GET /api/v1/titles/{id}/ - Детали произведения

PATCH /api/v1/titles/{id}/ - Обновление произведения (admin)

 Отзывы (Reviews)
GET /api/v1/titles/{title_id}/reviews/ - Отзывы к произведению

POST /api/v1/titles/{title_id}/reviews/ - Создание отзыва

GET /api/v1/titles/{title_id}/reviews/{review_id}/ - Детали отзыва

 Комментарии (Comments)
GET /api/v1/titles/{title_id}/reviews/{review_id}/comments/

POST /api/v1/titles/{title_id}/reviews/{review_id}/comments/