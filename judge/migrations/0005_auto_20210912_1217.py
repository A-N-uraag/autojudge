# Generated by Django 3.1.6 on 2021-09-12 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0004_auto_20210912_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='enable_leaderboard',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='contest',
            name='show_leaderboard',
            field=models.BooleanField(default=False),
        ),
    ]
