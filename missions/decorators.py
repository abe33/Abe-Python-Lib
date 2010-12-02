# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser

from abe.missions.middleware import MissionTriggerResponse
from abe.missions import settings

def mission_triggers( *triggers ):
	def _mission_triggers( f ):
		def __mission_triggers( *args,  **kwargs):
			res = f( *args,  **kwargs )
			if isinstance( args[0].user, AnonymousUser ):
				return res
			else:
				return MissionTriggerResponse( res, triggers, args[0] )
		return __mission_triggers
	return _mission_triggers

def mission_map_update( f ):
	def _mission_map_update( *args,  **kwargs):
		res = f( *args,  **kwargs )
		print "mission_map_update"
#		settings.MISSION_MIDDLEWARE_INSTANCE.update_missions_map()
		return res
	return _mission_map_update
