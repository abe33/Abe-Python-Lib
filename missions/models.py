# -*- coding: utf-8 -*-
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from exceptions import *

from abe.missions import settings

def get_class( name,  package="abe.missions.models" ):
	exec 'from %s import %s as class_alias' % ( package, name )
	return class_alias

class MissionMetaClass(type):

	def to_python(cls, value):
		data = json.loads( value )
		return cls( **data )

class MissionCondition():
	__metaclass__ = MissionMetaClass

	def __init__(self, trigger ):
		self.trigger = trigger
		self.unfulfilled_data = None

	def get_prep_value(self):
		data = self.get_prep_value_args()
		return "%s%s" % ( type(self).__name__, json.dumps( data,  cls=DjangoJSONEncoder )  )

	def get_prep_value_args(self):
		return {'trigger' : self.trigger }

	def is_fulfilled(self, profile ):
		self.unfulfilled_data = {'reason':_(u"MissionCondition is a base class, you'd rather subclass MissionCondition and implement your own conditions.")}
		return False
	
	def get_unfulfilled_data(self):
		return self.unfulfilled_data

class MissionReward ():
	__metaclass__ = MissionMetaClass
	def __init(self):
		pass

	def get_prep_value(self):
		data = self.get_prep_value_args()
		return "%s" % type(self).__name__

	def get_prep_value_args(self):
		return  {}

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
		
		condition_list = value.split( settings.OBJECTS_LIST_SEPARATOR[:1] )
		return [ self.get_condition( s ) for s in condition_list ]

	def get_prep_value(self, value):
		if value is None :
			return ""
		else:
			return settings.OBJECTS_LIST_SEPARATOR[:1].join( [o.get_prep_value() for o in value] )

	def get_condition(self,  value ):
		cls = get_class( settings.OBJECTS_TYPE_RE.search( value ).group(0) )
		return cls.to_python( cls,  value )

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
		
		rewards_list = value.split( settings.OBJECTS_LIST_SEPARATOR[:1] )
		return [ self.get_reward( s ) for s in rewards_list ]

	def get_prep_value(self, value):
		if value is None :
			return ""
		else:
			return settings.OBJECTS_LIST_SEPARATOR[:1].join( [o.get_prep_value() for o in value] )

	def get_condition(self,  value ):
		cls = get_class( settings.OBJECTS_TYPE_RE.search( value ).group(0) )
		return cls.to_python( cls,  value )

class Mission(models.Model):
	name = models.CharField(_(u"Name"),  max_length=50)

	pre_conditions = MissionConditionsListField( _(u"Access Conditions"), 
																		help_text=_(u"A list of conditions the user have "
																							u"to fulfill to get access to this mission") )

	conditions = MissionConditionsListField( _(u"Fulfillment Conditions"), 
																 help_text=_(u"A list of conditions the user have to fulfill "
																					u"to complete this mission and get the rewards."))

	rewards = MissionRewardsListField(_(u"Mission Rewards"), 
														  help_text=_(u"A list of rewards the user gets "
																			 u"when he complete the mission."))
	
	def __init__(self,  name="Untitled Mission" ):
		self.name = name
	
	def check_availability(self, profile ):
		return self.check_conditions( profile, self.pre_conditions )

	def check_completion(self, profile ):
		return self.check_conditions( profile, self.conditions )

	def check_conditions(self, profile, conditions ) :
		if conditions is None or len( conditions ) == 0 : 
			return None

		b = []
		datas = []
		for condition in conditions : 
			data = self.check_condition( profile, condition )
			datas.append( data )
			if data is not None :
				b.append( data )
		if len(b)==0:
			return None
		
		return datas

	def check_condition( self,  profile, condition ):
		if condition.is_fulfilled( profile ):
			return None
		else :
			return condition.get_unfulfilled_data ()

	def get_condition_by_trigger(self, conditions, trigger ):
		for condition in conditions : 
			if condition.trigger == trigger:
				return condition
		
		return None

	def __str__(self):
		return "<Mission: %s>" % self.name

	def __unicode__(self):
		return u"%s" % self.name

class MissionList(list):
	def __init__(self, * args, **kwargs ):
		list.__init__( self, *args, **kwargs )
		self.missions_data = {}
		self.init_missions_data()

	def __setitem__(self, key, value):
		print "set item %s, %s, %s" % (self, key, value)
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
	
	def check_value(self, value ):
		if not isinstance( value, Mission ):
			raise TypeError(_(u"The value %s of type %s must be a Mission instance.") % ( value,  type(value) ) )
		elif value in self:
			raise ValueError(_(u"The value %s is already stored in this MissionList object.") % value )
	
	def register_mission_data(self, mission, data=None ):
		self.missions_data[ mission ] = data if data is not None else {}
	
	def init_missions_data(self):
		for m in self:
			self.register_mission_data( m )
	
	def reset_missions_data(self):
		self.init_missions_data()
	
	def get_mission_data(self, mission ):
		return self.missions_data[ mission ]
	
	def set_mission_data(self, mission, data,  value ):
		
		self.missions_data[ mission ][ data ] = value

	def __str__(self):
		return "<MissionList: %s>" % list.__str__(self)

class MissionsListField(models.Field):
	description = _(u"A list of MissionReward objects.")

	__metaclass__ = models.SubfieldBase

	def get_internal_type(self):
		return "TextField"

	def to_python(self, value):
		if value == "":
			return MissionList()
		elif not isinstance( value, basestring ):
			return value
		
		missions_list = value.split( settings.OBJECTS_LIST_SEPARATOR[:1] )

		l = MissionList()
		for s in missions_list :
			mission_id = settings.OBJECTS_TYPE_RE.search(s).group(0)
			m = self.get_mission( mission_id ) 
			s = s.replace( mission_id, "")
			data = json.loads(s)
			l.append( m )
			l.register_mission_data( m, data )
		return l

	def get_prep_value(self, value):
		if value is None :
			return ""
		return settings.OBJECTS_LIST_SEPARATOR[:1].join( [ self.get_string( o, value ) for o in value] )

	def get_string(self, o, missions ):
		return "%s%s" % ( str( o.id ), json.dumps( missions.get_mission_data( o ),  cls=DjangoJSONEncoder ) )

	def get_mission( self, value ):
		return settings.MISSION_MIDDLEWARE_INSTANCE.missions_map[ value ]

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
