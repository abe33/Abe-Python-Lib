# -*- coding: utf-8 -*-
from abe.posts.models import *
from django.contrib import admin
from django.conf import settings as locsettings
from tagging.fields import TagField
from django.utils.translation import ugettext as _

class PostAdmin(admin.ModelAdmin):
	list_display=( "name", "category", "allow_comments","comments_count", "published", "published_date", "tags", "slug", "orphan", "orphan_id", )
	list_filter=("published", "published_date","category", "tags", )
	search_fields = ("name", "tags", "category", )
	list_display_links = ('name', 'slug', )
	list_editable=("published","tags","allow_comments",  )
	fieldsets = [
		( _(u'Content'),               {'fields': ['name','excerpt', 'content', 'allow_comments'] }),
		( _(u'Categorization'),   {'fields': ['category','tags'] }),
		( _(u'Publication'),        {'fields': ['published','published_date'] }),
		( _(u'Orphan page'),   {'fields': ['orphan','orphan_id'] }),
	]
	class Media:
		css = {"all": ("%scss/admin_enhancements.css" % locsettings.MEDIA_URL,)}
		js = (
					"%sjs/jquery-1.4.2.min.js" % locsettings.MEDIA_URL,
					"%sjs/ckeditor/ckeditor.js" % locsettings.MEDIA_URL,
					"%sjs/admin_enhancements.js" % locsettings.MEDIA_URL,
				)

class PostCategoryAdmin(admin.ModelAdmin):
	list_display=("name","creation_date", "update_date", )
	list_display_links = ('name', )
	fieldsets = [
		( _(u'Content'),               {'fields': ['name',  'description', 'allow_comments'] }),
	]
	class Media:
		css = {"all": ("%scss/admin_enhancements.css" % locsettings.MEDIA_URL,)}
		js = (
					"%sjs/jquery-1.4.2.min.js" % locsettings.MEDIA_URL,
					"%sjs/ckeditor/ckeditor.js" % locsettings.MEDIA_URL,
					"%sjs/admin_enhancements.js" % locsettings.MEDIA_URL,
				)

class SiteLinkAdmin(admin.ModelAdmin):
	list_display=("name","creation_date", "update_date", )
	list_display_links = ('name', )
	fieldsets = [
		( _(u'Content'),               {'fields': ['name',  'description', 'url', 'icon'] }),
	]
	class Media:
		css = {"all": ("%scss/admin_enhancements.css" % locsettings.MEDIA_URL,)}
		js = (
					"%sjs/jquery-1.4.2.min.js" % locsettings.MEDIA_URL,
					"%sjs/ckeditor/ckeditor.js" % locsettings.MEDIA_URL,
					"%sjs/admin_enhancements.js" % locsettings.MEDIA_URL,
				)

admin.site.register(Post, PostAdmin )
admin.site.register(PostCategory, PostCategoryAdmin )
admin.site.register(SiteLink, SiteLinkAdmin )
