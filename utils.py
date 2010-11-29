# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django import template
import hashlib

class BaseTemplateNode(template.Node):
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

class BaseTemplateForObjectNode(BaseTemplateNode):
	def handle_token(cls, parser, token):
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
