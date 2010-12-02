# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from abe.utils import get_classpath

class MissionRewardMetaClass(type):

	def to_python( cls, value):
		data = json.loads( value )
		return cls( **data )

class MissionReward ():
	__metaclass__ = MissionRewardMetaClass
	
	fields = ()
	
	def __init(self):
		pass

	def get_prep_value(self):
		data = self.get_prep_value_args()
		cls =type(self)
		return "%s.%s%s" % ( cls.__dict__["__module__"], cls.__name__, json.dumps( data,  cls=DjangoJSONEncoder )  )

	def get_prep_value_args(self):
		return  {}

	def to_vo(self):
		return dict( { 'type':get_classpath( type(self) ) }, **self.get_prep_value_args() )

	def to_type(self):
		t = {}
		for i in type(self).fields :
			t [ i [ 0 ] ] = i [ 1 ]
		
		t["type"] = get_classpath(type(self))
		return t
	
	def to_vo(self):
		return dict( { 'type':get_classpath( type(self) ) }, **self.get_prep_value_args() )
