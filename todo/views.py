from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Category, Task


# Create your views here.


def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(due_at_value)) if due_at_value else None,
        )
        task.save()

        for category_name in request.POST.getlist("categories"):
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)

    selected_category = request.GET.get("category")

    if request.GET.get("order") == "due":
        tasks = Task.objects.order_by("due_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    if selected_category:
        tasks = tasks.filter(categories__name=selected_category).distinct()

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
        due_at_value = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task.save()

        task.categories.clear()
        for category_name in request.POST.getlist('categories'):
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)
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
