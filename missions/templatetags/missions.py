# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.contrib.auth.models import *

from abe.missions.settings import *

register = Library()

def render_mission_notification():
	return MISSION_NOTIFICATION_TOKEN

register.simple_tag( render_mission_notification )
