# -*- coding: utf-8 -*-
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from exceptions import *
from datetime import datetime

from abe.missions.conditions import *
from abe.missions.rewards import *
from abe.missions import utils as mutils
from abe.missions import settings as msettings
from abe.utils import *
from abe.types import *

import inspect
import operator

class MissionConditionList(list):
	def __init__(self, * args, **kwargs ):
		list.__init__( self, *args, **kwargs )
	
	def __contains__(self, o ):
		if isinstance( o, Mission ):
			for c in self : 
				if isinstance( c, MissionRequiredCondition ) and c.item == str(o.id) :
					return True
			return False
		
		elif isinstance( o, basestring ):
			for c in self : 
				if c.trigger == o :
					return True
			return False
		
		elif inspect.isclass( o ):
			for c in self : 
				if isinstance( c, o ):
					return True
			return False
			
		elif isinstance( o, MissionCondition ):
			return list.__contains__(self, o)

class MissionConditionsListField(models.Field):

	description = _(u"A list of MissionCondition objects.")

	__metaclass__ = models.SubfieldBase

	def __init__(self, *args, **kwargs) :
		super(MissionConditionsListField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "TextField"

	def to_python(self, value):
		if value == "":
			return None
		elif not isinstance( value, basestring ):
			return value
		
		condition_list = value.split( msettings.OBJECTS_LIST_SEPARATOR[:1] )
		return MissionConditionList([ self.get_condition( s ) for s in condition_list ])

	def get_prep_value(self, value):
		if value is None :
			return ""
		else:
			return msettings.OBJECTS_LIST_SEPARATOR[:1].join( [o.get_prep_value() for o in value] )

	def get_condition(self, value ):
		res = msettings.OBJECTS_TYPE_RE.search( value )
		cls = get_definition( res.group(3), res.group(2) )
		value = value.replace( res.group(0), "" )
		return cls.to_python( value )

class MissionRewardsListField(models.Field):

	description = _(u"A list of MissionReward objects.")

	__metaclass__ = models.SubfieldBase

	def __init__(self, *args, **kwargs) :
		super(MissionRewardsListField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "TextField"

	def to_python(self, value):
		if value == "":
			return None
		elif not isinstance( value, basestring ):
			return value
		
		rewards_list = value.split( msettings.OBJECTS_LIST_SEPARATOR[:1] )
		return [ self.get_reward( s ) for s in rewards_list ]

	def get_prep_value(self, value):
		if value is None :
			return ""
		else:
			print value
			return msettings.OBJECTS_LIST_SEPARATOR[:1].join( [o.get_prep_value() for o in value] )

	def get_reward(self,  value ):
		res = msettings.OBJECTS_TYPE_RE.search( value )
		cls = get_definition( res.group(3), res.group(2) )
		value = value.replace( res.group(0), "" )
		return cls.to_python( value )

class Mission(models.Model):
	""" A mission is defined by several elements : 
	pre_conditions -- A list of conditions needed to allow the user to have access to this mission.
	conditions -- A list of conditions the user have to fulfill to complete this mission.
	validity_conditions -- A list of conditions that make the mission unavailable to the user when fulfilled.
	rewards -- A list of MissionReward objects that the user will gain after having completed this mission.
	enabled -- A boolean value indicate whether this mission is enabled or not. An inactive mission is not registerered by the MissionMiddleware instance.
	"""
	
	name = models.CharField(_(u"Name"),  max_length=50,  
											help_text=_(u"The name of the mission is used as a default representation for the mission. "
																u"For a more detailled way to describe a mission use a custom MissionDescriptor model."))
	
	enabled = models.BooleanField(_(u"Enabled"), default=False, blank=True,
													 help_text=_(u"An enabled mission is a mission that is available for users.") )
	
	auto_activate = models.BooleanField(_(u"Auto Activate"), default=False, blank=True,
																help_text=_(	u"An auto activable mission will automatically move from the "
																					u"elligibles missions to the actives mission without needing "
																					u"the user to activate it."))
	
	pre_conditions = MissionConditionsListField( _(u"Access Conditions"), blank=True, default="", 
																		help_text=_(u"A list of conditions the user have "
																							u"to fulfill to get access to this mission") )

	conditions = MissionConditionsListField( _(u"Fulfillment Conditions"), blank=True, default="", 
																 help_text=_(u"A list of conditions the user have to fulfill "
																					u"to complete this mission and get the rewards."))

	validity_conditions = MissionConditionsListField(_(u"Validity Conditions"),  blank=True,  default="", 
																			 help_text=_(u"A list of conditions which made the mission "
																								u"unavailable to a user if fulfilled. "
																								u"You can use these conditions in order to build "
																								u"temporary missions, like a mission which can be "
																								u"only fulfilled on a specific date."))

	rewards = MissionRewardsListField(_(u"Completion Rewards"), blank=True, default="", 
														  help_text=_(u"A list of rewards the user gets when he complete the mission."))
	
	failure_rewards = MissionRewardsListField(_(u"Failure Rewards"), blank=True, default="", 
														  help_text=_(u"A list of rewards the user gets when he fail to complete the mission. "
																			 u"The mission is considered as failed when the validity conditions come true "
																			 u"for an active mission."))
	
	help_text=_(u"A Mission object is defined by a set of conditions and rewards.")
	fields = (
					('name', 'String'), 
					('enabled', 'Boolean'),
					('auto_activate', 'Boolean'), 
					('pre_conditions', 'Array<abe.missions.conditions.MissionCondition>', 'ConditionArray'), 
					('conditions', 'Array<abe.missions.conditions.MissionCondition>', 'ConditionArray'), 
					('validity_conditions', 'Array<abe.missions.conditions.MissionCondition>', 'ConditionArray'), 
					('rewards', 'Array<abe.missions.rewards.MissionReward>', 'RewardArray'), 
					('failure_rewards', 'Array<abe.missions.rewards.MissionReward>', 'RewardArray'), 
				)
	
	def __init__(self, *args, **kwargs ):
		super(Mission, self ).__init__(*args, **kwargs)
		self.descriptor = None

	def check_availability(self, context, past_states = None ):
		return mutils.check_conditions( context, self.pre_conditions, past_states )

	def check_completion(self, context, past_states = None ):
		return mutils.check_conditions( context, self.conditions, past_states, )

	def check_validity(self, context, past_states = None ):
		return mutils.check_conditions( context, self.validity_conditions, past_states, )

	def __str__(self):
		return "<Mission: %s>" % self.name

	def __unicode__(self):
		return u"%s" % self.name
	
	@classmethod
	def to_type( cls ):
		struct = {}
		form_struct = {}
		l = cls.fields
		
		for i in l :
			struct [ i [ 0 ] ] = i [ 1 ]
			if len( i ) == 3 : 
				form_struct [ i [ 0 ] ] = i [ 2 ]
			else : 
				form_struct [ i [ 0 ] ] = i [ 1 ]

		return Type( 	type=get_classpath( cls ), 
								struct=struct, 
								form_struct=form_struct, 
								help_text=cls.help_text
							)

	def to_vo(self):
		return TypeInstance( type( self ).to_type(),  
										{
											'name':self.name , 
											'pre_conditions':[ o.to_vo() for o in self.pre_conditions ] if self.pre_conditions is not None else [],
											'conditions':[ o.to_vo() for o in self.conditions ] if self.conditions is not None else [],
											'validity_conditions':[ o.to_vo() for o in self.validity_conditions ] if self.validity_conditions is not None else [],
											'rewards':[ o.to_vo() for o in self.rewards ] if self.rewards is not None else [],
											'failure_rewards':[ o.to_vo() for o in self.failure_rewards ] if self.failure_rewards is not None else [],
											'enabled':self.enabled, 
											'auto_activate':self.auto_activate, 
										},
										self.id )
	
	def get_descriptor(self):
		if self.descriptor is None : 
			cls_path = msettings.MISSION_DESCRIPTOR_CLASS
			if cls_path is not None :
				try:
					cls = get_definition_with_path( cls_path )
					res = cls.objects.get( mission=self.id )
					if res is None : 
						self.descriptor = {}
					else : 
						self.descriptor = res
				except:
					self.descriptor = {}
			else:
				self.descriptor = {}
			
		return self.descriptor
	
	def get_condition_descriptor(self, condition):
		
		if self.descriptor is not None and "conditions" in self.descriptor : 
			if condition in self.descriptor["conditions"]:
				return self.descriptor["conditions"][condition]
		
		return condition.get_descriptor()

class MissionDescriptor(models.Model):
	mission = models.IntegerField( _(u"Mission") )
	description = models.TextField(_(u"Mission Description"), 
													blank=True, 
													default="", 
													help_text=_(u"The description the user will see about the corresponding mission, "
																	   u"the description should include a briefing about what the user can "
																	   u"do to fulfill the mission using the gameplay terminology."))
	
	help_text=_(u"A MissionDescriptor instance is associated with a Mission object and provide site specific informations for this object.")
	fields = (
					('description', 'String', 'text'), 
					('mission', 'String'), 
				)
	
	@classmethod
	def to_type( cls ):
		struct = {}
		form_struct = {}
		l = cls.fields
		for i in l :
			struct [ i [ 0 ] ] = i [ 1 ]
			if len( i ) == 3 : 
				form_struct [ i [ 0 ] ] = i [ 2 ]
			else : 
				form_struct [ i [ 0 ] ] = i [ 1 ]

		return Type( 	type=get_classpath( cls ), 
								struct=struct, 
								form_struct=form_struct, 
								help_text=cls.help_text
							)

	def to_vo(self):
		return TypeInstance( type(self).to_type(),  
										{
											'mission':str(self.mission), 
											'description':self.description, 
										}, 
										self.id)

class MissionList(list):
	def __init__(self, * args, **kwargs ):
		list.__init__( self, *args, **kwargs )
		self.missions_data = {}
		self.init_missions_data()

	def __setitem__(self, key, value):
		if key >= self.__len__() or key < 0 :
			raise IndexError(_(u"Index out of bounds : %s in range 0-%s") % ( key, self.__len__() - 1 ) )

		self.check_value( value )
		res = list.__setitem__( self, key, value )
		self.register_mission_data( value )
		return res

	def append(self, value ):
		self.check_value( value )
		
		res = list.append(self,  value )
		self.register_mission_data( value )
		return res

	def pop(self, n = -1 ):
		res = list.pop( self, n )
		self.unregister_mission_data( res )
		return res

	def check_value(self, value ):
		if not isinstance( value, Mission ):
			raise TypeError(_(u"The value %s of type %s must be a Mission instance.") % ( value,  type(value) ) )
		elif value in self:
			raise ValueError(_(u"The value %s is already stored in this MissionList object.") % value )

	def register_mission_data(self, mission, data=None ):
		self.missions_data[ mission ] = data if data is not None else {'added':datetime.now(),  'fulfilled' : False }

	def unregister_mission_data(self, mission ):
		del self.missions_data[ mission ]

	def init_missions_data(self):
		for m in self:
			self.register_mission_data( m )

	def reset_missions_data(self):
		self.init_missions_data()

	def get_mission_data(self, mission, data = None ):
		if data is None : 
			return self.missions_data[ mission ]
		else:
			return getattr( self.missions_data[ mission ], str(data), None )

	def set_mission_data(self, mission, value, data = None ):
		if data is None :
			for k, v in value.items() : 
				self.missions_data[ mission ][ k ] = v
		else :
			self.missions_data[ mission ][ data ] = value

	def __str__(self):
		return "<MissionList: %s>" % list.__str__(self)

class MissionsListField( models.Field):
	description = _(u"A list of MissionList objects with data associated with them.")

	__metaclass__ = models.SubfieldBase

	def get_internal_type(self):
		return "TextField"

	def to_python(self, value):
		if value == "":
			return MissionList()
		elif not isinstance( value, basestring ):
			return value
		
		missions_list = value.split( msettings.OBJECTS_LIST_SEPARATOR[:1] )

		l = MissionList()
		for s in missions_list :
			mission_id = msettings.OBJECTS_TYPE_RE.search(s).group(0)
			m = self.get_mission( mission_id ) 
			s = s.replace( mission_id, "", 1)
			data = json.loads(s)
			l.append( m )
			l.register_mission_data( m, data )
		return l

	def get_prep_value(self, value):
		if value is None :
			return ""
		return msettings.OBJECTS_LIST_SEPARATOR[:1].join( [ self.get_string( o, value ) for o in value] )

	def get_string(self, o, missions ):
		return "%s%s" % ( str( o.id ), json.dumps( missions.get_mission_data( o ),  cls=DjangoJSONEncoder ) )

	def get_mission( self, value ):
		return msettings.MISSION_MIDDLEWARE_INSTANCE.missions_map[ value ]

class TempMissionRewardsList(list):
	"""A list which contains temporary mission's rewards.
	
	Each entry is in fact a tuple with with for indices : 
		0 -- the mission containing the reward
		1 -- the property of the mission that contains the reward
		2 -- the reward object
	
	# Create a mission and its rewards
	>>> mission = Mission(id=1,name="A mission")
	>>> tmp_reward = TemporaryMissionReward()
	>>> mission.rewards = [ tmp_reward, MissionReward() ]
	
	# Create the list 
	>>> tmp_rewards = TempMissionRewardsList()
	>>> tmp_rewards.append_reward( mission, "rewards", mission.rewards[0] )
	
	# Performs tests
	>>> tmp_rewards[0][2] == tmp_reward
	True
	>>> tmp_rewards[0][0] == mission
	True
	
	"""
	def append_reward(self, mission, property, reward ):
		self.append( ( mission,  property, reward, ) )

	def __str__(self):
		return "<TempMissionRewardsList: %s>" % list.__str__(self)

class TempMissionRewardsListField( models.Field):
	""" A model's Field that handle TempMissionRewardsList objects and serialize/deserialize it
	according to the model's fields behavior.
	
	# Create a test middleware
	>>> from abe.missions.middleware import MissionMiddleware
	>>> msettings.MISSION_MIDDLEWARE_INSTANCE = MissionMiddleware()
	
	# Create a mission and its rewards
	>>> mission = Mission(id=1,name="A mission")
	>>> msettings.MISSION_MIDDLEWARE_INSTANCE.missions_map[ mission.id ] = mission
	>>> tmp_reward = TemporaryMissionReward()
	>>> mission.rewards = [ tmp_reward, MissionReward() ]
	
	# Create the list 
	>>> tmp_rewards = TempMissionRewardsList()
	>>> tmp_rewards.append_reward( mission, "rewards", mission.rewards[0] )
	
	# Create the field 
	>>> field= TempMissionRewardsListField()
	
	# Testing serialization
	>>> str = field.get_prep_value( tmp_rewards )
	>>> str
	'1:rewards:0'
	
	# Testing deserialization
	>>> nl = field.to_python( str )
	>>> tuple = nl[0]
	>>> tuple[0] == mission
	True
	>>> tuple[1]
	'rewards'
	>>> tuple[2] == tmp_reward
	True
	
	"""
	description = _(u"A list of TemporaryMissionReward objects.")

	__metaclass__ = models.SubfieldBase

	def get_internal_type(self):
		return "TextField"

	def to_python(self, value):
		if value == "":
			return TempMissionRewardsList()
		elif not isinstance( value, basestring ):
			return value
		
		missions_list = value.split( msettings.OBJECTS_LIST_SEPARATOR[:1] )
		l = TempMissionRewardsList()
		for s in missions_list :
			a = s.split(":")
			mission_id = a[0]
			property = a[1]
			condition_index = int(a[2])
			m = self.get_mission( mission_id ) 
			
			l.append_reward( m, property, getattr( m, property ) [ condition_index ] )
		return l

	def get_prep_value(self, value):
		if value is None :
			return ""
		return msettings.OBJECTS_LIST_SEPARATOR[:1].join( [ self.get_string( o ) for o in value] )

	def get_string(self, rewards ):
		m = rewards[0]
		p = rewards[1]
		c = rewards[2]
		return "%s:%s:%s" % ( m.id, p, getattr ( m, p ).index( c ) ) 

	def get_mission( self, value ):
		return msettings.MISSION_MIDDLEWARE_INSTANCE.missions_map[ value ]

class MissionProfile(models.Model):
	# the related user
	user = models.ForeignKey( "auth.User", 
											  related_name="mission_profile_user", 
											  verbose_name=_(u"Related User"), 
											  help_text=_(u"The user related to this profile.") )
	# missions completed by the user
	missions_done = MissionsListField(_(u"Missions Done"), 
													  help_text=_(u"A list of the missions completed by the user."), 
													  default="" )
	# missions activated by the user but not yet completed
	missions_active = MissionsListField(_(u"Active Missions"), 
													  help_text=_(u"A list of the active missions of the user."), 
													  default="")
	# missions available to the user
	missions_available = MissionsListField(_(u"Missions Available"), 
													  help_text=_(u"A list of the missions available for the user but not yet activated."), 
													  default="")
	# missions tested by the middleware to detect when they become available
	missions_elligible = MissionsListField(_(u"Missions elligible"), 
													  help_text=_(u"A list of the missions that are not available to the user "
																		 u"but should become available soon."), 
													  default="")
	# rewards that don't last ever are stored here until they end
	temporary_rewards = TempMissionRewardsListField(_(u"Temporary Rewards"), 
													  help_text=_(u"All the temporary rewards gained by the user."), 
													  default="")

	def __unicode__(self):
		return u"%s" % self.user.username
