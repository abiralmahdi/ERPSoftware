from django.shortcuts import render, redirect, get_object_or_404
from .models import *

# Create your views here.
def projects(request):
    project = Projects.objects.all().first()
    return redirect("/wms/projects/"+str(project.id))


def indivProject(request, projectID):
    return redirect("/wms/projects/"+str(projectID)+"/tasks")

def projectTasks(request, projectID):
    project = Projects.objects.get(id=projectID)
    tasks = Task.objects.filter(project=project)
    projects = Projects.objects.all()
    currentTab = "tasks"
    context = {
        'indivProject': project,
        'tasks': tasks,
        'projects': projects,
        'currentTab': currentTab
    }
    return render(request, 'tasks.html', context)

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
            "dependencies": ""  # add dependency IDs here if needed
        })

    context = {
        "indivProject": project,
        "tasks": task_data,
        "currentTab": currentTab,
        "projects": projects
    }
    return render(request, "timeline.html", context)
