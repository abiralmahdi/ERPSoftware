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
    ).all().prefetch_related('offer')

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
    offer = Offer.objects.get_or_create(lead=lead, offer_date=lead.offerSubmissionDate)

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
        offer.offerValue = request.POST.get('offerValue')
        offer.status = request.POST.get('status')
        offer.save()
        print(offer.status)
        if request.POST.get('status') == "Win":
            offer = Offer.objects.get(id=offerID)
            if offer.status == "Win":
                order = Order.objects.create(offer=offer)
                order.save()
        # File handling
        if 'offerFile' in request.FILES:
            offer.offerFile = request.FILES['offerFile']

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



from django.db.models import Q
from django.shortcuts import render
from .models import Order, Customer, Employee, Lead
from datetime import date

def orders(request):
    orders_qs = Order.objects.select_related('offer', 'offer__lead').all()

    # GET params
    search = request.GET.get('search', '').strip()
    customer_id = request.GET.get('customer')
    agent_id = request.GET.get('agent')
    employee_id = request.GET.get('employee')        # AssignedTo
    market_person_id = request.GET.get('marketPersons')  # Lead Generator
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Search in Offer.note or Lead.scopeOfSupply
    if search:
        orders_qs = orders_qs.filter(
            Q(offer__note__icontains=search) |
            Q(offer__lead__scopeOfSupply__icontains=search)
        )

    # Filter by Market Person (Lead Generator)
    if market_person_id:
        orders_qs = orders_qs.filter(
            Q(offer__lead__customerVisit__employee_id=market_person_id) |
            Q(offer__lead__employee_id=market_person_id)
        )

    # Filter by Customer
    if customer_id:
        orders_qs = orders_qs.filter(
            Q(offer__lead__customer_id=customer_id) |
            Q(offer__lead__customerVisit__customer_id=customer_id)
        )

    # Filter by Agent
    if agent_id:
        orders_qs = orders_qs.filter(
            Q(offer__lead__agent_id=agent_id) |
            Q(offer__lead__customerVisit__agent_id=agent_id)
        )

    # Filter by AssignedTo (Sales Person)
    if employee_id:
        orders_qs = orders_qs.filter(offer__lead__assignedTo_id=employee_id)

    # Filter by delivery_date
    if start_date:
        orders_qs = orders_qs.filter(delivery_date__gte=start_date)
    if end_date:
        orders_qs = orders_qs.filter(delivery_date__lte=end_date)

    # Remove duplicates from reverse FK joins

    today = date.today()
    orders_qs = orders_qs.distinct()

    for order in orders_qs:
        order.is_overdue = order.delivery_date and today > order.delivery_date
    context = {
        "orders": orders_qs,
        "customers": Customer.objects.all(),
        "agents": CustomerAgent.objects.all(),
        "employees": Employee.objects.all(),
    }
    return render(request, "order.html", context)


def addOrder(request, offerID):
    offer = Offer.objects.get(id=offerID)
    if offer.status == "Win":
        order = Order.objects.create(offer=offer)
        order.save()
    return redirect("/crm/orders")



def editOrder(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.delivery_date = request.POST.get("delivery_date")
        order.status = request.POST.get("status")
        order.advance_payment = request.POST.get("advance_payment")
        order.order_value = request.POST.get("order_value")
        order.note = request.POST.get("note")
        order.poRef = request.POST.get("poRef")

        # validate date
        if order.delivery_date:
            order.delivery_date = parse_date(order.delivery_date)

        order.save()

        # Handle files
        if request.FILES.getlist("order_files"):
            for f in request.FILES.getlist("order_files"):
                OrderFiles.objects.create(order=order, file=f)
        
        if order.status == 'Delivered' or order.status == 'Partial Delivered':
            sale = Sales.objects.create(order=order, status=order.status)

        return redirect("/crm/orders")


from django.db.models import Q
from django.shortcuts import render
from .models import Sales, Customer

def sales(request):
    # Base queryset with related fields to minimize queries
    sales_qs = Sales.objects.select_related(
        'order',
        'order__offer',
        'order__offer__lead',
        'order__offer__lead__customer',
        'order__offer__lead__customerVisit'
    ).all()

    # --- Get filter parameters from GET ---
    invoiceRef = request.GET.get("invoiceRef", "").strip()
    poRef = request.GET.get("poRef", "").strip()
    soRef = request.GET.get("soRef", "").strip()
    customer_id = request.GET.get("customer", "").strip()
    status = request.GET.get("status", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()
    # invoiceDate = request.GET.get("invoiceDate", "").strip()

    # --- Apply filters ---
    if invoiceRef:
        sales_qs = sales_qs.filter(invoiceRef__icontains=invoiceRef)

    if poRef:
        sales_qs = sales_qs.filter(order__poRef__icontains=poRef)
    
    if soRef:
        sales_qs = sales_qs.filter(saleOrderReference__icontains=soRef)

    if customer_id:
        sales_qs = sales_qs.filter(
            Q(order__offer__lead__customer__id=customer_id) |
            Q(order__offer__lead__customerVisit__customer__id=customer_id)
        )

    if status:
        sales_qs = sales_qs.filter(status=status)

    if start_date:
        sales_qs = sales_qs.filter(invoiceDate__gte=start_date)

    if end_date:
        sales_qs = sales_qs.filter(invoiceDate__lte=end_date)

    # --- Prepare context data for the table ---
    sales_data = []
    for sale in sales_qs:
        order = sale.order
        offer = order.offer
        lead = offer.lead

        # prefer lead.customer if available, else fallback to customer from visit
        customer = lead.customer if lead and lead.customer else (
            lead.customerVisit.customer if lead and lead.customerVisit else None
        )

        try:
            vatAmount = sale.vat*sale.totalInvoiceValue/100
            x = sale.totalInvoiceValue - vatAmount
            aitAmount = sale.ait*x/100
            total_order_value = x - aitAmount
        except:
            vatAmount = 0
            aitAmount = 0
            total_order_value = 0



        sales_data.append({
            "id": sale.id,
            "poRef": order.poRef,
            "customer": customer.name if customer else "",
            "invoice_ref": sale.invoiceRef,
            "total_invoice_value": sale.totalInvoiceValue,
            "vat": sale.vat,
            "ait": sale.ait,
            "invoice_date": sale.invoiceDate,
            "total_order_value": total_order_value,
            "status": sale.status,
            "remarks": sale.remarks,
            "saleOrderReference":sale.saleOrderReference,
            "vatAmount":vatAmount,
            "aitAmount":aitAmount,
            "invoiceDate":sale.invoiceDate

        })

    # Customers dropdown
    customers = Customer.objects.all()

    context = {
        "sales_data": sales_data,
        "customers": customers,
    }
    return render(request, "sales.html", context)


def editSale(request, saleID):
    sale = get_object_or_404(Sales, id=saleID)


    if request.method == "POST":
        sale.invoiceRef = request.POST.get("invoiceRef")
        sale.totalInvoiceValue = request.POST.get("totalInvoiceValue")
        sale.vat = request.POST.get("vat")
        sale.ait = request.POST.get("ait")
        sale.status = request.POST.get("status")
        sale.remarks = request.POST.get("remarks")
        sale.saleOrderReference = request.POST.get("saleOrderReference")
        sale.invoiceDate = request.POST.get('invoiceDate')

        sale.save()

        AccountsRecieveable.objects.get_or_create(sales=sale, amount=sale.totalInvoiceValue, status='Due', invoiceRef=sale.invoiceRef)

        return redirect("/crm/sales")



def accountsRecieveable(request):
    ar_qs = AccountsRecieveable.objects.select_related('sales', 'sales__order', 'sales__order__offer', 
                                                       'sales__order__offer__lead', 
                                                       'sales__order__offer__lead__customer').all()

    # --- Filtering ---
    poRef = request.GET.get('poRef')
    invoiceRef = request.GET.get('invoiceRef')
    customer_id = request.GET.get('customer')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    soRef = request.GET.get('soRef')

    if poRef:
        ar_qs = ar_qs.filter(sales__order__poRef__icontains=poRef)

    if soRef:
        ar_qs = ar_qs.filter(sales__saleOrderReference__icontains=soRef)

    if invoiceRef:
        ar_qs = ar_qs.filter(invoiceRef__icontains=invoiceRef)

    if customer_id:
        ar_qs = ar_qs.filter(
            sales__order__offer__lead__customer__id=customer_id
        )

    if status:
        ar_qs = ar_qs.filter(status=status)

    if start_date:
        ar_qs = ar_qs.filter(sales__invoiceDate__gte=start_date)

    if end_date:
        ar_qs = ar_qs.filter(sales__invoiceDate__lte=end_date)
    
    

    # --- Prepare data for template ---
    accountsRecieveable = []
    for ar in ar_qs:
        sale = ar.sales
        try:
            vatAmount = sale.vat*sale.totalInvoiceValue/100
            x = sale.totalInvoiceValue - vatAmount
            aitAmount = sale.ait*x/100
            total_order_value = x - aitAmount
        except:
            vatAmount = 0
            aitAmount = 0
            total_order_value = 0

        order = sale.order
        lead = order.offer.lead if order.offer else None
        try:
            customer = lead.customer.name
        except:
            customer = lead.customerVisit.customer.name

        # Calculations
        receivable_amount = ar.amount or 0
        aging = -(date.today() - (sale.invoiceDate or date.today())).days if sale.invoiceDate else 0

        accountsRecieveable.append({
            "id": ar.id,
            "saleOrderRef": sale.saleOrderReference or "",
            "poRef": order.poRef or "",
            "invoiceRef": ar.invoiceRef or "",
            "customer": customer,
            "receivable_amount": receivable_amount,
            "aging": aging,
            "status": ar.status or "",
            "remarks": ar.remarks or "",
            "paymentDate": ar.paymentDate,
            "total_invoice_value": sale.totalInvoiceValue,
            'total_order_value':total_order_value,
            "vatAmount":vatAmount,
            "aitAmount":aitAmount,
            "recieved_amount": sale.totalInvoiceValue - receivable_amount
        })


    # Get all customers for filter dropdown
    customers = Customer.objects.all()

    context = {
        "accountsRecieveable": accountsRecieveable,
        "customers": customers,
    }
    return render(request, "accountRecieveable.html", context)


from django.utils.dateparse import parse_date

def updateAccountsRecieveable(request, pk):
    ar = get_object_or_404(AccountsRecieveable, pk=pk)

    if request.method == "POST":
        ar.invoiceRef = request.POST.get("invoiceRef") or ar.invoiceRef
        
        ar.status = request.POST.get("status") or ar.status
        ar.remarks = request.POST.get("remarks") or ar.remarks
        
        sale = ar.sales
        try:
            vatAmount = sale.vat*sale.totalInvoiceValue/100
            x = sale.totalInvoiceValue - vatAmount
            aitAmount = sale.ait*x/100
            total_order_value = x - aitAmount
        except:
            vatAmount = 0
            aitAmount = 0
            total_order_value = 0

        if request.POST.get('status') == 'Paid Without VAT':
            ar.amount = vatAmount
        elif request.POST.get('status') == 'Paid':
            ar.amount = 0
        elif request.POST.get('status') == 'Paid Without AIT':
            ar.amount = aitAmount
        elif request.POST.get('status') == 'Paid Without VAT and AIT':
            ar.amount = aitAmount + vatAmount

        paymentDate_raw = request.POST.get("paymentDate")
        ar.paymentDate = parse_date(paymentDate_raw) if paymentDate_raw else ar.paymentDate

        totalInvoiceValue_raw = request.POST.get("totalInvoiceValue")
        ar.totalInvoiceValue = totalInvoiceValue_raw if totalInvoiceValue_raw else ar.totalInvoiceValue

        ar.save()
    return redirect("/crm/accountsRecieveable")