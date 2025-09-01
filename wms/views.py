from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

# Create your views here.
def projects(request):
    project = Projects.objects.all().first()
    projects = Projects.objects.all()
    employees = Employee.objects.all()
    if project:
        return redirect("/wms/projects/"+str(project.id))
    else:
        return render(request, "newProject.html", {"projects":projects, "indivProject":project, "employees":employees})


from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Projects, Employee

@login_required
def addProject(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        startDate = request.POST.get("startDate")
        endDate = request.POST.get("endDate")
        status = request.POST.get("status")
        projectLeader_id = request.POST.get("projectLeader")

        projectLeader = Employee.objects.get(id=projectLeader_id) if projectLeader_id else None

        project = Projects.objects.create(
            title=title,
            description=description,
            startDate=startDate,
            endDate=endDate,
            status=status,
            projectLeader=projectLeader
        )

        # Send email to project leader
        if projectLeader and projectLeader.user.email:
            project_url = request.build_absolute_uri(
                reverse("projectTasks", args=[project.id])
            )

            subject = "New Project Assigned"
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [projectLeader.user.email]

            # Plain text fallback
            text_content = (
                f"You have been assigned as the leader of project: {title}\n"
                f"View project here: {project_url}"
            )

            # HTML version with hidden URL
            html_content = f"""
                <p>You have been assigned as the leader of project: <strong>{title}</strong></p>
                <p><a href="{project_url}">Click here to view project</a></p>
            """

            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        return redirect(request.META.get("HTTP_REFERER", "/"))

    employees = Employee.objects.all()
    return render(request, "projects.html", {"employees": employees})


def indivProject(request, projectID):
    return redirect("/wms/projects/"+str(projectID)+"/tasks")


def projectTasks(request, projectID):
    project = get_object_or_404(Projects, id=projectID)
    tasks = Task.objects.filter(project=project)
    projects = Projects.objects.all()
    currentTab = "tasks"
    employees = Employee.objects.all()

    # Handle task edit submission
    if request.method == "POST" and "edit_task" in request.POST:
        task_id = request.POST.get("task_id")
        task = get_object_or_404(Task, id=task_id)

        # Save old record in TaskHistory
        TaskHistory.objects.create(
            task=task,
            name=task.name,
            assignedTo=task.assignedTo,
            assignTime=task.assignTime,
            deadline=task.deadline,
            status=task.status,
            priority=task.priority,
            description=task.description,
            progress=task.progress,
            edited_by=request.user.employee  # assuming user has related employee
        )

        # Update task
        task.name = request.POST.get("name")
        task.assignedTo = Employee.objects.get(id=request.POST.get("assignedTo"))
        task.assignTime = request.POST.get("assignTime")
        task.deadline = request.POST.get("deadline")
        task.status = request.POST.get("status")
        task.priority = request.POST.get("priority")
        task.description = request.POST.get("description")
        task.progress = request.POST.get("progress") or 0
        task.save()

        return redirect(request.path_info)

    context = {
        'indivProject': project,
        'tasks': tasks,
        'projects': projects,
        'currentTab': currentTab,
        "employees":employees
    }
    return render(request, 'tasks.html', context)


@login_required
def addTask(request, projectID):
    project = get_object_or_404(Projects, id=projectID)
    employees = Employee.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        assignedTo_id = request.POST.get("assignedTo")
        assignTime = request.POST.get("assignTime")
        deadline = request.POST.get("deadline")
        status = request.POST.get("status")
        priority = request.POST.get("priority")
        description = request.POST.get("description")
        progress = request.POST.get("progress", 0)

        try:
            assignedTo = Employee.objects.get(id=assignedTo_id)
        except Employee.DoesNotExist:
            return redirect("project_detail", project_id=project.id)

        task = Task.objects.create(
            project=project,
            name=name,
            created_at=now(),
            assignedTo=assignedTo,
            assignTime=assignTime,
            deadline=deadline,
            status=status,
            priority=priority,
            description=description,
            createdBy=request.user.employee,  # assuming Employee linked with User
            progress=progress,
        )

        # Send email to assigned employee
        if assignedTo.user.email:
            task_url = request.build_absolute_uri(
                reverse("projectTasks", args=[project.id])
            )
            subject = "New Task Assigned"
            message = f"You have been assigned a new task: {name}\n\nView task here: {task_url}"
            html_message = f"""
                <p>You have been assigned a new task: <b>{name}</b></p>
                <p><a href="{task_url}" style="color:#1a73e8; text-decoration:none;">👉 Click here to view the task</a></p>
            """
            send_mail(
                subject=subject,
                message=message,  # fallback for plain text clients
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[assignedTo.user.email],
                html_message=html_message,
            )

        return redirect(f"/wms/projects/{project.id}/tasks")

        
def deleteTask(request, projectID, taskID):
    task = get_object_or_404(Task, id=taskID)
    task.delete()
    return redirect(f'/wms/projects/{projectID}/tasks')



def view_task_history(request, project_id, task_id):
    project = get_object_or_404(Projects, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)

    # Fetch all history entries for this task, newest first
    histories = TaskHistory.objects.filter(task=task).order_by('-edited_at')

    projects = Projects.objects.all()

    context = {
        'indivProject': project,
        'task': task,
        'histories': histories,
        'projects':projects,
        'currentTab': 'tasks'        
    }
    return render(request, 'taskHistory.html', context)


def board(request, projectID):
    project = Projects.objects.get(id=projectID)
    projects = Projects.objects.all()
    tasks = Task.objects.filter(project=project)
    statuses = []
    currentTab = "board"
    for ts in tasks:
        if ts.status not in statuses:
            statuses.append(ts.status)
    
    context = {
        'indivProject': project,
        'tasks': tasks,
        'statuses': statuses,
        'projects': projects,
        'currentTab': currentTab
    }
    return render(request, 'board.html', context)

from django.utils.timezone import now
from django.shortcuts import get_object_or_404, render

def timeline(request, projectID):
    project = get_object_or_404(Projects, id=projectID)
    projects = Projects.objects.all()
    currentTab = "timeline"

    tasks_qs = Task.objects.filter(project=project)

    today = now().date()

    # Sort tasks by how close the deadline is to today
    tasks_qs = sorted(
        tasks_qs,
        key=lambda task: (task.deadline.date() - today).days
    )

    task_data = []
    for task in tasks_qs:
        start_date = task.assignTime.date()
        end_date = task.deadline.date()

        task_data.append({
            "id": str(task.id),                     # unique id for Frappe Gantt
            "name": task.name,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "progress": getattr(task, 'progress', 0),  # optional field
            "dependencies": "",  # add dependency IDs here if needed
            "progress":task.progress,
            "status":task.status
        })

    context = {
        "indivProject": project,
        "tasks": task_data,
        "currentTab": currentTab,
        "projects": projects
    }
    return render(request, "timeline.html", context)


from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from collections import defaultdict
from django.shortcuts import get_object_or_404, render

def calendar_view(request, projectID):
    year = date.today().year
    projects = Projects.objects.all()
    project = get_object_or_404(Projects, id=projectID)
    currentTab = "calendar"

    # Fetch all tasks for all projects
    all_tasks = Task.objects.all().select_related('project', 'assignedTo')

    # Prepare a mapping: date -> list of tasks
    tasks_by_date = defaultdict(list)
    for task in all_tasks:
        deadline = task.deadline.date()
        tasks_by_date[deadline].append({
            "name": task.name,
            "project": task.project.title,
            "assignedTo": task.assignedTo.user.get_full_name()
        })

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
        days = []
        for i in range(delta):
            day_date = start_day + timedelta(days=i)
            day_tasks = tasks_by_date.get(day_date, [])
            days.append({
                "day": day_date.day,
                "date": day_date,
                "tasks": day_tasks
            })
        months.append({"number": month, "name": start_day.strftime("%B"), "days": days})

    context = {
        "year": year,
        "months": months,
        "indivProject": project,
        "projects": projects,
        "currentTab": currentTab,
        "current_month":date.today().month
    }
    return render(request, "calendar.html", context)


