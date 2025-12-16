import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.users.models import User

try:
    admin = User.objects.get(username='admin')
    admin.role = 'super_admin'
    admin.save()
    print(f"Updated {admin.username} to role: {admin.role}")
except User.DoesNotExist:
    print("Admin user not found")
