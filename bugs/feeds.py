# -*- coding: utf-8 -*-
from django.contrib.syndication.views import Feed
from abe.bugs.models import Ticket,  Component
from django.core.urlresolvers import reverse
from django.shortcuts import *
from django.utils.translation import ugettext as _

class LatestTicketsFeed(Feed):
	title = _(u"Derniers tickets")
	link = ""
	description = ""

	def link (self,  ticket ):
		return reverse("tickets_list")

	def items(self):
		return Ticket.objects.order_by('-creation_date')[:10]

	def item_title(self, item):
		return item.name

	def item_description(self, item):
		return item.description

class LatestTicketsByComponentFeed(Feed):
	title = ""
	link = ""
	description = ""
	
	def link (self,  component ):
		return reverse("tickets_by_component",  args=(component.name, ))

	def title (self,  component):
		return _u( "Derniers tickets pour le composant %s" % component.name ) 

	def get_object(self, request, component):
		return get_object_or_404(Component, name=component)

	def items(self, cat ):
		return Ticket.objects.filter(published=True,  component__name=component.name).order_by('-creation_date')[:10]

	def item_title(self, item):
		return item.name

	def item_description(self, item):
		return item.description
