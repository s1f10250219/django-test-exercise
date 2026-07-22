from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True, default="")
    completed = models.BooleanField(default=False)
    posted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True, related_name="tasks")

    def is_overdue(self, dt):
        if self.due_at is None:
            return False
        return self.due_at < dt
