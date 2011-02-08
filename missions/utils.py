# -*- coding: utf-8 -*-
from abe.missions import settings as msettings
from abe.utils import *

from django.contrib.auth.models import User, AnonymousUser

def check_condition( context, condition, past_state, mission_data ):
	return condition.check( context, past_state, mission_data )

def check_conditions( context, conditions, past_states = None ) :
	if conditions is None or len( conditions ) == 0 : 
		return {'fulfilled':False}

	fulfilled = 0
	datas = {}
	for i, condition in enumerate( conditions ) : 
		past_state = getattr( past_states, str(i), None )
		if past_state is not None : 
			if 'triggers' in context and not some_in_list( context["triggers"] , condition.triggers ): 
				data = past_state
			else:
				data = check_condition( context, condition, past_state, past_states )
		else:
			data = check_condition( context, condition, past_state, past_states )

		datas[ str(i) ] = data
		if data['fulfilled'] :
			fulfilled += 1
	
	if fulfilled == len(conditions) :
		datas["fulfilled"] = True
	else:
		datas["fulfilled"] = False
	
	return datas

def get_user_mission_profile( request ):
	from abe.missions.models import MissionProfile
	
	user = request.user
	try :
		profile = MissionProfile.objects.get(user=user) 
	except :
		profile = msettings.MISSION_MIDDLEWARE_INSTANCE.init_user_missions_profile( user )
		processor = get_definition_with_path( msettings.MISSION_CONTEXT_PROCESSOR )
		context = processor( request )
		msettings.MISSION_MIDDLEWARE_INSTANCE.check_user_missions( context )
	return profile

def is_valid_minimal_context( context ):
	"""Verify that a context dict is wellformed and raise errors if it's not the case."""
	from abe.missions.models import MissionProfile
	
	if "profile" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'profile'. The profile is mandatory") )
	elif "user" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'user'. The user is mandatory") )
	elif not isinstance( context["profile"], MissionProfile ) :
		raise ValueError( _(u"The provided profile is not an instance of the MissionProfile model.") )
	elif isinstance( context["user"],  AnonymousUser ):
		raise ValueError( _(u"The user in the context object must be a valid User, not an AnonymousUser.") )

def default_mission_results_processor( context, results ):
	""" This function is used to handle the results of the missions check. By default 
	this function look for completed missions and then call the affect_reward on each
	rewards of each missions.
	"""
	from abe.missions.rewards import TemporaryMissionReward
	
	profile = context["profile"]
	for m in results["done"]:
		if m.rewards is not None :  
			for r in m.rewards :
				if isinstance( r, TemporaryMissionReward):
					profile.temporary_rewards.append_reward ( m, "rewards", r )
				
				r.affect_reward( context )
	
	for m in results["failed"]:
		if m.failure_rewards is not None : 
			for r in m.failure_rewards :
				if isinstance( r, TemporaryMissionReward):
					profile.temporary_rewards.append_reward ( m, "failure_rewards", r )
				r.affect_reward( context )

def default_mission_response_processor( request, response, response_data ):
	"""Handle the process of notifying the missions changes in the view response. A
	token can be inserted in your template and then replace it by the concret notification
	when changes occurs.
	"""
	response.response.content = response.response.content.replace( msettings.MISSION_NOTIFICATION_TOKEN, str( response_data ) )

def default_mission_context_processor( request ):
	"""Default context processor for the mission middleware checking context.
	A minimal context must contains a user and profile fields with respectively
	the target user and its associated MissionProfile.
	"""
	user = request.user
	profile = get_user_mission_profile( request )
	return {'user': user,  'profile':profile, 'request':request }

def activate_mission( request, mission ):
	"""Activate the specfied mission for the user making the request."""
	processor = get_definition_with_path( msettings.MISSION_CONTEXT_PROCESSOR )
	context = processor( request )
	profile = context["profile"]

	if mission in profile.missions_available : 
		profile.missions_available.pop( profile.missions_available.index( mission ) )
		profile.missions_active.append(mission)
		msettings.MISSION_MIDDLEWARE_INSTANCE.check_user_missions ( context )
	else : 
		raise ValueError(_("You cannot activate a mission which is not in the available missions list."))
