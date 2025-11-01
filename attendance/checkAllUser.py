# import os
# import django
# from datetime import date

# # Setup Django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")
# django.setup()

# from django.contrib.auth.models import User
# from attendance.models import Employee
# from zk import ZK, const

# # Device configuration
# DEVICE_IP = "192.168.1.201"
# DEVICE_PORT = 4370
# TIMEOUT = 5  # seconds

# zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=TIMEOUT)

# try:
#     print(f"🔌 Connecting to ZKTeco device at {DEVICE_IP}:{DEVICE_PORT} ...")
#     conn = zk.connect()
#     conn.disable_device()

#     users = conn.get_users() or []
#     print(f"✅ Total users on device: {len(users)}")

#     for user in users:
#         # Normalize username: lowercase, remove spaces
#         username = user.name.replace(" ", "").lower()
#         email = f"{username}@example.com"
#         password = user.password or "password123"

#         # Get or create Django user
#         django_user, created_user = User.objects.get_or_create(
#             username=username,
#             defaults={
#                 "email": email,
#                 "password": password,
#                 "first_name": user.name.split(' ')[0] if ' ' in user.name else user.name,
#                 "last_name": ' '.join(user.name.split(' ')[1:]) if ' ' in user.name else '',
#             }
#         )

#         if not created_user:
#             # Update existing user
#             django_user.email = email
#             django_user.set_password(password)
#             django_user.first_name = user.name.split(' ')[0] if ' ' in user.name else user.name
#             django_user.last_name = ' '.join(user.name.split(' ')[1:]) if ' ' in user.name else ''
#             django_user.save()

#         # Get or create Employee linked to Django user
#         employee, created_emp = Employee.objects.get_or_create(
#             fingerPrintID=user.user_id,
#             defaults={
#                 "user": django_user,
#                 "password": password,
#                 "date_of_birth": date(2000, 1, 1),  # placeholder
#                 "salary": 0,
#             }
#         )

#         if not created_emp:
#             employee.user = django_user
#             employee.password = password
#             employee.save()

#         print(f"✅ Processed user: ID={user.user_id}, Name='{user.name}'")

#     print("🔓 Re-enabling device and disconnecting...")
#     conn.enable_device()
#     conn.disconnect()
#     print("🎉 All users processed successfully.")

# except Exception as e:
#     print(f"❌ Error connecting to device {DEVICE_IP}: {e}")





import os
import django
from datetime import date

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")
django.setup()

from django.contrib.auth.models import User
from attendance.models import Employee
from zk import ZK, const

# Device configuration
DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370
TIMEOUT = 5  # seconds

zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=TIMEOUT)

print(f"🔌 Connecting to ZKTeco device at {DEVICE_IP}:{DEVICE_PORT} ...")
conn = zk.connect()
conn.disable_device()

users = conn.get_users() or []
print(f"✅ Total users on device: {len(users)}")

for user in users:
    # Normalize username: lowercase, remove spaces
    username = user.name.replace(" ", "").lower()
    email = f"{username}@example.com"
    password = user.password or "password123"

    # Get or create Django user
    django_user, created_user = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "password": password,
            "first_name": user.name.split(' ')[0] if ' ' in user.name else user.name,
            "last_name": ' '.join(user.name.split(' ')[1:]) if ' ' in user.name else '',
        }
    )

    if not created_user:
        # Update existing user
        django_user.email = email
        django_user.set_password(password)
        django_user.first_name = user.name.split(' ')[0] if ' ' in user.name else user.name
        django_user.last_name = ' '.join(user.name.split(' ')[1:]) if ' ' in user.name else ''
        django_user.save()

    # Get or create Employee linked to Django user
    employee, created_emp = Employee.objects.get_or_create(
        fingerPrintID=user.user_id,
        defaults={
            "user": django_user,
            "password": password,
            "date_of_birth": date(2000, 1, 1),  # placeholder
            "salary": 0,
        }
    )

    if not created_emp:
        employee.user = django_user
        employee.password = password
        employee.save()

    print(f"✅ Processed user: ID={user.user_id}, Name='{user.name}'")

print("🔓 Re-enabling device and disconnecting...")
conn.enable_device()
conn.disconnect()
print("🎉 All users processed successfully.")
