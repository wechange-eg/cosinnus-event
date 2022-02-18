# Generated by Django 2.2 on 2022-02-18 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cosinnus_event', '0021_auto_20211022_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='conferenceevent',
            name='is_description_visible_on_microsite',
            field=models.BooleanField(default=True, help_text="Provides an option to choose if the particular conference event's description should be shown on microsite or not", verbose_name="Event's description is visible on the conference microsite"),
        ),
        migrations.AddField(
            model_name='conferenceevent',
            name='is_visible_on_microsite',
            field=models.BooleanField(default=True, help_text='Provides an option to choose if the particular conference event should be shown on microsite or not', verbose_name='Event is visible on the conference microsite'),
        ),
    ]
