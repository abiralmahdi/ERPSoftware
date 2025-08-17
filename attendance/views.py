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

    context = {
        'attendances': attendanceList,
        'departments': Department.objects.all(),
        'designations': Designation.objects.all(),
        'absentees':absentEmployees,
        'globalConfig':globalConfig
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