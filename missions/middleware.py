# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.contrib.auth.models import User

from abe.missions.models import *
from abe.missions.conditions import *
from abe.missions.rewards import *

from abe.missions import settings as msettings

from abe.utils import *
from datetime import *

import pprint
pp = pprint.PrettyPrinter(indent=4)

def is_valid_minimal_context( context ):
	if "profile" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'profile'. The profile is mandatory") )
	if "user" not in context :
		raise KeyError( _(u"The provided context don't have any entry with the key 'user'. The user is mandatory") )

class MissionTriggerResponse( HttpResponse ):
	def __init__(self, response, context, *args, **kwargs):
		super(MissionTriggerResponse, self).__init__(*args,  **kwargs)
		self.response = response
		
		is_valid_minimal_context( context )
		
		self.context = context

class MissionMiddleware():

	def __init__(self):
		# setup the instance holder
		msettings.MISSION_MIDDLEWARE_INSTANCE= self
		self.missions_map = {}
		self.update_missions_map()
		
#		d = date.today()
#		print d
#		s = str(d)
#		n = date_from_string(s)
#		print n
#		print n==d
#		n = datetime.now()
#		s = str(n)
#		print s
#		d= datetime_from_string(s)
#		print d
#		print n == d
#		d =  timedelta(1, 1)
#		print d
#		s = str(d)
#		n = timedelta_from_string(s)
#		print n
#		print n == d
#		d1 = date(2010, 12, 12)
#		d2 = date(2012, 12, 12)
#		d3 = date(2013, 12, 12)
#		dl1 = d2 - d1
#		dl2 = d3 - d1
#		print dl1 < dl2
		
		# HERE COMES THE TESTS
		m1 = Mission( name="Mission#1")
		m1.id = 1
		m1.pre_conditions = MissionConditionList()
		self.missions_map[ m1.id ] = m1

		m2 = Mission( name="Mission#2")
		m2.id = 2
		m2.pre_conditions = MissionConditionList( [ MissionCondition(["trigger1"]), TrueCondition(["trigger2"])] )
		self.missions_map[ m2.id ] = m2

		m3 = Mission( name="Mission#3")
		m3.id = 3
		m3.conditions = MissionConditionList()
		self.missions_map[ m3.id ] = m3

		m4 = Mission( name="Mission#4" )
		m4.id = 4
		m4.conditions = MissionConditionList( [ 
																	 MissionCondition(["trigger1"]), 
																	 TrueCondition(["trigger2"]), 
																	 MissionRequiredCondition(triggers=["trigger3"], item=m3.id ), 
																	 NumericComparisonCondition(triggers=["trigger4"], value=4)
																	] )
		m4.validity_conditions = MissionConditionList( [ TimeBombCondition ( triggers=["trigger5"] ) ] )
		self.missions_map[ m4.id ] = m4
		
		m5 = Mission( name="Mission#5" )
		m5.id = 5
		m5.pre_conditions = MissionConditionList( [ MissionRequiredCondition(triggers=["trigger3"], item=m3.id ) ] )
		self.missions_map[ m5.id ] = m5

		self.default_missions_elligible_data = [ m1, m2 ]
		self.default_missions_available_data = []
		self.default_missions_active_data = [ m3, m4 ]
		
#		print m5.get_descriptor()
#		print m5.pre_conditions[0].get_descriptor()
#		
#		o = instance_from_type( { 'type':"abe.missions.conditions.MissionRequiredCondition", 
#													'item':1
#												 } )
#		print o
#		print o.item
		
#		o = instance_from_type( {'type':"abe.missions.conditions.TimeBombCondition"})
		
#		print some_in_list( ["foo", "oof"], ["foo", "pouet",  "tata",  "mama"] )
#		print some_in_list( ["foo"], ["oof", "pouet"] )
#		print some_in_list( ["foo", "oof"], ["foo"] )
#		print some_in_list( [ "foo", "oof" ], ["foo", "pouet",  "tata",  "mama", "oof" ] )

#		self.default_missions_elligible_data = []
#		self.default_missions_available_data = []
#		self.default_missions_active_data = []
#		
#		# testing custom contains query on MissionConditionList
#		print m3 in m4.conditions
#		print m3 in m2.pre_conditions
#		print "trigger3" in m4.conditions
#		print "trigger3" in m2.pre_conditions
#		print MissionCondition in m4.conditions
#		print MissionRequiredCondition in m2.pre_conditions
		
#		# testing conditions serialization
#		field = MissionConditionsListField()
#		s = field.get_prep_value( m4.conditions )
#		print s 
#		o = field.to_python( s )
#		print o
		pass

	def update_missions_map(self):
		map = {}
		missions = Mission.objects.all()
		
		for mission in missions:
			map[ str ( mission.id ) ] = mission
		
		self.missions_map = map

	def update_user_elligible_missions( self, profile, mission ):
		"""
		Update the missions_elligible list of the profile with missions which 
		require the specified mission as pre-condition.
		"""
		exclusion_list = profile.missions_elligible + profile.missions_available + profile.missions_active + profile.missions_done
		for k in self.missions_map : 
			m = self.missions_map[k]
			if m in exclusion_list :
				continue
			else:
				if mission in m.pre_conditions :
					profile.missions_elligible.append( m )

	def init_user_missions_profile(self, user):
		profile = MissionProfile()
		profile.user = user
#		profile.save()
		
		#HERE COMES THE TESTS
		if profile.missions_elligible is None or len( profile.missions_elligible ) == 0 :
			profile.missions_elligible = MissionList( self.default_missions_elligible_data)
		
		if profile.missions_available is None or len( profile.missions_available ) == 0 :
			profile.missions_available = MissionList( self.default_missions_available_data)
		
		if profile.missions_active is None  or len( profile.missions_active ) == 0: 
			profile.missions_active	= MissionList( self.default_missions_active_data )
		
		if profile.missions_done is None:
			profile.mission_done = MissionList()
		
		self.check_user_missions( { 'profile':profile, 'user':user } )
		return profile

	def check_user_missions(self, context ):
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
			if validity["fulfilled"] :
				to_pop.append( n )
				elligibles.append( m )
				response_data['deactivated'].append( m )
			else:
				data = m.check_completion( context, mission_data )
				
				#perform changes due to completed active missions
				# no list for the mission == no failed condition == success
				if data["fulfilled"] : 
					to_pop.append( n )
					dones.append( m )
					response_data['done'].append( m )
					self.update_user_elligible_missions( profile, m )
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

		#save 
#		profile.save()
		pp.pprint(response_data)
		return response_data

	def process_request( self, request):
		return None

	def process_view( self, request, view_func, view_args, view_kwargs):
		return None

	def process_response( self, request, response):
		if not isinstance( response, MissionTriggerResponse):
			response.content = response.content.replace( msettings.MISSION_NOTIFICATION_TOKEN, "")
			return response
		
		print response.context["triggers"]
		
		#HERE COMES THE CHECK
#		response_data = self.check_user_missions( profile )
		
#		field = MissionsListField()
#		print "missions elligibles"
#		print  field.get_prep_value( profile.missions_elligible )
#		
#		print "missions availables"
#		print  field.get_prep_value( profile.missions_available )
#		
#		print "missions actives"
#		print  field.get_prep_value( profile.missions_active )
#		
#		print "missions dones"
#		print  field.get_prep_value( profile.missions_done )
#		
#		s = field.get_prep_value( profile.missions_elligible )
#		o = field.to_python( s )
#		
#		print s
#		print o
#		print o.get_mission_data( o[1] )

		#TODO : Handling injection of rewards and missions notifications
		response.response.content = response.response.content.replace( msettings.MISSION_NOTIFICATION_TOKEN, str( "" ) )
		return response.response

	def process_exception( self, request, exception):
		print "process exception"
		return None
