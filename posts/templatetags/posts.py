# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django import template
from django.contrib.comments.models import Comment
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from abe.posts.models import *
from abe.posts import settings as msettings
from abe.utils import *

from tagging.models import *

import hashlib

import os
import Image

register = Library()


class SiteLinkNode(AdvancedTemplateNode):
    def  get__new_context_value(self,  context):    
        f = self.for_object
        l = f.split("=")
        
        kwargs = { l[0] : l[1] }
        
        print kwargs
        
        return list( SiteLink.objects.filter( **kwargs ).order_by("name") )

class SiteLinkCategoryNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( SiteLinkCategory.objects.filter(parent__isnull=True) )

class CommentArchivesNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( Comment.objects.dates('submit_date', 'month', order='DESC') )

class PostCategoryNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( PostCategory.objects.filter(parent__isnull=True) )
    
class PostFeaturedNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( Post.objects.filter( published=True, orphan=False, featured=True ) )
        
class PostArchivesNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( Post.objects.filter( published=True, orphan=False ).dates('published_date', 'month', order='DESC') )

class PostTagsNode(BaseTemplateNode):
    def  get__new_context_value(self,  context):
        return list( Tag.objects.cloud_for_model( Post ) )

class PostNode(BaseTemplateForObjectNode):
    def  get__new_context_value(self,  context):
        id = self.object_expr.resolve(context)
        return Post.objects.get(id=id )

class PostByCommentIDNode(PostNode):
    def  get__new_context_value(self,  context):
        id = self.object_expr.resolve(context)
        return Post.objects.get( id=Comment.objects.get(id=id).object_pk ) 

class SmartURLNode(AdvancedTemplateNode):
    def  get__new_context_value(self,  context):
        args = [ self.resolve( s, context ) for s in self.args ]
        if len( args ) > 1 :
            return reverse( args[0], args=args[1:] )
        else:
            return reverse( args[0] )

def smart_url ( parser,  token ):
    return SmartURLNode.handle_token( parser, token )

def get_post ( parser,  token ):
    return PostNode.handle_token( parser, token )

def get_post_by_comment_id ( parser,  token ):
    return PostByCommentIDNode.handle_token( parser, token )

def get_site_links_list ( parser,  token ):
    return SiteLinkNode.handle_token( parser, token )

def get_comment_archives_list ( parser,  token ):
    return CommentArchivesNode.handle_token( parser, token )

def get_link_category_list ( parser,  token ):
    return SiteLinkCategoryNode.handle_token( parser, token )

def get_post_category_list ( parser,  token ):
    return PostCategoryNode.handle_token( parser, token )

def get_post_featured_list ( parser,  token ):
    return PostFeaturedNode.handle_token( parser, token )
    
def get_post_archives_list ( parser,  token ):
    return PostArchivesNode.handle_token( parser, token )

def get_post_tags_list ( parser,  token ):
    return PostTagsNode.handle_token( parser, token )

def render_post_with_id ( id ):
    return { 'post':Post.objects.get(id=id), }
    
def render_post ( post ):
    return { 'post':post,  }
    
def render_orphan ( post ):
    return { 'post':post, }
    
def render_link ( link ):
    return { 'link':link, }

def render_tag ( tag, tag_view=None):
    return { 'tag':tag, 'tag_view':tag_view }

def render_comment( comment, index=0 ):
    return{ 'comment':comment, 'index':index }

def render_categories_list( categories=None ):
    if categories is None : 
        objects = PostCategory.objects.filter(parent__isnull=True)
    else:
        objects = categories
    
    return { 'categories':objects }
    
def render_archives_list( archives, archive_view=None, archive_view_year=None, archive_view_month=None ):
    return { 'archives':archives, 
             'archive_view':archive_view, 
             'archive_view_year':archive_view_year, 
             'archive_view_month':archive_view_month }
    
def render_links_list( links=None ):
    if links is None:
        objects = SiteLink.objects.all().order_by('?')[:6]
    else:
        objects = links
    return { 'links':objects }

def render_tags_cloud( tags, tag_view=None ):
    return {'tags':tags, 'tag_view':tag_view}

def get_gravatar_md5 ( mail ):
    return hashlib.md5( mail.strip() ).hexdigest()

def get_page_description_meta( request ):
    l = msettings.URLS_META_DESCRIPTION
    path = request.META["PATH_INFO"]
    desc = msettings.DEFAULT_META_DESCRIPTION
    for t in l:
        if len(t) == 2 :
            r = re.compile( t[0] )
            d = t[1]
            
            try :
                c = get_definition_with_path(d)
                if c is not None :
                    d = c
            except:
                pass
            
            res = r.search( path )
            if res is not None :
                if callable(d):
                    desc = d(res)
                else:
                    desc = d
    
    return '<meta name="description" content="%s"/>' % _(desc)
    
counter = 0

def init_counter( v ):
    from abe.posts.templatetags import posts
    posts.counter = v
    return ""

def increment_counter():
    from abe.posts.templatetags import posts
    c = posts.counter
    posts.counter = c + 1
    return ""

def cycle_counter( odd, even ):
    from abe.posts.templatetags import posts
    if posts.counter % 2 == 0:
        return even
    else:
        return odd

render_tag = register.inclusion_tag("posts/tag.html")(render_tag)
render_link = register.inclusion_tag("posts/link.html")(render_link)
render_post = register.inclusion_tag("posts/post_view.html")(render_post)
render_comment = register.inclusion_tag("comments/comment.html")(render_comment)
render_post_with_id = register.inclusion_tag("posts/post_view.html")(render_post_with_id)
render_orphan = register.inclusion_tag("posts/orphan_view.html")(render_orphan)
render_categories_list = register.inclusion_tag('posts/categories_list.html')(render_categories_list)
render_archives_list = register.inclusion_tag('posts/archives_list.html')(render_archives_list)
render_tags_cloud = register.inclusion_tag('posts/tags_cloud.html')(render_tags_cloud)
render_links_list = register.inclusion_tag('posts/links_list.html')(render_links_list)

register.simple_tag( get_gravatar_md5 )
register.simple_tag( get_page_description_meta )

register.simple_tag( init_counter )
register.simple_tag( increment_counter )
register.simple_tag( cycle_counter )

register.tag( smart_url )
register.tag( get_post )
register.tag( get_post_by_comment_id )
register.tag( get_comment_archives_list )
register.tag( get_link_category_list )
register.tag( get_post_category_list )
register.tag( get_post_featured_list )
register.tag( get_post_archives_list )
register.tag( get_post_tags_list )
register.tag( get_site_links_list )
