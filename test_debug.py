import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_yamdb.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

# Создаем админа
admin_user = User.objects.create_user(
    username='admin',
    email='admin@test.com',
    password='testpass',
    role='admin'
)

client = APIClient()
client.force_authenticate(user=admin_user)

# Тестовый запрос
data = {'name': 'Фильм', 'slug': 'films'}
response = client.post('/api/v1/categories/', data=data)

print(f"Status: {response.status_code}")
print(f"Response: {response.data}")
