# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django import template

from datetime import *

import hashlib
import re

def get_class( name, path=None ):
	if path is None or len(path)==0:
		exec "import %s as class_alias" % name
	else:
		exec 'from %s import %s as class_alias' % ( path,  name )
	return class_alias

def get_class_with_path( path ):
	a = path.split(".")
	return get_class( a[-1],".".join(a[0:-1]) )

def get_classpath( cls ):
	return "%s.%s" % ( cls.__dict__["__module__"], cls.__name__ )

def date_from_string( d ):
	r = re.compile("([\d]{4})-([\d]{1,2})-([\d]{1,2})")
	res = r.search( d )
	return date( int(res.group(1)),  int(res.group(2)),  int(res.group(3)) )

def datetime_from_string( s ):
	"""
	Create datetime object representing date/time
	expressed in a string

	Takes a string in the format produced by calling str()
	on a python datetime object and returns a datetime
	instance that would produce that string.

	Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
										"YYYY-MM-DD HH:MM:SS.ssssss",
										"YYYY-MM-DD HH:MM:SS+HH:MM",
										"YYYY-MM-DD HH:MM:SS"
	Where ssssss represents fractional seconds.	 The timezone
	is optional and may be either positive or negative
	hours/minutes east of UTC.
	"""
	if s is None:
		return None
	# Split string in the form 2007-06-18 19:39:25.3300-07:00
	# into its constituent date/time, microseconds, and
	# timezone fields where microseconds and timezone are
	# optional.
	m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
				 str(s))
	datestr, fractional, tzname, tzhour, tzmin = m.groups()

	# Create tzinfo object representing the timezone
	# expressed in the input string.  The names we give
	# for the timezones are lame: they are just the offset
	# from UTC (as it appeared in the input string).  We
	# handle UTC specially since it is a very common case
	# and we know its name.
	if tzname is None:
		tz = None
	else:
		tzhour, tzmin = int(tzhour), int(tzmin)
		if tzhour == tzmin == 0:
			tzname = 'UTC'
		tz = FixedOffset(timedelta(hours=tzhour,
								   minutes=tzmin), tzname)

	# Convert the date/time field into a python datetime
	# object.
	x = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")

	# Convert the fractional second portion into a count
	# of microseconds.
	if fractional is None:
		fractional = '0'
	fracpower = 6 - len(fractional)
	fractional = float(fractional) * (10 ** fracpower)

	# Return updated datetime object with microseconds and
	# timezone information.
	return x.replace(microsecond=int(fractional), tzinfo=tz)

def timedelta_from_string( s ):
	"""
	Create timedelta object representing time delta
	expressed in a string

	Takes a string in the format produced by calling str() on
	a python timedelta object and returns a timedelta instance
	that would produce that string.

	Acceptable formats are: "X day(s), HH:MM:SS" or "HH:MM:SS".
	"""
	if s is None:
		return None
	
	d = re.search(
			r'((?P<days>\d+) day[s]*, )?(?P<hours>\d+):'
			r'(?P<minutes>\d+):(?P<seconds>\d+)',
			str(s)).groupdict(0)
	return timedelta(**dict(( (key, int(value))
							  for key, value in d.items() )))

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
