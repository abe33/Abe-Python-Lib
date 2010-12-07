# -*- coding: utf-8 -*-

from django.contrib.admin.templatetags.admin_list import *
from django.conf import settings
from django.contrib.admin.views.main import ALL_VAR, EMPTY_CHANGELIST_VALUE
from django.contrib.admin.views.main import ORDER_VAR, ORDER_TYPE_VAR, PAGE_VAR, SEARCH_VAR
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import dateformat
from django.utils.html import escape, conditional_escape
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.translation import get_date_formats, get_partial_date_formats, ugettext as _
from django.utils.encoding import smart_unicode, smart_str, force_unicode
from django.template import Library

from abe.bugs import settings as bsettings

import datetime

register = Library()

def _boolean_icon(field_val):
	BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
	return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" />' % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], field_val))

def tickets_items_for_result(cl, result, form):
	first = True
	pk = cl.lookup_opts.pk.attname

	row_classes = "pain%s" % result.pain_as_int()
	if result.block_milestone() :
		row_classes += ' block'

		if result.killer_bug :
			row_classes += ' killer'
		else:
			if result.is_affected() :
				row_classes += ' affected'
	
	if not result.active :
		row_classes += ' done'
	
	for field_name in cl.list_display:
		row_class = ' class="%s"' % (row_classes, )
		#if( field_name == "name" or field_name == "active" or field_name == "pain" ):
		#    row_class = ' class="%s"' % (row_classes, )
		#else:
		#    row_class = ''    
		try:
			f = cl.lookup_opts.get_field(field_name)
		except models.FieldDoesNotExist:
			# For non-field list_display values, the value is either a method,
			# property or returned via a callable.
			try:
				if callable(field_name):
					attr = field_name
					value = attr(result)
				elif hasattr(cl.model_admin, field_name) and \
				   not field_name == '__str__' and not field_name == '__unicode__':
					attr = getattr(cl.model_admin, field_name)
					value = attr(result)
				else:
					attr = getattr(result, field_name)
					if callable(attr):
						value = attr()
					else:
						value = attr
				allow_tags = getattr(attr, 'allow_tags', False)
				boolean = getattr(attr, 'boolean', False)
				if boolean:
					allow_tags = True
					result_repr = _boolean_icon(value)
				else:
					result_repr = smart_unicode(value)
			except (AttributeError, ObjectDoesNotExist):
				result_repr = EMPTY_CHANGELIST_VALUE
			else:
				# Strip HTML tags in the resulting text, except if the
				# function has an "allow_tags" attribute set to True.
				if not allow_tags:
					result_repr = escape(result_repr)
				else:
					result_repr = mark_safe(result_repr)
		else:
			field_val = getattr(result, f.attname)

			if isinstance(f.rel, models.ManyToOneRel):
				if field_val is not None:
					result_repr = escape(getattr(result, f.name))
				else:
					result_repr = EMPTY_CHANGELIST_VALUE
			# Dates and times are special: They're formatted in a certain way.
			elif isinstance(f, models.DateField) or isinstance(f, models.TimeField):
				if field_val:
					(date_format, datetime_format, time_format) = get_date_formats()
					if isinstance(f, models.DateTimeField):
						result_repr = capfirst(dateformat.format(field_val, datetime_format))
					elif isinstance(f, models.TimeField):
						result_repr = capfirst(dateformat.time_format(field_val, time_format))
					else:
						result_repr = capfirst(dateformat.format(field_val, date_format))
				else:
					result_repr = EMPTY_CHANGELIST_VALUE
				row_class = ' class="nowrap %s"' % (row_classes, )
			# Booleans are special: We use images.
			elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
				result_repr = _boolean_icon(field_val)
			# DecimalFields are special: Zero-pad the decimals.
			elif isinstance(f, models.DecimalField):
				if field_val is not None:
					result_repr = ('%%.%sf' % f.decimal_places) % field_val
				else:
					result_repr = EMPTY_CHANGELIST_VALUE
			# Fields with choices are special: Use the representation
			# of the choice.
			elif f.flatchoices:
				result_repr = dict(f.flatchoices).get(field_val, EMPTY_CHANGELIST_VALUE)
			else:
				result_repr = escape(field_val)
		if force_unicode(result_repr) == '':
			result_repr = mark_safe('&nbsp;')
		# If list_display_links not defined, add the link tag to the first field
		if (first and not cl.list_display_links) or field_name in cl.list_display_links:
			table_tag = {True:'th', False:'td'}[first]
			first = False
			url = cl.url_for_result(result)
			# Convert the pk to something that can be used in Javascript.
			# Problem cases are long ints (23L) and non-ASCII strings.
			if cl.to_field:
				attr = str(cl.to_field)
			else:
				attr = pk
			value = result.serializable_value(attr)
			result_id = repr(force_unicode(value))[1:]
			yield mark_safe(u'<%s%s><a href="%s"%s>%s</a></%s>' % \
				(table_tag, row_class, url, (cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or ''), conditional_escape(result_repr), table_tag))
		else:
			# By default the fields come from ModelAdmin.list_editable, but if we pull
			# the fields out of the form instead of list_editable custom admins
			# can provide fields on a per request basis
			if form and field_name in form.fields:
				bf = form[field_name]
				result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
			else:
				result_repr = conditional_escape(result_repr)
			yield mark_safe(u'<td%s>%s</td>' % (row_class, result_repr))
	if form:
		yield mark_safe(force_unicode(form[cl.model._meta.pk.name]))


def tickets_results(cl):
	if cl.formset:
		for res, form in zip(cl.result_list, cl.formset.forms):
			yield list(tickets_items_for_result(cl, res, form))
	else:
		for res in cl.result_list:
			yield list(tickets_items_for_result(cl, res, None))

def tickets_result_list(cl):
	return {	'cl': cl,
					'result_headers': list(result_headers(cl)),
					'results': list(tickets_results(cl))}
tickets_result_list = register.inclusion_tag("admin/change_list_results.html")(tickets_result_list)
