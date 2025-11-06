from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib.auth.models import User
from .checkNewUser import sync_employees_from_zkteco
from leave.models import LeaveApplications, VisitApplications
from attendance.models import Attendance
from core.models import GlobalConfig
from crm.models import *
from django.contrib.auth.decorators import login_required

def homeRedirection(request):
    if not request.user.is_anonymous:
        userModel = Employee.objects.get(user=request.user)
        if request.user.is_superuser or userModel.department.name == "HR" or userModel.department.name == "Human Resource":
            return redirect('/employees/employeeList')
        else:
            return redirect('/employees/indivEmployee/'+str(request.user.employee.id))
    else:
        return redirect('/employees/login')
    
def scanNewEmployee(request):
    sync_employees_from_zkteco()
    return redirect('employee_list')

@login_required(login_url='/employees/login')
def employee_list(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.designation.level == 2 or userModel.department.name == "HR" or userModel.department.name == "Human Resource":
        globalConfig = GlobalConfig.objects.all().first()
        employees = Employee.objects.select_related('user', 'department', 'designation')
        departments = Department.objects.all()
        designations = Designation.objects.all()

        if not request.user.is_superuser and userModel.designation.level == 2:
            employees = employees.filter(department=userModel.department)

        context = {
            'employees': employees,
            'departments': departments,
            'designations': designations,
            'globalConfig':globalConfig
        }
        return render(request, 'employeeList.html', context)
    else:
        return HttpResponse("You do not have permission to view the employee list.")

@login_required(login_url='/employees/login')
def addEmployee(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name == "HR" or userModel.department.name == "Human Resource":
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
    else:
        return HttpResponse("You do not have permission to add employees.")


@login_required(login_url='/employees/login')
def editEmployee(request, employeeID):
    employee = get_object_or_404(Employee, id=employeeID)
    userModel = Employee.objects.get(user=request.user)
    can_edit_details = (
        request.user.is_superuser or
        userModel.department.name in ["HR", "Human Resource"]
    )
    can_change_password = (employee.user == request.user)

    if request.method == 'POST':
        # Check if editing password only by employee himself
        if can_change_password and not can_edit_details:
            # Allow only password change for own user
            user = employee.user
            if request.POST.get('password'):
                user.set_password(request.POST['password'])  # Securely set new password
                user.save()
                # Optionally update password field in Employee model if it stores raw password (not recommended)
                employee.password = request.POST['password']
                employee.save()
            return redirect('/employees/indivEmployee/' + str(employee.id))

        # Check if HR, Human Resource, or superuser is editing details
        elif can_edit_details:
            user = employee.user
            user.username = request.POST['email']
            user.email = request.POST['email']
            if request.POST.get('password'):
                user.set_password(request.POST['password'])
            user.save()

            employee.department = Department.objects.get(id=int(request.POST['department']))
            employee.designation = Designation.objects.get(id=int(request.POST['designation']))
            employee.phone = request.POST['phone']
            employee.salary = request.POST['salary']
            employee.status = request.POST['status']
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                employee.profile_picture = profile_picture
            if request.POST.get('password'):
                employee.password = request.POST['password']
            employee.save()
            return redirect('/employees/indivEmployee/' + str(employee.id))

        else:
            return HttpResponse("You do not have permission to edit employees.")
    else:
        # GET request logic (if needed): render template or return info
        return HttpResponse("Bad request.")



from django.db.models import Value, CharField
from django.db.models.functions import Concat
@login_required(login_url='/employees/login')
def getEmployee(request):
    globalConfig = GlobalConfig.objects.all().first()
    departments = Department.objects.all()
    designations = Designation.objects.all()
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name == "HR" or userModel.department.name == "Human Resource" or userModel.designation.level == 2:
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
    else:
        return HttpResponse("You do not have permission to search employees.")
    

from datetime import date, timedelta
from django.db.models import Q
@login_required(login_url='/employees/login')
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
    
    userModel = Employee.objects.get(user=request.user)
    if (
        employee.user.id == request.user.id
        or request.user.is_superuser
        or (userModel.designation.level == 2 and userModel.department == employee.department)
        or (userModel.department.name in ['HR', 'Human Resource'])
    ):
        # Get CustomerVisits related to the employee
        customerVisitPlans = CustomerVisits.objects.filter(employee=employee)

        # Leads as a marketer: full objects, not just IDs
        leadsAsAMarketer = Lead.objects.filter(
            Q(employee=employee) |
            Q(customerVisit__in=CustomerVisits.objects.filter(employee=employee))
        ).distinct()

        # Offers and orders as marketer
        offersAsAMarketer = Offer.objects.filter(lead__in=leadsAsAMarketer)
        ordersAsAMarketer = Order.objects.filter(offer__in=offersAsAMarketer)

        # Leads as salesman: full objects
        leadsAsASalesman = Lead.objects.filter(assignedTo=employee)
        offersAsASalesman = Offer.objects.filter(lead__in=leadsAsASalesman)
        ordersAsASalesman = Order.objects.filter(offer__in=offersAsASalesman)


        today = date.today()
        today_minus_30 = today - timedelta(days=30)
        today_minus_365 = today - timedelta(days=365)
        

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
            'globalConfig':globalConfig,
            'today':today,
            'today_minus_30':today_minus_30,
            'today_minus_365':today_minus_365,
            'customerVisitPlans':customerVisitPlans,
            'leadsAsAMarketer':leadsAsAMarketer,
            'offersAsAMarketer':offersAsAMarketer,
            'ordersAsAMarketer':ordersAsAMarketer,
            'leadsAsASalesman':leadsAsASalesman,
            'offersAsASalesman':offersAsASalesman,
            'ordersAsASalesman':ordersAsASalesman,

        })
    else:
        return HttpResponse("You do not have permission to view this employee's details.")

@login_required
def viewAwards(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    awards = Award.objects.all()
    employees = Employee.objects.all()

    if request.user.is_superuser:
        awards = Award.objects.all()
    elif userModel.designation.level == 2:
        if userModel.designation.level == 2:
            awards = awards.filter(employee__department=userModel.department)
    else:
        # Normal employees see their own awards only
        awards = awards.filter(employee=userModel)

    context = {
        'awards': awards,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'awards.html', context)


@login_required(login_url='/employees/login')
def addAwards(request):
    globalConfig = GlobalConfig.objects.all().first()
    if request.user.is_superuser:
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
    else:
        return HttpResponse("You do not have permission to add awards.")


@login_required(login_url='/employees/login')
def viewHealthInsurance(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    health_insurances = HealthInsurance.objects.all()
    employees = Employee.objects.all()

    if request.user.is_superuser or userModel.designation.level == 2:
        if userModel.designation.level == 2:
            health_insurances = health_insurances.filter(employee__department=userModel.department)
    else:
        # Normal employees see their own insurance only
        health_insurances = health_insurances.filter(employee=userModel)

    context = {
        'insurances': health_insurances,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'healthInsurance.html', context)


from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
@require_POST
@login_required(login_url='/employees/login')
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


@login_required
def viewCar(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    cars = Car.objects.all()
    carAmenities = CarUsage.objects.all()
    employees = Employee.objects.all()

    if request.user.is_superuser or (userModel.department.name in ["Administration", "Admin"]):
        pass
    else:
        # Normal employees see only car usages related to them and their own cars if applicable
        carAmenities = carAmenities.filter(employee=userModel)

    context = {
        'cars': cars,
        'carUsage': carAmenities,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'car.html', context)

@login_required(login_url='/employees/login')
def addCar(request):
    if request.user.is_superuser:
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
    else:
        return HttpResponse("You do not have permission to add cars.")

@login_required(login_url='/employees/login')
def addCarAmenity(request):
    userModel = Employee.objects.get(user=request.user)
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

        if (
            request.user.is_superuser
            or (userModel.designation.level == 2 and userModel.department == employee.department)
            or userModel.department.name in ["Admin", "Administration"]
        ):
            CarUsage.objects.create(car=car, employee=employee, usage_date=date, distance_covered=distance_covered, purpose=purpose, 
                                    startTime=startingTime, endTime=endingTime, origin=origin, destination=destination)
        else:
            return HttpResponse("You are not allowed to issue car facilities.")

        return redirect('/employees/benefits/viewCars')

    return redirect('/employees/benefits/viewCars')


@login_required(login_url='/employees/login')
def viewMobile(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    mobiles = Mobile.objects.all()
    employees = Employee.objects.all()

    if (request.user.is_superuser or
        userModel.department.name in ["Administration", "Admin", "HR", "Human Resource"] or
        userModel.designation.level == 2):
        if userModel.designation.level == 2:
            mobiles = mobiles.filter(employee__department=userModel.department)
    else:
        # Normal employees see their own mobiles
        mobiles = mobiles.filter(employee=userModel)

    context = {
        'mobiles': mobiles,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'mobile.html', context)

@login_required(login_url='/employees/login')
def addMobile(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser:
        if request.method == 'POST':
            employeeID = request.POST['employee']
            mobileModel = request.POST['mobileModel']
            amount = request.POST['amount']
            voucher = request.FILES.get('voucher')

            employee = Employee.objects.get(id=employeeID)

            if (userModel.designation.level == 2 and (userModel.department.name == "Admin" or userModel.department.name == "Administration")) or request.user.is_superuser:
                Mobile.objects.create(
                    employee=employee,
                    mobileModel=mobileModel,
                    amount = amount,
                    file=voucher
                )
                return redirect('/employees/benefits/viewMobile')  # or wherever your list page is
            else:
                return HttpResponse("You do not have permission to add mobile benefits for this employee.")

        return redirect('/employees/benefits/viewMobile')
    else:
        return HttpResponse("You do not have permission to add mobile benefits.")



@login_required(login_url='/employees/login')
def viewAccomodation(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    accomodations = Accomodation.objects.all()
    employees = Employee.objects.all()

    if (request.user.is_superuser or userModel.designation.level == 2 or
        userModel.department.name in ["HR", "Human Resource", "Admin", "Administration"]):
        if userModel.designation.level == 2:
            accomodations = accomodations.filter(employee__department=userModel.department)
    else:
        accomodations = accomodations.filter(employee=userModel)

    context = {
        'accomodations': accomodations,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'accomodation.html', context)


@login_required(login_url='/employees/login')
def addAccomodation(request):
    userModel = Employee.objects.get(user=request.user)
    
    if (
        request.user.is_superuser
        or userModel.department.name in ['Admin', 'Administration']
    ):
        if request.method == 'POST':
            employeeID = request.POST['employee']
            reimbursement = request.POST['reimbursement']
            voucher = request.FILES.get('voucher')

            employee = Employee.objects.get(id=employeeID)

            if (userModel.department == employee.department and userModel.designation.level == 2) or request.user.is_superuser or userModel.department.name == 'Admin' or userModel.department.name == 'Administration':
                Accomodation.objects.create(
                    employee=employee,
                    reimbursement=reimbursement,
                    file=voucher
                )

                return redirect('/employees/benefits/viewAccomodation')  # or wherever your list page is
            else:
                return HttpResponse("You do not have permission to add accomodation benefits for this employee.")

        return redirect('/employees/benefits/viewAccomodation')
    else:
        return HttpResponse("You do not have permission to add accomodation benefits.")



@login_required(login_url='/employees/login')
def viewTravelAllowance(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    travel_allowances = TravelAllowance.objects.all()
    employees = Employee.objects.all()

    if (request.user.is_superuser or userModel.designation.level == 2 or
        userModel.department.name in ["HR", "Human Resource", "Admin", "Administration"]):
        if userModel.designation.level == 2:
            travel_allowances = travel_allowances.filter(employee__department=userModel.department)
    else:
        travel_allowances = travel_allowances.filter(employee=userModel)

    context = {
        'allowances': travel_allowances,
        'employees': employees,
        'globalConfig': globalConfig
    }
    return render(request, 'travelAllowance.html', context)

@login_required(login_url='/employees/login')
def addTravelAllowance(request):
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or userModel.department.name in ["HR", "Human Resource", "Admin", "Administration"]:
        if request.method == 'POST':
            employeeID = request.POST['employee']
            amount = request.POST['amount']

            employee = Employee.objects.get(id=employeeID)
            
            if (userModel.department.name in ["HR", "Human Resource", "Admin", "Administration"]) or request.user.is_superuser:    
                TravelAllowance.objects.create(
                    employee=employee,
                    amount=amount
                )

                return redirect('/employees/benefits/viewTravelAllowance')  # or wherever your list page is
            else:
                return HttpResponse("You do not have permission to add travel allowance for this employee.")

        return redirect('/employees/benefits/viewTravelAllowance')


@login_required(login_url='/employees/login')
def departments(request):
    globalConfig = GlobalConfig.objects.all().first()
    userModel = Employee.objects.get(user=request.user)
    if request.user.is_superuser or (userModel.department.name in ['HR', 'Human Resource']):
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
    else:
        return HttpResponse("You do not have permission to manage departments.")

from datetime import datetime
@login_required(login_url='/employees/login')
def viewFoodAndMeals(request):
    userModel = Employee.objects.get(user=request.user)
    globalConfig = GlobalConfig.objects.all().first()
    date_str = request.GET.get('date')
    selected_date = None
    isAdmin = False

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = None

    # Check permissions
    if request.user.is_superuser or userModel.department.name in ['Admin', 'Administration']:
        isAdmin = True
        enrollments = LunchEnrollment.objects.filter(is_active=True)
        if selected_date:
            enrollments = enrollments.filter(enrolled_on__date=selected_date)
    else:
        isAdmin = False
        # Normal employee can view only own enrollments
        enrollments = LunchEnrollment.objects.filter(employee=userModel, is_active=True)
        if selected_date:
            enrollments = enrollments.filter(enrolled_on__date=selected_date)

    enrollments = enrollments.select_related('employee__user', 'employee__department')
    employees = Employee.objects.select_related('user', 'department')

    return render(request, 'food.html', {
        'enrollments': enrollments,
        'employees': employees,
        'selected_date': date_str,
        'globalConfig': globalConfig,
        'isAdmin':isAdmin,
        'userModel':userModel
    })


@login_required(login_url='/employees/login')
def add_lunch_enrollment(request):
    userModel = Employee.objects.get(user=request.user)
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
    if request.user.is_superuser or request.user.employee.department.name == 'Commercial' or request.user.employee.designation.level == 2:
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
    else:
        return HttpResponse("You do not have permission to view reimbursement requests.")



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
            return redirect('/') 
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def logout_(request):
    logout(request)
    return redirect('/employees/login')  # Redirect to login page after logout