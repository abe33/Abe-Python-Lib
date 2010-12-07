# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser

from abe.missions.middleware import MissionTriggerResponse
from abe.missions import settings as msettings

def mission_triggers( *triggers ):
	def _mission_triggers( f ):
		def __mission_triggers( *args,  **kwargs):
			res = f( *args,  **kwargs )
			user = args[0].user
			if isinstance( user, AnonymousUser ):
				return res
			else:
				try :
					profile = MissionProfile.objects.get(user__id=response.userID) 
				except :
					profile = msettings.MISSION_MIDDLEWARE_INSTANCE.init_user_missions_profile( user )
				
				return MissionTriggerResponse( res, {'triggers':triggers, 'profile':None, 'user':user } )
		return __mission_triggers
	return _mission_triggers

def mission_map_update( f ):
	def _mission_map_update( *args,  **kwargs):
		res = f( *args,  **kwargs )
		print "mission_map_update"
#		msettings.MISSION_MIDDLEWARE_INSTANCE.update_missions_map()
		return res
	return _mission_map_update
