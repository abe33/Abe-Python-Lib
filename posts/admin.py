# -*- coding: utf-8 -*-
from django.contrib.admin.filterspecs import FilterSpec
from abe.posts.models import *
from django.contrib import admin
from django.conf import settings as locsettings
from tagging.fields import TagField
from django.utils.translation import ugettext as _

class TagFilterSpec(FilterSpec):
	def __init__(self, f, request, params, model, model_admin):
		super( TagFilterSpec, self).__init__(f, request, params, model, model_admin)
		self.lookup_kwarg = '%s__contains' % f.name
		self.lookup_val = request.GET.get(self.lookup_kwarg, None)
		self.objects = model.tags.split(" ")
		#self.objects = model.objects.all()

	def choices(self, cl):
		yield {'selected': self.lookup_val is None,
				   'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
				   'display': _('All')}

		for tag in self.objects:
			tag = tag.strip()
			yield {'selected':tag == self.lookup_val,
						'query_string': cl.get_query_string({self.lookup_kwarg: tag}),
						'display': tag }

FilterSpec.filter_specs.insert(0, (lambda f: isinstance(f, TagField), TagFilterSpec))


class PostAdmin(admin.ModelAdmin):
	list_display=( "name", "category", "allow_comments","comments_count", "published", "published_date", "tags", "slug", "orphan", "orphan_id", )
	list_filter=("published", "published_date","category", "tags", )
	search_fields = ("name", "tags", "category", )
	list_display_links = ('name', 'slug', )
	list_editable=("published","tags","allow_comments",  )
	fieldsets = [
		( 'Contenu',               {'fields': ['name','excerpt', 'content', 'allow_comments'] }),
		( 'Classification',   {'fields': ['category','tags'] }),
		( 'Publication',        {'fields': ['published','published_date'] }),
		( 'Page Orpheline',   {'fields': ['orphan','orphan_id'] }),
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
		( 'Contenu',               {'fields': ['name',  'description', 'allow_comments'] }),
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
		( 'Contenu',               {'fields': ['name',  'description', 'url', 'icon'] }),
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
