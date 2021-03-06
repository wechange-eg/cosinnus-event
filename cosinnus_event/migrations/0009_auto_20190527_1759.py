# Generated by Django 2.1.5 on 2019-05-27 15:47

from django.db import migrations
from django.db.models import F


def set_last_action_to_created(apps, schema_editor):
    """ One-Time sets all BaseTaggable Models' `last_updated` field value 
        to its `created` field value.  """
    
    Object = apps.get_model("cosinnus_event", "Event")
    Object.objects.all().update(last_action=F('created'))
    Object.objects.all().update(last_action_user=F('creator'))
    
    
class Migration(migrations.Migration):

    dependencies = [
        ('cosinnus_event', '0008_auto_20190527_1744'),
    ]

    operations = [
        migrations.RunPython(set_last_action_to_created, migrations.RunPython.noop),
    ]
