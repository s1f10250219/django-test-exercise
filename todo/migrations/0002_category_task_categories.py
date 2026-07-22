from django.db import migrations, models


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('todo', 'Category')
    if not Category.objects.exists():
        Category.objects.create(name='work')
        Category.objects.create(name='study')


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='tasks', to='todo.category'),
        ),
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
    ]
