# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Comment'
        db.create_table(u'cosinnus_event_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'event_comments', on_delete=models.PROTECT, to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'comments', to=orm['cosinnus_event.Event'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'cosinnus_event', ['Comment'])


        # Changing field 'Event.creator'
        db.alter_column(u'cosinnus_event_event', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['auth.User']))

    def backwards(self, orm):
        # Deleting model 'Comment'
        db.delete_table(u'cosinnus_event_comment')


        # Changing field 'Event.creator'
        db.alter_column(u'cosinnus_event_event', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['auth.User']))

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
        u'cosinnus.attachedobject': {
            'Meta': {'ordering': "(u'content_type',)", 'unique_together': "((u'content_type', u'object_id'),)", 'object_name': 'AttachedObject'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'cosinnus.cosinnusgroup': {
            'Meta': {'ordering': "(u'name',)", 'unique_together': "((u'slug', u'portal'),)", 'object_name': 'CosinnusGroup'},
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'deactivated_apps': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'media_tag': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cosinnus.TagObject']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'groups'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['cosinnus.CosinnusGroup']"}),
            'portal': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "u'groups'", 'to': u"orm['cosinnus.CosinnusPortal']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'cosinnus_groups'", 'blank': 'True', 'through': u"orm['cosinnus.CosinnusGroupMembership']", 'to': u"orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'cosinnus.cosinnusgroupmembership': {
            'Meta': {'unique_together': "((u'user', u'group'),)", 'object_name': 'CosinnusGroupMembership'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'memberships'", 'to': u"orm['cosinnus.CosinnusGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cosinnus_memberships'", 'to': u"orm['auth.User']"})
        },
        u'cosinnus.cosinnusportal': {
            'Meta': {'object_name': 'CosinnusPortal'},
            'background_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'bottom_color': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'description': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'extra_css': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']", 'unique': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'top_color': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'cosinnus_portals'", 'blank': 'True', 'through': u"orm['cosinnus.CosinnusPortalMembership']", 'to': u"orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'cosinnus.cosinnusportalmembership': {
            'Meta': {'unique_together': "((u'user', u'group'),)", 'object_name': 'CosinnusPortalMembership'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'memberships'", 'to': u"orm['cosinnus.CosinnusPortal']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cosinnus_portal_memberships'", 'to': u"orm['auth.User']"})
        },
        u'cosinnus.tagobject': {
            'Meta': {'object_name': 'TagObject'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'null': 'True', 'to': u"orm['cosinnus.CosinnusGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_place': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'people_name': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'persons': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'+'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'visibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'blank': 'True'})
        },
        u'cosinnus_event.comment': {
            'Meta': {'ordering': "[u'created_on']", 'object_name': 'Comment'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'event_comments'", 'on_delete': 'models.PROTECT', 'to': u"orm['auth.User']"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'comments'", 'to': u"orm['cosinnus_event.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'cosinnus_event.event': {
            'Meta': {'ordering': "[u'from_date', u'to_date']", 'unique_together': "((u'group', u'slug'),)", 'object_name': 'Event'},
            'attached_objects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['cosinnus.AttachedObject']", 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cosinnus_event_event_set'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'from_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'cosinnus_event_event_set'", 'to': u"orm['cosinnus.CosinnusGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'location': ('osm_field.fields.OSMField', [], {'null': 'True', 'blank': 'True'}),
            'location_lat': ('osm_field.fields.LatitudeField', [], {'null': 'True', 'blank': 'True'}),
            'location_lon': ('osm_field.fields.LongitudeField', [], {'null': 'True', 'blank': 'True'}),
            'media_tag': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cosinnus.TagObject']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55', 'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'selected_name'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['cosinnus_event.Suggestion']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'cosinnus_event.suggestion': {
            'Meta': {'ordering': "[u'event', u'-count']", 'unique_together': "((u'event', u'from_date', u'to_date'),)", 'object_name': 'Suggestion'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'suggestions'", 'to': u"orm['cosinnus_event.Event']"}),
            'from_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None'})
        },
        u'cosinnus_event.vote': {
            'Meta': {'unique_together': "((u'suggestion', u'voter'),)", 'object_name': 'Vote'},
            'choice': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'votes'", 'to': u"orm['cosinnus_event.Suggestion']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'votes'", 'to': u"orm['auth.User']"})
        },
        u'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['cosinnus_event']