from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from employee.models import *
from django.db.models import Q
from datetime import datetime
import random
from django.utils import timezone
from leave.models import *
from core.models import GlobalConfig
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# docker exec -it mydjango_app python manage.py migrate


@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST required"})

    data = json.loads(request.body.decode("utf-8"))
    username = data.get("username")
    password = data.get("password")

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({"success": False, "message": "Invalid credentials"})

    try:
        employee = user.employee   # because User → Employee (OneToOne)
    except:
        return JsonResponse({"success": False, "message": "Employee profile missing"})

    return JsonResponse({
        "success": True,
        "employee_id": employee.id,   # <-- RETURN EMPLOYEE ID HERE
        "username": user.username,
    })


@login_required(login_url='/employees/login')
def attendanceList(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
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
            if userModel.designation.level == 2 and not request.user.is_superuser:
                attendances = attendances.filter(
                    Q(employee__user__first_name__icontains=employee_search) |
                    Q(employee__user__last_name__icontains=employee_search), employee__department=userModel.department
                )
            else:
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
    else:
        return HttpResponse("You are not authorized to view attendance records")

@login_required(login_url='/employees/login')
def attendanceDashboard(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
        globalConfig = GlobalConfig.objects.all().first()
        attendanceList = Attendance.objects.all().order_by('-date')
        absentEmployees = Employee.objects.exclude(id__in=attendanceList.filter(date=datetime.today()))
        office_start_time = globalConfig.officeStartTime.strftime("%H:%M")
        weekend = globalConfig.weekend
        if userModel.designation.level == 2 and not request.user.is_superuser:
            attendanceList = attendanceList.filter(employee__department=userModel.department)
            absentEmployees = absentEmployees.filter(department=userModel.department)
        context = {
            'attendances': attendanceList,
            'departments': Department.objects.all(),
            'designations': Designation.objects.all(),
            'absentees':absentEmployees,
            'globalConfig':globalConfig,
            'officeStartTime':office_start_time,
            'weekend':weekend
        }
        return render(request, 'attendanceDashboard.html', context)
    else:
        return HttpResponse("You are not authorized to view the attendance dashboard")


@login_required(login_url='/employees/login')
def get_quickview(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
        globalConfig = GlobalConfig.objects.all().first()
        name = request.GET.get("name", "")
        department = request.GET.get("department", "")
        status = request.GET.get("status", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        attendances = Attendance.objects.all()
        if userModel.designation.level == 2 and not request.user.is_superuser:
            attendances = attendances.filter(employee__department=userModel.department)

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
    else:
        return JsonResponse({"error": "You are not authorized to view this data"}, status=403)



from .attendanceScript import process_attendance_last_3_months
def scanAttendance(request):
    process_attendance_last_3_months()
    return redirect('/attendance/attendanceDashboard')


from django.http import JsonResponse
from django.utils.dateparse import parse_date
from datetime import date
@login_required(login_url='/employees/login')
def get_absentees(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
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

        if userModel.designation.level == 2 and not request.user.is_superuser:
            present_ids = present_ids.filter(employee__department=userModel.department)
            absentees_qs = absentees_qs.filter(department=userModel.department)

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


from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
@login_required(login_url='/employees/login')
def attendance_chart_data(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
        start_date = request.GET.get("start")
        end_date = request.GET.get("end")
        office_time_str = request.GET.get("officeStartTime")  # e.g., "09:00"

        try:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            office_time = datetime.strptime(office_time_str, "%H:%M").time()
        except:
            return JsonResponse({"error": "Invalid date or time format"}, status=400)

        if not start_date or not end_date:
            return JsonResponse({"error": "Missing date parameters"}, status=400)

        global_config = GlobalConfig.objects.first()
        weekend_day = getattr(global_config, 'weekend', 'Friday')  # default 'Friday'
        work_hours_per_day = 8

        qs = Attendance.objects.filter(date__range=[start_date, end_date])
        holidays = set(Holiday.objects.filter(date__range=[start_date, end_date]).values_list('date', flat=True))

        # get all employees (to calculate working hours & absentees)
        all_employees = Attendance.objects.values_list('employee', flat=True).distinct()
        total_employees = len(all_employees)

        if userModel.designation.level == 2 and not request.user.is_superuser:
            qs = qs.filter(employee__department=userModel.department)
            all_employees = Employee.objects.filter(department=userModel.department).values_list('id', flat=True).distinct()
            total_employees = len(all_employees)

        date_list = []
        present_data, absent_data, leave_data, late_data, weekend_data = [], [], [], [], []
        total_late_hours_list, total_absent_hours_list, total_working_hours_list = [], [], []

        current_date = start_date
        while current_date <= end_date:
            daily_records = qs.filter(date=current_date)
            date_list.append(current_date.strftime("%Y-%m-%d"))

            present_count = 0
            weekend_count = 0
            absent_count = 0
            leave_count = 0
            late_count = 0
            total_late_hours = 0
            total_absent_hours = 0

            # Check weekend / holiday
            is_weekend = current_date.strftime("%A") == weekend_day
            is_holiday = current_date in holidays

            for attn in daily_records:
                leave_app = LeaveApplications.objects.filter(
                    employee=attn.employee,
                    startDate__lte=current_date,
                    endDate__gte=current_date,
                    finalApproval='approved'
                ).first()

                if leave_app:
                    leave_count += 1
                elif not is_weekend and not is_holiday:
                    if attn.inTime and attn.inTime > office_time:
                        late_count += 1
                        present_count += 1
                        late_delta = datetime.combine(datetime.min, attn.inTime) - datetime.combine(datetime.min, office_time)
                        total_late_hours += late_delta.total_seconds() / 3600
                    elif attn.inTime:
                        present_count += 1
                    else:
                        absent_count += 1
                        total_absent_hours += work_hours_per_day
                elif is_weekend or is_holiday:
                    if attn.inTime:
                        weekend_count += 1

            # Count absent for employees without attendance record
            employees_with_attendance = [a.employee.id for a in daily_records]
            for emp_id in set(all_employees) - set(employees_with_attendance):
                if not is_weekend and not is_holiday:
                    absent_count += 1
                    total_absent_hours += work_hours_per_day

            # calculate working hours
            if not is_weekend and not is_holiday:
                total_working_hours = total_employees * work_hours_per_day
            else:
                total_working_hours = 0

            # append results
            present_data.append(present_count)
            weekend_data.append(weekend_count)
            absent_data.append(absent_count)
            leave_data.append(leave_count)
            late_data.append(late_count)
            total_late_hours_list.append(round(total_late_hours, 2))
            total_absent_hours_list.append(round(total_absent_hours, 2))
            total_working_hours_list.append(total_working_hours)

            current_date += timedelta(days=1)

        return JsonResponse({
            "labels": date_list,
            "present": present_data,
            "weekend": weekend_data,
            "absent": absent_data,
            "leave": leave_data,
            "late": late_data,
            "total_late_hours": total_late_hours_list,
            "total_absent_hours": total_absent_hours_list,
            "total_working_hours": total_working_hours_list,
        })


@login_required(login_url='/employees/login')
def remoteAttendance(request):
    userModel = Employee.objects.get(user=request.user)
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

@login_required(login_url='/employees/login')
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

@login_required(login_url='/employees/login')
def outTime(request, attendanceID):
    attendance = Attendance.objects.get(id=int(attendanceID))
    if attendance.outTime is None:
        attendance.outTime = timezone.now()
        attendance.save()
    return redirect("/attendance/remoteAttendance")  # adjust redirect

from django.http import JsonResponse
from datetime import date, datetime, timedelta, time
@login_required(login_url='/employees/login')
def attendance_pie_chart(request, employee_id):
    userModel = Employee.objects.get(user=request.user)
    employee = Employee.objects.get(id=int(employee_id))
    if (
            userModel == employee or 
            (userModel.designation.level == 2 and userModel.department == employee.department) or 
            request.user.is_superuser or 
            userModel.department.name in ["HR" or "Human Resource"]
        ):
        start = request.GET.get("start_date")
        end = request.GET.get("end_date")

        if not start or not end:  # default last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()

        global_config = GlobalConfig.objects.first()
        office_start = global_config.officeStartTime  # TimeField
        work_hours_per_day = 8  # assume 8-hour workday
        weekend_day = getattr(global_config, 'weekend', 'Friday')  # default 'Friday'

        holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))

        all_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        present_count = 0
        late_count = 0
        absent_count = 0
        leave_count = 0
        weekend_present_count = 0
        total_late_hours = 0
        total_absent_hours = 0
        total_working_days = 0

        for day in all_days:
            leave_exists = LeaveApplications.objects.filter(
                employee=employee,
                finalApproval='approved',
                startDate__lte=day,
                endDate__gte=day
            ).exists()
            if leave_exists:
                leave_count += 1
                continue

            day_name = day.strftime("%A")
            is_weekend = (day_name == weekend_day)
            is_holiday = day in holidays

            attn = Attendance.objects.filter(employee=employee, date=day).first()
            if attn:
                if attn.inTime and attn.inTime > office_start and not (is_weekend or is_holiday):
                    late_count += 1
                    present_count += 1
                    total_working_days += 1
                    late_delta = datetime.combine(date.min, attn.inTime) - datetime.combine(date.min, office_start)
                    total_late_hours += late_delta.total_seconds() / 3600
                elif attn.status == "present" and not (is_weekend or is_holiday):
                    present_count += 1
                    total_working_days += 1
                elif attn.status == "present" and is_weekend:
                    weekend_present_count += 1
                elif attn.status == "leave":
                    leave_count += 1
                elif not (is_weekend or is_holiday):
                    absent_count += 1
                    total_absent_hours += work_hours_per_day
            else:
                if not (is_weekend or is_holiday):
                    absent_count += 1
                    total_absent_hours += work_hours_per_day

        total_working_hours = total_working_days * work_hours_per_day

        data = {
            "labels": ["Present", "Weekend Present", "Late", "Absent", "Leave"],
            "counts": [present_count - late_count, weekend_present_count, late_count, absent_count, leave_count],
            "employee": employee.user.get_full_name(),
            "total_late_hours": round(total_late_hours, 2),
            "total_absent_hours": round(total_absent_hours, 2),
            "total_working_hours": total_working_hours,
        }

        return JsonResponse(data)
    else:
        return JsonResponse({"error": "You are not authorized to view this data"}, status=403)




from django.utils.timezone import now
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
@login_required(login_url='/employees/login')
def employee_monthly_attendance(request, employee_id):
    userModel = Employee.objects.get(user=request.user)
    employee = Employee.objects.get(id=int(employee_id))
    if (
            userModel == employee or 
            (userModel.designation.level == 2 and userModel.department == employee.department) or 
            request.user.is_superuser or 
            userModel.department.name in ["HR" or "Human Resource"]
        ):
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
        office_start = global_config.officeStartTime
        weekend_day = getattr(global_config, 'weekend', 'Friday')

        monthly_data = defaultdict(lambda: {'present':0, 'weekend_present':0, 'late':0, 'leave':0, 'absent':0})

        current = start_date.replace(day=1)
        while current <= end_date:
            monthly_data[current.strftime("%Y-%m")] = {'present':0, 'weekend_present':0, 'late':0, 'leave':0, 'absent':0}
            if current.month == 12:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+1)

        attendances = Attendance.objects.filter(employee=employee, date__range=(start_date, end_date))
        leaves = LeaveApplications.objects.filter(
            employee=employee,
            finalApproval='approved',
            startDate__lte=end_date,
            endDate__gte=start_date
        )

        holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))

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

            day_name = day.strftime("%A")
            is_weekend = (day_name == weekend_day)
            is_holiday = day in holidays

            if day in leave_days:
                monthly_data[month_str]['leave'] += 1
            elif attn:
                if attn.inTime and attn.inTime > office_start and not (is_weekend or is_holiday):
                    monthly_data[month_str]['late'] += 1
                    monthly_data[month_str]['present'] += 1
                elif attn.status == 'present' and not (is_weekend or is_holiday):
                    monthly_data[month_str]['present'] += 1
                elif attn.status == 'present' and is_weekend:
                    monthly_data[month_str]['weekend_present'] += 1
                else:
                    if not is_weekend and not is_holiday:
                        monthly_data[month_str]['absent'] += 1
            else:
                if not is_weekend and not is_holiday:
                    monthly_data[month_str]['absent'] += 1
            day += timedelta(days=1)

        months = sorted(monthly_data.keys())
        return JsonResponse({
            'months': months,
            'present': [monthly_data[m]['present'] - monthly_data[m]['late'] for m in months],
            'weekend_present': [monthly_data[m]['weekend_present'] for m in months],
            'late': [monthly_data[m]['late'] for m in months],
            'leave': [monthly_data[m]['leave'] for m in months],
            'absent': [monthly_data[m]['absent'] for m in months],
        })
    else:
        return JsonResponse({"error": "You are not authorized to view this data"}, status=403)



from django.views.decorators.csrf import csrf_exempt
import json
@login_required(login_url='/employees/login')
def calendar_view(request):
    year = date.today().year
   # Prepare months
    months = []
    for month in range(1, 13):
        # Generate days of the month
        if month == 12:
            next_month = date(year+1, 1, 1)
        else:
            next_month = date(year, month+1, 1)
        start_day = date(year, month, 1)
        delta = (next_month - start_day).days
        days = [start_day + timedelta(days=i) for i in range(delta)]
        months.append({"number": month, "name": start_day.strftime("%B"), "days": days})

    # Fetch existing holidays
    holidays = {h.date: h.name for h in Holiday.objects.filter(date__year=year)}

    context = {
        "year": year,
        "months": months,
        "holidays_json": json.dumps({h.date.strftime("%Y-%m-%d"): h.name for h in Holiday.objects.filter(date__year=year)})
    }
    return render(request, "calendarPage.html", context)


@csrf_exempt
def add_holiday(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"]:
        if request.method == "POST":
            date_str = request.POST.get("date")
            name = request.POST.get("name")

            holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            holiday, created = Holiday.objects.update_or_create(
                date=holiday_date, defaults={"name": name}
            )
            return JsonResponse({"success": True, "holiday": holiday.name, "date": date_str})
        return JsonResponse({"success": False})
    else:
        return JsonResponse({"error": "You are not authorized to perform this action"}, status=403)


def sendLocation(request):
    return render(request, 'mobileApp.html', {'employee':Employee.objects.get(user=request.user)})

@csrf_exempt
def getLocation(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            print(f"Received location: Latitude={latitude}, Longitude={longitude}")
            # You can save to DB if needed here
            return JsonResponse({"status": "success"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


from geopy.geocoders import Nominatim

def get_address_from_latlon(lat, lon):
    geolocator = Nominatim(user_agent="my_django_app")
    location = geolocator.reverse((lat, lon), language="en")
    if location:
        return location.address
    return "Unknown location"

@csrf_exempt
def getLocation2(request, employeeID):
    employee = Employee.objects.get(id=employeeID)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            print(f"Received location: Latitude={latitude}, Longitude={longitude} and employee: {employee.user.get_full_name()}")
            EmployeeLocation.objects.create(
                employee=employee,
                lat=latitude,
                lon=longitude,
                location=get_address_from_latlon(latitude, longitude),
            )
            return JsonResponse({"status": "success"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@login_required(login_url='/employees/login')
def seeEmployeeLocation(request):
    if request.user.is_superuser:
        employees = Employee.objects.all().prefetch_related('employeeLocations')

        employee_data = []
        for emp in employees:
            latest_location = emp.employeeLocations.order_by('-date', '-time').first()
            employee_data.append({
                "id": emp.id,
                "name": f"{emp.user.first_name} {emp.user.last_name}",
                "designation": emp.designation.title if emp.designation else "",
                "department": emp.department.name if emp.department else "",
                "lat": latest_location.lat if latest_location else None,
                "lon": latest_location.lon if latest_location else None,
                "location": latest_location.location if latest_location else "No location available",
                "date": latest_location.date if latest_location else None,
                "time": latest_location.time if latest_location else None,
            })

        context = {
            "employees": employee_data
        }
        return render(request, "seeEmployeeLocation.html", context)
    else:
        return HttpResponse("You are not authorized to view this page")

