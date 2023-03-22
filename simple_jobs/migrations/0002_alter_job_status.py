# Generated by Django 4.1.7 on 2023-03-22 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_jobs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.TextField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In progress'), ('FAILED', 'Failed'), ('SUCCESS', 'Success')], default='PENDING'),
        ),
    ]
