# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from abe.utils import get_classpath
from abe.types import *

class MissionRewardMetaClass(type):

	def to_python( cls, value):
		data = json.loads( value )
		return cls( **data )

class MissionReward ():
	__metaclass__ = MissionRewardMetaClass
	
	help_text=_("MissionReward is a base reward that does nothing.")
	fields = ()

	def get_prep_value(self):
		data = self.get_prep_value_args()
		cls =type(self)
		return "%s.%s%s" % ( cls.__dict__["__module__"], cls.__name__, json.dumps( data,  cls=DjangoJSONEncoder )  )

	def get_prep_value_args(self):
		return {}

	def affect_reward(self):
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
								help_text=cls.help_text
							)
	
	def to_vo(self):
		return TypeInstance( type(self).to_type(), self.get_prep_value_args() )
