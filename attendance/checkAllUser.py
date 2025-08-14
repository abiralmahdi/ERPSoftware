import os
import django
from datetime import date

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")  # Change to your project
django.setup()

from django.contrib.auth.models import User
from attendance.models import Employee  # Change to your app name
from zk import ZK, const

# Device configuration
DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5)

try:
    print("Connecting to ZKTeco device...")
    conn = zk.connect()
    conn.disable_device()

    users = conn.get_users()
    print(f"Total users on device: {len(users)}")

    for user in users:
        # Prepare username and email
        username = user.name.replace(" ", "").lower()  # remove spaces, lowercase
        email = f"{username}@example.com"  # or any valid domain

        # Password from device or default
        password = user.password if user.password else "password123"

        # Check if Django user already exists
        if User.objects.filter(username=username).exists():
            django_user = User.objects.get(username=username)
        else:
            django_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=user.name.split(' ')[0] if ' ' in user.name else user.name,
                last_name=' '.join(user.name.split(' ')[1:]) if ' ' in user.name else ''
            )

        # Create or update Employee
        employee, created = Employee.objects.get_or_create(
            fingerPrintID=user.user_id,
            defaults={
                'user': django_user,
                'password': password,
                'date_of_birth': date(2000, 1, 1),  # placeholder
                'salary':0
            }
        )
        if not created:
            # Update password if needed
            employee.password = password
            employee.user = django_user
            employee.save()

        print(f"Processed user: {user.user_id} - {user.name}")

    conn.enable_device()
    conn.disconnect()
    print("All users processed successfully.")

except Exception as e:
    print("Error:", e)
