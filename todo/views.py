from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware, now
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Q
from datetime import timedelta
from todo.models import Task
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

def dashboard(request):
    """進捗状況表示とダッシュボード"""
    all_tasks = Task.objects.all()
    completed_tasks = all_tasks.filter(completed=True)
    uncompleted_tasks = all_tasks.filter(completed=False)
    
    total_count = all_tasks.count()
    completed_count = completed_tasks.count()
    uncompleted_count = uncompleted_tasks.count()
    
    # 完了率を計算
    if total_count > 0:
        completion_rate = round((completed_count / total_count) * 100, 1)
    else:
        completion_rate = 0
    
    # 期限切れタスク（期限日時が過去で、未完了）
    current_time = now()
    overdue_tasks = uncompleted_tasks.filter(
        due_at__isnull=False,
        due_at__lt=current_time
    )
    overdue_count = overdue_tasks.count()
    
    # 今週中に期限があるタスク（未完了）
    week_later = current_time + timedelta(days=7)
    upcoming_tasks = uncompleted_tasks.filter(
        due_at__isnull=False,
        due_at__gte=current_time,
        due_at__lte=week_later
    )
    upcoming_count = upcoming_tasks.count()
    
    # 期限がないタスク（未完了）
    no_deadline_tasks = uncompleted_tasks.filter(due_at__isnull=True)
    no_deadline_count = no_deadline_tasks.count()
    
    context = {
        'total_count': total_count,
        'completed_count': completed_count,
        'uncompleted_count': uncompleted_count,
        'completion_rate': completion_rate,
        'overdue_count': overdue_count,
        'upcoming_count': upcoming_count,
        'no_deadline_count': no_deadline_count,
        'overdue_tasks': overdue_tasks,
        'upcoming_tasks': upcoming_tasks,
    }
    return render(request, "todo/dashboard.html", context)

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
