from django.core.management.base import BaseCommand
from django.utils.timezone import localdate
from zk import ZK, const
from attendance.models import Attendance
from employee.models import Employee
from datetime import datetime

class Command(BaseCommand):
    help = "Sync attendance from ZKTeco device into Attendance model"

    def handle(self, *args, **kwargs):
        zk = ZK('192.168.1.201', port=4370, timeout=5)
        current_date = localdate()

        try:
            self.stdout.write("🔌 Connecting to device...")
            conn = zk.connect()
            self.stdout.write("✅ Connected!")

            # Get all users + logs from device
            users = conn.get_users()
            logs = conn.get_attendance()

            # Track employees who already have attendance today
            present_emp_ids = set()

            for log in logs:
                try:
                    emp = Employee.objects.get(fingerPrintID=int(log.user_id))
                except Employee.DoesNotExist:
                    self.stdout.write(f"⚠️ No Employee with fingerprintID={log.user_id}")
                    continue

                in_time = log.timestamp.time()
                out_time = None  # You can enhance this to detect last punch
                status = "present"
                remote = False

                # Handle duplicates: only keep one attendance per (employee, date)
                attendance_qs = Attendance.objects.filter(employee=emp, date=current_date)

                if attendance_qs.exists():
                    attendance_obj = attendance_qs.first()
                    if attendance_qs.count() > 1:
                        attendance_qs.exclude(id=attendance_obj.id).delete()
                        self.stdout.write(f"⚠️ Cleaned duplicates for {emp.user.username} on {current_date}")

                    attendance_obj.inTime = in_time if in_time else attendance_obj.inTime
                    attendance_obj.outTime = out_time if out_time else attendance_obj.outTime
                    attendance_obj.status = status
                    attendance_obj.remote = remote
                    attendance_obj.save()
                else:
                    Attendance.objects.create(
                        employee=emp,
                        date=current_date,
                        inTime=in_time,
                        outTime=out_time,
                        status=status,
                        remote=remote,
                    )

                present_emp_ids.add(emp.id)

            # Mark absentees
            all_emps = Employee.objects.all()
            for emp in all_emps:
                if emp.id not in present_emp_ids:
                    attendance_qs = Attendance.objects.filter(employee=emp, date=current_date)
                    if not attendance_qs.exists():
                        Attendance.objects.create(
                            employee=emp,
                            date=current_date,
                            inTime=None,
                            outTime=None,
                            status="absent",
                            remote=False,
                        )

            self.stdout.write("🎉 Attendance sync completed successfully!")

        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
        finally:
            try:
                conn.disconnect()
            except:
                pass
