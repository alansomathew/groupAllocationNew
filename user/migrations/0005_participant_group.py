# Generated by Django 5.0.6 on 2024-07-24 05:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_interest'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.group'),
        ),
    ]