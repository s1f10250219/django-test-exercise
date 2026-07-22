from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.db.models import Case, IntegerField, When
from django.conf import settings
import json
import os
from todo.models import Category, Task


# File-backed descriptions to avoid DB migrations
DESC_PATH = os.path.join(settings.BASE_DIR, 'todo', 'data', 'descriptions.json')


def load_descriptions():
    os.makedirs(os.path.dirname(DESC_PATH), exist_ok=True)
    if not os.path.exists(DESC_PATH):
        with open(DESC_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
    try:
        with open(DESC_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_descriptions(data):
    os.makedirs(os.path.dirname(DESC_PATH), exist_ok=True)
    with open(DESC_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
from todo.models import Category, Task


# Create your views here.


def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(due_at_value)) if due_at_value else None,
            priority=request.POST.get("priority", "medium"),
        )
        task.save()

        for category_name in request.POST.getlist("categories"):
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)
        # store description separately in JSON to avoid DB migration
        desc = request.POST.get("description", "")
        descriptions = load_descriptions()
        descriptions[str(task.id)] = desc
        save_descriptions(descriptions)

    selected_category = request.GET.get("category")
    order = request.GET.get("order")
    if order == "due":

    selected_category = request.GET.get("category")

    if request.GET.get("order") == "due":
        tasks = Task.objects.order_by("due_at")
    elif order == "priority":
        priority_order = Case(
            When(priority="high", then=0),
            When(priority="medium", then=1),
            When(priority="low", then=2),
            default=1,
            output_field=IntegerField(),
        )
        tasks = Task.objects.order_by(priority_order, "-posted_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    if selected_category:
        tasks = tasks.filter(categories__name=selected_category).distinct()
    # attach descriptions from file to task objects
    descriptions = load_descriptions()
    for t in tasks:
        setattr(t, 'description', descriptions.get(str(t.id), ''))

    context = {
        "tasks": tasks,
        "categories": Category.objects.order_by("name"),
        "selected_category": selected_category,
    }
    return render(request, "todo/index.html", context)

def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    descriptions = load_descriptions()
    setattr(task, 'description', descriptions.get(str(task.id), ''))

    context = {"task": task}
    return render(request, "todo/detail.html", context)

def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    descriptions = load_descriptions()
    descriptions.pop(str(task_id), None)
    save_descriptions(descriptions)
    return redirect(index)

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        due_at_value = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task.priority = request.POST.get('priority', 'medium')
        desc = request.POST.get('description', '')
        task.save()

        task.categories.clear()
        for category_name in request.POST.getlist('categories'):
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)
        # persist description separately
        descriptions = load_descriptions()
        descriptions[str(task.id)] = desc
        save_descriptions(descriptions)
        return redirect(detail, task_id)

    context = {
        'task': task,
        'categories': Category.objects.order_by('name'),
        'selected_categories': list(task.categories.values_list('name', flat=True)),
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
