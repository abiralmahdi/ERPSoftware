import os
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: F401
from attendance.models import Employee, Attendance
from leave.models import LeaveApplications, VisitApplications
from zk import ZK

# Device configurations (use hostnames if you added them in docker-compose extra_hosts)
DEVICE_IPS = ["192.168.1.201", "103.29.60.50", "192.168.1.202"]
DEVICE_PORT = 4370

today = date.today()
three_months_ago = today - timedelta(days=90)

all_attendances = []  # store logs from all devices

# ---------- Collect logs from all devices ----------
for ip in DEVICE_IPS:
    print(f"🔌 Trying to connect to ZKTeco device at {ip}:{DEVICE_PORT} ...")
    zk = ZK(ip, port=DEVICE_PORT, timeout=60)
    conn = None
    try:
        conn = zk.connect()
        conn.disable_device()
        device_attendances = conn.get_attendance() or []
        print(f"✅ Logs fetched from {ip}: {len(device_attendances)}")
        all_attendances.extend(device_attendances)
    except Exception as e:
        print(f"❌ Could not connect to device {ip}: {e}")
    finally:
        if conn:
            try:
                conn.enable_device()
                conn.disconnect()
            except Exception:
                pass

print(f"\n📊 Total logs combined from devices: {len(all_attendances)}")

# ---------- Build a dict: {user_id: {date: [timestamps...]}} ----------
attendance_dict = {}
for att in all_attendances:
    att_date = att.timestamp.date()
    if three_months_ago <= att_date <= today:
        attendance_dict.setdefault(str(att.user_id), {}).setdefault(att_date, []).append(att.timestamp)

# ---------- Process attendance ----------
print("🛠️ Processing attendance data...")
Attendance.objects.all().delete()
employees = Employee.objects.filter(status="Active")

for emp in employees:
    # Normalize: user_id may be str or int
    emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {}) or attendance_dict.get(emp.fingerPrintID, {})

    for n in range(91):
        current_date = three_months_ago + timedelta(days=n)
        punches = emp_attendance.get(current_date, [])

        # ----- Check Leave / Visit -----
        leave_exists = LeaveApplications.objects.filter(
            employee=emp,
            startDate__lte=current_date,
            endDate__gte=current_date,
            deptApproval="approved",
            HRApproval="approved",
            finalApproval="approved",
        ).exists()

        visit_exists = VisitApplications.objects.filter(
            employee=emp,
            startDate__lte=current_date,
            endDate__gte=current_date,
            deptApproval="approved",
            HRApproval="approved",
            finalApproval="approved",
        ).exists()

        # ----- Decide status -----
        if punches:
            in_time = min(p.time() for p in punches)
            out_time = max(p.time() for p in punches)
            status = "present"
            remote = bool(visit_exists)
        else:
            in_time, out_time = None, None
            if leave_exists:
                status, remote = "leave", False
            elif visit_exists:
                status, remote = "present", True
            else:
                status, remote = "absent", False

        # ----- Safe upsert -----
        qs = Attendance.objects.filter(employee=emp, date=current_date).order_by("id")
        if qs.exists():
            att_obj = qs.first()
            if qs.count() > 1:
                qs.exclude(id=att_obj.id).delete()
                print(f"⚠️ Cleaned duplicates for {emp.user.get_full_name()} on {current_date}")

            # Update kept record
            if in_time and (not att_obj.inTime or in_time < att_obj.inTime):
                att_obj.inTime = in_time
            if out_time and (not att_obj.outTime or out_time > att_obj.outTime):
                att_obj.outTime = out_time
            att_obj.status = status
            att_obj.remote = remote
            att_obj.save()
        else:
            Attendance.objects.create(
                employee=emp,
                date=current_date,
                inTime=in_time,
                outTime=out_time,
                status=status,
                remote=remote,
            )

    print(f"✅ Processed attendance for {emp.user.get_full_name()}")

print("\n🎉 Attendance for last 3 months processed successfully from all devices.")




# import os
# import django
# from datetime import date, timedelta

# # Setup Django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")
# django.setup()

# from django.contrib.auth.models import User  # noqa: F401
# from attendance.models import Employee, Attendance
# from leave.models import LeaveApplications, VisitApplications
# from zk import ZK

# # Device configurations (use hostnames if you added them in docker-compose extra_hosts)
# DEVICE_IPS = ["192.168.1.201", "103.29.60.50", "192.168.1.202"]
# DEVICE_PORT = 4370

# today = date.today()
# three_months_ago = today - timedelta(days=90)

# all_attendances = []  # store logs from all devices

# # ---------- Collect logs from all devices ----------
# for ip in DEVICE_IPS:
#     print(f"🔌 Trying to connect to ZKTeco device at {ip}:{DEVICE_PORT} ...")
#     zk = ZK(ip, port=DEVICE_PORT, timeout=60)
#     conn = zk.connect()
#     conn.disable_device()
#     device_attendances = conn.get_attendance() or []
#     print(f"✅ Logs fetched from {ip}: {len(device_attendances)}")
#     all_attendances.extend(device_attendances)
#     conn.enable_device()
#     conn.disconnect()

# print(f"\n📊 Total logs combined from devices: {len(all_attendances)}")

# # ---------- Build a dict: {user_id: {date: [timestamps...]}} ----------
# attendance_dict = {}
# for att in all_attendances:
#     att_date = att.timestamp.date()
#     if three_months_ago <= att_date <= today:
#         attendance_dict.setdefault(str(att.user_id), {}).setdefault(att_date, []).append(att.timestamp)

# # ---------- Process attendance ----------
# print("🛠️ Processing attendance data...")
# Attendance.objects.all().delete()
# employees = Employee.objects.filter(status="Active")

# for emp in employees:
#     # Normalize: user_id may be str or int
#     emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {}) or attendance_dict.get(emp.fingerPrintID, {})

#     for n in range(91):
#         current_date = three_months_ago + timedelta(days=n)
#         punches = emp_attendance.get(current_date, [])

#         # ----- Check Leave / Visit -----
#         leave_exists = LeaveApplications.objects.filter(
#             employee=emp,
#             startDate__lte=current_date,
#             endDate__gte=current_date,
#             deptApproval="approved",
#             HRApproval="approved",
#             finalApproval="approved",
#         ).exists()

#         visit_exists = VisitApplications.objects.filter(
#             employee=emp,
#             startDate__lte=current_date,
#             endDate__gte=current_date,
#             deptApproval="approved",
#             HRApproval="approved",
#             finalApproval="approved",
#         ).exists()

#         # ----- Decide status -----
#         if punches:
#             in_time = min(p.time() for p in punches)
#             out_time = max(p.time() for p in punches)
#             status = "present"
#             remote = bool(visit_exists)
#         else:
#             in_time, out_time = None, None
#             if leave_exists:
#                 status, remote = "leave", False
#             elif visit_exists:
#                 status, remote = "present", True
#             else:
#                 status, remote = "absent", False

#         # ----- Safe upsert -----
#         qs = Attendance.objects.filter(employee=emp, date=current_date).order_by("id")
#         if qs.exists():
#             att_obj = qs.first()
#             if qs.count() > 1:
#                 qs.exclude(id=att_obj.id).delete()
#                 print(f"⚠️ Cleaned duplicates for {emp.user.get_full_name()} on {current_date}")

#             # Update kept record
#             if in_time and (not att_obj.inTime or in_time < att_obj.inTime):
#                 att_obj.inTime = in_time
#             if out_time and (not att_obj.outTime or out_time > att_obj.outTime):
#                 att_obj.outTime = out_time
#             att_obj.status = status
#             att_obj.remote = remote
#             att_obj.save()
#         else:
#             Attendance.objects.create(
#                 employee=emp,
#                 date=current_date,
#                 inTime=in_time,
#                 outTime=out_time,
#                 status=status,
#                 remote=remote,
#             )

#     print(f"✅ Processed attendance for {emp.user.get_full_name()}")

# print("\n🎉 Attendance for last 3 months processed successfully from all devices.")
