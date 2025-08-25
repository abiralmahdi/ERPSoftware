from crm.models import Customer, CustomerAgent, CustomerVisits
from employee.models import Employee
from leave.models import VisitApplications
from datetime import datetime, timedelta
import random

# Create Customers
customers = []
for i in range(5):
    customer, _ = Customer.objects.get_or_create(
        name=f"Customer {i+1}",
        address=f"Address {i+1}"
    )
    customers.append(customer)

# Create Customer Agents
agents = []
for customer in customers:
    for j in range(2):  # two agents per customer
        agent, _ = CustomerAgent.objects.get_or_create(
            customer=customer,
            agent_name=f"Agent {customer.id}-{j+1}",
            agent_email=f"agent{customer.id}{j+1}@example.com",
            agent_contact=f"01700000{customer.id}{j+1}"
        )
        agents.append(agent)

# Pick some employees (assuming you already have some in DB)
employees = list(Employee.objects.all())
if not employees:
    print("⚠️ No employees found! Please create employees first.")

# Pick some visit applications if available
visit_apps = list(VisitApplications.objects.all())

# Create Customer Visits
for i in range(10):
    customer = random.choice(customers)
    agent = random.choice(customer.agent.all())
    employee = random.choice(employees) if employees else None
    visit_application = random.choice(visit_apps) if visit_apps else None

    start = datetime.now() + timedelta(days=random.randint(-10, 10))
    end = start + timedelta(hours=random.randint(1, 5))

    CustomerVisits.objects.create(
        customer=customer,
        agent=agent,
        employee=employee,
        visit_application=visit_application,
        purpose=random.choice(["Business Meeting", "Product Demo", "Contract Discussion", "Follow-up"]),
        startDate=start,
        endDate=end,
        note=f"Note for visit {i+1}",
        potentialScope=random.choice(["High", "Medium", "Low"]),
        scopeFile="files/dummy.pdf"  # Put any file path or leave blank if not required
    )

print("✅ Sample data created successfully!")
