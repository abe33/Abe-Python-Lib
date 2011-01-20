# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *

from abe.bugs.views import *
from abe.bugs.models import *
from abe.utils import *
from abe.bugs import settings as msettings

register = Library()

class ComponentsListNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( Component.objects.all() )

def get_labels_for(model, cap=True, esc=True): 
	labels = {} 
	for field in model._meta.fields: 
		label = field.verbose_name 
		if cap : 
			label = capfirst(label) 
		if esc: 
			label = escape(label) 
		labels[field.name] = label 
	return labels 

def with_labels(context, cap=True, esc=True): 
	result = context.copy() 
	for k, v in context.iteritems(): 
		if isinstance(v, Model): 
			result[k + '_labels'] = get_labels_for(v, cap, esc) 
		elif hasattr(v, '__getitem__') and len(v) > 0: 
			if isinstance(v[0], Model): 
				result[k + '_labels'] = get_labels_for(v[0], cap, esc) 
	return result 

def render_user_ticket_form( ticket=None ):
	return UserTicketForm()

def render_ticket( ticket ):
	return {
					'ticket':ticket, 
					'labels' : get_labels_for(ticket),
					'next_ticket':ticket.next_ticket(), 
					'previous_ticket':ticket.previous_ticket(), 
				}
render_ticket = register.inclusion_tag("bugs/ticket_detail.html")(render_ticket)

def render_tickets_table( tickets, user, table_id="tickets_list"):
	return {
					'tickets':tickets, 
					'user':user, 
					'table_id':table_id, 
					'MEDIA_URL':settings.MEDIA_URL, 
					'milestone' : MileStone.objects.get(active=True),
				}
render_tickets_table = register.inclusion_tag("bugs/tickets_table.html")(render_tickets_table)

def render_user_tickets_table( user ):
	return {
					'tickets':Ticket.objects.filter( assignees__id__contains=user.id ).order_by("-pain"), 
					'user':user, 
					'table_id':"my_tickets", 
					'MEDIA_URL':settings.MEDIA_URL, 
					'milestone' : MileStone.objects.get(active=True),
				}
render_user_tickets_table = register.inclusion_tag("bugs/tickets_table.html")(render_user_tickets_table)

def render_ticket_with_id( id ):
	ticket = Ticket.objects.get(id=id)
	return {
					'ticket':ticket, 
				}
render_ticket_with_id = register.inclusion_tag("bugs/ticket_detail.html")(render_ticket_with_id)

def render_components_select ( component = None ):
	return {
					'components':Component.objects.all(), 
					'component':component, 
				}
render_components_select = register.inclusion_tag("bugs/component_select.html")(render_components_select)

def render_ticket_form( request,  ticket=None ):
	if request.method == "POST" : 
		data = request.POST
	else:
		data = None
	return {
						'form':get_ticket_form( request.user, data, ticket ), 
						'user':request.user, 
				}
render_ticket_form = register.inclusion_tag("bugs/ticket_form.html")(render_ticket_form)

def render_ajax_ticket_form( request ):
	return { 
					'form':UserTicketForm( data=None, instance=None ), 
					'request':request, 
				}
render_ajax_ticket_form = register.inclusion_tag("bugs/ajax_ticket_form.html")(render_ajax_ticket_form)

def get_components_list ( parser,  token ):
	return ComponentsListNode.handle_token( parser,  token )

def pain_css (ticket):
	css = "pain%s" % ticket.pain_as_int()
	css += ' status%i' % ticket.status
	
	if ticket.block_milestone() :
		css += ' block'
		
	if ticket.killer_bug :
		css += ' killer'
	
	if not ticket.active :
		css += ' done'
	else:
		if ticket.is_affected() :
			css += ' affected'
	
	return css
register.simple_tag( pain_css )

def ticket_user_name (user):
	name = ""
	if user.get_full_name() != "" :
		name = user.get_full_name()
	else:
		name = user.username
	return name
register.simple_tag( ticket_user_name )

def ticket_user_profil_url(user, target_user, link_title="", link_class="" ):
	anchor = ""
	if user.is_staff:
		anchor = "<a href='%s' title='%s' class='%s'>%s</a>" % ( "#", link_title, link_class, ticket_user_name(target_user), )
	else:
		anchor = ticket_user_name(target_user)
	return anchor
register.simple_tag( ticket_user_profil_url )

def milestone_header(milestone, component=None):
	return {
					'milestone':milestone,
					'component':component, 
				}
milestone_header = register.inclusion_tag("bugs/milestone_header.html")(milestone_header)

def print_style(color,style_name):
	i = 0
	l = 100
	r = 0
	g = 0
	b = 0
	css = ''
	while( i <= l ):
		ref_r = 255-( color >> 16 & 0xff )
		ref_g = 255-( color >> 8 & 0xff )
		ref_b = 255-( color & 0xff )
		r = ( 255 - int(i*ref_r / 100) ) << 16
		g = ( 255 - int(i*ref_g /100) ) << 8
		b = ( 255 - int(i*ref_b / 100) )
		css += ( style_name % i ) + '{ background:' + hex( int( r + g + b  ) ).replace( '0x', '#' ) + '; }\n'
		i=i+1
	return css + '\n'

def print_pain_css ():
	css = print_style( msettings.PAIN_COLOR, msettings.PAIN_PREFIX )
	css += print_style( msettings.PAIN_BLOCK_COLOR, msettings.PAIN_PREFIX + msettings.PAIN_BLOCK_PREFIX )
	css += print_style( msettings.PAIN_AFFECTED_COLOR, msettings.PAIN_PREFIX  + msettings.PAIN_BLOCK_PREFIX + msettings.PAIN_AFFECTED_PREFIX )
	css += print_style( msettings.PAIN_DONE_COLOR, msettings.PAIN_PREFIX + msettings.PAIN_BLOCK_PREFIX + msettings.PAIN_DONE_PREFIX )
	return css
register.simple_tag( print_pain_css )
