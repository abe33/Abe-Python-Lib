# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('abe.missions',
	#AMF Gateway
	url (r'gateway/',																								'amfgateway.missions_gateway',			name="missions_gateway"),
)
