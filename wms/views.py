from django.shortcuts import render, redirect, get_object_or_404
from .models import *

# Create your views here.
def projects(request):
    project = Projects.objects.all().first()
    return redirect("/wms/projects/"+str(project.id))


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
            "progress":task.progress
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


