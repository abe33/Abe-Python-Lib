# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django import template
from django.contrib.comments.models import Comment

from abe.posts.models import *
from tagging.models import *

import hashlib

register = Library()

class BasePostNode(template.Node):
	def handle_token(cls, parser, token):
		tokens = token.contents.split()
		if tokens[1] != 'as':
			raise template.TemplateSyntaxError("Second argument in %r tag must be 'as'" % tokens[0])
		
		return cls( as_varname=tokens[2],  )

	handle_token = classmethod(handle_token)
	
	def __init__(self, as_varname=None,  object_expr=None ):
		self.as_varname = as_varname
		self.object_expr = object_expr

	def render(self, context):
		context[self.as_varname] = self.get__new_context_value(context)
		return ''
	
	def get__new_context_value(self,  context):
		raise NotImplementedPostError

class PostCategoryNode(BasePostNode):
	def  get__new_context_value(self,  context):
		return list( PostCategory.objects.all() )

class SiteLinkNode(BasePostNode):
	def  get__new_context_value(self,  context):
		return list( SiteLink.objects.all().order_by("?")[:5] )

class PostArchivesNode(BasePostNode):
	def  get__new_context_value(self,  context):
		return list( Post.objects.filter( published=True, orphan=False ).dates('published_date', 'month', order='DESC') )

class CommentArchivesNode(BasePostNode):
	def  get__new_context_value(self,  context):
		return list( Comment.objects.dates('submit_date', 'month', order='DESC') )

class PostTagsNode(BasePostNode):
	def  get__new_context_value(self,  context):
		return list( Tag.objects.cloud_for_model( Post ) )
		
class PostNode(BasePostNode):
	def handle_token(cls, parser, token):
		tokens = token.contents.split()
		tokens = token.contents.split()
		if tokens[1] != 'for':
			raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

		# {% get_whatever for obj as varname %}
		if len(tokens) == 5:
			if tokens[3] != 'as':
				raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
			return cls(
				object_expr = parser.compile_filter(tokens[2]),
				as_varname = tokens[4],
		)
		return cls( as_varname=tokens[2],  )

	handle_token = classmethod(handle_token)
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

def get_gravatar_md5 ( mail ):
	return hashlib.md5( mail.strip() ).hexdigest()

render_post = register.inclusion_tag("posts/post_view.html")(render_post)
render_post_with_id = register.inclusion_tag("posts/post_view.html")(render_post_with_id)
render_orphan = register.inclusion_tag("posts/orphan_view.html")(render_orphan)

register.simple_tag( get_gravatar_md5 )

register.tag( get_post )
register.tag( get_post_by_comment_id )
register.tag( get_post_category_list )
register.tag( get_post_archives_list )
register.tag( get_comment_archives_list )
register.tag( get_post_tags_list )
register.tag( get_site_links_list )
