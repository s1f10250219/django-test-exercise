from django.db import migrations, models


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
            name='priority',
            field=models.CharField(choices=[('high', '高'), ('medium', '中'), ('low', '低')], default='medium', max_length=10),
        ),
        migrations.AddField(
            model_name='task',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='tasks', to='todo.category'),
        ),
    ]
