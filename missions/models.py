# -*- coding: utf-8 -*-
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from exceptions import *
from datetime import datetime

from abe.missions.conditions import *
from abe.missions.rewards import *
from abe.missions import settings as msettings
from abe.utils import get_class
from abe.utils import get_classpath

import inspect
import operator

class MissionConditionList(list):
	def __init__(self, * args, **kwargs ):
		list.__init__( self, *args, **kwargs )
	
	def __contains__(self, o ):
		if isinstance( o, Mission ):
			for c in self : 
				if isinstance( c, MissionRequiredCondition ) and c.item == o.id :
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
		cls = get_class( res.group(3), res.group(2) )
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
			return msettings.OBJECTS_LIST_SEPARATOR[:1].join( [o.get_prep_value() for o in value] )

	def get_condition(self,  value ):
		res = msettings.OBJECTS_TYPE_RE.search( value )
		cls = get_class( res.group(3), res.group(2) )
		value = value.replace( res.group(0), "" )
		return cls.to_python( value )

class Mission(models.Model):
	name = models.CharField(_(u"Name"),  max_length=50)
	active = models.BooleanField(_(u"Active"), default=False )

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

	rewards = MissionRewardsListField(_(u"Mission Rewards"), blank=True, default="", 
														  help_text=_(u"A list of rewards the user gets "
																			 u"when he complete the mission."))

	def __init__(self, *args, **kwargs ):
		super(Mission, self ).__init__(*args, **kwargs)
		self.descriptor = None

	def check_availability(self, context, past_states = None ):
		return self.check_conditions( context, self.pre_conditions, past_states )

	def check_completion(self, context, past_states = None ):
		return self.check_conditions( context, self.conditions, past_states, )

	def check_validity(self, context, past_states = None ):
		return self.check_conditions( context, self.validity_conditions, past_states, )

	def check_conditions(self, context, conditions, past_states = None ) :
		if conditions is None or len( conditions ) == 0 : 
			return {'fulfilled':True}

		fulfilled = 0
		datas = {}
		for i, condition in enumerate( conditions ) : 
			past_state = getattr( past_states, str(i), None )
			if past_state is not None : 
				if 'triggers' in context and not some_in_list( context["triggers"] , condition.triggers ): 
					data = past_state
				else:
					data = self.check_condition( context, condition, past_state, past_states )
			else:
				data = self.check_condition( context, condition, past_state, past_states )
			
			datas[ str(i) ] = data
			if getattr( data, 'fulfilled', False ):
				fulfilled += 1
		
		if fulfilled == len(conditions) :
			datas["fulfilled"] = True
		else:
			datas["fulfilled"] = False
		
		return datas

	def check_condition( self, context, condition, past_state, mission_data ):
		return condition.check( context, past_state, mission_data )

	def __str__(self):
		return "<Mission: %s>" % self.name

	def __unicode__(self):
		return u"%s" % self.name
	
	def to_vo(self):
		return {
						'name':self.name , 
						'pre_conditions':[ o.to_vo() for o in self.pre_conditions ] if self.pre_conditions is not None else [],
						'conditions':[ o.to_vo() for o in self.conditions ] if self.conditions is not None else [],
						'validity_conditions':[ o.to_vo() for o in self.validity_conditions ] if self.validity_conditions is not None else [],
						'rewards':[ o.to_vo() for o in self.rewards ] if self.rewards is not None else [],
					}
	
	def get_descriptor(self):
		if self.descriptor is None : 
			cls_path = msettings.MISSION_DESCRIPTOR_CLASS
			if cls_path is not None :
				try:
					cls = get_class_with_path( cls_path )
					res = cls.objects.get( mission__id=self.id )
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
	mission = models.ForeignKey( Mission, verbose_name=_(u"Mission"), related_name="mission_descriptor_mission")
	description = models.TextField(_(u"Mission Description"), 
													blank=True, 
													default="", 
													help_text=_(u"The description the user will see about the corresponding mission, "
																	   u"the description should include a briefing about what the user can "
																	   u"do to fulfill the mission using the gameplay terminology."))
	
	fields = (
					('description', 'String'), 
					('mission', 'Mission'), 
				)
	
	def to_type(self):
		t = {}
		for i in type(self).fields :
			t [ i [ 0 ] ] = i [ 1 ]
		
		t["type"] = get_classpath(type(self))
		return t

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
	description = _(u"A list of MissionReward objects.")

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
		return msettings.MISSION_MIDDLEWARE_INSTANCE.missions_map[ int(value) ]

class MissionProfile(models.Model):
	# l'utilisateur cible
	user = models.ForeignKey( "auth.User", 
											  related_name="mission_profile_user", 
											  verbose_name=_(u"Related User"), 
											  help_text=_(u"The user related to this profile.") )
	# les missions terminées par le joueur
	missions_done = MissionsListField(_(u"Missions Done"), 
													  help_text=_(u"A list of the missions completed by the user."), 
													  default="" )
	# les missions en cours du joueurs
	missions_active = MissionsListField(_(u"Active Missions"), 
													  help_text=_(u"A list of the active missions of the user."), 
													  default="")
	# les missions accessible au joueur mais non entamées
	missions_available = MissionsListField(_(u"Missions Available"), 
													  help_text=_(u"A list of the missions available for the user but not yet activated."), 
													  default="")
	# les missions pouvant devenir accessible au joueur 
	missions_elligible = MissionsListField(_(u"Missions elligible"), 
													  help_text=_(u"A list of the missions that are not available to the user "
																		 u"but should become available soon."), 
													  default="")

	def __unicode__(self):
		return u"%s" % self.user.username
