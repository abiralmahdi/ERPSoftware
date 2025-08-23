from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from leave.models import *
from django.db.models import Q
from django.utils.dateparse import parse_date

def customerVisitPlan(request):
    customers = Customer.objects.all().prefetch_related('agent')
    customerVisits = CustomerVisits.objects.all()

    # --- Filtering logic ---
    if request.method == "POST":
        # Employee search
        employee_query = request.POST.get("employeeSearch", "").strip()
        if employee_query:
            customerVisits = customerVisits.filter(
                Q(employee__user__first_name__icontains=employee_query) |
                Q(employee__user__last_name__icontains=employee_query) |
                Q(employee__user__username__icontains=employee_query)
            )

        # Date range filter
        start_date = request.POST.get("startDateFilter")
        end_date = request.POST.get("endDateFilter")

        if start_date:
            customerVisits = customerVisits.filter(startDate__date__gte=parse_date(start_date))
        if end_date:
            customerVisits = customerVisits.filter(endDate__date__lte=parse_date(end_date))

    context = {
        'customers': customers,
        'customerVisits': customerVisits
    }
    return render(request, 'customerVisitPlan.html', context)

def addCustomer(request):
    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        Customer.objects.create(name=name, address=address)

        return redirect('/crm/customerList')
    
def addCustomerVisit(request):
    if request.method == 'POST':
        visitTo = request.POST['visitTo']
        reason = request.POST['reason']
        startDate = request.POST['startDate']
        endDate = request.POST['endDate']
        visitToAgent = request.POST['visitToAgent']

        visitAppl = VisitApplications.objects.create(employee=Employee.objects.get(user=request.user), startDate=startDate.split("T")[0], endDate=endDate.split("T")[0], visitTo=Customer.objects.get(id=int(visitTo)).name, reason=reason)
        visitAppl.save()

        customerVisit = CustomerVisits.objects.create(customer=Customer.objects.get(id=int(visitTo)), agent=CustomerAgent.objects.get(id=int(visitToAgent)), employee=Employee.objects.get(user=request.user), visit_application=visitAppl, purpose=reason, startDate=startDate, endDate=endDate)
        customerVisit.save()

        return redirect('/crm/customerVisitPlan')
    
def completeVisit(request, visitID):
    visit = CustomerVisits.objects.get(id=int(visitID))
    if request.method == 'POST':
        note = request.POST['note']
        potentialScope = request.POST['potentialScope']
        visit.note = note
        visit.potentialScope = potentialScope
        visit.save()

        return redirect('/crm/customerVisitPlan')


def addContactPerson(reqeust):
    if reqeust.method == 'POST':
        customer = reqeust.POST['customer']
        name = reqeust.POST['name']
        email = reqeust.POST['email']
        phone = reqeust.POST['phone']

        contactPerson = CustomerAgent.objects.create(customer=Customer.objects.get(id=int(customer)), agent_name=name, agent_email=email, agent_contact=phone)
        contactPerson.save()

        return redirect('/crm/customerList')

def customerList(request):
    contactPersons = CustomerAgent.objects.all()
    customers = Customer.objects.all()
    context = {
        'customers':customers,
        'contactPersons':contactPersons
    }
    return render(request, 'customerList.html', context)



def lead(request):
    leads = Lead.objects.select_related(
        "customerVisit__customer",
        "customerVisit__employee",
        "customerVisit__agent"
    ).all()

    # --- Filters ---
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    # Apply search (on customer, employee, agent, scopeOfSupply)
    if search_query:
        leads = leads.filter(
            Q(customerVisit__customer__name__icontains=search_query) |
            Q(customerVisit__employee__user__first_name__icontains=search_query) |
            Q(customerVisit__employee__user__last_name__icontains=search_query) |
            Q(customerVisit__agent__agent_name__icontains=search_query) |
            Q(scopeOfSupply__icontains=search_query)
        )

    # Status filter
    if status_filter:
        leads = leads.filter(status=status_filter)

    # Date range filter
    if start_date:
        leads = leads.filter(date__gte=start_date)
    if end_date:
        leads = leads.filter(date__lte=end_date)

    context = {
        "leads": leads.order_by("-date"),
        "statuses": ["Open", "In Progress", "Closed"],  # you can adjust this
        "request": request,
    }
    return render(request, "leads.html", context)


def addLead(request, visit_id):
    customer_visit = get_object_or_404(CustomerVisits, id=visit_id)

    if request.method == "POST":
        scope = request.POST.get("scopeOfSupply")
        status = request.POST.get("status")

        try:
            Lead.objects.create(
                customerVisit=customer_visit,
                scopeOfSupply=scope,
                status=status
            )
        except Exception as e:
            pass
        return redirect("/crm/lead")  # change to your detail view

