# -*- coding: utf-8 -*-
from django.http import *
from django.contrib.auth.models import *
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
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from abe.bugs.models import *
from abe.bugs import settings as mssettings
from datetime import *


num_ticket_per_page = "50"
start_page = "1"

class UserTicketForm(forms.ModelForm):
	class Meta:
		model = Ticket
		fields = ['name', 'description', ]

class StaffTicketForm(UserTicketForm):
	likelihood = forms.ChoiceField(	widget=forms.RadioSelect(), 
													choices=LIKELIHOOD_CHOICES, 
													help_text=_(u"Select the value corresponding to the issue you encounter."),  
													required=False, 
													initial=1, 
													label=_(u"Who will be affected by this bug?")	)
	priority = forms.ChoiceField( widget=forms.RadioSelect(),  
												choices=PRIORITY_CHOICES, 
												help_text=_(u"Select the value corresponding to the issue you encounter."), 
												required=False, 
												initial=1, 
												label=_(u"How will those affected feel about the bug?"))
	type = forms.ChoiceField( widget=forms.RadioSelect(),  
											choices=TYPE_CHOICES, 
											help_text=_(u"Select the value corresponding to the issue you encounter."),  
											required=False, 
											initial=1, 
											label=_(u"What type of bug is this?"))

	class Meta:
		model = Ticket
		fields = ['name', 'description', 'type','priority','likelihood', 'allow_comments']

class SuperUserTicketForm(StaffTicketForm):
	def __init__(self,  user,  data=None,  instance = None):
		super( SuperUserTicketForm,  self ).__init__(data=data,  instance=instance)
		#if instance.assignees is not None and instance.assignees == user :
	
	class Meta:
		model = Ticket
		exclude = ('creator', )

def get_ticket_form( user, data=None,  instance=None ):
	if user.is_superuser:
		return SuperUserTicketForm( user, data=data,  instance=instance)
	
	elif user.is_staff:
		return StaffTicketForm( data=data,  instance=instance )
	
	else:
		return UserTicketForm( data=data,  instance=instance )

def tickets_list_generic (   request, 
										tickets_list, 
										component=None, 
										page_title=_(u'Untitled Page'), 
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
													'now':datetime.now(), 
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
										   _(u"Tickets for component %s" % component), 
										   "tickets_by_component_archive", 
										   "tickets_by_component_rss", 
										   {
												'component':component, 
											}, 
										   page, 
										   num )

def ticket_by_tag ( request,  tag, page=start_page,  num=num_ticket_per_page ):
	 return tickets_list_generic(	request,  
											Ticket.objects.filter(active=True, tags__contains=tag).order_by("-pain"), 
											None, 
											(u"Tickets for tag : %s") % tag , 
											"ticket_by_tag_archive", 
											None, 
											{
											'tag':tag
											}, 
											page, 
											num )

def ticket_detail ( request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
	except Ticket.DoesNotExist:
		raise Http404
	return render_to_response( 'bugs/ticket_view.html', 
							   { 
									'ticket': ticket,
									'milestone' : MileStone.objects.get(active=True),
									'component':None, 
									'page_title':_(u"Ticket Details")
								},
							   context_instance=RequestContext(request) )

@login_required
def ticket_affect (request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
	except Ticket.DoesNotExist:
		raise Http404
	
	#if request.user not in ticket.assignees :
	ticket.assignees.add( request.user )
	ticket.save()
	
	return redirect( reverse("tickets_list"))

def ticket_new ( request ):
	if request.method == 'POST':
		ticket = Ticket(creator=request.user, active=True)
		form = get_ticket_form( request.user,  request.POST, ticket )
		
		if form.is_valid():

			if not ticket.is_valid_int( ticket.type ) :
				ticket.type = 1
			
			if not ticket.is_valid_int( ticket.likelihood ) :
				ticket.likelihood = 1
				
			if not ticket.is_valid_int( ticket.priority ) :
				ticket.priority = 1
			
			if not ticket.is_valid_int( ticket.status ) :
				ticket.status = 0
			
			if not ticket.active :
				ticket.active = True
			
			form.save()

			if "js" in request.POST :
				return HttpResponse(content= json.dumps({'status':'1', }, cls=DjangoJSONEncoder ))
			else:
				return redirect(reverse("tickets_list"))
		else:
			if "js" in request.POST :
				return HttpResponse(content= json.dumps({'status':'0', 'errors':form.errors}, cls=DjangoJSONEncoder ))
			else :
				return render_to_response('bugs/ticket_edit.html', 
									{ 
										'ticket':ticket, 
										'milestone' : MileStone.objects.get(active=True),
										'form': form, 
										'ticket_url': reverse("ticket_create"),  
										'component':None,
									},
									context_instance=RequestContext(request))
	else :
		return render_to_response('bugs/ticket_edit.html', 
								{
									'ticket':None, 
									'milestone' : MileStone.objects.get(active=True),
									'form':  get_ticket_form(request.user), 
									'ticket_url':reverse("ticket_create"), 
									'component':None,
									'page_title':_(u"New Ticket Form"), 
								},
								context_instance=RequestContext(request))

@login_required
def ticket_edit ( request, id ):
	try:
		ticket = Ticket.objects.get(pk=id)
		if request.method == 'POST': # If the form has been submitted...
			form = get_ticket_form(request.user,  request.POST , ticket) # A form bound to the ticket data
			if form.is_valid(): # All validation rules pass
				# Process the data in form.cleaned_data
				# ...
				form.save()
				return redirect(reverse("tickets_list")) # Redirect after ticket
			else:
				return render_to_response('bugs/ticket_edit.html', 
								  { 
									'ticket':ticket, 
									'milestone' : MileStone.objects.get(active=True),
									'form': form,
									'ticket_url':reverse("ticket_edit", kwargs={'id':id,} ), 
									'component':None,
									'page_title':_(u"Edit %s") % ticket.name, 
									},
								  context_instance=RequestContext(request))
		else:
			form = get_ticket_form( user=request.user, instance=ticket) # An unbound form
			return render_to_response('bugs/ticket_edit.html', 
								  {
									'ticket':ticket, 
									'milestone' : MileStone.objects.get(active=True),
									'form': form,
									'ticket_url':reverse("ticket_edit", kwargs={'id':id,} ),
									'component':None,
									'page_title':_(u"Edit %s") % ticket.name, 
									}, 
								  context_instance=RequestContext(request))
	
	except Ticket.DoesNotExist:
		raise Http404
	return redirect(reverse("tickets_list"))
