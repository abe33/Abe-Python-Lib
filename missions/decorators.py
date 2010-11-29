# -*- coding: utf-8 -*-
from abe.missions.middleware import MissionTriggerResponse

def mission_triggers( *triggers ):
	def _mission_triggers( f ):
		def __mission_triggers( *args,  **kwargs):
			res = f( *args,  **kwargs )
			return MissionTriggerResponse( res, triggers,  args[0].user.id )
		return __mission_triggers
	return _mission_triggers
