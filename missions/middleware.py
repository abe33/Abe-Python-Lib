# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.contrib.auth.models import User

from abe.missions.models import *
from abe.missions.settings import *
from abe.missions import settings

class MissionTriggerResponse( HttpResponse ):
	def __init__(self, response, triggers,  userID, *args, **kwargs):
		super(MissionTriggerResponse, self).__init__(*args,  **kwargs)
		self.response = response
		self.triggers = triggers
		self.userID = userID

class MissionMiddleware():

	def __init__(self):
		# setup the instance holder
		settings.MISSION_MIDDLEWARE_INSTANCE= self
		
		self.missions_map = {}
		self.update_missions_map()
		
		# HERE COMES THE TESTS
		mission = Mission( "Some tricky mission" )
		mission.id = "16"
		mission.pre_conditions = ( MissionCondition("trigger#1"), MissionCondition("trigger#2"), )
		mission.conditions =  ( MissionCondition("trigger#1"), MissionCondition("trigger#2"), )
		self.missions_map[ mission.id ] = mission
		
		l = MissionList([mission, ])
		print l
		print l[0]
		m = Mission("A really simple mission")
		m.id = "2"
		m.pre_conditions = MissionList()
		m.conditions =  ( MissionCondition("trigger#1"), MissionCondition("trigger#2"), )
		self.missions_map[ m.id ] = m
		l.append(m)
		print l
		print mission in l
		l.set_mission_data( mission, mission.pre_conditions[0].trigger, 12)
		print l.get_mission_data( mission )
		
		field = MissionsListField()
		s = field.get_prep_value( l )
		print s
		o = field.to_python( s )
		print o	
		print o.get_mission_data( o[0] )
		print o[0] == mission
		
		pass

	def update_missions_map(self):
		map = {}
		missions = Mission.objects.all()
		
		for mission in missions:
			map[ str ( mission.id ) ] = mission
		
		self.missions_map = map

	def process_request( self, request):
		return None

	def process_view( self, request, view_func, view_args, view_kwargs):
		return None

	def process_response( self, request, response):
		if not isinstance( response, MissionTriggerResponse):
			response.content = response.content.replace( settings.MISSION_NOTIFICATION_TOKEN, "")
			return response
		
		try :
			profile = MissionProfile.objects.get(user__id=response.userID) 
		except :
			profile = MissionProfile()
			profile.user = User.objects.get(id=response.userID)
			profile.save()
		
		#TODO : 
		if profile.missions_available is None or len( profile.missions_available  )== 0 :
			profile.missions_available = MissionList([self.missions_map["2"] ] )
		if profile.missions_active is None : 
			profile.missions_active	= MissionList()
		
		unfulfilled_data = [ o.check_availability( profile ) for o in profile.missions_available ]
		
		n = 0
		for res in unfulfilled_data : 
			if res is None : 
				m = profile.missions_available.pop( n )
				profile.missions_active.append( m )
				profile.missions_active
			else:
				m = profile.missions_available[n]
				msg = res.reason
				for r in res :
					condition = m.conditions[n]
					if r is None : 
						profile.missions_available.set_mission_data( m, condition.trigger, True )
					else:
						profile.missions_available.set_mission_data( m, condition.trigger, False )
			
			n+=1
		
		profile.save()
		
		#TODO : Handling injection of rewards and missions notifications
		response.response.content = response.response.content.replace( settings.MISSION_NOTIFICATION_TOKEN, str( unfulfilled_data ) )
		return response.response

	def process_exception( self, request, exception):
		print "process exception"
		return None
