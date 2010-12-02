# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *

from abe.bugs.views import *
from abe.bugs.models import *
from abe.utils import *
from abe.bugs import settings

register = Library()

class ComponentsListNode(BaseTemplateNode):
	def  get__new_context_value(self,  context):
		return list( Component.objects.all() )

def get_labels_for(model, cap=True, esc=True): 
	labels = {} 
	for field in model._meta.fields: 
		print( field.name )
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
	"""
	Renvoie l'ensemble des classes css indiquant l'état du ticket passé en paramètre.

	Usage : ::

		{% pain_css ticket %}
		
	Un ticket ne peut avoir que trois styles d'état simultanément parmi les style suivants :

	- painX : où X est un entier allant de 0 à 100 inclus
	- block : si le ticket est bloquant pour le cycle de développement courant
	- affected : si le ticket à été affecter à un membre du staff
	- done : si le ticket est fermé

	À noter qu'un ticket ne peux pas être affecté et fermé en même temps. 

	Exemple de style possible : ::

		pain20 status0
		pain20 status0 block
		pain20 status0 done
		pain20 status0 block affected
	"""
	css = "pain%s" % ticket.pain_as_int()
	css += ' status%i' % ticket.status
	
	if( ticket.block_milestone() ):
		css += ' block'
		
	if( ticket.is_done() ):
		css += ' done'
	else:
		if( ticket.is_affected() ):
			css += ' affected'
	return css
register.simple_tag( pain_css )

def user_name (user):
	"""
	Renvoie le nom complet de l'objet User passé en paramètre, si celui-ci n'est pas vide, 
	autrement, la fonction renvoie le login de l'utilisateur.

	Usage : ::

		{% user_name user %}
	"""
	name = ""
	if( user.get_full_name() != "" ):
		name = user.get_full_name()
	else:
		name = user.username
	return name
register.simple_tag( user_name )

def user_profil_url(user, target_user, link_title="", link_class="" ):
	"""
	Renvoie un lien HTML vers la page de profil de l'utilisateur en fonction des paramètres.
	 
	Usage : ::

		{% user_profil_url user target_user link_title link_class %}
		
	- Le premier argument est l'utilisateur en train de visualiser la page.
	- Le deuxième argument est l'utilisateur pour lequel on souhaite créer un lien vers le profil.
	- Le troisième paramètre est optionnel, il s'agit de la valeur de l'attribut title du lien crée.
	- Le quatrième paramètre est optionnel, il s'agit de la valeur de l'attribut class du lien crée.

	Un lien n'est renvoyée que dans les conditions suivantes : 

	- L'utilisateur en train de visualiser la page possède les droits nécessaires pour visualiser les profils utilisateurs.
	- Le site autorise les pages de profils utilisateurs.

	Si l'une de ces conditions n'est pas validée, le résutat retourné est le même qu'avec le tag user_name.
	"""
	anchor = ""
	if user.is_staff:
		anchor = "<a href='%s' title='%s' class='%s'>%s</a>" % ( "#", link_title, link_class, user_name(target_user), )
	else:
		anchor = user_name(target_user)
	return anchor
register.simple_tag( user_profil_url )

def milestone_header(milestone, component=None):
	"""
	Inclus le template d'affichage des informations du cycle de développement
	passé en paramètre.

	Usage : ::

		{% milestone_header milestone component %}
		
	Le template utilisé est situé à l'adresse suivante :  
	  
		bugreport/milestone_header.html
	"""
	return {
					'milestone':milestone,
					'component':component
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
	"""
	Génère l'ensemble des styles css utilisés pour la représentation de la pénibilité d'un ticket.

	Usage::

		{% print_pain_css %}
		
	Ce tag est désormais déprécié. À la place il est conseillé d'ajouter la feuille de style suivante
	dans les pages d'affichages de ticket :

		bugrepot/css/pain_colors.css
	"""
	css = print_style( settings.PAIN_COLOR, settings.PAIN_PREFIX )
	css += print_style( settings.PAIN_BLOCK_COLOR, settings.PAIN_PREFIX + settings.PAIN_BLOCK_PREFIX )
	css += print_style( settings.PAIN_AFFECTED_COLOR, settings.PAIN_PREFIX  + settings.PAIN_BLOCK_PREFIX + settings.PAIN_AFFECTED_PREFIX )
	css += print_style( settings.PAIN_DONE_COLOR, settings.PAIN_PREFIX + settings.PAIN_BLOCK_PREFIX + settings.PAIN_DONE_PREFIX )
	return css
register.simple_tag( print_pain_css )
