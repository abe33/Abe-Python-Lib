# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.models import User

admin.autodiscover()

#handler404 = 'abe.posts.views.page_not_found'

urlpatterns = patterns('',
	 (r'^site/', include('abe.posts.urls')),
	 (r'^bugs/', include('abe.bugs.urls')),
	 (r'^missions/',  include('abe.missions.urls')), 
	 (r'^comments/', include('django.contrib.comments.urls')),
	 (r'^admin/doc/', include('django.contrib.admindocs.urls')),
	  (r'^admin/', include(admin.site.urls)),
	  
	 url(r'^crossdomain\.xml$', 'abe.utils.crossdomain'),
)
