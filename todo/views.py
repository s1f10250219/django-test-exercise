from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from django.core.paginator import Paginator
from todo.models import Task, Category


# Create your views here.


def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task = Task(
            title=request.POST.get("title", ""),
            due_at=due_at,
        )
        task.save()

        for category_name in request.POST.getlist("categories"):
            category, _ = Category.objects.get_or_create(name=category_name)
            task.categories.add(category)

    # 検索クエリとカテゴリーの取得
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category")

    # 並び替え
    if request.GET.get("order") == "due":
        tasks = Task.objects.order_by("due_at")
    else:
        tasks = Task.objects.order_by("-posted_at")

    # 検索機能による絞り込み
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(categories__name__icontains=query)).distinct()

    # カテゴリー選択による絞り込み
    if selected_category:
        tasks = tasks.filter(categories__name=selected_category).distinct()

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
