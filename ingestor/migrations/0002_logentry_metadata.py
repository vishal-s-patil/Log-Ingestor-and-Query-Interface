# Generated by Django 4.2.7 on 2023-11-18 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingestor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='metadata',
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
    ]