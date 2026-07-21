from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from todo.models import Task


# Create your views here.


def index(request):
    if request.method == "POST":
        due_value = request.POST.get("due_at")
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(due_value)) if due_value else None,
        )
        task.save()

    show_completed = request.GET.get("show_completed") == "1"
    order = request.GET.get("order")

    if order == "due":
        tasks = Task.objects.filter(completed=False).order_by("due_at", "-posted_at")
        completed_tasks = Task.objects.filter(completed=True).order_by("due_at", "-posted_at")
    else:
        tasks = Task.objects.filter(completed=False).order_by("-posted_at")
        completed_tasks = Task.objects.filter(completed=True).order_by("-posted_at")

    context = {
        "tasks": tasks,
        "completed_tasks": completed_tasks,
        "show_completed": show_completed,
        "order": order,
    }
    return render(request, "todo/index.html", context)

def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {"task": task}
    return render(request, "todo/detail.html", context)

def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    return redirect(index)

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        task.due_at = make_aware(parse_datetime(request.POST['due_at']))
        task.save()
        return redirect(detail, task_id)

    context = {
        'task': task
    }
    return render(request, "todo/edit.html", context)

def close(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.completed = True
    task.completed_at = timezone.now()
    task.save()
    return redirect('index')
