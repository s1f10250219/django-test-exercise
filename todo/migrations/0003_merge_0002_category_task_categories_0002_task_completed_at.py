from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("todo", "0002_category_task_categories"),
        ("todo", "0002_task_completed_at"),
    ]

    operations = []
