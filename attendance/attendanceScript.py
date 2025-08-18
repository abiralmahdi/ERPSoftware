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

# Device configurations
DEVICE_IPS = ["192.168.1.201", "103.29.60.50"]
DEVICE_PORT = 4370

today = date.today()
three_months_ago = today - timedelta(days=365)  # last ~1 year

all_attendances = []  # store logs from all devices

# ---------- Collect logs from all devices ----------
for ip in DEVICE_IPS:
    print(f"🔌 Connecting to ZKTeco device at {ip}...")
    zk = ZK(ip, port=DEVICE_PORT, timeout=60)
    conn = None
    try:
        conn = zk.connect()
        conn.disable_device()
        device_attendances = conn.get_attendance()
        print(f"✅ Logs fetched from {ip}: {len(device_attendances)}")
        all_attendances.extend(device_attendances)
    except Exception as e:
        print(f"❌ Could not connect to device {ip}: {e}")
    finally:
        try:
            if conn:
                conn.enable_device()
                conn.disconnect()
        except Exception:
            pass

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
    # Normalize keys: some SDKs return int user_id
    emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {}) or attendance_dict.get(emp.fingerPrintID, {})

    for n in range(91):
        current_date = three_months_ago + timedelta(days=n)
        punches = emp_attendance.get(current_date, [])

        # Pre-checks: Leave must be approved by dept, HR, final
        leave_exists = LeaveApplications.objects.filter(
            employee=emp,
            startDate__lte=current_date,
            endDate__gte=current_date,
            deptApproval='approved',
            HRApproval='approved',
            finalApproval='approved'
        ).exists()

        # Visit must be approved by dept, HR, final
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
            remote = True if visit_exists else False  # mark remote when on approved visit even with punches
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

        # ---------- Safe upsert with duplicate cleanup ----------
        qs = Attendance.objects.filter(employee=emp, date=current_date).order_by("id")
        if qs.exists():
            att_obj = qs.first()
            # If duplicates exist, delete extras
            if qs.count() > 1:
                qs.exclude(id=att_obj.id).delete()
                print(f"⚠️ Cleaned duplicates for {emp.user.get_full_name()} on {current_date}")

            # Update the single kept record
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
