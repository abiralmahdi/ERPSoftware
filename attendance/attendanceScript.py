import os
import django
from datetime import datetime, date, timedelta

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HRManagementSoftware.settings")  # change to your project
django.setup()

from django.contrib.auth.models import User
from attendance.models import Employee, Attendance
from leave.models import LeaveApplications

# ZKTeco imports
from zk import ZK, const

# Device configuration
DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=5)

try:
    print("Connecting to ZKTeco device...")
    conn = zk.connect()
    conn.disable_device()

    # Fetch all attendance logs
    device_attendances = conn.get_attendance()
    today = date.today()
    three_months_ago = today - timedelta(days=90)  # last 3 months
    print(f"Total logs fetched from device: {len(device_attendances)}")

    # Map device user_id to all punches in last 3 months
    attendance_dict = {}
    for att in device_attendances:
        att_date = att.timestamp.date()
        if three_months_ago <= att_date <= today:
            attendance_dict.setdefault(att.user_id, {}).setdefault(att_date, []).append(att.timestamp)

    # Process all employees
    employees = Employee.objects.all()
    for emp in employees:
        emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {})

        # Iterate through each date in the last 3 months
        for n in range(91):
            current_date = three_months_ago + timedelta(days=n)
            punches = emp_attendance.get(current_date, [])

            if punches:
                # Employee present
                in_time = min(p.time() for p in punches)
                out_time = max(p.time() for p in punches)
                status = "present"
            else:
                # Check if employee is on approved leave
                leave = LeaveApplications.objects.filter(
                    employee=emp,
                    startDate__lte=current_date,
                    endDate__gte=current_date,
                    deptApproval='approved',
                    HRApproval='approved',
                    finalApproval='approved'
                ).first()

                if leave:
                    status = "leave"
                else:
                    status = "absent"

                in_time = None
                out_time = None

            # Avoid duplicate entries
            attendance_obj, created = Attendance.objects.get_or_create(
                employee=emp,
                date=current_date,
                defaults={
                    'inTime': in_time,
                    'outTime': out_time,
                    'status': status
                }
            )

            if not created:
                attendance_obj.inTime = in_time if in_time else attendance_obj.inTime
                attendance_obj.outTime = out_time if out_time else attendance_obj.outTime
                attendance_obj.status = status
                attendance_obj.save()

        print(f"Processed attendance for {emp.user.get_full_name()}")

    conn.enable_device()
    conn.disconnect()
    print("Attendance for last 3 months processed successfully.")

except Exception as e:
    print("Error:", e)
