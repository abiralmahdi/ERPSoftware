from django.shortcuts import render
from .models import *
from employee.models import *
from django.db.models import Q
from datetime import datetime
import random
from django.utils import timezone
def attendanceList(request):

    # # Date range
    # start_date = date(2025, 7, 1)
    # end_date = date(2025, 8, 13)
    # delta = end_date - start_date

    # # Get all employees
    # employees = Employee.objects.all()

    # statuses = ['present', 'absent', 'leave']

    # for i in range(delta.days + 1):
    #     current_date = start_date + timedelta(days=i)
    #     for emp in employees:
    #         # Randomly pick status
    #         status = random.choices(
    #             statuses, weights=[0.7, 0.2, 0.1], k=1
    #         )[0]  # More likely to be present

    #         # Randomly decide if remote (only if present)
    #         remote = random.choice([True, False]) if status == 'present' else False

    #         # Random in/out times for present
    #         if status == 'present':
    #             in_hour = random.randint(8, 10)
    #             in_minute = random.randint(0, 59)
    #             out_hour = random.randint(17, 19)
    #             out_minute = random.randint(0, 59)
    #             in_time = timezone.datetime(2025, 1, 1, in_hour, in_minute).time()
    #             out_time = timezone.datetime(2025, 1, 1, out_hour, out_minute).time()
    #         else:
    #             in_time = None
    #             out_time = None

    #         # Optional: random reason for leave/absent
    #         reason = ""
    #         if status in ['absent', 'leave']:
    #             reason = random.choice([
    #                 "Medical", "Personal", "Vacation", "Family reason", ""
    #             ])

    #         # Create Attendance record
    #         Attendance.objects.create(
    #             employee=emp,
    #             date=current_date,
    #             inTime=in_time if in_time else timezone.datetime(2025,1,1,9,0).time(),
    #             outTime=out_time if out_time else None,
    #             status=status,
    #             remote=remote,
    #             reason=reason,
    #             location="Office",
    #             longitude="",
    #             latitude=""
    #         )

    # print("Attendance data populated successfully!")




    # Get filter/search inputs
    employee_search = request.GET.get('employeeSearch', '')
    dept_id = request.GET.get('department', '')
    desig_id = request.GET.get('designation', '')

    # Base queryset
    attendances = Attendance.objects.all()

    # Search by employee name
    if employee_search:
        attendances = attendances.filter(
            Q(employee__user__first_name__icontains=employee_search) |
            Q(employee__user__last_name__icontains=employee_search)
        )

    # Filter by department
    if dept_id:
        attendances = attendances.filter(employee__department_id=dept_id)

    # Filter by designation
    if desig_id:
        attendances = attendances.filter(employee__designation_id=desig_id)

    context = {
        'attendances': attendances.order_by('-date'),
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
    }
    return render(request, 'attendanceList.html', context)


def attendanceDashboard(request):
    attendanceList = Attendance.objects.all().order_by('-date')
    absentEmployees = Employee.objects.exclude(id__in=attendanceList.filter(date=datetime.today()))

    context = {
        'attendances': attendanceList,
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
        'absentees':absentEmployees
    }
    return render(request, 'attendanceDashboard.html', context)


from django.http import JsonResponse
from django.utils.dateparse import parse_date
from datetime import date

def get_absentees(request):
    # Get and validate date
    date_str = request.GET.get("date")
    selected_date = parse_date(date_str)
    if not selected_date:
        return JsonResponse({"error": "Invalid date"}, status=400)

    # Restrict future dates
    if selected_date > date.today():
        return JsonResponse({"error": "Future dates are not allowed"}, status=400)

    # Filters from query params
    department = request.GET.get("department", "").strip()
    designation = request.GET.get("designation", "").strip()
    name = request.GET.get("name", "").strip()

    # Get employees who have attendance as 'present' on that date
    present_ids = Attendance.objects.filter(
        date=selected_date, status="present"
    ).values_list("employee_id", flat=True)

    # Base queryset: all employees NOT in present_ids
    absentees_qs = Employee.objects.exclude(id__in=present_ids)

    # Apply filters
    if department:
        absentees_qs = absentees_qs.filter(department__name__icontains=department)
    if designation:
        absentees_qs = absentees_qs.filter(designation__title__icontains=designation)
    if name:
        absentees_qs = absentees_qs.filter(user__first_name__icontains=name) | absentees_qs.filter(user__last_name__icontains=name)


    # Build response
    absentees_list = [
        {
            "id": emp.id,
            "name": emp.user.get_full_name(),
            "department": emp.department.name if emp.department else "",
            "designation": emp.designation.title if emp.designation else "",
        }
        for emp in absentees_qs
    ]

    return JsonResponse({"absentees": absentees_list})




from datetime import timedelta
from django.db.models import Count

def attendance_chart_data(request):
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    try:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    except:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    if not start_date or not end_date:
        return JsonResponse({"error": "Missing date parameters"}, status=400)

    # Filter attendance records
    qs = Attendance.objects.filter(date__range=[start_date, end_date])

    # Group by date
    date_list = []
    present_data = []
    absent_data = []
    leave_data = []

    current_date = start_date
    while current_date <= end_date:
        daily_records = qs.filter(date=current_date)
        date_list.append(current_date.strftime("%Y-%m-%d"))
        present_data.append(daily_records.filter(status="present").count())
        absent_data.append(daily_records.filter(status="absent").count())
        leave_data.append(daily_records.filter(status="leave").count())
        current_date += timedelta(days=1)

    return JsonResponse({
        "labels": date_list,
        "present": present_data,
        "absent": absent_data,
        "leave": leave_data
    })