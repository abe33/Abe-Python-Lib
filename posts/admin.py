# -*- coding: utf-8 -*-
from abe.posts.models import *
from django.contrib import admin
from django.conf import settings
from tagging.fields import TagField
from django.utils.translation import ugettext as _
from abe.posts import settings as post_settings

from babelfish.admin import BabelFishAdmin

class PostAdmin(BabelFishAdmin):
    list_display=( "name", "author", "category", 'group', 'group_order', "allow_comments","comments_count", "featured", "published", "published_date", "tags", "slug", "orphan", "orphan_id", )
    list_filter=( "author","featured", "published", "published_date","category", "tags", )
    search_fields = ( "author", "name", "tags", "category", )
    list_display_links = ( 'name', 'slug', )
    list_editable=( "featured","published","tags","allow_comments" )
    fieldsets = [
        ( _(u'Content'),       {'fields': ['name','excerpt', 'content'] }),
        ( _(u'BabelFish'),     {'fields': ['bf_translations',] }),
        ( _(u'Categorization'),{'fields': ['category','tags'] }),
        ( _(u'Publication'),   {'fields': ['author','published','published_date', 'featured','allow_comments'] }),
        ( _(u'Orphan page'),   {'fields': ['orphan','orphan_id'] }),
        ( _(u'Post Group'),    {'fields': ['group','group_order'] }),
    ]
    class Media:
        css = {"all": post_settings.POST_ADMIN_CSS + ( "%scss/post_enhancements.css" % settings.MEDIA_URL, )}
        js = post_settings.POST_ADMIN_JS + ( "%sjs/post_enhancements.js" % settings.MEDIA_URL, )

class PostCategoryAdmin(BabelFishAdmin):
    list_display=("name","slug","creation_date", "update_date", "parent", )
    list_display_links = ('name', )
    fieldsets = [
        ( _(u'Content'),   {'fields': ['name', 'description'] }),
        ( _(u'BabelFish'), {'fields': ['bf_translations',] }),
        ( _(u'Extra'),   {'fields': [ 'slug','allow_comments','parent'] }),
    ]
    class Media:
        css = {"all": post_settings.POST_ADMIN_CSS + ( "%scss/post_enhancements.css" % settings.MEDIA_URL, )}
        js = post_settings.POST_ADMIN_JS + ( "%sjs/post_enhancements.js" % settings.MEDIA_URL, )

class PostGroupAdmin(BabelFishAdmin):
    list_display=("name","slug" )
    list_display_links = ('name', )
    fieldsets = [
        ( _(u'Content'),   {'fields': ['name', 'description'] }),
        ( _(u'BabelFish'), {'fields': ['bf_translations',] }),
        ( _(u'Extra'), {'fields': ['slug',] }),
    ]
    class Media:
        css = {"all": post_settings.POST_ADMIN_CSS + ( "%scss/post_enhancements.css" % settings.MEDIA_URL, )}
        js = post_settings.POST_ADMIN_JS + ( "%sjs/post_enhancements.js" % settings.MEDIA_URL, )

class SiteLinkCategoryAdmin(BabelFishAdmin):
    list_display=("name","creation_date", "update_date", 'slug' )
    list_display_links = ('name', 'slug', )
    fieldsets = [
        ( _(u'Content'),   {'fields': ['name','description','slug' ] } ),
        ( _(u'BabelFish'), {'fields': ['bf_translations',] }),
        ( _(u'Extra'),     {'fields': ['parent',] } ),
    ]
    class Media:
        css = {"all": post_settings.POST_ADMIN_CSS + ( "%scss/post_enhancements.css" % settings.MEDIA_URL, )}
        js = post_settings.POST_ADMIN_JS + ( "%sjs/post_enhancements.js" % settings.MEDIA_URL, )

class SiteLinkAdmin(BabelFishAdmin):
    list_display=("name","creation_date", "update_date", 'featured', 'rel','category' )
    list_display_links = ('name', )
    list_filter=("featured", "rel", ) 
    list_editable=("rel", 'featured', )
    fieldsets = [
        ( _(u'Content'),   {'fields': ['name','url','description', ] } ),
        ( _(u'BabelFish'), {'fields': ['bf_translations',] }),
        ( _(u'Extra'),     {'fields': ['icon','featured','rel','category'] } ),
    ]
    class Media:
        css = {"all": post_settings.POST_ADMIN_CSS + ( "%scss/post_enhancements.css" % settings.MEDIA_URL, )}
        js = post_settings.POST_ADMIN_JS + ( "%sjs/post_enhancements.js" % settings.MEDIA_URL, )

admin.site.register(Post, PostAdmin )
admin.site.register(PostGroup, PostGroupAdmin )
admin.site.register(PostCategory, PostCategoryAdmin )
admin.site.register(SiteLink, SiteLinkAdmin )
admin.site.register(SiteLinkCategory, SiteLinkCategoryAdmin )

