# Generated by Django 2.0 on 2020-01-26 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_auto_20180605_0842'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='questionoption',
            unique_together={('question', 'number')},
        ),
    ]
