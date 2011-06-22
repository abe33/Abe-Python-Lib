# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.db import models
from django import template
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.contrib.admin.filterspecs import FilterSpec
from django.utils.translation import ugettext as _
from django.db.models import Q, Count

from datetime import *

from tagging.fields import TagField

import hashlib
import re
import pyamf


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

def convert_to_builtin_type(obj):
    # Convert objects to a dictionary of their representation
    d = { '__class__':obj.__class__.__name__, 
          '__module__':obj.__module__,
          }
    d.update(obj.__dict__)
    return d
    
def dict_to_object(  d ):
    if '__class__' in d:
        class_name = d.pop('__class__')
        module_name = d.pop('__module__')
        class_ = get_definition( class_name, module_name )
        args = dict( (key.encode('ascii'), value) for key, value in d.items())
        inst = class_(**args)
    else:
        inst = d
    return inst

def json_dumps( data ):
    try:
        d = json.dumps(data, cls=DjangoJSONEncoder )
        return d
    except TypeError, err:
        d = json.dumps( data, default=convert_to_builtin_type, cls=DjangoJSONEncoder )
        return d

def json_loads( data ):
    return json.loads( data, object_hook=dict_to_object)

def get_definition( name, path=None ):
    if path is None or len(path)==0:
        exec "import %s as class_alias" % name
    else:
        exec 'from %s import %s as class_alias' % ( path,  name )
    return class_alias

def get_definition_with_path( path ):
    a = path.split(".")
    return get_definition( a[-1],".".join(a[0:-1]) )

def get_classpath( cls ):
    return "%s.%s" % ( cls.__dict__["__module__"], cls.__name__ )

def date_from_string( s ):
    if s is None:
        return None
    if isinstance( s, date ):
        return s
    
    r = re.compile("^([\d]{4})-([\d]{1,2})-([\d]{1,2})")
    res = r.search( s )
    return date( int(res.group(1)),  int(res.group(2)),  int(res.group(3)) )

def some_in_list( a, b ):
    n = 0
    for o in a : 
        if o in b :
            n+=1
    return n>=1

def every_in_list( a, b ):
    for o in a : 
        if o not in b :
            return False
    return True

def remove_html_tags(data):
    p = re.compile(r'<.*?>|\s\s+')
    return p.sub('', data)

def crossdomain(request, user=None):
    return render_to_response(
                'crossdomain.xml',
                {
                },
                mimetype="application/xhtml+xml")

class TimeDelta:
    def __init__(self, delta=None, total_seconds=None ):
        if delta is not None : 
            self.total_seconds = ((delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10**6) / 10**6 ) if delta is not None else 0
        elif total_seconds is not None : 
            self.total_seconds = total_seconds
        else:
            self.total_seconds = 0

    class __amf__:
        external = True
        amf3 = True

    def __writeamf__(self, output):
        output.writeInt( int( self.total_seconds * 1000 ) )

    def __readamf__(self, input):
#        print "read amf for timedelta"
        sec = input.readInt() 
#        print "delta sec"
        self.total_seconds = sec / 1000
    
    def to_timedelta(self):
        return timedelta(seconds=self.total_seconds)

    def __repr__(self):
        return str( self.to_timedelta() )

pyamf.register_class( TimeDelta, 'aesia.com.mon.utils.TimeDelta' )

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
    Where ssssss represents fractional seconds.     The timezone
    is optional and may be either positive or negative
    hours/minutes east of UTC.
    """
    if s is None:
        return None
    if isinstance( s, datetime ):
        return s
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
    if isinstance( s, timedelta ):
        return s
    if isinstance( s, TimeDelta ):
        return s.to_timedelta()
        
    d = re.search(
            r'((?P<days>\d+) day[s]*, )?(?P<hours>\d+):'
            r'(?P<minutes>\d+):(?P<seconds>\d+)',
            str(s)).groupdict(0)
    return timedelta(**dict(( (key, int(value))
                              for key, value in d.items() )))

class TagFilterSpec(FilterSpec):
    def __init__(self, f, request, params, model, model_admin, **kwargs ):
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

class AdvancedTemplateNode(template.Node):
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        as_varname = None
        for_object = None
        if "as" in tokens:
            as_index = tokens.index("as")
            if as_index + 1 < len(tokens):
                as_varname = tokens[as_index + 1]
        
        if "for" in tokens:
            for_index = tokens.index("for")
            if for_index + 1 < len(tokens):
                for_object = tokens[for_index + 1]
            
        return cls( tokens=tokens, as_varname=as_varname, for_object=for_object, parser=parser )
    
    handle_token = classmethod(handle_token)

    def __init__(self, tokens=None, as_varname=None, for_object=None, parser=None ):
        self.tokens = tokens
        self.as_varname = as_varname
        self.for_object = for_object
        self.parser = parser
        
        args_end = len(tokens)
        if self.as_varname is not None : 
            args_end = self.tokens.index( self.as_varname ) - 1
        if self.for_object is not None : 
            args_end = min( self.tokens.index( self.for_object ) - 1, args_end )
            
        self.args = self.tokens[1:args_end]

    def render(self, context):
        res = self.get__new_context_value(context)
        if self.as_varname is not None :
            context[self.as_varname] = res
            return ''
        else:
            return res
    
    def resolve_token( self, index, context ):
        return self.parser.compile_filter( self.tokens[ index ] ).resolve( context )
    
    def resolve( self, s, context ):
        return self.parser.compile_filter( s ).resolve( context )

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
