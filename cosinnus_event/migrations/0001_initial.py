# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Event'
        db.create_table(u'event_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('from_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('to_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='events', on_delete=models.PROTECT, to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=2)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('suggestion', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='selected_name', null=True, on_delete=models.SET_NULL, to=orm['event.Suggestion'])),
        ))
        db.send_create_signal(u'event', ['Event'])

        # Adding model 'Suggestion'
        db.create_table(u'event_suggestion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('to_date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='suggestions', to=orm['event.Event'])),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'event', ['Suggestion'])

        # Adding model 'Vote'
        db.create_table(u'event_vote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('suggestion', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['event.Suggestion'])),
            ('voter', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'event', ['Vote'])

        # Adding unique constraint on 'Vote', fields ['suggestion', 'voter']
        db.create_unique(u'event_vote', ['suggestion_id', 'voter_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Vote', fields ['suggestion', 'voter']
        db.delete_unique(u'event_vote', ['suggestion_id', 'voter_id'])

        # Deleting model 'Event'
        db.delete_table(u'event_event')

        # Deleting model 'Suggestion'
        db.delete_table(u'event_suggestion')

        # Deleting model 'Vote'
        db.delete_table(u'event_vote')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'event.event': {
            'Meta': {'ordering': "['from_date', 'to_date']", 'object_name': 'Event'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'on_delete': 'models.PROTECT', 'to': u"orm['auth.User']"}),
            'from_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'selected_name'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['event.Suggestion']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'to_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'event.suggestion': {
            'Meta': {'ordering': "['event', '-count']", 'object_name': 'Suggestion'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'to': u"orm['event.Event']"}),
            'from_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'})
        },
        u'event.vote': {
            'Meta': {'unique_together': "(('suggestion', 'voter'),)", 'object_name': 'Vote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['event.Suggestion']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['event']