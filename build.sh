#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# TRUCO: Crear superusuario automático si no existe
# (Usuario: admin, Email: admin@example.com, Pass: admin123)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Superusuario ya existe')" | python manage.py shell