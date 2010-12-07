# -*- coding: utf-8 -*-
import pyamf
from django.contrib import auth
from django.contrib.auth.decorators import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
 
from pyamf.remoting.gateway.django import DjangoGateway

from abe.bugs.models import Ticket

try:
    pyamf.register_class( User,  'django.contrib.auth.models.User')
except ValueError:
    print "Classes already registered"

def tickets_all( request ):
    return Ticket.objects.all()
 
def logout_user(http_request):
    logout(http_request)
 
def login_user(http_request, username, password):
    user = authenticate(username=username, password=password)
    if user is not None:
        login(http_request, user)
        return user
    return None

services = {
	'tickets.all': tickets_all, 
	'main.login'           : login_user,
	'main.logout'         : logout_user,
}

tickets_gateway = DjangoGateway(services)
