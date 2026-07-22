from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware, now
from django.utils.dateparse import parse_datetime
from todo.models import Task


# Create your views here.

def get_task_status(task):
    if task.due_at is None or task.completed:
        return 'normal'

    time_until_due = task.due_at - now()

    if time_until_due.total_seconds() < 0:
        return 'overdue'
    if time_until_due.total_seconds() < 86400:
        return 'urgent'
    return 'normal'


def index(request):
    if request.method == "POST":
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(request.POST["due_at"])),
        )
        task.save()

    if request.GET.get("order") == "due":
        tasks = Task.objects.order_by("due_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    for task in tasks:
        task.status = get_task_status(task)

    context = {"tasks": tasks}
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
    task.save()
    return redirect('index')


def bulk_complete(request):
    try:
        task_ids = request.POST.getlist('task_ids')
    except AttributeError:
        task_ids = []

    if task_ids:
        Task.objects.filter(pk__in=task_ids).update(completed=True)

    return redirect('index')


def bulk_delete(request):
    try:
        task_ids = request.POST.getlist('task_ids')
    except AttributeError:
        task_ids = []

    if task_ids:
        Task.objects.filter(pk__in=task_ids).delete()

    return redirect('index')
