# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django import template
from django.contrib.comments.models import Comment

from abe.posts.models import *
from abe.posts import settings as msettings
from abe.utils import *

from tagging.models import *

import hashlib

register = Library()

class PostCategoryNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( PostCategory.objects.all() )

class SiteLinkNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( SiteLink.objects.all().order_by("?")[:5] )

class PostArchivesNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( Post.objects.filter( published=True, orphan=False ).dates('published_date', 'month', order='DESC') )

class CommentArchivesNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( Comment.objects.dates('submit_date', 'month', order='DESC') )

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

def get_post ( parser,  token ):
	return PostNode.handle_token( parser,  token )

def get_post_by_comment_id ( parser,  token ):
	return PostByCommentIDNode.handle_token( parser,  token )

def get_post_category_list ( parser,  token ):
	return PostCategoryNode.handle_token( parser,  token )

def get_site_links_list ( parser,  token ):
	return SiteLinkNode.handle_token( parser,  token )

def get_post_archives_list ( parser,  token ):
	return PostArchivesNode.handle_token( parser,  token )

def get_comment_archives_list ( parser,  token ):
	return CommentArchivesNode.handle_token( parser,  token )

def get_post_tags_list ( parser,  token ):
	return PostTagsNode.handle_token( parser,  token )

def render_post_with_id ( id ):
    return {
                    'post':Post.objects.get(id=id),  
                 }
def render_post ( post ):
    return {
                    'post':post,  
                 }

def render_orphan ( post ):
    return {
                    'post':post,  
                 }

def render_categories_list():
	objects = PostCategory.objects.all()
	s = '<ul>'
	for o in objects :  
		s += '<li><a href="%s">%s</a></li>' % ( o.get_absolute_url(), o.name )
	s += '</ul>'
	return s

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
	
	return '<meta name="description" content="%s"/>' % desc

render_post = register.inclusion_tag("posts/post_view.html")(render_post)
render_post_with_id = register.inclusion_tag("posts/post_view.html")(render_post_with_id)
render_orphan = register.inclusion_tag("posts/orphan_view.html")(render_orphan)

register.simple_tag( get_gravatar_md5 )
register.simple_tag( render_categories_list )
register.simple_tag( get_page_description_meta )
register.tag( get_post )
register.tag( get_post_by_comment_id )
register.tag( get_post_category_list )
register.tag( get_post_archives_list )
register.tag( get_comment_archives_list )
register.tag( get_post_tags_list )
register.tag( get_site_links_list )
