# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from abe.bugs.models import *
from django.conf import settings as locsettings

class MileStoneAdmin(admin.ModelAdmin):
	list_display = ('__unicode__','active','public', 'creation_date')
	list_display_links = ('__unicode__',)
	list_filter = ('active','public',)
	list_editable = ('active',)
	search_fields = ('name',)
#	class Media:
#		css = {"all": ("%scss/admin_enhancements.css" % locsettings.MEDIA_URL,)}
#		js = (
#					"%sjs/jquery-1.4.2.min.js" % locsettings.MEDIA_URL,
#					"%sjs/ckeditor/ckeditor.js" % locsettings.MEDIA_URL,
#					"%sjs/admin_enhancements.js" % locsettings.MEDIA_URL,
#				)

class ComponentAdmin(admin.ModelAdmin):
	list_display = ('__unicode__',)
	list_display_links = ('__unicode__',)
	#list_filter = ('active','public',)
	#list_editable = ('active',)
	search_fields = ('name',)
	class Media:
		css = {"all": ("%scss/admin_enhancements.css" % locsettings.MEDIA_URL,)}
		js = (
					"%sjs/jquery-1.4.2.min.js" % locsettings.MEDIA_URL,
					"%sjs/ckeditor/ckeditor.js" % locsettings.MEDIA_URL,
					"%sjs/admin_enhancements.js" % locsettings.MEDIA_URL,
				)

class TicketAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'pain_percent', 'component', 'tags','active', 'status', 'killer_bug', 'creator', 'creation_date', 'assignee_head','update_date', )
	list_filter = ('active','creation_date','component', 'status', 'assignees', 'tags')
	list_display_links = ('__unicode__',)
	list_editable = ('active','status', 'tags')
	search_fields = ('name','tags', 'description', 'assignee_note')
	filter_horizontal=('assignees',)
	fieldsets = (
				 ( _(u'Properties'), { 'fields': ('name','description','tags', ) } ),
				 ( _(u'Context'), { 'fields': ('type','priority','likelihood','component', 'contextual_data', 'attached_url', ) } ),
				 ( _(u'Status'), {'fields':('active', 'status', 'killer_bug', 'planified_to_milestone', 'closed_in_milestone', ) }), 
				 ( _(u'Team'), { 'fields': ('assignees', 'assignee_head','assignee_note', ) } ),
				)

	def pain_percent (self, obj):
		return u'%.1f%%' % obj.pain
	pain_percent.short_description = _(u"User Pain")

	def save_model(self, request, obj, form, change):
		if not change:
			obj.creator = request.user
		obj.save()

admin.site.register( Ticket, TicketAdmin )
admin.site.register( MileStone, MileStoneAdmin )
admin.site.register( Component, ComponentAdmin )
