from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware, now
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Q
from datetime import timedelta
from todo.models import Task
from django.db.models import Q
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
from django.core.paginator import Paginator
from todo.models import Task, Category


# Create your views here.


def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(due_at_value)) if due_at_value else None,
            priority=request.POST.get("priority", "medium"),
            title=request.POST.get("title", ""),
            due_at=due_at,
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

    # 検索クエリとカテゴリーの取得
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category")

    # 並び替え
    tasks = Task.objects.all()

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
        tasks = tasks.order_by("due_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    # 検索機能による絞り込み
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(categories__name__icontains=query)).distinct()

    # カテゴリー選択による絞り込み
        tasks = tasks.order_by("-posted_at")
    if selected_category:
        tasks = tasks.filter(categories__name=selected_category).distinct()
    # attach descriptions from file to task objects
    descriptions = load_descriptions()
    for t in tasks:
        setattr(t, 'description', descriptions.get(str(t.id), ''))

    # ページネーション処理
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "tasks": page_obj,
        "categories": Category.objects.order_by("name"),
        "selected_category": selected_category,
        "query": query,
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
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        Task.objects.filter(id__in=task_ids).update(completed=True)
    return redirect("todo:index")

def bulk_delete(request):
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        Task.objects.filter(id__in=task_ids).delete()
    return redirect("todo:index")
