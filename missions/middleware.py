# -*- coding: utf-8 -*-
from django.http import HttpResponse

from django.contrib.auth.models import User, AnonymousUser

from abe.missions import settings as msettings
from abe.utils import *
from abe.missions.models import *
from abe.missions.conditions import *
from abe.missions.rewards import *

from datetime import *

import pprint

pp = pprint.PrettyPrinter(indent=4)

def get_user_mission_profile( user ):
	try :
		profile = MissionProfile.objects.get(user=user) 
	except :
		profile = msettings.MISSION_MIDDLEWARE_INSTANCE.init_user_missions_profile( {'user':user } )
	return profile

def is_valid_minimal_context( context ):
	"""Verify that a context dict is wellformed and raise errors if it's not the case."""
	if "profile" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'profile'. The profile is mandatory") )
	elif "user" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'user'. The user is mandatory") )
	elif not isinstance( context["profile"], MissionProfile ) :
		raise ValueError( _(u"The provided profile is not an instance of the MissionProfile model.") )
	elif isinstance( context["user"],  AnonymousUser ):
		raise ValueError( _(u"The user in the context object must be a valid User, not an AnonymousUser.") )

def default_mission_results_processor( profile, results ):
	""" This function is used to handle the results of the missions check. By default 
	this function look for completed missions and then call the affect_reward on each
	rewards of each missions.
	"""
	for m in results["done"]:
		if m.rewards is not None :  
			for r in m.rewards :
				r.affect_reward()

def default_mission_response_processor( request, response, response_data ):
	"""Handle the process of notifying the missions changes in the view response. A
	token can be inserted in your template and then replace it by the concret notification
	when changes occurs.
	"""
	response.response.content = response.response.content.replace( msettings.MISSION_NOTIFICATION_TOKEN, str( response_data ) )

def default_mission_context_processor( user ):
	"""Default context processor for the mission middleware checking context.
	A minimal context must contains a user and profile fields with respectively
	the target user and its associated MissionProfile.
	"""
	profile = get_user_mission_profile( user )
	return {'user': user,  'profile':profile }

def activate_mission( user, mission ):
	processor = get_definition_with_path( msettings.MISSION_CONTEXT_PROCESSOR )
	context = processor( user )
	profile = context["profile"]

	if mission in profile.missions_available : 
		profile.missions_available.pop( profile.missions_available.index( mission ) )
		profile.missions_active.append(mission)
		msettings.MISSION_MIDDLEWARE_INSTANCE.check_user_missions ( context )
	else : 
		raise ValueError(_("You cannot activate a mission which is not in the available missions list."))
	pass

class MissionTriggerResponse( HttpResponse ):
	""" The MissionTriggerResponse is used as a wrapper for
	response from views decorated with the @mission_triggers
	decorator.
	The MissionTriggerResponse contains the normal view response
	and a context dict to use in the conditions check.
	"""
	def __init__(self, response, context, *args, **kwargs):
		super(MissionTriggerResponse, self).__init__(*args,  **kwargs)
		self.response = response
		
		is_valid_minimal_context( context )
		
		self.context = context

class MissionMiddleware():
	""" The MissionMiddleware class handle the per user checks for missions conditions.
	Active missions are retreived during the middleware initialization and then used to
	construct the default availables missions list.
	Missions and conditions are checked after the process of a view decorated with the
	@mission_triggers decorator. Only conditions with triggers matching the decorator
	arguments are checked after the view process. It ensure that there's no useless
	test during the check.
	
	The middleware instance is accessible using the abe.missions.settings.MISSION_MIDDLEWARE_INSTANCE
	property. It allow the AMF gateway services to update and work with the middleware.
	"""
	default_missions_elligible_data = []
	default_missions_available_data = []
	default_missions_active_data = []

	def __init__(self):
		# setup the instance holder
		self.default_missions_elligible_data = []
		self.default_missions_available_data = []
		self.default_missions_active_data = []
		
		msettings.MISSION_MIDDLEWARE_INSTANCE= self
		self.missions_map = {}
		self.update_missions_map()

	def update_missions_map(self):
		""" Update the missions list stored by the middleware. 
		The missions list contains only active missions.
		At the same time, the function construct the default
		available missions list which contains only missions without
		any preconditions of type MissionRequiredCondition.
		"""
		map = {}
		missions = Mission.objects.filter ( active=True)
		
		for mission in missions:
			map[ str ( mission.id ) ] = mission
		self.missions_map = map
		
		for k in self.missions_map : 
			m = self.missions_map[k]
			if m.pre_conditions is None or len( m.pre_conditions ) == 0 :
				self.default_missions_available_data.append( m )

	def update_user_elligible_missions( self, profile ):
		""" Update the missions_elligible list of the profile with missions which 
		require the specified mission as pre-condition.
		"""
		l = profile.missions_active + profile.missions_done
		exclusion_list = profile.missions_elligible + profile.missions_available + profile.missions_active + profile.missions_done
		
		for mission in l : 
			for k in self.missions_map : 
				m = self.missions_map[k]
				if m in exclusion_list :
					continue
				else:
					if mission in m.pre_conditions and m not in profile.missions_elligible :
						profile.missions_elligible.append( m )

	def init_user_missions_profile(self, ctx ):
		""" Create and initialize the profile for the user specified in ctx["user"].
		The different missions list stored by the profile are created during
		the call. 
		At the end of the call, a forced check is performed for the newly
		created profile in order to ensure that the profile is up to date
		after its creation.
		The created profile is retruned by the function at the end of the call
		"""
		profile = MissionProfile()
		profile.user = ctx["user"]
		profile.save()
		
		#HERE COMES THE TESTS
		if profile.missions_elligible is None or len( profile.missions_elligible ) == 0 :
			profile.missions_elligible = MissionList( self.default_missions_elligible_data)
		
		if profile.missions_available is None or len( profile.missions_available ) == 0 :
			profile.missions_available = MissionList( self.default_missions_available_data)
		
		if profile.missions_active is None  or len( profile.missions_active ) == 0: 
			profile.missions_active	= MissionList( self.default_missions_active_data )
		
		if profile.missions_done is None:
			profile.mission_done = MissionList()
		
		ctx["profile"] = profile

		self.check_user_missions( ctx )

		return profile

	def check_user_missions(self, context ):
		""" Performs the check of missions and conditions actually registered
		in the user  profile and return a dict object which contains the details of
		the changes that have occured due to this check.
		
		The context dict should contains any valuable datas that concret conditions
		may use in their check. 
		
		Keyword arguments : 
		context -- a dict object that contains the data used during the conditions checks.
		
		The context must contains at least the following items : 
		user -- the user for which perform the mission check
		profile -- the instance of the MissionProfile class associated with the user
			
		The context dict can contains another specific item : 
		triggers -- a list of string which represents the triggers concerned by this call
			
		If triggers is not defined in the context dict the check will not discriminate any missions nor conditions.
		
		At the end of the process, the profile and the results dict are passed to the MISSION_RESULTS_PROCESSOR.
		This processor is a simple function that take two arguments and should affect the rewards to the user.
		"""
		profile = context["profile"]
		
		elligibles = profile.missions_elligible
		availables = profile.missions_available
		actives = profile.missions_active
		dones = profile.missions_done
		response_data = {'available':[], 'elligible':[], 'active':[], 'done':[], 'deactivated':[] }

		#check active missions
		to_pop = []
		n = 0
		for m in actives :
			#first we check for the validity conditions of  the actives missions
			
			mission_data = actives.get_mission_data( m )
			validity = m.check_validity( context, mission_data )
#			print "checking validity of mission %s with data %s and results %s" % (m, str(mission_data), str(validity))
			if validity["fulfilled"] :
				to_pop.append( n )
				elligibles.append( m )
				response_data['deactivated'].append( m )
			else:
				data = m.check_completion( context, mission_data )
#				print data
				#perform changes due to completed active missions
				# no list for the mission == no failed condition == success
				if data["fulfilled"] : 
					to_pop.append( n )
					dones.append( m )
					response_data['done'].append( m )
				else:
					q = 0
					for k, r in data.items() :
						if k == 'fulfilled':
							q-=1
							continue
						
						condition = m.conditions[q]
						# no dict for the condition == success
						if r["fulfilled"] : 
							# already true, no change
							if getattr ( actives.get_mission_data( m, str(k) ), "fulfilled", False ) :
								continue

							response_data['active'].append( ( m, condition, data[k] ) )
						q+=1
					
					actives.set_mission_data( m, data )
			n+=1
		
		self.update_user_elligible_missions( profile )
		
		for n in to_pop :
			actives.pop( n )
		
		#check elligible missions 
		to_pop = []
		n = 0
		
		for m in availables :
			#we check for the validity conditions of  the available missions
			#an available mission can be deactivated as well
			mission_data = availables.get_mission_data( m )
			validity = m.check_validity( context, mission_data )
			
			if validity["fulfilled"] :
				to_pop.append( n )
				elligibles.append( m )
				response_data['deactivated'].append( m )
			n+=1
		
		for n in to_pop :
			availables.pop( n )
		
		#check elligible missions 
		to_pop = []
		n = 0
	
		for m in elligibles :
			data = m.check_availability( context, elligibles.get_mission_data( m ) )
#			print data
			
			#perform changes due to available elligible missions
			# no list for the mission == no failed condition == success
			if data["fulfilled"] : 
				to_pop.append( n )
				availables.append( m )
				response_data['available'].append( m )
			else:
				q = 0
				for k, r in data.items() :
					if k == 'fulfilled':
						q-=1
						continue
					
					condition = m.pre_conditions[q]
					# no dict for the condition == success
					if r is None: 
						if elligibles.get_mission_data( m, k ):
							continue
						
						response_data['elligible'].append( ( m, condition, data[k] ) )
					
					q+=1 
			elligibles.set_mission_data( m, data )
			n+=1
		
		for n in to_pop :
			elligibles.pop( n )
		#save 
		profile.save()
		
		print response_data
		
		processor = get_definition_with_path( msettings.MISSION_RESULTS_PROCESSOR )
		processor( profile, response_data )
		
		return response_data

	def process_request( self, request):
		return None

	def process_view( self, request, view_func, view_args, view_kwargs):
		return None

	def process_response( self, request, response):
		""" Perform the missions and conditions checks after a view response.
		The distinction between views that trigger a check and those who don't
		is made by testing the type of the response object. When the mission_triggers 
		decorator is set on a view function, the decorator wrap the view response
		in a MissionTriggerResponse object. This object contains the view response
		along with the context to use when testing missions and conditions.
		
		The response, the request and the missions data are passed to the 
		MISSION_RESPONSE_PROCESSOR. This processor is a simple function 
		which is in charge of handle the notification of the changes in the mission
		profile.
		"""
		if not isinstance( response, MissionTriggerResponse):
			response.content = response.content.replace( msettings.MISSION_NOTIFICATION_TOKEN, "")
			return response
		
		#HERE COMES THE CHECK
		response_data = self.check_user_missions( response.context )
		
		processor = get_definition_with_path( msettings.MISSION_RESPONSE_PROCESSOR )
		processor( request, response, response_data )

		return response.response

	def process_exception( self, request, exception):
		print "process exception"
		return None
