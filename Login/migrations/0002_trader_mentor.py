# Generated by Django 3.0.7 on 2020-07-09 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='mentor',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]
