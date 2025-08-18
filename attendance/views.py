from django.shortcuts import render, redirect
from .models import *
from employee.models import *
from django.db.models import Q
from datetime import datetime
import random
from django.utils import timezone
from leave.models import *
from core.models import GlobalConfig

def attendanceList(request):
    globalConfig = GlobalConfig.objects.all().first()
    # Get filter/search inputs
    employee_search = request.GET.get('employeeSearch', '')
    dept_id = request.GET.get('department', '')
    desig_id = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    selected_date = request.GET.get('date', '')

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

    # Filter by status
    if status_filter:
        attendances = attendances.filter(status=status_filter)

    # Filter by date
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            attendances = attendances.filter(date=date_obj)
        except ValueError:
            pass  # Ignore if date parsing fails

    # Show only latest 500 records if no filters are applied
    if not (employee_search or dept_id or desig_id or status_filter or selected_date):
        attendances = attendances.order_by('-date')[:500]
    else:
        attendances = attendances.order_by('-date')

    context = {
        'attendances': attendances,
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
        'globalConfig':globalConfig
    }
    return render(request, 'attendanceList.html', context)

def attendanceDashboard(request):
    globalConfig = GlobalConfig.objects.all().first()
    attendanceList = Attendance.objects.all().order_by('-date')
    absentEmployees = Employee.objects.exclude(id__in=attendanceList.filter(date=datetime.today()))
    office_start_time = globalConfig.officeStartTime.strftime("%H:%M")
    context = {
        'attendances': attendanceList,
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
        'absentees':absentEmployees,
        'globalConfig':globalConfig,
        'officeStartTime':office_start_time
    }
    return render(request, 'attendanceDashboard.html', context)



def get_quickview(request):
    globalConfig = GlobalConfig.objects.all().first()
    name = request.GET.get("name", "")
    department = request.GET.get("department", "")
    status = request.GET.get("status", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    attendances = Attendance.objects.all()

    if name:
        attendances = attendances.filter(
            Q(employee__user__first_name__icontains=name) |
            Q(employee__user__last_name__icontains=name)
        )

    if department:
        attendances = attendances.filter(employee__department__name__iexact=department)

    if status:
        attendances = attendances.filter(status=status)

    # Filter by date range
    if start_date:
        try:
            start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            attendances = attendances.filter(date__gte=start_obj)
        except ValueError:
            pass

    if end_date:
        try:
            end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            attendances = attendances.filter(date__lte=end_obj)
        except ValueError:
            pass

    data = []
    for attn in attendances.order_by("-date"):
        data.append({
            "name": attn.employee.user.get_full_name() if attn.employee and attn.employee.user else "",
            "designation": attn.employee.designation.title if attn.employee and attn.employee.designation else "",
            "department": attn.employee.department.name if attn.employee and attn.employee.department else "",
            "date": attn.date.strftime("%Y-%m-%d") if attn.date else "",
            "in_time": attn.inTime.strftime("%H:%M:%S") if attn.inTime else "",
            "out_time": attn.outTime.strftime("%H:%M:%S") if attn.outTime else "",
            "remote": attn.remote if attn.remote is not None else False,
            "reason": attn.reason if attn.reason else "",
            "location": attn.location if attn.location else "",
            "status": attn.status if attn.status else "",
            
        })

    return JsonResponse({"attendances": data})




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
            "absentNumber":len(absentees_qs)
        }
        for emp in absentees_qs
    ]

    return JsonResponse({"absentees": absentees_list})




from datetime import timedelta
from django.db.models import Count

def attendance_chart_data(request):
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")
    office_time_str = request.GET.get("officeStartTime")  # pass from template, e.g., "09:00"

    try:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        office_time = datetime.strptime(office_time_str, "%H:%M").time()
    except:
        return JsonResponse({"error": "Invalid date or time format"}, status=400)

    if not start_date or not end_date:
        return JsonResponse({"error": "Missing date parameters"}, status=400)

    qs = Attendance.objects.filter(date__range=[start_date, end_date])
    date_list = []
    present_data, absent_data, leave_data, late_data = [], [], [], []

    current_date = start_date
    while current_date <= end_date:
        daily_records = qs.filter(date=current_date)
        date_list.append(current_date.strftime("%Y-%m-%d"))

        present_count = 0
        absent_count = 0
        leave_count = 0
        late_count = 0

        for attn in daily_records:
            # Check leave applications
            leave_app = LeaveApplications.objects.filter(
                employee=attn.employee,
                startDate__lte=current_date,
                endDate__gte=current_date,
                finalApproval='approved'
            ).first()

            if leave_app:
                leave_count += 1
            elif attn.inTime and attn.inTime > office_time:
                late_count += 1
                present_count += 1  # late still counts as present
            elif attn.inTime:
                present_count += 1
            else:
                absent_count += 1

        # Count absent if no attendance record exists
        employees_with_attendance = [a.employee.id for a in daily_records]
        all_employees = Attendance.objects.values_list('employee', flat=True).distinct()
        absent_count += len(set(all_employees) - set(employees_with_attendance))

        present_data.append(present_count)
        absent_data.append(absent_count)
        leave_data.append(leave_count)
        late_data.append(late_count)

        current_date += timedelta(days=1)

    return JsonResponse({
        "labels": date_list,
        "present": present_data,
        "absent": absent_data,
        "leave": leave_data,
        "late": late_data
    })


def remoteAttendance(request):
    globalConfig = GlobalConfig.objects.all().first()
    # Get filter/search inputs
    employee_search = request.GET.get('employeeSearch', '')
    dept_id = request.GET.get('department', '')
    desig_id = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    selected_date = request.GET.get('date', '')

    # Base queryset
    attendances = Attendance.objects.filter(remote=True)

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

    # Filter by status
    if status_filter:
        attendances = attendances.filter(status=status_filter)

    # Filter by date
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            attendances = attendances.filter(date=date_obj)
        except ValueError:
            pass  # Ignore if date parsing fails


    context = {
        'attendances': attendances.order_by('-date'),
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
        'globalConfig':globalConfig
    }
    return render(request, 'remoteAttendance.html', context)


import base64
from django.core.files.base import ContentFile

 
def submitAttendance(request):
    if request.method == "POST":
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return redirect("/attendance/remoteAttendance")  # adjust redirect

        # --- Attendance form data ---
        reason = request.POST.get("reason", "")
        location = request.POST.get("location", "")
        lat = request.POST.get("latitude", "")
        lon = request.POST.get("longitude", "")
        

        # Handle image (if captured from camera as base64)
        image_data = request.POST.get("captured_image")  # base64 string from hidden input
        image_file = None
        if image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"{request.user.username}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            )

        VisitApplications.objects.create(
            employee=employee,
            visitTo=location,
            reason=reason,
            startDate=timezone.now().date(),
            endDate=timezone.now().date(),
            photo=image_file,
            latitude=lat,
            longitude=lon, 
        )

        return redirect("/attendance/remoteAttendance")  # adjust redirect

    return redirect("/attendance/remoteAttendance")


def outTime(request, attendanceID):
    attendance = Attendance.objects.get(id=int(attendanceID))
    if attendance.outTime is None:
        attendance.outTime = timezone.now()
        attendance.save()
    return redirect("/attendance/remoteAttendance")  # adjust redirect



from django.http import JsonResponse
from datetime import date, timedelta

def attendance_pie_chart(request, employee_id):
    employee = Employee.objects.get(id=int(employee_id))

    # Get start & end dates from query params
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")

    if not start or not end:  # default: last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()

    # Office start time from GlobalConfig
    global_config = GlobalConfig.objects.first()
    office_start = datetime.strptime(global_config.officeStartTime.strftime("%H:%M"), "%H:%M").time()

    # Generate all days in range
    all_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    present_count, absent_count, leave_count, late_count = 0, 0, 0, 0

    for day in all_days:
        # Check leave
        leave_exists = LeaveApplications.objects.filter(
            employee=employee,
            finalApproval='approved',
            startDate__lte=day,
            endDate__gte=day
        ).exists()
        if leave_exists:
            leave_count += 1
            continue

        # Check attendance
        attn = Attendance.objects.filter(employee=employee, date=day).first()
        if attn:
            if attn.inTime and attn.inTime > office_start:
                late_count += 1
                present_count += 1  # late is also counted as present
            elif attn.status == "present":
                present_count += 1
            elif attn.status == "leave":
                leave_count += 1
            else:
                absent_count += 1
        else:
            absent_count += 1

    data = {
        "labels": ["Present", "Late", "Absent", "Leave"],
        "counts": [present_count - late_count, late_count, absent_count, leave_count],
        "employee": employee.user.get_full_name(),
    }
    return JsonResponse(data)


from django.utils.timezone import now
from datetime import datetime
from collections import defaultdict

def employee_monthly_attendance(request, employee_id):
    employee = Employee.objects.get(id=int(employee_id))
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = (now() - timedelta(days=365)).date()
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        end_date = now().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    global_config = GlobalConfig.objects.first()
    office_start = datetime.strptime(global_config.officeStartTime.strftime("%H:%M"), "%H:%M").time()

    monthly_data = defaultdict(lambda: {'present':0, 'late':0, 'leave':0, 'absent':0})

    # Initialize months
    current = start_date.replace(day=1)
    while current <= end_date:
        monthly_data[current.strftime("%Y-%m")] = {'present':0, 'late':0, 'leave':0, 'absent':0}
        if current.month == 12:
            current = current.replace(year=current.year+1, month=1)
        else:
            current = current.replace(month=current.month+1)

    # Fetch attendance records & leaves
    attendances = Attendance.objects.filter(employee=employee, date__range=(start_date, end_date))
    leaves = LeaveApplications.objects.filter(
        employee=employee,
        finalApproval='approved',
        startDate__lte=end_date,
        endDate__gte=start_date
    )

    leave_days = set()
    for leave in leaves:
        day = leave.startDate
        while day <= leave.endDate and day <= end_date:
            if day >= start_date:
                leave_days.add(day)
            day += timedelta(days=1)

    day = start_date
    while day <= end_date:
        month_str = day.strftime("%Y-%m")
        attn = attendances.filter(date=day).first()
        if day in leave_days:
            monthly_data[month_str]['leave'] += 1
        elif attn:
            if attn.inTime and attn.inTime > office_start:
                monthly_data[month_str]['late'] += 1
                monthly_data[month_str]['present'] += 1
            elif attn.status == 'present':
                monthly_data[month_str]['present'] += 1
            else:
                monthly_data[month_str]['absent'] += 1
        else:
            monthly_data[month_str]['absent'] += 1
        day += timedelta(days=1)

    months = sorted(monthly_data.keys())
    return JsonResponse({
        'months': months,
        'present': [monthly_data[m]['present'] - monthly_data[m]['late'] for m in months],
        'late': [monthly_data[m]['late'] for m in months],
        'leave': [monthly_data[m]['leave'] for m in months],
        'absent': [monthly_data[m]['absent'] for m in months],
    })
