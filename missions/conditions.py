# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from abe.missions import settings as msettings
from abe.utils import *

from datetime import *

import operator


class MissionConditionMetaClass(type):

	def to_python( cls, value):
		data = json.loads( value )
		return cls( **data )

class MissionCondition():
	"""The base class for all the conditions used by missions
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

	def check( self, context, past_state, mission_data ):
		return {
						'fulfilled':False, 
						'reason':_(u"MissionCondition is a base class and is always unfulfilled. Extend it to create a real condition."),  
					}

	def to_type(self):
		t = {}
		cls = type(self)
		l = cls.fields
		print l 
		for i in l :
			t [ i [ 0 ] ] = i [ 1 ]
		
		t["type"] = get_classpath(type(self))
		t["help"] = cls.__doc__
		return t
	
	def to_vo(self):
		return dict( { 'type':get_classpath( type(self) ) }, **self.get_prep_value_args() )

class NumericComparisonCondition(MissionCondition):
	"""A condition that checks two numerical values using a comparison operator
	
	The comparison is performed such as : 
	
	self.get_test_value() [comparison operator] self.value
	
	Where [comparison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	"""
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
					('value', 'Number', ) ,
					('comparison', 'String(==,!=,<,<=,>,>=)', ) ,
				)
	def __init__(self, value=0, comparison="==", **kwargs):
		super( NumericComparisonCondition, self ).__init__( **kwargs )
		self.value = value
		self.comparison = comparison

	def get_test_value(self, context, past_state, mission_data ):
		return 0

	def perform_comparison(self, a, b, comparison ):
		op = getattr ( msettings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		return op( a, b )

	def check(self, context, past_state, mission_data ):
		test_value = self.get_test_value( context, past_state, mission_data )
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
	"""A condition that check that a specific item exist in a list
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
	
	def check(self, context, past_state, mission_data ):
		l = self.get_list( context, past_state, mission_data )
		fulfilled = self.item in l
		if fulfilled :
			return {
							'fulfilled':True, 
							'item':str( self.item ), 
							'items_list': l,
						}
		else:
			return {
							'fulfilled':False, 
							'reason':_(u"The item '%s' can't be found in the list '%s'.") % ( self.item, l ), 
							'item':str( self.item ), 
							'items_list':l,
						}
	
	def get_list(self, context, past_state, mission_data ):
		return []

	def get_prep_value_args(self):
		return dict( super(ItemInListCondition, self).get_prep_value_args(), **{'item' : self.item })


class TimeDeltaCondition(MissionCondition):
	"""A condition that check the time delta between an arbitrary date
	and the specified date using the specified operator.
	
	The comparison is performed such as : 
	
	( self.get_test_date() - self.get_date() ) [comparison operator] self.delta
	
	Where [comparison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	And self.get_date() and self.get_test_date() return respectively : 
		- The date related to the user, like the date at which he start a mission, or the date he register to the website.
		- The date related to the condition mecanics like the current date, or the fixed date of a competition end.
	And self.delta is a timedelta object, meaning a distance between two dates.
	"""
	fields = (
					('triggers', 'Array', ),
					('hidden', 'Boolean', ),
					('delta', 'TimeDelta', ), 
					('comparison', 'String(==,!=,<,<=,>,>=)', ) ,
				)
	
	def __init__(self, delta=timedelta(), comparison="==", **kwargs ):
		self.delta = timedelta_from_string( delta )
		self.comparison = comparison
	
	def ckeck( self, context, past_state, mission_data ):
		op = getattr ( msettings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		d1 = self.get_date( context, past_state, mission_data )
		d2 = self.get_test_date( context, past_state, mission_data )
		delta = d2 - d1
		fulfilled = op( self.delta, delta )
		if fulfilled:
			return {
							'fulfilled':True, 
							'user_date':d1, 
							'condition_date':d2, 
							'user_delta':delta, 
							'condition_delta':self.delta,
						}
		else:
			return {
							'fulfilled':False, 
							'reason':_(u"The"), 
							'user_date':d1, 
							'condition_date':d2, 
							'user_delta':delta, 
							'condition_delta':self.delta,
						}
	
	def get_date(self, context, past_state, mission_data ):
		return date.today()
	
	def get_test_date(self, context, past_state, mission_data ):
		return date.today()
	
	def get_prep_value_args(self):
		return dict( super(DateCondition, self).get_prep_value_args(), **{
																												'delta' : self.delta, 
																												'comparison':self.comparison, 
																											})

class DateCondition(MissionCondition):
	"""A condition which is true only if an arbitrary date validate
	the comparison with the condition date.
	
	The comparison is performed such as : 
	
	self.get_date() [comparison operator] self.get_test_date()
	
	Where [comparison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	And self.get_date() and self.get_test_date() return respectively : 
		- The date related to the user, like the date at which he start a mission, or the date he register to the website.
		- The date related to the condition mecanics like the current date, or the fixed date of a competition end.
	
	For exemple, if you want to create a condition in which the condition is true until a fixed day in the future you can do : 
	
	class TimeBombCondition( conditions.DateCondition ):
		def __init__(self, date=date.today(), **kwargs ):
			super( TimeBombCondition, self ).__init__( **kwargs )
			self.date = date
		
		def get_test_date( profile, past_state, mission_data ):
			return self.date
		
		def get_date ( profile, past_state, mission_data ):
			return date.today()
	
	condition = TimeBombCondition( date( 2012, 12, 12 ), "<" )
	"""
	
	fields = (
					('triggers', 'Array', ),
					('hidden', 'Boolean', ),
					('date', 'Date', ), 
					('comparison', 'String(==,!=,<,<=,>,>=)', ) ,
				)
	def __init__(self, date=date.today(), comparison="==", **kwargs ):
		self.date = date_from_string( date )
		self.comparison = comparison

	def ckeck( self, context, past_state, mission_data ):
		op = getattr ( msettings.COMPARISON_OPERATORS_MAP, comparison, operator.eq )
		d1 = self.get_date(context, past_state, mission_data )
		d2 = self.get_test_date( context, past_state, mission_data )
		fulfilled = op( d1, d2 )
		if fulfilled :
			return {
							'fulfilled':True, 
							'condition_date':d2, 
							'user_date':d1, 
						}
	
	def get_date(self, context, past_state, mission_data ):
		return date.today()
	
	def get_test_date(self, context, past_state, mission_data ):
		return date.today()

	def get_prep_value_args(self):
		return dict( super(DateCondition, self).get_prep_value_args(), **{'date' : self.date, 'comparison':self.comparison})

class TrueCondition(MissionCondition):
	"""A fake condition which always return True.
	"""
	def check(self, context, past_state, mission_data):
		return {
						'fulfilled':True, 
					}

class MissionsDoneCountCondition(NumericComparisonCondition):
	"""A condition that checks the number of missions done by a user.
	
	The comparison is performed such as : 
	
	len( profile.missions_done ) [comparison operator] self.value
	
	Where [comparison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	
	For exemple, to fix a condition which become true when the user 
	have completed ten missions you can do : 
	
	c = MissionsDoneCountCondition( 10, ">=" )
	"""
	def get_test_value(self, context ):
		return len(context["profile"].missions_done)

class MissionRequiredCondition(ItemInListCondition):
	"""A condition which check if a specific mission have been completed
	by a user.
	
	Only the mission id is used in order to be able to store it in a json string.
	
	Exemple : 
	c = MissionRequiredCondition( 3 )
	"""
	fields = (
					('triggers', 'Array'),
					('hidden', 'Boolean'),
					('item', 'Mission', ) ,
				)

	def get_list(self, context, past_state, mission_data ):
		return [ o.id for o in context["profile"].missions_done ]

class MissionStartedSinceCondition(TimeDeltaCondition):
	"""A condition which is true if the start date of the mission that own this condition
	satisfy the delta constraint of this condition
	
	The comparison is performed such as : 
	
	( today - mission.added ) [comparison operator] self.delta
	
	Where [comparison operator] can be one of the following operator : 
	==, !=, >, >=, <, <=
	
	For exemple, to fix a condition which become true after two weeks after
	the mission activation you can do : 
	
	c = MissionStartedSinceCondition( timedelta(14), ">=" )
	"""
	def get_date(self, context, past_state, mission_data ):
		return datetime_from_string( mission_data.added )

