from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.models import User
from .checkNewUser import sync_employees_from_zkteco
from leave.models import LeaveApplications, VisitApplications
from attendance.models import Attendance
from core.models import GlobalConfig

def scanNewEmployee(request):
    sync_employees_from_zkteco()
    return redirect('employee_list')

def employee_list(request):
    globalConfig = GlobalConfig.objects.all().first()
    employees = Employee.objects.select_related('user', 'department', 'designation')
    departments = Department.objects.all()
    designations = Designation.objects.all()

    context = {
        'employees': employees,
        'departments': departments,
        'designations': designations,
        'globalConfig':globalConfig
    }
    return render(request, 'employeeList.html', context)


def addEmployee(request):
    if request.method == 'POST':
        # Create user
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['username']
        password = request.POST['password']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create employee
        department_id = request.POST['department']
        designation_id = request.POST['designation']
        phone = request.POST['phone']
        date_of_birth = request.POST['date_of_birth']
        salary = request.POST['salary']
        status = request.POST['status']
        profile_picture = request.FILES.get('profile_picture')

        Employee.objects.create(
            user=user,
            department_id=department_id,
            designation_id=designation_id,
            phone=phone,
            date_of_birth=date_of_birth,
            salary=salary,
            status=status,
            profile_picture=profile_picture,
            password=password  # only if you really want it stored again
        )

        return redirect('employee_list')  # or wherever your list page is

    return redirect('employee_list')



def editEmployee(request, employeeID):
    employee = get_object_or_404(Employee, id=employeeID)

    if request.method == 'POST':
        # Update user fields
        user = employee.user
        user.username = request.POST['email']
        user.email = request.POST['email']  # same as username
        if request.POST.get('password'):
            user.set_password(request.POST['password'])  # Securely set new password
        user.save()

        # Update employee fields
        employee.department = Department.objects.get(id=int(request.POST['department']))
        employee.designation = Designation.objects.get(id=int(request.POST['designation']))
        employee.phone = request.POST['phone']
        employee.salary = request.POST['salary']
        employee.status = request.POST['status']
        profile_picture = request.FILES.get('profile_picture')

        if profile_picture:
            employee.profile_picture = profile_picture

        if request.POST.get('password'):
            employee.password = request.POST['password']  # Optional: if stored again

        employee.save()

        return redirect('/employees/indivEmployee/'+str(employee.id))  # or a detail page


from django.db.models import Value, CharField
from django.db.models.functions import Concat
def getEmployee(request):
    globalConfig = GlobalConfig.objects.all().first()
    departments = Department.objects.all()
    designations = Designation.objects.all()

    if request.method == 'POST':
        search_name = request.POST.get('employeeSearch', '').strip()

        employees = Employee.objects.select_related('user', 'department', 'designation') \
                .annotate(full_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField())) \
                .filter(full_name__icontains=search_name)

        # Filter from GET parameters
        department_id = request.POST.get('department')
        designation_id = request.POST.get('designation')

        if department_id:
            employees = employees.filter(department_id=department_id)

        if designation_id:
            employees = employees.filter(designation_id=designation_id)

        context = {
            'employees': employees,
            'departments': departments,
            'designations': designations,
        'globalConfig':globalConfig
        }
        return render(request, 'employeeList.html', context)
    


def indivEmployee(request, employeeID):
    globalConfig = GlobalConfig.objects.all().first()
    employee = get_object_or_404(Employee, id=employeeID)
    designations = Designation.objects.all()
    departments = Department.objects.all()
    lunchEnrollments = LunchEnrollment.objects.filter(employee=employee)
    carUsages = CarUsage.objects.filter(employee=employee)
    reimbursements = Reimbursements.objects.filter(employee=employee)
    leave = LeaveApplications.objects.filter(employee=employee)
    attendance = Attendance.objects.filter(employee=employee)
    visits = VisitApplications.objects.filter(employee=employee)
    

    # Example chart data (replace with actual data)
    chart_data = {
        "labels": ["Award", "Insurance", "Incentives", "Travel"],
        "values": [2, 1, 3, 1]
    }

    return render(request, 'indivEmployee.html', {
        'employee': employee,
        'chart_data': chart_data, 
        'designations':designations,
        'departments': departments,
        'lunchEnrollments': lunchEnrollments,
        'carUsages':carUsages, 
        'reimbursements':reimbursements,
        'leave':leave,
        'attendances':attendance.order_by('-date'),
        'visits':visits,
        'globalConfig':globalConfig
    })



def viewAwards(request):
    globalConfig = GlobalConfig.objects.all().first()
    awards = Award.objects.all()
    employees = Employee.objects.all()
    context = {
        'awards': awards,
        'employees':employees,
        'globalConfig':globalConfig
    }
    return render(request, 'awards.html', context)

def addAwards(request):
    globalConfig = GlobalConfig.objects.all().first()
    if request.method == 'POST':
        employee_id = request.POST['employee']
        title = request.POST['title']
        description = request.POST.get('description', '')
        date_awarded = request.POST['date_awarded']
        amount = request.POST['amount']

        employee = Employee.objects.get(id=employee_id)

        Award.objects.create(
            employee=employee,
            title=title,
            description=description,
            date_awarded=date_awarded,
            amount=amount
        )

        return redirect('viewAwards') 

    return redirect('viewAwards')


def viewHealthInsurance(request):
    globalConfig = GlobalConfig.objects.all().first()
    health_insurances = HealthInsurance.objects.all()
    employees = Employee.objects.all()
    context = {
        'insurances': health_insurances,
        'employees': employees,
        'globalConfig':globalConfig
    }
    return render(request, 'healthInsurance.html', context)


from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
@require_POST
def addHealthInsurance(request):
    try:
        employee_id = request.POST.get('employee')
        amount = request.POST.get('amount')
        start_date = request.POST.get('startDate')
        end_date = request.POST.get('endDate')

        employee = get_object_or_404(Employee, id=employee_id)

        HealthInsurance.objects.create(
            employee=employee,
            coverage_amount=amount,
            start_date=parse_date(start_date),
            end_date=parse_date(end_date)
        )

        messages.success(request, "Health insurance added successfully.")
    except Exception as e:
        messages.error(request, f"Error adding insurance: {e}")

    return redirect('/employees/benefits/healthInsurance') 


def viewCar(request):
    globalConfig = GlobalConfig.objects.all().first()
    cars = Car.objects.all()
    carAmenities = CarUsage.objects.all()
    employees = Employee.objects.all()
    context = {
        'cars': cars,
        'carUsage':carAmenities,
        'employees': employees,
        'globalConfig':globalConfig
    }
    return render(request, 'car.html', context)


def addCar(request):
    if request.method == 'POST':
        carModel = request.POST['carModel']
        number = request.POST['carNumber']
        inclusionDate = request.POST['inclusionDate']
        fuelReimbursement = request.POST['fuelReimbursement']

        Car.objects.create(
            carModel=carModel,
            number=number,
            inclusionDate=inclusionDate,
            fuelReimbursement=fuelReimbursement,

        )

        return redirect('/employees/benefits/viewCars')

    return redirect('/employees/benefits/viewCars')

def addCarAmenity(request):
    if request.method == 'POST':
        carID = request.POST['car']
        car = Car.objects.get(id=carID)
        employeeID = request.POST['employee']
        employee = Employee.objects.get(id=employeeID)
        date = request.POST['date']
        startingTime = request.POST['startTime']
        endingTime = request.POST['endTime']
        origin = request.POST['origin']
        destination = request.POST['destination']
        distance_covered = request.POST['distance']
        purpose = request.POST['purpose']

        CarUsage.objects.create(car=car, employee=employee, usage_date=date, distance_covered=distance_covered, purpose=purpose, 
                                startTime=startingTime, endTime=endingTime, origin=origin, destination=destination)

        return redirect('/employees/benefits/viewCars')

    return redirect('/employees/benefits/viewCars')


def viewMobile(request):
    globalConfig = GlobalConfig.objects.all().first()
    mobiles = Mobile.objects.all()
    employees = Employee.objects.all()
    context = {
        'mobiles':mobiles,
        'employees': employees,
        'globalConfig':globalConfig
    }
    return render(request, 'mobile.html', context)


def addMobile(request):
    if request.method == 'POST':
        employeeID = request.POST['employee']
        mobileModel = request.POST['mobileModel']
        amount = request.POST['amount']
        voucher = request.FILES.get('voucher')

        employee = Employee.objects.get(id=employeeID)

        Mobile.objects.create(
            employee=employee,
            mobileModel=mobileModel,
            amount = amount,
            file=voucher
        )

        return redirect('/employees/benefits/viewMobile')  # or wherever your list page is

    return redirect('/employees/benefits/viewMobile')


def viewAccomodation(request):
    globalConfig = GlobalConfig.objects.all().first()
    accomodations = Accomodation.objects.all()
    employees = Employee.objects.all()
    context = {
        'accomodations': accomodations,
        'employees': employees,
        'globalConfig':globalConfig
    }
    return render(request, 'accomodation.html', context)

def addAccomodation(request):
    if request.method == 'POST':
        employeeID = request.POST['employee']
        reimbursement = request.POST['reimbursement']
        voucher = request.FILES.get('voucher')

        employee = Employee.objects.get(id=employeeID)

        Accomodation.objects.create(
            employee=employee,
            reimbursement=reimbursement,
            file=voucher
        )

        return redirect('/employees/benefits/viewAccomodation')  # or wherever your list page is

    return redirect('/employees/benefits/viewAccomodation')


def viewTravelAllowance(request):
    globalConfig = GlobalConfig.objects.all().first()
    travel_allowances = TravelAllowance.objects.all()
    employees = Employee.objects.all()
    context = {
        'allowances': travel_allowances,
        'employees': employees,
        'globalConfig':globalConfig
    }
    return render(request, 'travelAllowance.html', context)

def addTravelAllowance(request):
    if request.method == 'POST':
        employeeID = request.POST['employee']
        amount = request.POST['amount']

        employee = Employee.objects.get(id=employeeID)

        TravelAllowance.objects.create(
            employee=employee,
            amount=amount
        )

        return redirect('/employees/benefits/viewTravelAllowance')  # or wherever your list page is

    return redirect('/employees/benefits/viewTravelAllowance')



def departments(request):
    globalConfig = GlobalConfig.objects.all().first()
    if request.method == 'POST':
        # Check which form was submitted
        if 'deptName' in request.POST:
            dept_name = request.POST.get('deptName')
            if dept_name:
                Department.objects.create(name=dept_name)
                messages.success(request, "Department added successfully.")

        elif 'title' in request.POST:
            designation_name = request.POST.get('title')
            if designation_name:
                Designation.objects.create(title=designation_name)
                messages.success(request, "Designation added successfully.")

        return redirect('/employees/departments')

    departments = Department.objects.all()
    designations = Designation.objects.all()
    return render(request, 'departments.html', {
        'departments': departments,
        'designations': designations,
        'globalConfig':globalConfig
    })

from datetime import datetime
def viewFoodAndMeals(request):
    globalConfig = GlobalConfig.objects.all().first()
    date_str = request.GET.get('date')
    selected_date = None

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            enrollments = LunchEnrollment.objects.filter(enrolled_on__date=selected_date, is_active=True)
        except ValueError:
            enrollments = LunchEnrollment.objects.filter(is_active=True)
    else:
        enrollments = LunchEnrollment.objects.filter(is_active=True)

    employees = Employee.objects.select_related('user', 'department')

    return render(request, 'food.html', {
        'enrollments': enrollments.select_related('employee__user', 'employee__department'),
        'employees': employees,
        'selected_date': date_str,
        'globalConfig':globalConfig
    })



def add_lunch_enrollment(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        if employee_id:
            employee = Employee.objects.get(id=employee_id)

            # Prevent duplicate active enrollments
            if LunchEnrollment.objects.filter(employee=employee, is_active=True).exists():
                messages.warning(request, f"{employee.user.get_full_name()} is already enrolled.")
            else:
                LunchEnrollment.objects.create(employee=employee)
                messages.success(request, f"{employee.user.get_full_name()} enrolled for lunch successfully.")
        return redirect('/employees/benefits/viewFoodAndMeals')
    

def reimbursement_requests(request):
    globalConfig = GlobalConfig.objects.all().first()
    user = request.user
    employee = Employee.objects.get(user=user)

    if request.user.is_superuser or request.user.employee.department.name == 'Commercial':
        reimbursementsAll = Reimbursements.objects.all()
    elif request.user.employee.designation.level == 2:
        reimbursementsAll = Reimbursements.objects.filter(employee__department=employee.department)
    else:
        reimbursementsAll = Reimbursements.objects.filter(employee=employee)

    # Handle form submission
    if request.method == "POST":
        reason = request.POST.get("reason")
        source = request.POST.get("source")
        amount = request.POST.get("amount")
        remarks = request.POST.get("remarks")
        voucher = request.FILES.get("voucher")

        Reimbursements.objects.create(
            employee=employee,
            reason=reason,
            purchasedFrom=source,
            amount=amount,
            remarks=remarks,
            file=voucher
        )
        return redirect("/employees/reimbursementRequests")  # replace with your URL name

    # Handle GET (listing with optional date filtering)
    selected_date = request.GET.get("date")
    if selected_date:
        reimbursements = reimbursementsAll.filter(dateRequested=selected_date)
    else:
        reimbursements = reimbursementsAll

    context = {
        "reimbursements": reimbursements.order_by('-dateRequested'),
        "selected_date": selected_date,
        'globalConfig':globalConfig
    }
    return render(request, "reimbursement.html", context)



def approveReimbursement(request, reimbursementID):
    reimbursement = Reimbursements.objects.get(id=reimbursementID)
    if request.user.employee.designation.level == 2:
        reimbursement.deptApproval = 'approved'
        reimbursement.deptApprovedBy = request.user.employee
    if request.user.employee.department.name == 'Commercial':
        reimbursement.commercialApproval = 'approved'
        reimbursement.commercialApprovedBy = request.user.employee
    if request.user.is_superuser:
        reimbursement.finalApproval = 'approved'
        reimbursement.finalApprovedBy = request.user.employee
    if request.user == reimbursement.employee.user:
        reimbursement.moneyRecieved = True

    reimbursement.save()
    return redirect('/employees/reimbursementRequests')

def declineReimbursement(request, reimbursementID):
    reimbursement = Reimbursements.objects.get(id=reimbursementID)
    if request.user.employee.designation.level == 2 and request.user.employee.department.name != 'Commercial':
        reimbursement.deptApproval = 'declined'
        reimbursement.deptApprovedBy = request.user.employee
    if request.user.employee.department.name == 'Commercial':
        reimbursement.commercialApproval = 'declined'
        reimbursement.commercialApprovedBy = request.user.employee
    if request.user.is_superuser:
        reimbursement.finalApproval = 'declined'
        reimbursement.finalApprovedBy = request.user.employee
    
    reimbursement.save()
    return redirect('/employees/reimbursementRequests')



from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

def login_(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/employees') 
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def logout_(request):
    logout(request)
    return redirect('/employees/login')  # Redirect to login page after logout