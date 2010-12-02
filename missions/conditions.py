# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from abe.missions import settings
from abe.utils import *

from datetime import *

import operator


class MissionConditionMetaClass(type):

	def to_python( cls, value):
		data = json.loads( value )
		return cls( **data )

class MissionCondition():
	"""
	The base class for all the conditions used by missions
	"""
	__metaclass__ = MissionConditionMetaClass
	
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
				)

	def __init__(self, triggers=['trigger'], hidden=False ):
		self.triggers = triggers
		self.hidden = hidden
	
	def get_prep_value(self):
		data = self.get_prep_value_args()
		cls =type(self)
		return "%s.%s%s" % ( cls.__dict__["__module__"], cls.__name__, json.dumps( data,  cls=DjangoJSONEncoder )  )

	def get_prep_value_args(self):
		return {'triggers' : self.triggers, 
					  'hidden':self.hidden}

	def check( self, profile, past_state, mission_data ):
		return {
						'fulfilled':False, 
						'reason':_(u"MissionCondition is a base class and is always unfulfilled. Extend it to create a real condition."),  
					}

	def to_type(self):
		t = {}
		for i in type(self).fields :
			t [ i [ 0 ] ] = i [ 1 ]
		
		t["type"] = get_classpath(type(self))
		return t
	
	def to_vo(self):
		return dict( { 'type':get_classpath( type(self) ) }, **self.get_prep_value_args() )

class NumericComparisonCondition(MissionCondition):
	"""
	A condition that checks two numerical values using a comparison operator
	"""
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
					('value', 'Number', ) ,
					('comparison', 'String[==|!=|<|<=|>|>=]', ) ,
				)
	def __init__(self, value=0, comparison="==", **kwargs):
		super( NumericComparisonCondition, self ).__init__( **kwargs )
		self.value = value
		self.comparison = comparison

	def get_test_value(self, profile):
		return 0

	def perform_comparison(self, a, b, comparison ):
		op = getattr ( settings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		return op( a, b )

	def check(self, profile, past_state, mission_data ):
		test_value = self.get_test_value( profile )
		res = self.perform_comparison( self.value, test_value, self.comparison )
		if not res : 
			return {
							'fulfilled':False, 
							'reason':_(u"The tested value %s don't validate the following expressions : %s %s %s") % (test_value, test_value, self.comparison, self.value ), 
							'user_value':str( test_value ), 
							'against_value':str( self.value), 
							'comparison':self.comparison, 
						}
		else:
			return {
							'fulfilled':True, 
							'user_value': str ( test_value ), 
							'against_value':str( self.value), 
							'comparison':self.comparison, 
						}

	def get_prep_value_args(self):
		return dict( super(NumericComparisonCondition, self).get_prep_value_args(), **{'value' : self.value, 
																															   'comparison':self.comparison})

class ItemInListCondition(MissionCondition):
	"""
	A condition that check that a specific item exist in a list
	"""
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
					('item', 'String', ) ,
				)
	def __init__(self, item=None, **kwargs ):
		super( ItemInListCondition, self ).__init__( **kwargs )
		self.item = item
		pass
	
	def check(self, profile, past_state, mission_data ):
		l = self.get_list( profile )
		fulfilled = self.item in l
		if fulfilled :
			return {
							'fulfilled':True, 
							'item':self.item, 
							'items_list':l,
						}
		else:
			return {
							'fulfilled':False, 
							'reason':_(u"The item '%s' can't be found in the list '%s'.") % ( self.item, l ), 
							'item':self.item, 
							'items_list':l,
						}
	
	def get_list(self, profile ):
		return []

	def get_prep_value_args(self):
		return dict( super(ItemInListCondition, self).get_prep_value_args(), **{'item' : self.item })


class TimeDeltaCondition(MissionCondition):
	"""
	A condition that check the time delta between an arbitrary date
	and the specified date using the specified operator.
	
	The comparison is performed such as : 
	
	self.get_date() + self.delta [comparison operator] self.date
	
	Where [comprison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	"""
	fields = (
					('triggers', 'Array', ),
					('hidden', 'Boolean', ),
					('delta', 'TimeDelta', ), 
					('date', 'Date', ), 
					('comparison', 'String[==|!=|<|<=|>|>=]', ) ,
				)
	
	def __init__(self, delta=timedelta(), data=date.today(), comparison="==", **kwargs ):
		self.delta = delta
		self.comparison = comparison
		self.date = date
	
	def ckeck( self, profile, past_state, mission_data ):
		op = getattr ( settings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		return op( self.get_date( profile, past_state, mission_data ) + self.delta, self.date )
	
	def get_date(self, profile, past_state, mission_data ):
		return date.today()
	
	def get_prep_value_args(self):
		return dict( super(DateCondition, self).get_prep_value_args(), **{
																												'delta' : self.delta, 
																												'comparison':self.comparison, 
																												'date':self.date 
																											})

class DateCondition(MissionCondition):
	"""
	A condition which is true only if an arbitrary date validate
	the comparison with the condition date.
	
	The comparison is performed such as : 
	
	self.get_date() [comparison operator] self.date
	
	Where [comprison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	"""
	fields = (
					('triggers', 'Array', ),
					('hidden', 'Boolean', ),
					('date', 'Date', ), 
					('comparison', 'String[==|!=|<|<=|>|>=]', ) ,
				)
	def __init__(self, date=date.today(), comparison="==", **kwargs ):
		self.date = date
		self.comparison = comparison

	def ckeck( self, profile, past_state, mission_data ):
		op = getattr ( settings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		return op( self.get_date( profile, past_state, mission_data ), self.date )
	
	def get_date(self, profile, past_state, mission_data ):
		return date.today()

	def get_prep_value_args(self):
		return dict( super(DateCondition, self).get_prep_value_args(), **{'date' : self.date, 'comparison':self.comparison})

class TrueCondition(MissionCondition):
	"""
	A fake condition which always return True.
	"""
	def check(self, profile, past_state, mission_data):
		return {
						'fulfilled':True, 
					}

class MissionsDoneCountCondition(NumericComparisonCondition):
	"""
	A condition that checks the number of missions done by a user.
	"""
	def get_test_value(self, profile ):
		return len(profile.missions_done)

class MissionRequiredCondition(ItemInListCondition):
	"""
	A condition which check if a specific mission have been completed
	by a user.
	"""
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
					('item', 'Mission', ) ,
				)

	def get_list(self, profile):
		return [ o.id for o in profile.missions_done ]

class MissionStartedSinceCondition(TimeDeltaCondition):
	"""
	A condition which is true if the start date of the mission that own this condition
	satisfy the delta constraint of this condition
	
	The comparison is performed such as : 
	
	mission_data.added + self.delta [comparison operator] self.date
	
	Where [comprison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	"""
	def get_date(self, profile, past_state, mission_data ):
		return datetime_from_string( mission_data.added )

