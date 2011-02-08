# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from abe.utils import get_classpath
from abe.missions import utils as mutils
from abe.types import *

class MissionRewardMetaClass(type):

	def to_python( cls, value):
		data = json_loads( value )
		return cls( **data )

class MissionReward ():
	__metaclass__ = MissionRewardMetaClass
	
	help_text=_("MissionReward is a base reward that does nothing.")
	fields = ()

	def get_prep_value(self):
		data = self.get_prep_value_args()
		cls =type(self)
		return "%s.%s%s" % ( cls.__dict__["__module__"], cls.__name__, json_dumps( data )  )

	def get_prep_value_args(self):
		return {}

	def affect_reward( self, context ): 
		print "reward affected"

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

		return Type(	type=get_classpath( cls ), 
								struct=struct, 
								form_struct=form_struct, 
								help_text=cls.help_text,
								parent_type="abe.missions.rewards.MissionReward",
							)
	
	def to_vo(self):
		return TypeInstance( type(self).to_type(), self.get_prep_value_args() )

class TemporaryMissionReward( MissionReward ):
	help_text=_("MissionReward is a base reward that does nothing.")
	fields = MissionReward.fields +(
						('conditions', 'Array<abe.missions.conditions.MissionCondition>', 'ConditionArray'), 
				)

	def __init__(self, conditions=None ):
		super( TemporaryMissionReward, self ).__init__()
		self.conditions = conditions
	
	def remove_reward( self, context ): 
		print "reward removed"
		
	def check_reward_conditions(self, context ):
		return mutils.check_conditions( context, self.conditions )
	
	def get_prep_value_args(self):
		return dict( super( TemporaryMissionReward, self ).get_prep_value_args(),  **{
																																	'conditions':[ o for o in self.conditions ] if self.conditions is not None else [],
																																} )
	
	def get_vo_data(self):
		return dict( super( TemporaryMissionReward, self ).get_prep_value_args(),  **{
																																	'conditions':[ o.to_vo() for o in self.conditions ] if self.conditions is not None else [],
																																} )
	
	def to_vo(self):
		return TypeInstance( type(self).to_type(), self.get_vo_data() )
