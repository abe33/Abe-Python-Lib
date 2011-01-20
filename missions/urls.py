# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('abe.missions',
	url (r'test/$',																									'views.test_view',			name="missions_test_view"),
	url (r'list/$', 																								'views.user_missions_list',  name="missions_list"), 
	url (r'activate/$', 																								'views.activate_missions',  name="activate_missions"), 
	
	#AMF Gateway
	url (r'gateway/',																								'amfgateway.missions_gateway',			name="missions_gateway"),
)
