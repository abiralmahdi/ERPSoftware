# import os
# import django
# from datetime import date
# from django.contrib.auth.models import User
# from .models import Employee  # Change to your app name
# from zk import ZK


# def sync_employees_from_zkteco():
#     # Device configuration
#     DEVICE_IP = "192.168.1.201"
#     DEVICE_PORT = 4370

#     zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5)

#     try:
#         print("Connecting to ZKTeco device...")
#         conn = zk.connect()
#         conn.disable_device()

#         users = conn.get_users()
#         print(f"Total users on device: {len(users)}")

#         # Get all existing fingerprint IDs from DB
#         existing_finger_ids = set(Employee.objects.values_list('fingerPrintID', flat=True))

#         new_users_count = 0
#         for user in users:
#             if int(user.user_id) in existing_finger_ids:
#                 print(f"Skipping existing employee: {user.user_id} - {user.name}")
#                 continue

#             # Prepare username & email
#             username = user.name.replace(" ", "").lower() or f"user{user.user_id}"
#             email = f"{username}@example.com"
#             password = user.password if user.password else "password123"

#             # Ensure unique username
#             base_username = username
#             counter = 1
#             while User.objects.filter(username=username).exists():
#                 username = f"{base_username}{counter}"
#                 counter += 1

#             # Create Django User
#             django_user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password,
#                 first_name=user.name.split(' ')[0] if ' ' in user.name else user.name,
#                 last_name=' '.join(user.name.split(' ')[1:]) if ' ' in user.name else ''
#             )

#             # Create Employee
#             Employee.objects.create(
#                 fingerPrintID=user.user_id,
#                 user=django_user,
#                 password=password,
#                 date_of_birth=date(2000, 1, 1),
#                 salary=0
#             )

#             print(f"✅ Added new employee: {user.user_id} - {user.name}")
#             new_users_count += 1

#         conn.enable_device()
#         print(f"\nProcess completed. {new_users_count} new employees added.")

#     except Exception as e:
#         print(f"❌ Error: {e}")

#     finally:
#         try:
#             conn.disconnect()
#         except:
#             pass


# sync_employees_from_zkteco()





import os
import django
from datetime import date
from django.contrib.auth.models import User
from .models import Employee  # Change to your app name
from zk import ZK

def sync_employees_from_zkteco():
    # Device configuration
    DEVICE_IP = "192.168.1.201"
    DEVICE_PORT = 4370

    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5)

    print("Connecting to ZKTeco device...")
    conn = zk.connect()
    conn.disable_device()

    users = conn.get_users()
    print(f"Total users on device: {len(users)}")

    # Get all existing fingerprint IDs from DB
    existing_finger_ids = set(Employee.objects.values_list('fingerPrintID', flat=True))

    new_users_count = 0
    for user in users:
        if int(user.user_id) in existing_finger_ids:
            print(f"Skipping existing employee: {user.user_id} - {user.name}")
            continue

        # Prepare username & email
        username = user.name.replace(" ", "").lower() or f"user{user.user_id}"
        email = f"{username}@example.com"
        password = user.password if user.password else "password123"

        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create Django User
        django_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=user.name.split(' ')[0] if ' ' in user.name else user.name,
            last_name=' '.join(user.name.split(' ')[1:]) if ' ' in user.name else ''
        )

        # Create Employee
        Employee.objects.create(
            fingerPrintID=user.user_id,
            user=django_user,
            password=password,
            date_of_birth=date(2000, 1, 1),
            salary=0
        )

        print(f"✅ Added new employee: {user.user_id} - {user.name}")
        new_users_count += 1

    conn.enable_device()
    print(f"\nProcess completed. {new_users_count} new employees added.")

    conn.disconnect()

sync_employees_from_zkteco()
