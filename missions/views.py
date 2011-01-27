# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import *
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import redirect
from django.shortcuts import render_to_response

from abe.missions.decorators import *
from abe.missions.models import *
from abe.missions.middleware import activate_mission

import re

@mission_triggers("trigger", "mission")
def test_view( request ):
	return HttpResponse("Mission Test : [[mission_notification_token]]")

@login_required
def user_missions_list( request ):
	try:
		missions = MissionProfile.objects.get( user=request.user ).missions_available
	except :
		missions = []
	return render_to_response( "missions/missions_list.html", 
												{
													'missions':missions
												}, 
												RequestContext( request ) )

@login_required
def activate_missions( request ):
	if request.method == "POST":
		test = re.compile("mission([\d]+)")
		l = [ m for m in request.POST if test.search(m)]
		for k in l:
			res = test.match( k )
			m = msettings.MISSION_MIDDLEWARE_INSTANCE.missions_map[res.group(1)]
			activate_mission( request, m )
			
		return redirect( "missions_list" )
	else :
		return redirect( "missions_list" )
	pass
