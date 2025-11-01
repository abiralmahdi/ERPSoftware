from datetime import date, timedelta
from attendance.models import Employee, Attendance
from leave.models import LeaveApplications, VisitApplications
from zk import ZK

DEVICE_IPS = ["192.168.1.201", "103.29.60.50", "192.168.1.202"]
DEVICE_PORT = 4370

def process_attendance_last_3_months():
    today = date.today()
    three_months_ago = today - timedelta(days=90)

    all_attendances = []

    # -------- Fetch logs ----------
    for ip in DEVICE_IPS:
        zk = ZK(ip, port=DEVICE_PORT, timeout=60)
        conn = None
        try:
            conn = zk.connect()
            conn.disable_device()
            logs = conn.get_attendance() or []
            all_attendances.extend(logs)
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.enable_device()
                    conn.disconnect()
                except Exception:
                    pass

    # -------- Format attendance into dict ----------
    attendance_dict = {}
    for att in all_attendances:
        att_date = att.timestamp.date()
        if three_months_ago <= att_date <= today:
            attendance_dict.setdefault(str(att.user_id), {}).setdefault(att_date, []).append(att.timestamp)

    Attendance.objects.all().delete()
    employees = Employee.objects.filter(status="Active")

    # -------- Process ----------
    for emp in employees:
        emp_attendance = attendance_dict.get(str(emp.fingerPrintID), {}) or attendance_dict.get(emp.fingerPrintID, {})

        for n in range(91):
            current_date = three_months_ago + timedelta(days=n)
            punches = emp_attendance.get(current_date, [])

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

            if punches:
                in_time = min(p.time() for p in punches)
                out_time = max(p.time() for p in punches)
                status = "present"
                remote = bool(visit_exists)
            else:
                in_time = out_time = None
                if leave_exists:
                    status, remote = "leave", False
                elif visit_exists:
                    status, remote = "present", True
                else:
                    status, remote = "absent", False

            qs = Attendance.objects.filter(employee=emp, date=current_date).order_by("id")
            if qs.exists():
                att_obj = qs.first()
                if qs.count() > 1:
                    qs.exclude(id=att_obj.id).delete()

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

    return True
