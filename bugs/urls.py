# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from abe.bugs.feeds import LatestTicketsFeed, LatestTicketsByComponentFeed

urlpatterns = patterns('abe.bugs',
	url (r'^$',																										'views.tickets_list',						name="tickets_list" ),
	url (r'page/(?P<page>\d+)/$',																		'views.tickets_list',						name="tickets_archive" ),
	url (r'page/(?P<page>\d+)/(?P<num>\d+)/$',													'views.tickets_list',						name="tickets_archive_num"),
	url (r'rss/$',																									LatestTicketsFeed(),								name="tickets_rss"),

	url (r'component/(?P<component>.+)/$',														'views.component_tickets_list',		name="tickets_by_component" ),
	url (r'component/(?P<component>.+)/(?P<page>\d+)/$',								'views.component_tickets_list',		name="tickets_by_component_archive" ),
	url (r'component/(?P<component>.+)/(?P<page>\d+)/(?P<num>\d+)/$',			'views.component_tickets_list',		name="tickets_by_component_archive_num" ),
	url (r'component/(?P<component>.+)/rss/$',													LatestTicketsByComponentFeed(),		name="tickets_by_component_rss"),
	
	url (r'new/$',																									'views.ticket_new',							name="ticket_create"),
	url (r'ticket/(?P<id>\d+)/$',																		'views.ticket_detail',						name="ticket_detail"),
	url (r'ticket/(?P<id>\d+)/edit/$',																'views.ticket_edit',							name="ticket_edit"),    
	url (r'ticket/(?P<id>\d+)/affect/$',															'views.ticket_affect',						name="ticket_affect"), 
	
	url( r'tag/(?P<tag>[\w_-]+)/$', 																	'views.ticket_by_tag',						name="ticket_by_tag" ),
    url( r'tag/(?P<tag>[\w_-]+)/page/(?P<page>\d+)/$', 									'views.ticket_by_tag',						name="ticket_by_tag_archive" ),
    url( r'tag/(?P<tag>[\w_-]+)/page/(?P<page>\d+)/(?P<num>\d+)/$', 			'views.ticket_by_tag',						name="ticket_by_tag_archive_num" ),
	
	#AMF Gateway
	url (r'gateway/',																								'amfgateway.tickets_gateway',			name="ticket_gateway"),

)
