import os
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")  # change to your project
django.setup()

from django.contrib.auth.models import User  # noqa: F401 (kept if you need it elsewhere)
from attendance.models import Employee, Attendance
from leave.models import LeaveApplications, VisitApplications
from zk import ZK

# Device configurations
DEVICE_IPS = ["192.168.1.201", "103.29.60.50"]
DEVICE_PORT = 4370

today = date.today()
three_months_ago = today - timedelta(days=90)  # last 3 months

all_attendances = []  # store logs from all devices

# ---------- Collect logs from all devices ----------
for ip in DEVICE_IPS:
    print(f"🔌 Connecting to ZKTeco device at {ip}...")
    zk = ZK(ip, port=DEVICE_PORT, timeout=60)
    try:
        conn = zk.connect()
        conn.disable_device()

        device_attendances = conn.get_attendance()
        print(f"✅ Logs fetched from {ip}: {len(device_attendances)}")

        all_attendances.extend(device_attendances)

        conn.enable_device()
        conn.disconnect()
    except Exception as e:
        print(f"❌ Could not connect to device {ip}: {e}")

print(f"\n📊 Total logs combined from devices: {len(all_attendances)}")

# ---------- Build a dict: {user_id: {date: [timestamps...]}} for last 3 months ----------
attendance_dict = {}
for att in all_attendances:
    att_date = att.timestamp.date()
    if three_months_ago <= att_date <= today:
        attendance_dict.setdefault(att.user_id, {}).setdefault(att_date, []).append(att.timestamp)

# ---------- Process attendance for each employee and each day ----------
employees = Employee.objects.all()
for emp in employees:
    # user_id from device is typically str or int; normalize both sides with str()
    emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {}) or attendance_dict.get(emp.fingerPrintID, {})

    for n in range(91):
        current_date = three_months_ago + timedelta(days=n)
        punches = emp_attendance.get(current_date, [])

        # Pre-checks for leave/visit approvals (only when needed)
        # Leave must be approved by dept, HR, and final
        leave_exists = LeaveApplications.objects.filter(
            employee=emp,
            startDate__lte=current_date,
            endDate__gte=current_date,
            deptApproval='approved',
            HRApproval='approved',
            finalApproval='approved'
        ).exists()

        # Visit must be approved by dept, HR, and final
        visit_exists = VisitApplications.objects.filter(
            employee=emp,
            startDate__lte=current_date,
            endDate__gte=current_date,
            deptApproval='approved',
            HRApproval='approved',
            finalApproval='approved'
        ).exists()

        # Decide status + times + remote
        if punches:
            in_time = min(p.time() for p in punches)
            out_time = max(p.time() for p in punches)
            status = "present"
            remote = True if visit_exists else False  # mark remote when on approved visit even if there are punches
        else:
            in_time = None
            out_time = None
            if leave_exists:
                status = "leave"
                remote = False
            elif visit_exists:
                status = "present"
                remote = True
            else:
                status = "absent"
                remote = False

        # Upsert Attendance
        attendance_obj, created = Attendance.objects.get_or_create(
            employee=emp,
            date=current_date,
            defaults={
                'inTime': in_time,
                'outTime': out_time,
                'status': status,
                'remote': remote,
            }
        )

        if not created:
            # Only overwrite with new information; keep previous times if we still have None
            attendance_obj.inTime = in_time if in_time else attendance_obj.inTime
            attendance_obj.outTime = out_time if out_time else attendance_obj.outTime
            attendance_obj.status = status
            attendance_obj.remote = remote
            attendance_obj.save()

    print(f"✅ Processed attendance for {emp.user.get_full_name()}")

print("\n🎉 Attendance for last 3 months processed successfully from all devices.")
