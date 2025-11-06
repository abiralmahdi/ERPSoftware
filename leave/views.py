from django.shortcuts import render, redirect, get_object_or_404
from .models import LeaveApplications, VisitApplications
from employee.models import *
from django.db.models import Q
from django.contrib.auth.models import User
from core.models import GlobalConfig
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url='/employees/login')
def leaveApplications(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    if request.method == 'POST' and 'apply_leave' in request.POST:
        duty_handover_id = request.POST.get('dutyHandOver')
        leave_type = request.POST.get('leaveType')
        start_date = request.POST.get('startDate')
        end_date = request.POST.get('endDate')
        reason = request.POST.get('reason')

        dutyHandOver = Employee.objects.get(user=User.objects.get(id=int(duty_handover_id)))

        LeaveApplications.objects.create(
            employee=Employee.objects.get(user=request.user),
            dutyHandOver=dutyHandOver,
            leaveType=leave_type,
            startDate=start_date,
            endDate=end_date,
            reason=reason,
        )
        globalConfig.leaveNotification = True
        globalConfig.save()
        return redirect('leaveApplications')  # Replace with your URL name

    # Search and filter logic
    employee_search = request.POST.get('employeeSearch', '')
    dept_id = request.POST.get('department')
    desig_id = request.POST.get('designation')

    user = request.user
    employee = Employee.objects.get(user=user)

    if request.user.is_superuser or request.user.employee.department.name == 'HR':
        leaveApplications = LeaveApplications.objects.all()
    elif request.user.employee.designation.level == 2:
        leaveApplications = LeaveApplications.objects.filter(employee__department=employee.department)
    else:
        leaveApplications = LeaveApplications.objects.filter(employee=employee)

    if employee_search:
        leaveApplications = leaveApplications.filter(
            Q(employee__user__first_name__icontains=employee_search) |
            Q(employee__user__last_name__icontains=employee_search)
        )
    if dept_id:
        leaveApplications = leaveApplications.filter(employee__department_id=dept_id)
    if desig_id:
        leaveApplications = leaveApplications.filter(employee__designation_id=desig_id)

    context = {
        "leave_applications": leaveApplications.order_by('-applyDate'),
        "departments": Department.objects.all(),
        "employees": Employee.objects.all(),
        "designations": Designation.objects.all(),
        'globalConfig':globalConfig
    }
    return render(request, 'leaveApplications.html', context)


@login_required(login_url='/employees/login')
def approveLeave(request, applicationID):
    globalConfig = GlobalConfig.objects.all().first()
    leaveApplication = LeaveApplications.objects.get(id=applicationID)
    difference = leaveApplication.endDate - leaveApplication.startDate
    if request.user.employee.designation.level == 2:
        leaveApplication.deptApproval = 'approved'
        leaveApplication.deptApprovedBy = request.user.employee
    if request.user.employee.department.name == 'HR':
        leaveApplication.HRApproval = 'approved'
        leaveApplication.HRApprovedBy = request.user.employee
    if request.user.is_superuser:
        leaveApplication.finalApproval = 'approved'
        leaveApplication.finalApprovedBy = request.user.employee

        if leaveApplication.leaveType == 'Casual Leave':
            count = leaveApplication.employee.casualLeave
            leaveApplication.employee.casualLeave = count - difference.days
        elif leaveApplication.leaveType == 'Medical Leave':
            count = leaveApplication.employee.medicalLeave
            leaveApplication.employee.medicalLeave = count - difference.days
        elif leaveApplication.leaveType == 'Annual Leave':
            count = leaveApplication.employee.annualLeave
            leaveApplication.employee.annualLeave = count - difference.days
        elif leaveApplication.leaveType == 'Other':
            count = leaveApplication.employee.otherLeave
            leaveApplication.employee.otherLeave = count - difference.days

        leaveApplication.employee.save()
        globalConfig.leaveNotification = False
        globalConfig.save()

    leaveApplication.save()
    return redirect('/leave/leaveApplications')


@login_required(login_url='/employees/login')
def declineLeave(request, applicationID):
    globalConfig = GlobalConfig.objects.all().first()
    leaveApplication = LeaveApplications.objects.get(id=applicationID)

    if request.method == 'POST':
        remarks = request.POST.get('remarks')
        leaveApplication.remarks = remarks
    
    if request.user.employee.designation.level == 2 and request.user.employee.department.name != 'HR':
        leaveApplication.deptApproval = 'declined'
        leaveApplication.deptApprovedBy = request.user.employee
    if request.user.employee.department.name == 'HR':
        leaveApplication.HRApproval = 'declined'
        leaveApplication.HRApprovedBy = request.user.employee
    if request.user.is_superuser:
        leaveApplication.finalApproval = 'declined'
        leaveApplication.finalApprovedBy = request.user.employee
    
    leaveApplication.save()
    globalConfig.leaveNotification = False
    globalConfig.save()
    return redirect('/leave/leaveApplications')

@login_required(login_url='/employees/login')
def leaveAdjustment(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"]:
        globalConfig = GlobalConfig.objects.first()
        employees = Employee.objects.all()

        # Get filters
        search_query = request.POST.get('employeeSearch', '').strip()
        selected_dept = request.POST.get('department', '')
        selected_designation = request.POST.get('designation', '')

        # Filter by search text (matches first name, last name, or full name)
        if search_query:
            employees = employees.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        # Filter by department
        if selected_dept:
            employees = employees.filter(department__id=selected_dept)

        # Filter by designation
        if selected_designation:
            employees = employees.filter(designation__id=selected_designation)

        # For dropdown options
        departments = Department.objects.all()
        designations = Designation.objects.all()

        context = {
            'employees': employees,
            'globalConfig': globalConfig,
            'departments': departments,
            'designations': designations
        }

        return render(request, 'leaveAdjustment.html', context)
    else:
        return HttpResponse("You are not authorized to view this page")


@login_required(login_url='/employees/login')
def updateLeaveAdjustment(request, employeeID):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"]:
        employee = Employee.objects.get(user=User.objects.get(id=employeeID))
        if request.method == 'POST':
            employee.casualLeave = request.POST['casualLeave']
            employee.medicalLeave = request.POST['medicalLeave']
            employee.annualLeave = request.POST['annualLeave']
            employee.otherLeave = request.POST['otherLeave']
            employee.save()

        return redirect('/leave/leaveAdjustment')
    else:
        return HttpResponse("You are not authorized to view this page")



@login_required(login_url='/employees/login')
def visitApplications(request):
    globalConfig = GlobalConfig.objects.all().first()

    # Handle new application submission
    if request.method == 'POST' and 'apply_visit' in request.POST:
        visitTo = request.POST.get('visitTo')
        start_date = request.POST.get('startDate')
        end_date = request.POST.get('endDate')
        reason = request.POST.get('reason')

        VisitApplications.objects.create(
            employee=Employee.objects.get(user=request.user),
            startDate=start_date,
            endDate=end_date,
            reason=reason,
            visitTo=visitTo
        )
        globalConfig.visitNotification = True
        globalConfig.save()
        return redirect('/leave/visitApplications')

    # Search and filter logic
    employee_search = request.POST.get('employeeSearch', '')
    dept_id = request.POST.get('department')
    desig_id = request.POST.get('designation')

    employee = Employee.objects.get(user=request.user)

    if request.user.is_superuser or employee.department.name == 'HR':
        visit_applications = VisitApplications.objects.all()
    elif employee.designation.level == 2:
        visit_applications = VisitApplications.objects.filter(employee__department=employee.department)
    else:
        visit_applications = VisitApplications.objects.filter(employee=employee)

    if employee_search:
        visit_applications = visit_applications.filter(
            Q(employee__user__first_name__icontains=employee_search) |
            Q(employee__user__last_name__icontains=employee_search)
        )
    if dept_id:
        visit_applications = visit_applications.filter(employee__department_id=dept_id)
    if desig_id:
        visit_applications = visit_applications.filter(employee__designation_id=desig_id)

    context = {
        "visit_applications": visit_applications.order_by('-applyDate'),
        "departments": Department.objects.all(),
        "employees": Employee.objects.all(),
        "designations": Designation.objects.all(),
        'globalConfig':globalConfig
    }
    return render(request, 'visitApplications.html', context)



import base64
from django.core.files.base import ContentFile
import requests
from attendance.models import Attendance
from django.utils import timezone

@login_required(login_url='/employees/login')
def approveVisit(request, applicationID):
    visitApplication = get_object_or_404(VisitApplications, id=applicationID)
    globalConfig = GlobalConfig.objects.first()
    if request.user.employee.designation.level == 2:
        visitApplication.deptApproval = 'approved'
        visitApplication.deptApprovedBy = request.user.employee
    if request.user.employee.department.name == 'HR':
        visitApplication.HRApproval = 'approved'
        visitApplication.HRApprovedBy = request.user.employee
    if request.user.is_superuser:
        visitApplication.finalApproval = 'approved'
        visitApplication.finalApprovedBy = request.user.employee

        # Save Attendance
        attendance = Attendance.objects.create(
            employee=visitApplication.employee,
            date=timezone.now().date(),
            inTime=timezone.now().time(),
            status="present",
            remote=True,
            reason=visitApplication.reason,
            location=visitApplication.visitTo,
            longitude=visitApplication.latitude,
            latitude=visitApplication.longitude,
            photo=visitApplication.photo  # optional: make sure your model has ImageField named 'photo'
        )

    visitApplication.save()
    globalConfig.visitNotification = False
    globalConfig.save()
    return redirect('/leave/visitApplications')

@login_required(login_url='/employees/login')
def declineVisit(request, applicationID):
    visitApplication = get_object_or_404(VisitApplications, id=applicationID)
    globalConfig = GlobalConfig.objects.all().first()
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        visitApplication.remarks = remarks

        if request.user.employee.designation.level == 2 and request.user.employee.department.name != 'HR':
            visitApplication.deptApproval = 'declined'
            visitApplication.deptApprovedBy = request.user.employee
        if request.user.employee.department.name == 'HR':
            visitApplication.HRApproval = 'declined'
            visitApplication.HRApprovedBy = request.user.employee
        if request.user.is_superuser:
            visitApplication.finalApproval = 'declined'
            visitApplication.finalApprovedBy = request.user.employee

        visitApplication.save()
        globalConfig.visitNotification = False
        globalConfig.save()


    return redirect('/leave/visitApplications')


from django.db.models import Count
from django.db.models.functions import ExtractMonth
import calendar
import json
from django.http import JsonResponse
from datetime import datetime
@login_required(login_url='/employees/login')
def leaveDashboard(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR" or "Human Resource"] or userModel.designation.level == 2:
        leave_types = ["Medical Leave", "Annual Leave", "Casual Leave", "Other"]
        year = int(request.GET.get('year', datetime.now().year))  # get year from request

        monthly_data = {month: {lt: 0 for lt in leave_types} for month in range(1, 13)}

        leaves = (LeaveApplications.objects
                .filter(startDate__year=year, finalApproval=True)
                .annotate(month=ExtractMonth('startDate'))
                .values('month', 'leaveType')
                .annotate(total=Count('id')))

        for entry in leaves:
            month = entry['month']
            leave_type = entry['leaveType']
            total = entry['total']
            monthly_data[month][leave_type] = total

        labels = [calendar.month_abbr[m] for m in range(1, 13)]
        colors = {
            "Medical Leave": "rgba(255, 99, 132, 0.7)",
            "Annual Leave": "rgba(54, 162, 235, 0.7)",
            "Casual Leave": "rgba(255, 206, 86, 0.7)",
            "Other": "rgba(75, 192, 192, 0.7)"
        }
        border_colors = {
            "Medical Leave": "rgba(255, 99, 132, 1)",
            "Annual Leave": "rgba(54, 162, 235, 1)",
            "Casual Leave": "rgba(255, 206, 86, 1)",
            "Other": "rgba(75, 192, 192, 1)"
        }

        datasets = []
        for lt in leave_types:
            datasets.append({
                "label": lt,
                "data": [monthly_data[m][lt] for m in range(1, 13)],
                "backgroundColor": colors[lt],
                "borderColor": border_colors[lt],
                "borderWidth": 1
            })

        # Correct AJAX check
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"labels": labels, "datasets": datasets})
        

        current_year = datetime.now().year
        years = list(range(current_year - 4, current_year + 1)) 

        employees = Employee.objects.all()
        leaveApplications = LeaveApplications.objects.all()

        if userModel.designation.level == 2:
            employees = employees.filter(department=userModel.department)
            leaveApplications = leaveApplications.filter(employee__department=userModel.department)

        globalConfig = GlobalConfig.objects.first()

        context = {
            "years": years,
            "current_year": current_year,
            "labels": labels,
            "datasets": datasets,
            "current_year": year,
            "employees": employees,
            "applications": leaveApplications,
            "globalConfig": globalConfig,
        }
        return render(request, 'leaveDashboard.html', context)
    else:
        return HttpResponse("You dont have access to the company's leave dashboard")


@login_required(login_url='/employees/login')
def leaveDashboardData(request, year):
    userModel = Employee.objects.get(user=request.user)
    leave_types = ["Medical Leave", "Annual Leave", "Casual Leave", "Other"]
    monthly_data = {m: {lt: 0 for lt in leave_types} for m in range(1, 13)}

    leaves = (LeaveApplications.objects
              .filter(startDate__year=year)
              .annotate(month=ExtractMonth('startDate'))
              .values('month', 'leaveType')
              .annotate(total=Count('id')))
    
    if userModel.designation.level == 2:
        leaves = leaves.filter(employee__department=userModel.department) 

    for entry in leaves:
        month = entry['month']
        lt = entry['leaveType']
        monthly_data[month][lt] = entry['total']

    datasets = []
    colors = {
        "Medical Leave": "rgba(255, 99, 132, 0.7)",
        "Annual Leave": "rgba(54, 162, 235, 0.7)",
        "Casual Leave": "rgba(255, 206, 86, 0.7)",
        "Other": "rgba(75, 192, 192, 0.7)"
    }
    border_colors = {
        "Medical Leave": "rgba(255, 99, 132, 1)",
        "Annual Leave": "rgba(54, 162, 235, 1)",
        "Casual Leave": "rgba(255, 206, 86, 1)",
        "Other": "rgba(75, 192, 192, 1)"
    }

    for lt in leave_types:
        datasets.append({
            "label": lt,
            "data": [monthly_data[m][lt] for m in range(1, 13)],
            "backgroundColor": colors[lt],
            "borderColor": border_colors[lt],
            "borderWidth": 1
        })

    labels = [calendar.month_abbr[m] for m in range(1, 13)]
    return JsonResponse({'labels': labels, 'datasets': datasets})