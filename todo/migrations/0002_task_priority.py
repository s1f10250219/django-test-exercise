from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(choices=[('high', '高'), ('medium', '中'), ('low', '低')], default='medium', max_length=10),
        ),
    ]
