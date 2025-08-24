from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from leave.models import *
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.utils.dateparse import parse_date

def customerVisitPlan(request):
    # Pre-fetch related for efficiency
    customers = Customer.objects.all().prefetch_related('agent')
    customerVisits = CustomerVisits.objects.select_related(
        'employee__user',
        'employee__department',
        'customer',
        'agent'
    ).all()

    # --- GET filters ---
    search_query = request.GET.get("employeeSearch", "").strip()
    start_date = request.GET.get("startDateFilter", "")
    end_date = request.GET.get("endDateFilter", "")
    customer_filter = request.GET.get("customer", "")
    agent_filter = request.GET.get("agent", "")

    if search_query:
        customerVisits = customerVisits.filter(
            Q(employee__user__first_name__icontains=search_query) |
            Q(employee__user__last_name__icontains=search_query) |
            Q(employee__user__username__icontains=search_query)
        )

    if start_date:
        customerVisits = customerVisits.filter(startDate__date__gte=parse_date(start_date))
    if end_date:
        customerVisits = customerVisits.filter(endDate__date__lte=parse_date(end_date))

    if customer_filter:
        customerVisits = customerVisits.filter(customer_id=customer_filter)
    if agent_filter:
        customerVisits = customerVisits.filter(agent_id=agent_filter)

    context = {
        'customers': customers,
        'agents': CustomerAgent.objects.all(),
        'customerVisits': customerVisits.order_by('-startDate'),
        'request': request,  # needed to populate form inputs
    }
    return render(request, 'customerVisitPlan.html', context)


def addCustomer(request):
    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        Customer.objects.create(name=name, address=address)

        return redirect('/crm/customerList')

from attendance.models import Attendance
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.core.files.base import ContentFile
import base64
def addCustomerVisit(request):
    if request.method == 'POST':
        visitTo = request.POST['visitTo']
        reason = request.POST['reason']
        startDate = request.POST['startDate']
        endDate = request.POST['endDate']
        visitToAgent = request.POST['visitToAgent']
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        # Handle image
        image_data = request.POST.get("capturedPhoto")  # base64 string
        image_file = None
        if image_data:
            try:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                image_file = ContentFile(
                    base64.b64decode(imgstr),
                    name=f"{request.user.username}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                )
            except Exception as e:
                print("Image decode error:", e)

        # Get related objects safely
        customer = get_object_or_404(Customer, id=int(visitTo))
        agent = get_object_or_404(CustomerAgent, id=int(visitToAgent))
        employee = get_object_or_404(Employee, user=request.user)

        # Visit Application
        visitAppl = VisitApplications.objects.create(
            employee=employee,
            visitTo=customer.name,
            reason=reason,
            startDate=startDate.split("T")[0],
            endDate=endDate.split("T")[0],
            photo=image_file,        # ✅ Saved to ImageField
            latitude=latitude,
            longitude=longitude,
        )

        # Customer Visit
        CustomerVisits.objects.create(
            customer=customer,
            agent=agent,
            employee=employee,
            visit_application=visitAppl,
            purpose=reason,
            startDate=startDate,
            endDate=endDate
        )

        return redirect('/crm/customerVisitPlan')


    
def completeVisit(request, visitID):
    visit = CustomerVisits.objects.get(id=int(visitID))

    if request.method == 'POST':
        note = request.POST.get('note')
        potentialScope = request.POST.get('potentialScope')

        visit.note = note
        visit.potentialScope = potentialScope

        # Handle file upload
        if 'potentialScopeFile' in request.FILES:
            visit.scopeFile = request.FILES['potentialScopeFile']

        visit.save()
        return redirect('/crm/customerVisitPlan')

    return render(request, 'crm/complete_visit.html', {'application': visit})



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
    if request.method == "POST":
        customer_id = request.POST.get("customer")
        agent_id = request.POST.get("agent")
        visit_id = request.POST.get("customerVisit")
        scope_of_supply = request.POST.get("scopeOfSupply")
        status = request.POST.get("status")
        note = request.POST.get("note")
        offer_submission_date = request.POST.get("offerSubmissionDate")
        scope_file = request.FILES.get("scopeFile")

        Lead.objects.create(
            customer_id=customer_id if customer_id else None,
            agent_id=agent_id if agent_id else None,
            customerVisit_id=visit_id if visit_id else None,
            scopeOfSupply=scope_of_supply,
            status=status,
            note=note,
            offerSubmissionDate=offer_submission_date,
            scopeFile=scope_file
        )
        return redirect("lead")

    # --- GET filters ---
    leads = Lead.objects.select_related(
        "customerVisit__customer",
        "customerVisit__employee",
        "customerVisit__agent",
        "customer",
        "agent",
    ).all()

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    customer_filter = request.GET.get("customer", "")
    agent_filter = request.GET.get("agent", "")
    employee_filter = request.GET.get("employee", "")

    if search_query:
        leads = leads.filter(
            Q(customerVisit__customer__name__icontains=search_query) |
            Q(customerVisit__employee__user__first_name__icontains=search_query) |
            Q(customerVisit__employee__user__last_name__icontains=search_query) |
            Q(customerVisit__agent__agent_name__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(agent__agent_name__icontains=search_query) |
            Q(scopeOfSupply__icontains=search_query) |
            Q(note__icontains=search_query)
        )

    if status_filter:
        leads = leads.filter(status__iexact=status_filter)

    if start_date:
        leads = leads.filter(date__gte=start_date)
    if end_date:
        leads = leads.filter(date__lte=end_date)

    if customer_filter:
        leads = leads.filter(Q(customerVisit__customer_id=customer_filter) | Q(customer_id=customer_filter))
    if agent_filter:
        leads = leads.filter(Q(customerVisit__agent_id=agent_filter) | Q(agent_id=agent_filter))
    if employee_filter:
        leads = leads.filter(customerVisit__employee_id=employee_filter)

    context = {
        "leads": leads.order_by("-date"),
        "statuses": ["Open", "In Progress", "Closed"],
        "request": request,
        "customers": Customer.objects.all(),
        "agents": CustomerAgent.objects.all(),
        "visits": CustomerVisits.objects.all(),
        "employees": Employee.objects.all(),  # assuming you have this model
    }
    return render(request, "leads.html", context)

def addLead(request, visit_id):
    customer_visit = get_object_or_404(CustomerVisits, id=visit_id)

    lead = Lead.objects.create(customerVisit=customer_visit, employee=Employee.objects.get(user=request.user))
    lead.save()
    
    return redirect("/crm/lead")  # change to your detail view


def completeLead(request, leadID):
    lead = Lead.objects.get(id=leadID)
    if request.method == 'POST':
        scope = request.POST.get('scopeOfSupply')
        note = request.POST.get('note')
        offerSubmissionDate = request.POST.get('offerSubmissionDate')
        assignedTo = request.POST.get('assignedTo')

        lead.scopeOfSupply = scope
        lead.note = note
        lead.offerSubmissionDate = offerSubmissionDate
        lead.assignedTo = Employee.objects.get(id=int(assignedTo))

        # Handle file upload
        if 'scopeFile' in request.FILES:
            lead.scopeFile = request.FILES['scopeFile']

        lead.save()
    return redirect('/crm/lead')




def addLeadSeperately(request):
    if request.method == "POST":
        customer_id = request.POST.get("customer")
        agent_id = request.POST.get("agent")
        scopeOfSupply = request.POST.get("scopeOfSupply")
        scopeFile = request.FILES.get("scopeFile")
        offerSubmissionDate = request.POST.get("offerSubmissionDate")
        note = request.POST.get("note")

        lead = Lead.objects.create(
            customer=Customer.objects.get(id=customer_id) if customer_id else None,
            agent=CustomerAgent.objects.get(id=agent_id) if agent_id else None,
            scopeOfSupply=scopeOfSupply,
            scopeFile=scopeFile,
            offerSubmissionDate=offerSubmissionDate,
            note=note,
            employee=Employee.objects.get(user=request.user)
        )
        lead.save()
        return redirect('/crm/lead')

    return redirect('/crm/lead')



def offer(request):
    offers = Offer.objects.select_related(
        'lead', 
        'lead__customer', 
        'lead__agent', 
        'lead__employee', 
        'lead__assignedTo', 
        'lead__customerVisit', 
        'lead__customerVisit__customer', 
        'lead__customerVisit__agent', 
        'lead__customerVisit__employee'
    ).all()

    # --- Filtering ---
    search_query = request.GET.get('search', '').strip()
    customer_id = request.GET.get('customer')
    agent_id = request.GET.get('agent')
    employee_id = request.GET.get('employee')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if search_query:
        offers = offers.filter(
            Q(note__icontains=search_query) |
            Q(lead__scopeOfSupply__icontains=search_query) |
            Q(lead__customer__name__icontains=search_query)|
            Q(lead__customerVisit__customer__name__icontains=search_query)|
            Q(lead__agent__agent_name__icontains=search_query)|
            Q(lead__customerVisit__agent__agent_name__icontains=search_query)
        )

    if customer_id:
        offers = offers.filter(
            Q(lead__customer__id=customer_id) |
            Q(lead__customerVisit__customer__id=customer_id)
        )
    if agent_id:
        offers = offers.filter(
            Q(lead__agent__id=agent_id) |
            Q(lead__customerVisit__agent__id=agent_id)
        )
    if employee_id:
        offers = offers.filter(
            Q(lead__employee__id=employee_id) |
            Q(lead__customerVisit__employee__id=employee_id)
        )
    if start_date:
        offers = offers.filter(offer_date__gte=parse_date(start_date))
    if end_date:
        offers = offers.filter(offer_date__lte=parse_date(end_date))

    # Fetch dropdown data
    customers = Customer.objects.all()
    agents = CustomerAgent.objects.all()
    employees = Employee.objects.all()

    context = {
        'offers': offers,
        'customers': customers,
        'agents': agents,
        'employees': employees,
    }

    return render(request, 'offers.html', context)

# Offer status: Submitted, In Progress, Pending
def addOffer(request, leadID):
    lead = Lead.objects.get(id=leadID)
    offer = Offer.objects.create(lead=lead, offer_date=lead.offerSubmissionDate, status='Pending')
    offer.save()

    return redirect("/crm/offers")


def editOffer(request, offerID):
    offer = get_object_or_404(Offer, id=offerID)

    if request.method == "POST":
        # Only update editable fields
        offer.negoDate = request.POST.get('negoDate')
        offer.discount = request.POST.get('discount')
        offer.scopeOfSupply = request.POST.get('scopeOfSupply')
        offer.note = request.POST.get('note')
        offer.tgtPrice = request.POST.get('tgtPrice')

        # Validate date input
        try:
            if offer.negoDate:
                offer.negoDate = parse_date(offer.negoDate)
        except:
            return redirect(request.META.get('HTTP_REFERER'))

        offer.save()
        return redirect(request.META.get('HTTP_REFERER'))

    # fallback if GET request (optional)
    context = {
        'offer': offer
    }
    return render(request, 'edit_offer.html', context)