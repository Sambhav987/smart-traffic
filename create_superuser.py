
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_traffic_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = 'sambhav'
email = 'sambhavagarwal6@gmail.com'
password = 'sambhav987'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser: {username}")
    User.objects.create_superuser(username, email, password)
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")
