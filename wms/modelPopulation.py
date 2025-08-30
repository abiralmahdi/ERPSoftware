from datetime import date, timedelta, datetime
import random
from wms.models import Projects, Task
from employee.models import Employee

# get some employees (make sure you already have Employee objects in DB)
employees = list(Employee.objects.all())
if not employees:
    raise Exception("No employees found! Please create some Employee records first.")

project_list = Projects.objects.filter(id=3)

# create sample projects
# project_list = []
# for i in range(5):   # create 5 projects
#     project = Projects.objects.create(
#         title=f"Project {i+1}",
#         description=f"Description for Project {i+1}",
#         startDate=date.today(),
#         endDate=date.today() + timedelta(days=random.randint(30, 120)),
#         status=random.choice(["Pending", "In Progress", "Completed"]),
#         projectLeader=random.choice(employees)
#     )
#     project_list.append(project)

# create tasks for each project
for project in project_list:
    for j in range(5):  # 5 tasks per project
        assign_time = datetime.now()
        deadline = assign_time + timedelta(days=random.randint(5, 20))
        Task.objects.create(
            project=project,
            name=f"Task {j+1} for {project.title}",
            created_at=datetime.now(),
            assignedTo=random.choice(employees),
            assignTime=assign_time,
            deadline=deadline,
            status=random.choice(["Pending", "In Progress", "Completed"]),
            priority=random.choice(["Low", "Medium", "High"]),
            description=f"Description for Task {j+1} in {project.title}",
            createdBy=random.choice(employees)
        )
