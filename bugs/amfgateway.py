# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import *
from abe.bugs.models import Ticket
from pyamf.remoting.gateway.django import DjangoGateway

def tickets_all( request ):
    return Ticket.objects.all()

services = {
    'tickets.all': tickets_all, 
    # could include other functions as well
}

tickets_gateway = DjangoGateway(services)
