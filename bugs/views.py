# -*- coding: utf-8 -*-
from django.http import *
from django.contrib.auth.decorators import *
from django.shortcuts import *
from django.template import RequestContext
from django.core.paginator import Paginator
from django import forms
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst 
from django.utils.html import escape 
from django.db.models import Model 
from django.utils.translation import ugettext as _

from abe.bugs.models import *
from abe.bugs import settings as mssettings

num_ticket_per_page = "4"
start_page = "1"

class UserTicketForm(forms.ModelForm):
	class Meta:
		model = Ticket
		fields = ['name', 'description', ]

class StaffTicketForm(forms.ModelForm):
	class Meta:
		model = Ticket
		fields = ['name', 'description', 'type','priority','likelihood', 'allow_comments']

class SuperUserTicketForm(forms.ModelForm):
	class Meta:
		model = Ticket
		exclude = ('creator', )

def get_ticket_form( user, data=None,  instance=None ):
	if user.is_superuser:
		return SuperUserTicketForm( data=data,  instance=instance)
	
	elif user.is_staff:
		return StaffTicketForm( data=data,  instance=instance )
	
	else:
		return UserTicketForm( data=data,  instance=instance )

def tickets_list_generic (   request, 
										tickets_list, 
										component=None, 
										page_title='Page Sans titre', 
										next_page_view="", 
										rss_page_view="", 
										pages_args=None, 
										page_index=start_page, 
										num=num_ticket_per_page ):
	if len( tickets_list ) == 0:
		return render_to_response( "bugs/tickets_list.html", 
												{
													'page_title':page_title,
													'rss_page_url':reverse("tickets_rss"), 
													'milestone' : MileStone.objects.get(active=True),
													'components_list':Component.objects.all(), 
													'component':component, 
												}, 
												RequestContext( request ) )

	paginator = Paginator( tickets_list,  int(num) )
	page = paginator.page( int(page_index) )

	has_next_page = page.has_next()
	has_previous_page = page.has_previous()
	rss_page_url = None
	next_page_url = None
	previous_page_url = None

	if rss_page_view is not None :
		rss_page_url = reverse( rss_page_view,  kwargs=pages_args )

	if has_next_page :
		pages_args["page"] = page.next_page_number()
		#pages_args["num"] = num
		next_page_url = reverse( next_page_view,  kwargs=pages_args )

	if has_previous_page :
		pages_args["page"] = page.previous_page_number()
		#pages_args["num"] = num
		previous_page_url = reverse( next_page_view,  kwargs=pages_args )

	return render_to_response( "bugs/tickets_list.html", 
												{
													'tickets_list':page.object_list, 
													
													'page_title':page_title,
													'page_index':page_index, 
													'pages_count':paginator.count, 
													'has_next_page':has_next_page, 
													'has_previous_page':has_previous_page, 
													'next_page_url':next_page_url, 
													'previous_page_url':previous_page_url, 
													'rss_page_url':rss_page_url, 
													'milestone' : MileStone.objects.get(active=True),
													'components_list':Component.objects.all(), 
													'component':component, 
												}, 
												RequestContext( request ) )

def tickets_list ( request, page=start_page,  num=num_ticket_per_page ):
	return tickets_list_generic( request,  
										   Ticket.objects.filter(active=True).order_by("-pain"), 
										   None, 
										   _(u"Tickets"), 
										   "tickets_archive", 
										   "tickets_rss", 
										   {}, 
										   page, 
										   num )

def component_tickets_list ( request, component="",  page=start_page,  num=num_ticket_per_page ):
	return tickets_list_generic( request,  
										   Ticket.objects.filter(active=True,  component__name=component).order_by("-pain"), 
										   Component.objects.get(name=component), 
										   _(u"Tickets pour le composant %s" % component), 
										   "tickets_by_component_archive", 
										   "tickets_by_component_rss", 
										   {
												'component':component, 
											}, 
										   page, 
										   num )

def ticket_detail ( request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
	except Ticket.DoesNotExist:
		raise Http404
	return render_to_response( 'bugs/ticket_detail.html', 
							   { 'ticket': ticket,
								 'milestone' : MileStone.objects.get(active=True),
								 'labels' : get_labels_for(ticket),},
							   context_instance=RequestContext(request) )

@login_required
def ticket_affect (request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
	except Ticket.DoesNotExist:
		raise Http404

	ticket.reviewer = request.user
	ticket.save()
	return redirect( reverse("tickets_list"))

def ticket_new ( request ):
	if request.method == 'POST':
	   
		ticket = Ticket(creator=request.user, active=True)
		form = get_ticket_form(request.user,  request.POST, ticket)

		if form.is_valid():
			form.save()
			return redirect(reverse("tickets_list"))
		else:
			return render_to_response('bugs/ticket_edit.html', 
								{ 'form': form, 
									'ticket_url': reverse("ticket_create"),  },
								context_instance=RequestContext(request))
	else :
		return render_to_response('bugs/ticket_edit.html', 
								{ 'form':  get_ticket_form(request.user), 
								'ticket_url':reverse("ticket_create"), },
								context_instance=RequestContext(request))

@login_required
def ticket_edit ( request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
		if request.method == 'ticket': # If the form has been submitted...
			form = get_ticket_form(request.user,  request.ticket, ticket) # A form bound to the ticket data
			if form.is_valid(): # All validation rules pass
				# Process the data in form.cleaned_data
				# ...
				form.save()
				return redirect(reverse("tickets_list")) # Redirect after ticket
			else:
				return render_to_response('bugs/ticket_edit.html', 
								  { 'form': form,
									'labels' : get_labels_for(ticket),
									'ticket_url':reverse("ticket_edit", kwargs={'id':id,} ), 
									},
								  context_instance=RequestContext(request))
		else:
			form = get_ticket_form( user=request.user, instance=ticket) # An unbound form
			return render_to_response('bugs/ticket_edit.html', 
								  { 'form': form,
									'labels' : get_labels_for(ticket), 
									'ticket_url':reverse("ticket_edit", kwargs={'id':id,} ),
									}, 
								  context_instance=RequestContext(request))
	
	except Ticket.DoesNotExist:
		raise Http404
	return redirect(reverse("tickets_list"))

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
