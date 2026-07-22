from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils.timezone import make_aware, now, is_aware
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from todo.models import Task, Category


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


def parse_due_at(due_at_value):
    """日時文字列を安全に aware な datetime に変換するヘルパー関数"""
    if not due_at_value:
        return None
    parsed_dt = parse_datetime(due_at_value)
    if parsed_dt and not is_aware(parsed_dt):
        return make_aware(parsed_dt)
    return parsed_dt


def index(request):
    error_message = None
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            error_message = "タイトルを入力してください。"
        else:
            due_at_value = request.POST.get("due_at")
            due_at = parse_due_at(due_at_value)
            
            task = Task(
                title=title,
                due_at=due_at,
            )
            task.save()

            for category_name in request.POST.getlist("categories"):
                category_name = category_name.strip()
                if not category_name:
                    continue
                category, _ = Category.objects.get_or_create(name=category_name)
                task.categories.add(category)

            # POST成功後は二重送信防止のためリダイレクト
            return redirect('index')

    selected_category = request.GET.get("category")
    show_completed = request.GET.get("show_completed") == "1"
    order = request.GET.get("order")

    tasks = Task.objects.all()
    if selected_category:
        tasks = tasks.filter(categories__name=selected_category).distinct()

    if order == "due":
        tasks = tasks.order_by("due_at", "-posted_at")
    else:
        tasks = tasks.order_by("-posted_at")

    incomplete_tasks = tasks.filter(completed=False)
    completed_tasks = tasks.filter(completed=True)

    for task in incomplete_tasks:
        task.status = get_task_status(task)

    paginator = Paginator(incomplete_tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "tasks": page_obj,
        "completed_tasks": completed_tasks,
        "show_completed": show_completed,
        "order": order,
        "categories": Category.objects.order_by("name"),
        "selected_category": selected_category,
        "error_message": error_message,
    }
    return render(request, "todo/index.html", context)


def detail(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    context = {"task": task}
    return render(request, "todo/detail.html", context)


def delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return redirect('index')


def update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            context = {
                'task': task,
                'categories': Category.objects.order_by('name'),
                'selected_categories': list(task.categories.values_list('name', flat=True)),
                'error_message': 'タイトルを入力してください。',
            }
            return render(request, "todo/edit.html", context)

        task.title = title
        due_at_value = request.POST.get('due_at')
        task.due_at = parse_due_at(due_at_value)
        task.save()

        task.categories.clear()
        for category_name in request.POST.getlist('categories'):
            category_name = category_name.strip()
            if not category_name:
                continue
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)
        return redirect('detail', task_id=task.id)

    context = {
        'task': task,
        'categories': Category.objects.order_by('name'),
        'selected_categories': list(task.categories.values_list('name', flat=True)),
    }
    return render(request, "todo/edit.html", context)


def close(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.completed = True
    task.completed_at = timezone.now()
    task.save()
    return redirect('index')


def bulk_complete(request):
    try:
        task_ids = request.POST.getlist('task_ids')
    except AttributeError:
        task_ids = []

    if task_ids:
        Task.objects.filter(pk__in=task_ids).update(completed=True, completed_at=timezone.now())

    return redirect('index')


def bulk_delete(request):
    try:
        task_ids = request.POST.getlist('task_ids')
    except AttributeError:
        task_ids = []

    if task_ids:
        Task.objects.filter(pk__in=task_ids).delete()

    return redirect('index')